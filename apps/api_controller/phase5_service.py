"""PostgreSQL read models and bounded browser commands for the Phase 5 UI."""

# ruff: noqa: E501 -- PostgreSQL statements are kept readable as single literals.

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Any, cast
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import structlog
from psycopg.types.json import Jsonb

from apps.api_controller.phase1_service import (
    DomainProblem,
    _all,
    _command_replay,
    _connection,
    _event,
    _execute,
    _hash,
    _one,
    _receipt,
    _workflow,
)
from apps.api_controller.phase3_verification_service import _evaluate, _external_observations
from apps.api_controller.phase5_models import (
    CreateCallRequest,
    CreateNoteRequest,
    ExperimentDraftRequest,
    HandoffCommand,
)
from packages.domain.phase3_verification import ClaimType

DEMO_RESIDENT_ID = UUID("33333333-3333-4333-8333-333333333333")
logger = structlog.get_logger(__name__)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _livekit_token(call_id: UUID, room: str, *, participant: str = "caller") -> str:
    key = os.environ.get("LIVEKIT_API_KEY", "devkey")
    secret = os.environ.get("LIVEKIT_API_SECRET", "secret")
    if not key or not secret:
        raise DomainProblem(
            "media-unavailable", "Media unavailable", "LiveKit credentials are not configured", 503
        )
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = {
        "iss": key,
        "sub": f"{participant}-{call_id}",
        "nbf": now - 5,
        "exp": now + 3600,
        "video": {"roomJoin": True, "room": room, "canPublish": True, "canSubscribe": True},
    }
    payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    signature = _b64(
        hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def public_config() -> dict[str, Any]:
    with _connection() as conn:
        resident = _one(
            conn,
            "SELECT id FROM residents WHERE id=%s AND actor_id=(SELECT id FROM actors WHERE subject='demo:maintenance')",
            (DEMO_RESIDENT_ID,),
        )
    return {
        "mode": "DEMO",
        "synthetic_resident_id": str(resident["id"]) if resident else None,
        "livekit_url": os.environ.get("PUBLIC_LIVEKIT_URL", "ws://127.0.0.1:7880"),
        "voice_path": "provider-neutral cascaded",
        "database": "PostgreSQL",
    }


def create_call(body: CreateCallRequest, command_id: UUID, trace_id: str) -> dict[str, Any]:
    if body.consent is not True:
        raise DomainProblem(
            "consent-required",
            "Consent required",
            "Recording and microphone consent is required",
            422,
        )
    request_hash = _hash(body.model_dump(mode="json"))
    with _connection() as conn:
        _execute(conn, "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(command_id),))
        prior = _command_replay(conn, command_id, "create_call", request_hash)
        if prior:
            prior["livekit_token"] = _livekit_token(UUID(prior["call_id"]), prior["livekit_room"])
            return prior
        resident = _one(
            conn,
            "SELECT r.id,r.actor_id,a.synthetic FROM residents r JOIN actors a ON a.id=r.actor_id WHERE r.id=%s",
            (body.resident_id,),
        )
        if resident is None or not resident["synthetic"]:
            raise DomainProblem(
                "resident-not-found",
                "Synthetic resident not found",
                "Select a synthetic resident",
                404,
            )
        if body.experiment_run_id is not None:
            run = _one(
                conn, "SELECT id FROM evaluation_runs WHERE id=%s", (body.experiment_run_id,)
            )
            if run is None:
                raise DomainProblem("run-not-found", "Run not found", "Unknown evaluation run", 404)
        call_id, workflow_id = uuid4(), uuid4()
        room = f"call-{call_id}"
        _execute(
            conn,
            "INSERT INTO call_sessions (id,actor_id,resident_id,experiment_run_id,media_status,consent_json,livekit_room) VALUES (%s,%s,%s,%s,'CREATED',%s,%s)",
            (
                call_id,
                resident["actor_id"],
                resident["id"],
                body.experiment_run_id,
                Jsonb({"microphone": True, "recording": True, "synthetic": True}),
                room,
            ),
        )
        _execute(
            conn,
            "INSERT INTO workflows (id,call_id,actor_id,resident_id,workflow_type) VALUES (%s,%s,%s,%s,'MAINTENANCE_APPOINTMENT')",
            (workflow_id, call_id, resident["actor_id"], resident["id"]),
        )
        workflow = _workflow(conn, workflow_id)
        _event(conn, workflow, "CallCreated", None, None, command_id, {"consent": True}, trace_id)
        response = {
            "call_id": str(call_id),
            "workflow_id": str(workflow_id),
            "media_status": "CREATED",
            "livekit_room": room,
        }
        _receipt(conn, command_id, "create_call", workflow_id, request_hash, response)
    response["livekit_token"] = _livekit_token(call_id, room)
    return response


def call_detail(call_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        call = _one(
            conn,
            "SELECT c.*,a.display_name,r.unit_ref FROM call_sessions c JOIN actors a ON a.id=c.actor_id JOIN residents r ON r.id=c.resident_id WHERE c.id=%s",
            (call_id,),
        )
        if call is None:
            raise DomainProblem("call-not-found", "Call not found", "Unknown call", 404)
        workflows = _all(
            conn, "SELECT * FROM workflows WHERE call_id=%s ORDER BY created_at,id", (call_id,)
        )
        operations = _all(
            conn,
            "SELECT o.* FROM operations o JOIN workflows w ON w.id=o.workflow_id WHERE w.call_id=%s ORDER BY o.created_at,o.id",
            (call_id,),
        )
        repairs = _all(
            conn,
            "SELECT ro.* FROM repair_obligations ro JOIN workflows w ON w.id=ro.workflow_id WHERE w.call_id=%s ORDER BY ro.created_at",
            (call_id,),
        )
    return {"call": call, "workflows": workflows, "operations": operations, "repairs": repairs}


def _join_voice_agent(call_id: UUID, workflow_id: UUID, room: str) -> bool:
    base_url = os.environ.get("VOICE_WORKER_BASE_URL")
    if not base_url:
        return False
    body = json.dumps(
        {
            "call_id": str(call_id),
            "workflow_id": str(workflow_id),
            "room_token": _livekit_token(call_id, room, participant="agent"),
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}/internal/phase5/rooms/join",
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload: dict[str, object] = json.load(response)
        return payload.get("status") == "READY"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning(
            "voice_agent_join_unavailable",
            call_id=str(call_id),
            workflow_id=str(workflow_id),
            error_type=type(exc).__name__,
        )
        return False


def call_media_token(call_id: UUID) -> dict[str, str]:
    with _connection() as conn:
        call = _one(
            conn,
            "SELECT c.livekit_room,c.media_status,w.id AS workflow_id "
            "FROM call_sessions c JOIN workflows w ON w.call_id=c.id WHERE c.id=%s "
            "ORDER BY w.created_at LIMIT 1",
            (call_id,),
        )
    if call is None:
        raise DomainProblem("call-not-found", "Call not found", "Unknown call", 404)
    if call["media_status"] == "ENDED":
        raise DomainProblem("call-ended", "Call ended", "Media has ended for this call")
    agent_ready = _join_voice_agent(call_id, call["workflow_id"], call["livekit_room"])
    return {
        "livekit_url": os.environ.get("PUBLIC_LIVEKIT_URL", "ws://127.0.0.1:7880"),
        "livekit_token": _livekit_token(call_id, call["livekit_room"]),
        "voice_agent_status": "READY" if agent_ready else "UNAVAILABLE",
    }


def call_summary(call_id: UUID) -> dict[str, Any]:
    detail = call_detail(call_id)
    call, workflows, operations, repairs = (
        detail["call"],
        detail["workflows"],
        detail["operations"],
        detail["repairs"],
    )
    workflow = workflows[-1] if workflows else None
    current = [
        op
        for op in operations
        if workflow
        and op["workflow_id"] == workflow["id"]
        and op["intent_revision"] == workflow["current_revision"]
        and op["applicability"] == "CURRENT"
    ]
    with _connection() as conn:
        receipts = _all(
            conn,
            "SELECT vr.* FROM verification_receipts vr JOIN workflows w ON w.id=vr.workflow_id WHERE w.call_id=%s ORDER BY vr.created_at DESC",
            (call_id,),
        )
        handoff = _one(
            conn,
            "SELECT h.* FROM handoffs h JOIN workflows w ON w.id=h.workflow_id WHERE w.call_id=%s AND h.state IN ('OPEN','ACKNOWLEDGED') ORDER BY h.created_at DESC LIMIT 1",
            (call_id,),
        )
    valid_receipt = None
    for receipt in receipts:
        if (
            not workflow
            or receipt["intent_revision"] != workflow["current_revision"]
            or receipt["result"] != "SATISFIED"
            or receipt["claim_type"] not in ("CURRENT_APPOINTMENT", "RESCHEDULED_APPOINTMENT")
            or receipt["invalidated_at"] is not None
            or receipt["valid_from"].timestamp() > time.time()
            or (
                receipt["valid_until"] is not None
                and receipt["valid_until"].timestamp() <= time.time()
            )
        ):
            continue
        operation = next((op for op in current if op["id"] == receipt["operation_id"]), None)
        if operation is None or operation["effect_knowledge"] != "PRESENT":
            continue
        predicate_id = receipt["predicates_json"].get("appointment_id")
        if not isinstance(predicate_id, str) or receipt["observed_resource_version"] is None:
            continue
        if operation["provider_adapter"] == "local_postgres":
            with _connection() as conn:
                appointment = _one(
                    conn,
                    "SELECT version,status FROM appointments WHERE id=%s AND source_workflow_id=%s",
                    (UUID(predicate_id), workflow["id"]),
                )
            if (
                appointment is None
                or appointment["status"] != "CONFIRMED"
                or str(appointment["version"]) != receipt["observed_resource_version"]
            ):
                continue
        elif operation["provider_adapter"] == "simulator":
            claim_type = ClaimType(receipt["claim_type"])
            observation = _external_observations(operation, claim_type)
            current_evaluation = _evaluate(claim_type, workflow, operation, observation, None)
            if (
                current_evaluation.result.value != "SATISFIED"
                or current_evaluation.resource_version != receipt["observed_resource_version"]
                or current_evaluation.predicates != receipt["predicates_json"]
            ):
                continue
        else:
            continue
        valid_receipt = receipt
        break
    active_repair = next(
        (row for row in repairs if row["state"] not in ("REPAIR_PLAYED", "CLOSED")), None
    )
    if active_repair:
        resolution = "REPAIR_PENDING"
    elif handoff:
        resolution = "HANDOFF_CREATED"
    elif valid_receipt:
        resolution = "RESOLVED_VERIFIED"
    else:
        resolution = "UNRESOLVED_RECOVERING"
    statement = {
        "REPAIR_PENDING": "Earlier information may have been superseded. A correction is pending.",
        "HANDOFF_CREATED": "A human follow-up has been created. The requested outcome is not yet verified.",
        "RESOLVED_VERIFIED": "The current outcome is verified against durable evidence.",
        "UNRESOLVED_RECOVERING": "Still checking the current outcome. No confirmation is available yet.",
    }[resolution]
    return {
        "call_id": call_id,
        "media_status": call["media_status"],
        "started_at": call["started_at"],
        "ended_at": call["ended_at"],
        "business_resolution": resolution,
        "latest_revision": workflow["current_revision"] if workflow else 0,
        "desired_state": workflow["desired_state_json"] if workflow else {},
        "current_statement": statement,
        "receipt_id": valid_receipt["id"] if valid_receipt else None,
        "verification_result": valid_receipt["result"] if valid_receipt else "UNKNOWN",
        "handoff_id": handoff["id"] if handoff else None,
        "repair_obligation_id": active_repair["id"] if active_repair else None,
        "operations": current,
    }


def call_timeline(call_id: UUID) -> dict[str, Any]:
    detail = call_detail(call_id)
    with _connection() as conn:
        events = _all(
            conn,
            "SELECT e.* FROM workflow_events e JOIN workflows w ON w.id=e.workflow_id WHERE w.call_id=%s ORDER BY e.occurred_at,e.workflow_sequence",
            (call_id,),
        )
        voice = _all(
            conn, "SELECT * FROM voice_events WHERE call_id=%s ORDER BY occurred_at,id", (call_id,)
        )
        receipts = _all(
            conn,
            "SELECT r.* FROM verification_receipts r JOIN workflows w ON w.id=r.workflow_id WHERE w.call_id=%s ORDER BY r.created_at",
            (call_id,),
        )
        segments = _all(
            conn, "SELECT * FROM audio_segments WHERE call_id=%s ORDER BY created_at", (call_id,)
        )
        playback = _all(
            conn,
            "SELECT * FROM playback_events WHERE call_id=%s ORDER BY server_received_at,id",
            (call_id,),
        )
        utterances = _all(
            conn, "SELECT * FROM utterances WHERE call_id=%s ORDER BY created_at,id", (call_id,)
        )
    for segment in segments:
        segment.pop("audio_data", None)
    return {
        **detail,
        "events": events,
        "voice_events": voice,
        "receipts": receipts,
        "segments": segments,
        "playback_events": playback,
        "utterances": utterances,
    }


def list_calls(limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    with _connection() as conn:
        total = _one(conn, "SELECT count(*) AS n FROM call_sessions")
        calls = _all(
            conn,
            "SELECT c.id AS call_id,c.started_at,c.ended_at,c.media_status,c.experiment_run_id,a.display_name AS actor_name,w.id AS workflow_id,w.current_revision,w.resolution_status FROM call_sessions c JOIN actors a ON a.id=c.actor_id LEFT JOIN LATERAL (SELECT * FROM workflows WHERE call_id=c.id ORDER BY created_at DESC LIMIT 1) w ON true ORDER BY c.started_at DESC,c.id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return calls, int(total["n"]) if total else 0


def list_appointments(
    limit: int,
    offset: int,
    status: str | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
) -> tuple[list[dict[str, Any]], int]:
    clauses: list[str] = []
    values: list[Any] = []
    if status:
        clauses.append("a.status::text=%s")
        values.append(status)
    if from_at:
        clauses.append("a.starts_at >= %s")
        values.append(from_at)
    if to_at:
        clauses.append("a.starts_at < %s")
        values.append(to_at)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    args = tuple(values)
    with _connection() as conn:
        total = _one(conn, f"SELECT count(*) AS n FROM appointments a {where}", args)
        rows = _all(
            conn,
            f"SELECT a.*,act.display_name AS resident_name,w.current_revision, (SELECT r.id FROM verification_receipts r JOIN operations op ON op.id=r.operation_id WHERE r.workflow_id=a.source_workflow_id AND r.intent_revision=w.current_revision AND r.claim_type IN ('CURRENT_APPOINTMENT','RESCHEDULED_APPOINTMENT') AND r.result='SATISFIED' AND r.invalidated_at IS NULL AND r.valid_from<=now() AND (r.valid_until IS NULL OR r.valid_until>now()) AND r.predicates_json->>'appointment_id'=a.id::text AND r.observed_resource_version=a.version::text AND a.status='CONFIRMED' AND op.applicability='CURRENT' AND op.effect_knowledge='PRESENT' ORDER BY r.created_at DESC LIMIT 1) AS current_receipt_id FROM appointments a JOIN residents resident ON resident.id=a.resident_id JOIN actors act ON act.id=resident.actor_id JOIN workflows w ON w.id=a.source_workflow_id {where} ORDER BY a.starts_at DESC,a.id DESC LIMIT %s OFFSET %s",
            (*args, limit, offset),
        )
    return rows, int(total["n"]) if total else 0


def appointment_detail(appointment_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        row = _one(
            conn,
            "SELECT a.*,w.current_revision,w.call_id,"
            "(SELECT r.id FROM verification_receipts r JOIN operations op ON op.id=r.operation_id "
            "WHERE r.workflow_id=a.source_workflow_id "
            "AND r.intent_revision=w.current_revision "
            "AND r.claim_type IN ('CURRENT_APPOINTMENT','RESCHEDULED_APPOINTMENT') "
            "AND r.result='SATISFIED' AND r.invalidated_at IS NULL "
            "AND r.valid_from<=now() AND (r.valid_until IS NULL OR r.valid_until>now()) "
            "AND r.predicates_json->>'appointment_id'=a.id::text "
            "AND r.observed_resource_version=a.version::text "
            "AND a.status='CONFIRMED' AND op.applicability='CURRENT' "
            "AND op.effect_knowledge='PRESENT' "
            "ORDER BY r.created_at DESC LIMIT 1) AS current_receipt_id "
            "FROM appointments a JOIN workflows w ON w.id=a.source_workflow_id WHERE a.id=%s",
            (appointment_id,),
        )
        if row is None:
            raise DomainProblem(
                "appointment-not-found", "Appointment not found", "Unknown appointment", 404
            )
        effects = _all(
            conn,
            "SELECT e.* FROM effect_ledger e JOIN operations o ON o.id=e.operation_id WHERE o.workflow_id=%s ORDER BY e.created_at",
            (row["source_workflow_id"],),
        )
        receipts = _all(
            conn,
            "SELECT * FROM verification_receipts WHERE workflow_id=%s ORDER BY created_at DESC",
            (row["source_workflow_id"],),
        )
    return {"appointment": row, "effects": effects, "receipts": receipts}


def list_residents(limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    with _connection() as conn:
        total = _one(
            conn,
            "SELECT count(*) AS n FROM residents r JOIN actors a ON a.id=r.actor_id WHERE a.synthetic=true",
        )
        rows = _all(
            conn,
            "SELECT r.*,a.display_name,p.display_name AS property_name,p.timezone,(SELECT count(*) FROM maintenance_tickets t WHERE t.resident_id=r.id AND t.status='OPEN') AS open_tickets FROM residents r JOIN actors a ON a.id=r.actor_id JOIN properties p ON p.id=r.property_id WHERE a.synthetic=true ORDER BY a.display_name,r.id LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return rows, int(total["n"]) if total else 0


def resident_detail(resident_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        resident = _one(
            conn,
            "SELECT r.*,a.display_name,a.subject,a.synthetic,p.display_name AS property_name,p.timezone FROM residents r JOIN actors a ON a.id=r.actor_id JOIN properties p ON p.id=r.property_id WHERE r.id=%s",
            (resident_id,),
        )
        if resident is None:
            raise DomainProblem("resident-not-found", "Resident not found", "Unknown resident", 404)
        tickets = _all(
            conn,
            "SELECT * FROM maintenance_tickets WHERE resident_id=%s ORDER BY created_at DESC",
            (resident_id,),
        )
        appointments = _all(
            conn,
            "SELECT * FROM appointments WHERE resident_id=%s ORDER BY starts_at DESC",
            (resident_id,),
        )
        notes = _all(
            conn,
            "SELECT * FROM resident_notes WHERE resident_id=%s ORDER BY created_at DESC",
            (resident_id,),
        )
        calls = _all(
            conn,
            "SELECT id,media_status,started_at,ended_at FROM call_sessions WHERE resident_id=%s ORDER BY started_at DESC",
            (resident_id,),
        )
    return {
        "resident": resident,
        "tickets": tickets,
        "appointments": appointments,
        "notes": notes,
        "calls": calls,
    }


def list_notes(limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    with _connection() as conn:
        total = _one(conn, "SELECT count(*) AS n FROM resident_notes")
        rows = _all(
            conn,
            "SELECT n.*,a.display_name AS resident_name FROM resident_notes n JOIN residents r ON r.id=n.resident_id JOIN actors a ON a.id=r.actor_id ORDER BY n.created_at DESC,n.id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return rows, int(total["n"]) if total else 0


def create_note(body: CreateNoteRequest) -> dict[str, Any]:
    forbidden = ("allergy", "medication", "diagnosis", "emergency", "ambulance")
    if any(term in body.note_text.casefold() for term in forbidden):
        raise DomainProblem(
            "note-scope",
            "Note outside maintenance scope",
            "Only maintenance and scheduling notes are accepted",
            422,
        )
    request_hash = _hash(body.model_dump(mode="json", exclude={"command_id"}))
    with _connection() as conn:
        _execute(
            conn, "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(body.command_id),)
        )
        prior = _one(
            conn,
            "SELECT command_type,request_hash,response_json FROM command_receipts WHERE command_id=%s",
            (body.command_id,),
        )
        if prior:
            if prior["command_type"] != "create_note" or prior["request_hash"] != request_hash:
                raise DomainProblem(
                    "idempotency-conflict",
                    "Command identity conflict",
                    "Command ID was reused with changed note",
                )
            return cast(dict[str, Any], prior["response_json"])
        resident = _one(
            conn, "SELECT version FROM residents WHERE id=%s FOR UPDATE", (body.resident_id,)
        )
        if resident is None:
            raise DomainProblem("resident-not-found", "Resident not found", "Unknown resident", 404)
        if resident["version"] != body.expected_resident_version:
            raise DomainProblem(
                "stale-resource-version",
                "Stale resident version",
                "Reload the resident before saving",
            )
        workflow = _one(
            conn,
            "SELECT id FROM workflows WHERE resident_id=%s ORDER BY created_at DESC LIMIT 1",
            (body.resident_id,),
        )
        if workflow is None:
            raise DomainProblem(
                "workflow-required",
                "Workflow required",
                "A call must exist before adding notes",
                409,
            )
        note_id = uuid4()
        _execute(
            conn,
            "INSERT INTO resident_notes (id,resident_id,category,note_text,source,validated) VALUES (%s,%s,%s,%s,'HUMAN',true)",
            (note_id, body.resident_id, body.category, body.note_text.strip()),
        )
        _execute(conn, "UPDATE residents SET version=version+1 WHERE id=%s", (body.resident_id,))
        result = {
            "note_id": str(note_id),
            "resident_id": str(body.resident_id),
            "version": resident["version"] + 1,
        }
        _receipt(conn, body.command_id, "create_note", workflow["id"], request_hash, result)
        return result


def list_handoffs(limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    with _connection() as conn:
        total = _one(conn, "SELECT count(*) AS n FROM handoffs")
        rows = _all(
            conn,
            "SELECT h.*,a.display_name AS resident_name FROM handoffs h JOIN residents r ON r.id=h.resident_id JOIN actors a ON a.id=r.actor_id ORDER BY h.created_at DESC,h.id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return rows, int(total["n"]) if total else 0


def update_handoff(
    handoff_id: UUID, body: HandoffCommand, target: str, trace_id: str
) -> dict[str, Any]:
    request_hash = _hash(
        {
            "handoff_id": str(handoff_id),
            "target": target,
            **body.model_dump(mode="json", exclude={"command_id"}),
        }
    )
    with _connection() as conn:
        locator = _one(conn, "SELECT workflow_id FROM handoffs WHERE id=%s", (handoff_id,))
        if locator is None:
            raise DomainProblem("handoff-not-found", "Handoff not found", "Unknown handoff", 404)
        workflow = _workflow(conn, locator["workflow_id"])
        prior = _command_replay(conn, body.command_id, f"handoff_{target.lower()}", request_hash)
        if prior:
            return prior
        row = _one(conn, "SELECT * FROM handoffs WHERE id=%s FOR UPDATE", (handoff_id,))
        assert row is not None
        if row["state"] != body.expected_state:
            raise DomainProblem(
                "stale-handoff-state", "Handoff changed", "Reload the current handoff state"
            )
        if target == "RESOLVED" and not body.administrative_closure:
            raise DomainProblem(
                "evidence-required",
                "Evidence required",
                "Use administrative closure or record independent evidence",
            )
        new_state = "ADMIN_CLOSED" if target == "RESOLVED" else "ACKNOWLEDGED"
        _execute(
            conn,
            "UPDATE handoffs SET state=%s,resolution_json=%s,updated_at=now() WHERE id=%s",
            (
                new_state,
                Jsonb({"note": body.note, "administrative_closure": body.administrative_closure})
                if target == "RESOLVED"
                else None,
                handoff_id,
            ),
        )
        _event(
            conn,
            workflow,
            "HandoffStateChanged",
            workflow["current_revision"],
            None,
            body.command_id,
            {"handoff_id": str(handoff_id), "state": new_state},
            trace_id,
        )
        result = {"handoff_id": str(handoff_id), "state": new_state}
        _receipt(
            conn, body.command_id, f"handoff_{target.lower()}", workflow["id"], request_hash, result
        )
        return result


def dashboard() -> dict[str, Any]:
    with _connection() as conn:
        counts = _one(
            conn,
            "SELECT (SELECT count(*) FROM call_sessions) AS calls,(SELECT count(*) FROM workflows WHERE current_revision>1) AS corrected_workflows,(SELECT count(*) FROM operations WHERE effect_knowledge='UNKNOWN') AS unknown_effects,(SELECT count(*) FROM repair_obligations WHERE state NOT IN ('REPAIR_PLAYED','CLOSED')) AS open_repairs,(SELECT count(*) FROM handoffs WHERE state IN ('OPEN','ACKNOWLEDGED')) AS open_handoffs,(SELECT count(*) FROM verification_receipts WHERE result='SATISFIED' AND invalidated_at IS NULL) AS satisfied_receipts",
        )
        recent = _all(
            conn,
            "SELECT id,event_name,occurred_at,workflow_id,intent_revision,trace_id FROM workflow_events ORDER BY occurred_at DESC LIMIT 12",
        )
    return {"counts": counts or {}, "recent_events": recent, "research_metrics_available": False}


def evaluation_runs(limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    with _connection() as conn:
        total = _one(conn, "SELECT count(*) AS n FROM evaluation_runs")
        rows = _all(
            conn,
            "SELECT r.*, (SELECT count(DISTINCT case_id) FROM executions WHERE run_id=r.id) AS independent_scenarios,(SELECT count(*) FROM executions WHERE run_id=r.id) AS executions,(SELECT count(*) FROM executions WHERE run_id=r.id AND status='EXCLUDED') AS exclusions,(SELECT count(*) FROM executions WHERE run_id=r.id AND status='TIMEOUT') AS timeouts FROM evaluation_runs r ORDER BY r.created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return rows, int(total["n"]) if total else 0


def evaluation_run(run_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        run = _one(conn, "SELECT * FROM evaluation_runs WHERE id=%s", (run_id,))
        if run is None:
            raise DomainProblem("run-not-found", "Run not found", "Unknown run", 404)
        cases = _all(
            conn, "SELECT * FROM scenario_cases WHERE run_id=%s ORDER BY scenario_key", (run_id,)
        )
        executions = _all(
            conn,
            "SELECT * FROM executions WHERE run_id=%s ORDER BY case_id,system_arm,repetition",
            (run_id,),
        )
        metrics = _all(
            conn,
            "SELECT m.* FROM metrics m JOIN executions e ON e.id=m.execution_id WHERE e.run_id=%s ORDER BY m.recorded_at",
            (run_id,),
        )
    return {"run": run, "cases": cases, "executions": executions, "metrics": metrics}


def create_experiment_draft(body: ExperimentDraftRequest) -> dict[str, Any]:
    manifest = body.model_dump(mode="json", exclude={"command_id", "name"})
    manifest["runner_status"] = "PHASE_6_PENDING"
    manifest_hash = _hash({"name": body.name, "manifest": manifest})
    with _connection() as conn:
        _execute(
            conn, "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (str(body.command_id),)
        )
        existing = _one(
            conn,
            "SELECT id,manifest_hash,status FROM evaluation_runs WHERE creation_command_id=%s",
            (body.command_id,),
        )
        if existing:
            if existing["manifest_hash"] != manifest_hash:
                raise DomainProblem(
                    "idempotency-conflict",
                    "Draft command conflict",
                    "Command ID was reused with changed manifest",
                )
            return {
                "run_id": str(existing["id"]),
                "status": existing["status"],
                "manifest_hash": manifest_hash,
            }
        same = _one(
            conn, "SELECT id,status FROM evaluation_runs WHERE manifest_hash=%s", (manifest_hash,)
        )
        if same:
            return {
                "run_id": str(same["id"]),
                "status": same["status"],
                "manifest_hash": manifest_hash,
            }
        run_id = uuid4()
        _execute(
            conn,
            "INSERT INTO evaluation_runs (id,name,status,manifest_json,manifest_hash,source_commit,migration_version,analysis_version,creation_command_id) VALUES (%s,%s,'DRAFT',%s,%s,%s,'0007_phase5_drafts','phase6-pending',%s)",
            (
                run_id,
                body.name,
                Jsonb(manifest),
                manifest_hash,
                os.environ.get("SOURCE_COMMIT", "unrecorded-draft"),
                body.command_id,
            ),
        )
        return {"run_id": str(run_id), "status": "DRAFT", "manifest_hash": manifest_hash}


def settings() -> dict[str, Any]:
    return {
        "environment": "DEMO",
        "database": "PostgreSQL",
        "strict_research_voice_path": "provider-neutral cascaded STT → LLM → TTS",
        "native_audio": "optional comparison adapter",
        "speech_policy": "permit gated",
        "simulator": "enabled",
        "evaluation_runner": "Phase 6 pending",
    }
