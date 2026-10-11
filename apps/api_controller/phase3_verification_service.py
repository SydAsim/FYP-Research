"""Independent provider reads become revision-bound, three-valued receipts."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

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
from apps.api_controller.phase3_models import VerifyRequest
from packages.domain.phase3_verification import (
    ClaimType,
    Evaluation,
    Result,
    _instant,
    evaluate_appointment,
)
from packages.provider_adapters.simulator import (
    Exchange,
    operation_status,
    resource_state,
)

VERIFIER_VERSION = "phase3-verifier-v1"


@dataclass(frozen=True)
class Observation:
    source_type: str
    source_identifier: str
    query: dict[str, Any]
    raw: dict[str, Any]
    facts: dict[str, Any] | None
    observed_at: datetime
    source_version: str | None = None


def _external_observations(operation: dict[str, Any], claim_type: ClaimType) -> list[Observation]:
    normalized = operation["normalized_request_json"]
    scenario_id = UUID(normalized["scenario_id"])
    result: list[Observation] = []
    if claim_type in (
        ClaimType.CURRENT_APPOINTMENT,
        ClaimType.RESCHEDULED_APPOINTMENT,
        ClaimType.COMPENSATED_APPOINTMENT,
    ):
        resource = resource_state(scenario_id, operation["id"], normalized["resource_key"])
        result.append(
            Observation(
                "SIMULATOR_RESOURCE",
                normalized["resource_key"],
                {
                    "scenario_id": str(scenario_id),
                    "operation_id": str(operation["id"]),
                    "resource_key": normalized["resource_key"],
                },
                resource.raw,
                resource.body if resource.status == 200 else None,
                datetime.now(UTC),
                str(resource.body["appointments"][0]["version"])
                if resource.status == 200
                and resource.body
                and len(resource.body.get("appointments", [])) == 1
                and "version" in resource.body["appointments"][0]
                else None,
            )
        )
    if claim_type in (
        ClaimType.HISTORICAL_EFFECT,
        ClaimType.RESCHEDULED_APPOINTMENT,
        ClaimType.COMPENSATED_APPOINTMENT,
    ):
        current: dict[str, Any] | None = operation
        depth = 0
        while current is not None and depth < 3:
            status: Exchange = operation_status(scenario_id, current["id"])
            result.append(
                Observation(
                    "SIMULATOR_OPERATION",
                    str(current["id"]),
                    {
                        "scenario_id": str(scenario_id),
                        "operation_id": str(current["id"]),
                        "action": current["normalized_request_json"]["action"],
                    },
                    status.raw,
                    status.body if status.status == 200 else None,
                    datetime.now(UTC),
                    str(status.body["facts"]["version"])
                    if status.status == 200
                    and status.body
                    and isinstance(status.body.get("facts"), dict)
                    and "version" in status.body["facts"]
                    else None,
                )
            )
            if claim_type is ClaimType.HISTORICAL_EFFECT:
                break
            parent_id = current["parent_operation_id"]
            if parent_id is None:
                break
            with _connection() as conn:
                current = _one(conn, "SELECT * FROM operations WHERE id=%s", (parent_id,))
            depth += 1
    # Raw ordinary observations are journaled independently of a receipt verdict.
    # This transaction survives a later authorization/playback rejection. Baseline
    # paths get the same evidence provenance without requiring receipt objects.
    with _connection() as conn:
        for observation in result:
            _execute(
                conn,
                "INSERT INTO provider_events (operation_id,event_kind,raw_json,"
                "normalized_json,content_hash,trace_id) VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    operation["id"],
                    "READINESS_OBSERVATION_V2",
                    Jsonb(observation.raw),
                    Jsonb(
                        {
                            "source_type": observation.source_type,
                            "source_identifier": observation.source_identifier,
                            "query": observation.query,
                            "facts": observation.facts,
                            "source_version": observation.source_version,
                            "observed_at": observation.observed_at.isoformat(),
                        }
                    ),
                    _hash({"query": observation.query, "raw": observation.raw}),
                    f"observation:{operation['id']}",
                ),
            )
    return result


def _local_observation(conn: Any, workflow: dict[str, Any]) -> Observation:
    rows = _all(
        conn,
        "SELECT id,resource_key,starts_at,ends_at,timezone,status,version "
        "FROM appointments WHERE source_workflow_id=%s ORDER BY created_at,id",
        (workflow["id"],),
    )
    facts = [
        {
            "appointment_id": str(row["id"]),
            "resource_key": row["resource_key"],
            "starts_at": row["starts_at"].isoformat(),
            "ends_at": row["ends_at"].isoformat(),
            "timezone": row["timezone"],
            "status": row["status"],
            "version": row["version"],
        }
        for row in rows
    ]
    body = {"authoritative": True, "appointments": facts}
    return Observation(
        "LOCAL_POSTGRES",
        str(workflow["id"]),
        {"workflow_id": str(workflow["id"]), "table": "appointments"},
        {"status": 200, "body": body},
        body,
        datetime.now(UTC),
    )


def _local_effect_observation(conn: Any, operation: dict[str, Any]) -> Observation:
    effect = _one(
        conn,
        "SELECT effect_type,resource_type,resource_id,before_facts,after_facts,"
        "observed_version,evidence_hash,observed_at FROM effect_ledger "
        "WHERE operation_id=%s ORDER BY observed_at DESC,id DESC LIMIT 1",
        (operation["id"],),
    )
    facts = {**effect, "observed_at": effect["observed_at"].isoformat()} if effect else None
    return Observation(
        "LOCAL_EFFECT",
        str(operation["id"]),
        {"operation_id": str(operation["id"]), "table": "effect_ledger"},
        {"effect": facts},
        facts,
        datetime.now(UTC),
        str(effect["observed_version"]) if effect else None,
    )


def _evaluate(
    claim_type: ClaimType,
    workflow: dict[str, Any],
    operation: dict[str, Any],
    observations: list[Observation],
    handoff: dict[str, Any] | None,
) -> Evaluation:
    if claim_type is ClaimType.HANDOFF_CREATED:
        if handoff is None:
            return Evaluation(Result.VIOLATED, {"handoff_id": None, "handoff_state": None}, None)
        return Evaluation(
            Result.SATISFIED,
            {
                "handoff_id": str(handoff["id"]),
                "handoff_state": handoff["state"],
            },
            None,
        )
    if claim_type is ClaimType.HISTORICAL_EFFECT:
        status = next((o for o in observations if o.source_type == "SIMULATOR_OPERATION"), None)
        if status is None or status.facts is None or status.facts.get("authoritative") is not True:
            return Evaluation(Result.UNKNOWN, {}, None)
        facts = status.facts.get("facts")
        prior = operation["normalized_request_json"]["desired_state"]
        if (
            status.facts.get("outcome") != "PRESENT"
            or not isinstance(facts, dict)
            or not isinstance(facts.get("starts_at"), str)
            or _instant(facts["starts_at"]) != _instant(prior["requested_start"])
        ):
            return Evaluation(Result.VIOLATED, {}, None)
        return Evaluation(
            Result.SATISFIED,
            {
                "historical_start": prior["requested_start"],
                "source_revision": operation["intent_revision"],
                "appointment_id": facts["appointment_id"],
            },
            str(facts["version"]),
        )
    desired = workflow["desired_state_json"]
    normalized = operation["normalized_request_json"]
    resource = next(
        (o for o in observations if o.source_type in ("SIMULATOR_RESOURCE", "LOCAL_POSTGRES")), None
    )
    evaluation = evaluate_appointment(
        desired,
        normalized["resource_key"]
        if operation["provider_adapter"] == "simulator"
        else (
            resource.facts["appointments"][0]["resource_key"]
            if resource and resource.facts and resource.facts["appointments"]
            else ""
        ),
        resource.facts if resource else None,
    )
    if evaluation.result is not Result.SATISFIED:
        return evaluation
    if claim_type is ClaimType.CURRENT_APPOINTMENT:
        return evaluation
    if operation["provider_adapter"] != "simulator":
        if claim_type is not ClaimType.RESCHEDULED_APPOINTMENT:
            return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
        effect = next((o for o in observations if o.source_type == "LOCAL_EFFECT"), None)
        facts = effect.facts if effect else None
        before = facts.get("before_facts") if facts else None
        after = facts.get("after_facts") if facts else None
        if (
            operation["action_type"] != "RESCHEDULE_APPOINTMENT"
            or operation["effect_knowledge"] != "PRESENT"
            or not facts
            or facts.get("effect_type") != "APPOINTMENT_RESCHEDULED"
            or facts.get("resource_type") != "appointment"
            or facts.get("resource_id") != evaluation.predicates["appointment_id"]
            or not isinstance(before, dict)
            or not isinstance(after, dict)
            or not isinstance(before.get("version"), int)
            or not isinstance(after.get("version"), int)
            or after["version"] != before["version"] + 1
            or str(after["version"]) != evaluation.resource_version
            or facts.get("observed_version") != evaluation.resource_version
            or before.get("starts_at") == after.get("starts_at")
            or after.get("starts_at") is None
            or after.get("ends_at") is None
            or _instant(after["starts_at"]) != _instant(desired["requested_start"])
            or _instant(after["ends_at"]) != _instant(desired["requested_end"])
        ):
            return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
        return evaluation
    statuses = [o for o in observations if o.source_type == "SIMULATOR_OPERATION"]
    if claim_type is ClaimType.RESCHEDULED_APPOINTMENT:
        # The earlier fixed two-operation chain rejected a second correction even
        # when CREATE -> RESCHEDULE -> RESCHEDULE was independently observed.
        # Retain the bounded three-status budget; deeper history is UNKNOWN.
        if not 2 <= len(statuses) <= 3:
            return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
        expected_actions = ["RESCHEDULE"] * (len(statuses) - 1) + ["CREATE"]
    else:
        expected_actions = ["CREATE", "CANCEL", "CREATE"]
    if len(statuses) != len(expected_actions):
        return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
    for item, action in zip(statuses, expected_actions, strict=True):
        if item.facts is None or item.facts.get("authoritative") is not True:
            return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
        if item.facts.get("outcome") != "PRESENT":
            return Evaluation(Result.VIOLATED, evaluation.predicates, evaluation.resource_version)
        # The action is derived from the stable provider operation request in the controller.
        # Provider status proves each linked effect was committed.
        if item.query.get("action") != action:
            return Evaluation(Result.VIOLATED, evaluation.predicates, evaluation.resource_version)
        facts = item.facts.get("facts")
        if not isinstance(facts, dict) or facts.get("resource_key") != normalized["resource_key"]:
            return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
    first_facts = statuses[0].facts
    if (
        first_facts is None
        or not isinstance(first_facts.get("facts"), dict)
        or str(first_facts["facts"]["version"]) != evaluation.resource_version
    ):
        return Evaluation(Result.UNKNOWN, evaluation.predicates, evaluation.resource_version)
    return evaluation


def issue_verification(request: VerifyRequest, trace_id: str) -> dict[str, Any]:
    with _connection() as conn:
        operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (request.operation_id,))
        if operation is None:
            raise DomainProblem(
                "operation-not-found", "Operation not found", "Unknown operation", 404
            )
        replay = _command_replay(
            conn,
            request.command_id,
            "issue_verification",
            _hash(request.model_dump(mode="json", exclude={"command_id"})),
        )
        if replay is not None:
            return replay
    observations = (
        _external_observations(operation, request.claim_type)
        if operation["provider_adapter"] == "simulator"
        else []
    )
    request_hash = _hash(request.model_dump(mode="json", exclude={"command_id"}))
    with _connection() as conn:
        workflow = _workflow(conn, operation["workflow_id"])
        replay = _command_replay(conn, request.command_id, "issue_verification", request_hash)
        if replay is not None:
            return replay
        if workflow["current_revision"] != request.expected_intent_revision:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                "Verification revision is no longer current",
            )
        current_op = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (request.operation_id,)
        )
        assert current_op is not None
        if (
            request.claim_type not in (ClaimType.HISTORICAL_EFFECT, ClaimType.HANDOFF_CREATED)
            and current_op["intent_revision"] != workflow["current_revision"]
            and current_op["applicability"] != "REUSABLE"
        ):
            raise DomainProblem(
                "stale-operation",
                "Stale operation",
                "Current-state receipt needs a current operation",
            )
        if current_op["workflow_id"] != workflow["id"]:
            raise DomainProblem(
                "operation-scope",
                "Operation scope mismatch",
                "Operation does not belong to this workflow",
            )
        handoff = None
        if request.claim_type is ClaimType.HANDOFF_CREATED:
            handoff = _one(
                conn,
                "SELECT * FROM handoffs WHERE workflow_id=%s "
                "AND state IN ('OPEN','ACKNOWLEDGED') ORDER BY created_at DESC LIMIT 1",
                (workflow["id"],),
            )
            observations.append(
                Observation(
                    "LOCAL_HANDOFF",
                    str(workflow["id"]),
                    {"workflow_id": str(workflow["id"]), "table": "handoffs"},
                    {"handoff": {"id": str(handoff["id"]), "state": handoff["state"]}}
                    if handoff
                    else {"handoff": None},
                    {"handoff": {"id": str(handoff["id"]), "state": handoff["state"]}}
                    if handoff
                    else None,
                    datetime.now(UTC),
                )
            )
        elif current_op["provider_adapter"] == "local_postgres":
            observations.append(_local_observation(conn, workflow))
            if request.claim_type is ClaimType.RESCHEDULED_APPOINTMENT:
                observations.append(_local_effect_observation(conn, current_op))
        evaluation = _evaluate(request.claim_type, workflow, current_op, observations, handoff)
        observed_at = datetime.now(UTC)
        receipt_id = uuid4()
        receipt_hash = _hash(
            {
                "id": str(receipt_id),
                "workflow_id": str(workflow["id"]),
                "operation_id": str(current_op["id"]),
                "revision": workflow["current_revision"],
                "claim_type": request.claim_type.value,
                "predicates": evaluation.predicates,
                "result": evaluation.result.value,
                "evidence": [_hash(o.raw) for o in observations],
                "verifier_version": VERIFIER_VERSION,
            }
        )
        valid_until = observed_at + timedelta(seconds=30)
        _execute(
            conn,
            "INSERT INTO verification_receipts (id,workflow_id,operation_id,intent_revision,"
            "actor_assumption,claim_type,predicates_json,result,observed_resource_version,"
            "verifier_version,valid_from,valid_until,receipt_hash) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s::verification_result,%s,%s,%s,%s,%s)",
            (
                receipt_id,
                workflow["id"],
                current_op["id"],
                workflow["current_revision"],
                str(workflow["actor_id"]),
                request.claim_type.value,
                Jsonb(evaluation.predicates),
                evaluation.result.value,
                evaluation.resource_version,
                VERIFIER_VERSION,
                observed_at,
                valid_until,
                receipt_hash,
            ),
        )
        for observation in observations:
            _execute(
                conn,
                "INSERT INTO evidence_items (receipt_id,source_type,source_identifier,"
                "query_hash,observed_facts,source_version,observed_at,evidence_hash) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    receipt_id,
                    observation.source_type,
                    observation.source_identifier,
                    _hash(observation.query),
                    Jsonb(observation.raw),
                    observation.source_version,
                    observation.observed_at,
                    _hash({"query": observation.query, "raw": observation.raw}),
                ),
            )
            if observation.source_type.startswith("SIMULATOR"):
                _execute(
                    conn,
                    "INSERT INTO provider_events (operation_id,event_kind,raw_json,"
                    "normalized_json,content_hash,trace_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (
                        current_op["id"],
                        "VERIFICATION_READ",
                        Jsonb(observation.raw),
                        Jsonb(
                            {
                                "result": evaluation.result.value,
                                "claim_type": request.claim_type.value,
                            }
                        ),
                        _hash(observation.raw),
                        trace_id,
                    ),
                )
        _event(
            conn,
            workflow,
            "Verification" + evaluation.result.value.title(),
            workflow["current_revision"],
            current_op["id"],
            request.command_id,
            {"receipt_id": str(receipt_id), "result": evaluation.result.value},
            trace_id,
        )
        _event(
            conn,
            workflow,
            "ReceiptIssued",
            workflow["current_revision"],
            current_op["id"],
            request.command_id,
            {"receipt_id": str(receipt_id), "receipt_hash": receipt_hash},
            trace_id,
        )
        response = {
            "receipt_id": str(receipt_id),
            "result": evaluation.result.value,
            "claim_type": request.claim_type.value,
            "intent_revision": workflow["current_revision"],
            "observed_resource_version": evaluation.resource_version,
            "valid_until": valid_until.isoformat(),
        }
        _receipt(
            conn, request.command_id, "issue_verification", workflow["id"], request_hash, response
        )
        return response


def receipt_detail(receipt_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        receipt = _one(conn, "SELECT * FROM verification_receipts WHERE id=%s", (receipt_id,))
        if receipt is None:
            raise DomainProblem("receipt-not-found", "Receipt not found", "Unknown receipt", 404)
        evidence = _all(
            conn,
            "SELECT * FROM evidence_items WHERE receipt_id=%s ORDER BY observed_at,id",
            (receipt_id,),
        )
    return {"receipt": receipt, "evidence_items": evidence}
