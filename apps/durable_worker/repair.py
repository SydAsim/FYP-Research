"""Discover and deliver outstanding repairs from PostgreSQL after process restart.

No client ACK is manufactured here. Publication is a durable deliverable; client
playback (or explicit human escalation) alone closes the obligation. The worker
never obtains simulator truth. Stable command IDs recover crashes at every stage.
"""

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import URLError
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from psycopg.types.json import Jsonb

from apps.api_controller.phase1_service import (
    DomainProblem,
    _connection,
    _event,
    _one,
    _workflow,
)
from apps.api_controller.phase3_claim_service import authorize, queue
from apps.api_controller.phase3_models import AuthorizeClaimRequest, PermitCommand, VerifyRequest
from apps.api_controller.phase3_verification_service import issue_verification
from apps.voice_worker.cascade import DeterministicToneTTS
from apps.voice_worker.offline_adapters import LocalEspeakTTS
from apps.voice_worker.scheduler import HttpControllerPort, VoiceScheduler
from packages.domain.phase3_verification import ClaimType
from packages.speech_policy.phase4 import repair_capable


def command(obligation: dict[str, Any], stage: str) -> UUID:
    return uuid5(
        NAMESPACE_URL, f"repair-v2:{obligation['id']}:{obligation['triggering_revision']}:{stage}"
    )


def discover(owner: str, workflow_id: UUID | None = None) -> dict[str, Any] | None:
    with _connection() as conn:
        candidate = _one(
            conn,
            "SELECT r.* FROM repair_obligations r JOIN workflows w ON w.id=r.workflow_id "
            "WHERE r.state IN ('OPEN','REPAIR_AUTHORIZED') "
            "AND (w.research_arm IS NULL OR w.research_arm='P2') "
            "AND (r.delivery_lease_until IS NULL OR r.delivery_lease_until<=now()) "
            "AND (%s::uuid IS NULL OR r.workflow_id=%s) ORDER BY r.created_at,r.id LIMIT 1",
            (workflow_id, workflow_id),
        )
        if candidate is None:
            return None
        workflow = _workflow(conn, candidate["workflow_id"])
        obligation = _one(
            conn,
            "SELECT * FROM repair_obligations WHERE id=%s FOR UPDATE SKIP LOCKED",
            (candidate["id"],),
        )
        if (
            obligation is None
            or obligation["state"] not in ("OPEN", "REPAIR_AUTHORIZED")
            or not repair_capable(workflow.get("research_arm"))
            or (
                obligation["delivery_lease_until"]
                and obligation["delivery_lease_until"] > datetime.now(UTC)
            )
        ):
            return None
        conn.execute(
            "UPDATE repair_obligations SET delivery_lease_owner=%s,delivery_lease_until=%s,"
            "delivery_attempt_count=delivery_attempt_count+1 WHERE id=%s",
            (owner, datetime.now(UTC) + timedelta(seconds=30), obligation["id"]),
        )
        _event(
            conn,
            workflow,
            "RepairDeliveryLeased",
            workflow["current_revision"],
            None,
            uuid4(),
            {"repair_obligation_id": str(obligation["id"]), "owner": owner},
            owner,
        )
        return obligation


def deliver(obligation: dict[str, Any], owner: str, crash_at: str | None = None) -> dict[str, Any]:
    def boundary(name: str) -> None:
        if crash_at == name:
            # Actual subprocess crash: committed facts and lease survive, no cleanup.
            os._exit(73)

    boundary("after_lease")
    if obligation["deadline_at"] <= datetime.now(UTC) or (
        obligation["delivery_attempt_count"] >= 8 and obligation["delivery_error_json"]
    ):
        with _connection() as conn:
            workflow = _workflow(conn, obligation["workflow_id"])
            conn.execute(
                "INSERT INTO handoffs (id,workflow_id,resident_id,reason_code,priority,"
                "known_facts,unknown_facts,deadline_at,state) "
                "VALUES (%s,%s,%s,'REPAIR_DELIVERY_UNRESOLVED','HIGH',%s,%s,now(),'OPEN') "
                "ON CONFLICT (id) DO NOTHING",
                (
                    command(obligation, "handoff"),
                    workflow["id"],
                    workflow["resident_id"],
                    Jsonb({"repair_obligation_id": str(obligation["id"])}),
                    Jsonb({"playback_completion": "UNKNOWN"}),
                ),
            )
            conn.execute(
                "UPDATE repair_obligations SET state='ESCALATED' WHERE id=%s", (obligation["id"],)
            )
            _event(
                conn,
                workflow,
                "RepairEscalated",
                workflow["current_revision"],
                None,
                command(obligation, "handoff"),
                {"repair_obligation_id": str(obligation["id"])},
                owner,
            )
        return {"action": "escalated"}
    revision = obligation["triggering_revision"]
    with _connection() as conn:
        found_workflow = _one(
            conn, "SELECT * FROM workflows WHERE id=%s", (obligation["workflow_id"],)
        )
        assert found_workflow is not None
        workflow = found_workflow
        segment = _one(
            conn,
            "SELECT * FROM audio_segments WHERE repair_obligation_id=%s "
            "AND intent_revision=%s ORDER BY generated_at DESC LIMIT 1",
            (obligation["id"], revision),
        )
        operation = _one(
            conn,
            "SELECT * FROM operations WHERE workflow_id=%s AND intent_revision=%s "
            "AND applicability='CURRENT' AND effect_knowledge='PRESENT' "
            "ORDER BY created_at DESC LIMIT 1",
            (workflow["id"], revision),
        )
    if workflow["current_revision"] != revision:
        raise DomainProblem("stale-repair", "Stale repair", "Accepted target changed")
    if segment and segment["state"] in ("PUBLISHED", "STARTED", "COMPLETED"):
        return {"action": "awaiting_ack", "segment_id": str(segment["id"])}
    if operation is None:
        return {"action": "waiting_for_evidence"}
    if segment is None:
        receipt = issue_verification(
            VerifyRequest(
                command_id=command(obligation, "verify"),
                operation_id=operation["id"],
                expected_intent_revision=revision,
                claim_type=ClaimType.CURRENT_APPOINTMENT
                if revision == 1
                else ClaimType.RESCHEDULED_APPOINTMENT,
            ),
            owner,
        )
        if receipt["result"] != "SATISFIED":
            return {"action": "waiting_for_evidence", "receipt_id": receipt["receipt_id"]}
        boundary("after_verification")
        permit = authorize(
            AuthorizeClaimRequest(
                command_id=command(obligation, "authorize"),
                receipt_id=UUID(receipt["receipt_id"]),
                expected_intent_revision=revision,
            ),
            owner,
        )
        boundary("after_authorization")
        queue(
            UUID(permit["permit_id"]),
            PermitCommand(
                command_id=command(obligation, "permit_queue"),
                expected_intent_revision=revision,
            ),
            owner,
        )
        scheduler = VoiceScheduler(
            HttpControllerPort(os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")),
            DeterministicToneTTS() if os.getenv("EXPERIMENT_MODE") == "true" else LocalEspeakTTS(),
        )
        staged = scheduler.stage_claim(
            UUID(permit["permit_id"]), revision, UUID(str(obligation["id"]))
        )
        boundary("after_generation")
        segment = {"id": staged["segment_id"], "state": "GENERATED"}
    controller = HttpControllerPort(os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    if segment["state"] == "GENERATED":
        controller.post(
            f"/internal/phase4/audio-segments/{segment['id']}/queue",
            {
                "command_id": str(command(obligation, "audio_queue")),
                "expected_intent_revision": revision,
            },
        )
    boundary("after_queue")
    released = controller.post(
        f"/internal/phase4/audio-segments/{segment['id']}/release",
        {
            "command_id": str(command(obligation, "release")),
            "expected_intent_revision": revision,
        },
    )
    boundary("after_publication")
    return {"action": "published", **released}


def run_once(
    owner: str, workflow_id: UUID | None = None, crash_at: str | None = None
) -> dict[str, Any]:
    if crash_at == "before_discovery":
        os._exit(73)
    obligation = discover(owner, workflow_id)
    if obligation is None:
        return {"action": "idle", "owner": owner, "pid": os.getpid()}
    try:
        result = deliver(obligation, owner, crash_at)
    except (DomainProblem, ValueError, URLError, TimeoutError) as exc:
        result = {
            "action": "delivery_pending",
            "error_type": type(exc).__name__,
            "detail": str(exc),
        }
    with _connection() as conn:
        workflow = _workflow(conn, obligation["workflow_id"])
        error = result if result["action"] in ("delivery_pending", "waiting_for_evidence") else None
        conn.execute(
            "UPDATE repair_obligations SET delivery_lease_owner=NULL,delivery_lease_until=%s,"
            "delivery_error_json=%s WHERE id=%s AND delivery_lease_owner=%s",
            (
                datetime.now(UTC) + timedelta(seconds=5),
                Jsonb(error) if error else None,
                obligation["id"],
                owner,
            ),
        )
        _event(
            conn,
            workflow,
            "RepairDeliveryObserved",
            workflow["current_revision"],
            None,
            uuid4(),
            {"repair_obligation_id": str(obligation["id"]), **result},
            owner,
        )
    return {
        "repair_obligation_id": str(obligation["id"]),
        "owner": owner,
        "pid": os.getpid(),
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=UUID)
    parser.add_argument("--crash-at")
    args = parser.parse_args()
    print(json.dumps(run_once(f"repair-worker:{uuid4()}", args.workflow, args.crash_at)))


if __name__ == "__main__":
    main()
