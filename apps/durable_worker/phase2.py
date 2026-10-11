"""Lease-based dispatch and reconcile-before-retry for simulator operations."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb

from apps.api_controller.phase1_service import (
    _connection,
    _event,
    _execute,
    _hash,
    _one,
    _workflow,
)
from packages.domain.revision_policy import revision_transition
from packages.provider_adapters.simulator import (
    Exchange,
    operation_status,
    resource_state,
    scenario_config,
    send_operation,
)


class WorkerCrash(Exception):
    """Deterministic crash injection immediately after a durable boundary."""

    def __init__(self, boundary: str) -> None:
        self.boundary = boundary
        super().__init__(boundary)


def _crash(boundary: str, crash_at: str | None) -> None:
    if crash_at == boundary:
        raise WorkerCrash(boundary)


@dataclass(frozen=True)
class Lease:
    id: UUID
    operation_id: UUID
    job_type: str
    attempt_count: int
    max_attempts: int


def lease_one(owner: str, operation_id: UUID | None = None) -> Lease | None:
    """PostgreSQL SKIP LOCKED lease; no network action occurs in this transaction."""
    with _connection() as conn:
        scope = "AND operation_id=%s " if operation_id is not None else ""
        row = _one(
            conn,
            "SELECT * FROM reconciliation_jobs WHERE "
            "((state='READY' AND next_run_at<=now()) OR "
            "(state='LEASED' AND lease_until<now())) "
            + scope
            + "ORDER BY next_run_at,id FOR UPDATE SKIP LOCKED LIMIT 1",
            (operation_id,) if operation_id is not None else (),
        )
        if row is None:
            return None
        updated = _one(
            conn,
            "UPDATE reconciliation_jobs SET state='LEASED',lease_owner=%s,"
            "lease_until=now()+interval '180 seconds',attempt_count=attempt_count+1,"
            "updated_at=now() WHERE id=%s RETURNING attempt_count,max_attempts",
            (owner, row["id"]),
        )
        assert updated is not None
        return Lease(
            row["id"],
            row["operation_id"],
            row["job_type"],
            updated["attempt_count"],
            updated["max_attempts"],
        )


def _job_done(conn: psycopg.Connection[Any], job_id: UUID) -> None:
    _execute(
        conn,
        "UPDATE reconciliation_jobs SET state='DONE',lease_owner=NULL,lease_until=NULL,"
        "updated_at=now() WHERE id=%s",
        (job_id,),
    )


def _job_ready(conn: psycopg.Connection[Any], job_id: UUID) -> None:
    _execute(
        conn,
        "UPDATE reconciliation_jobs SET state='READY',lease_owner=NULL,lease_until=NULL,"
        "next_run_at=now(),updated_at=now() WHERE id=%s",
        (job_id,),
    )


def _enqueue(conn: psycopg.Connection[Any], operation_id: UUID, job_type: str) -> None:
    _execute(
        conn,
        "INSERT INTO reconciliation_jobs (operation_id,job_type) VALUES (%s,%s) "
        "ON CONFLICT DO NOTHING",
        (operation_id, job_type),
    )


def _provider_event(
    conn: psycopg.Connection[Any],
    operation_id: UUID,
    attempt_id: UUID | None,
    kind: str,
    raw: dict[str, Any],
    normalized: dict[str, Any],
    trace_id: str,
) -> None:
    _execute(
        conn,
        "INSERT INTO provider_events (operation_id,attempt_id,event_kind,raw_json,"
        "normalized_json,content_hash,trace_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (operation_id, attempt_id, kind, Jsonb(raw), Jsonb(normalized), _hash(raw), trace_id),
    )


def _attempt_number(conn: psycopg.Connection[Any], operation_id: UUID) -> int:
    row = _one(
        conn,
        "SELECT COALESCE(max(attempt_number),0)+1 AS next "
        "FROM operation_attempts WHERE operation_id=%s",
        (operation_id,),
    )
    assert row is not None
    value: int = row["next"]
    return value


def _provider_payload(operation: dict[str, Any]) -> dict[str, Any]:
    normalized = operation["normalized_request_json"]
    desired = normalized["desired_state"]
    return {
        "scenario_id": normalized["scenario_id"],
        "operation_id": str(operation["id"]),
        "idempotency_key": operation["idempotency_key"],
        "request_hash": operation["request_hash"],
        "action": normalized["action"],
        "resource_key": normalized["resource_key"],
        "requested_start": desired.get("requested_start")
        if normalized["action"] != "CANCEL"
        else None,
        "requested_end": desired.get("requested_end") if normalized["action"] != "CANCEL" else None,
        "timezone": desired.get("timezone") if normalized["action"] != "CANCEL" else None,
        "appointment_id": normalized.get("appointment_id") or desired.get("appointment_id"),
        "expected_resource_version": normalized.get("expected_resource_version"),
    }


def _same_instant(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    return datetime.fromisoformat(left) == datetime.fromisoformat(right)


def _ambiguous_after_possible_send(
    conn: psycopg.Connection[Any],
    workflow: dict[str, Any],
    operation: dict[str, Any],
    lease: Lease,
    trace_id: str,
    raw: dict[str, Any],
    attempt_id: UUID | None,
) -> None:
    _execute(
        conn,
        "UPDATE operations SET processing_phase='RECONCILING',effect_knowledge='UNKNOWN',"
        "reconciliation_required=true,version=version+1,updated_at=now() WHERE id=%s",
        (operation["id"],),
    )
    _provider_event(
        conn,
        operation["id"],
        attempt_id,
        "AMBIGUOUS_RESPONSE",
        raw,
        {"outcome": "UNKNOWN"},
        trace_id,
    )
    _event(
        conn,
        workflow,
        "OperationOutcomeUnknown",
        operation["intent_revision"],
        operation["id"],
        uuid4(),
        {"reason": raw},
        trace_id,
    )
    _job_done(conn, lease.id)
    _enqueue(conn, operation["id"], "RECONCILE_OPERATION")
    _event(
        conn,
        workflow,
        "ReconciliationScheduled",
        operation["intent_revision"],
        operation["id"],
        uuid4(),
        {"reason": "ambiguous_dispatch"},
        trace_id,
    )


def _dispatch(lease: Lease, trace_id: str, crash_at: str | None) -> dict[str, Any]:
    with _connection() as conn:
        locator = _one(
            conn, "SELECT workflow_id FROM operations WHERE id=%s", (lease.operation_id,)
        )
        assert locator is not None
        workflow = _workflow(conn, locator["workflow_id"])
        operation = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (lease.operation_id,)
        )
        assert operation is not None
        if operation["processing_phase"] in ("TERMINAL", "RECONCILING", "RESPONSE_RECEIVED"):
            _job_done(conn, lease.id)
            if operation["effect_knowledge"] == "UNKNOWN":
                _enqueue(conn, lease.operation_id, "RECONCILE_OPERATION")
            return {"job_id": str(lease.id), "action": "dispatch_skipped", "state": "DONE"}
        if (
            workflow["current_revision"] != operation["intent_revision"]
            and operation["dispatch_recorded_at"] is None
        ):
            _execute(
                conn,
                "UPDATE operations SET processing_phase='TERMINAL',effect_knowledge='ABSENT',"
                "applicability='SUPERSEDED',updated_at=now() WHERE id=%s",
                (lease.operation_id,),
            )
            _job_done(conn, lease.id)
            _event(
                conn,
                workflow,
                "OperationCancelledBeforeDispatch",
                operation["intent_revision"],
                lease.operation_id,
                uuid4(),
                {},
                trace_id,
            )
            return {"job_id": str(lease.id), "action": "cancelled_before_dispatch", "state": "DONE"}
        attempt = _one(
            conn,
            "SELECT * FROM operation_attempts WHERE operation_id=%s "
            "ORDER BY attempt_number DESC LIMIT 1 FOR UPDATE",
            (lease.operation_id,),
        )
        if operation["processing_phase"] == "READY":
            attempt_id = uuid4()
            _execute(
                conn,
                "INSERT INTO operation_attempts (id,operation_id,attempt_number,attempt_type,"
                "request_hash,trace_id) VALUES (%s,%s,%s,'WRITE',%s,%s)",
                (
                    attempt_id,
                    lease.operation_id,
                    _attempt_number(conn, lease.operation_id),
                    operation["request_hash"],
                    trace_id,
                ),
            )
            _execute(
                conn,
                "UPDATE operations SET processing_phase='DISPATCH_RECORDED',"
                "effect_knowledge='NOT_ATTEMPTED',dispatch_recorded_at=now(),"
                "updated_at=now(),version=version+1 WHERE id=%s",
                (lease.operation_id,),
            )
            _event(
                conn,
                workflow,
                "DispatchRecorded",
                operation["intent_revision"],
                lease.operation_id,
                uuid4(),
                {"attempt_id": str(attempt_id)},
                trace_id,
            )
        else:
            if attempt is None:
                raise RuntimeError("Dispatch marker has no durable attempt")
            attempt_id = attempt["id"]
            if attempt["request_sent_at"] is not None:
                _ambiguous_after_possible_send(
                    conn,
                    workflow,
                    operation,
                    lease,
                    trace_id,
                    {"recovered_after_crash": True},
                    attempt_id,
                )
                return {
                    "job_id": str(lease.id),
                    "action": "reconciled_without_resend",
                    "state": "DONE",
                }
    _crash("AFTER_DISPATCH_RECORDED", crash_at)

    with _connection() as conn:
        locator = _one(
            conn, "SELECT workflow_id FROM operations WHERE id=%s", (lease.operation_id,)
        )
        assert locator is not None
        workflow = _workflow(conn, locator["workflow_id"])
        operation = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (lease.operation_id,)
        )
        assert operation is not None
        if workflow["current_revision"] != operation["intent_revision"]:
            _execute(
                conn,
                "UPDATE operations SET processing_phase='TERMINAL',"
                "effect_knowledge='ABSENT',applicability='SUPERSEDED',"
                "reconciliation_required=false,updated_at=now() WHERE id=%s",
                (lease.operation_id,),
            )
            _job_done(conn, lease.id)
            return {"job_id": str(lease.id), "action": "cancelled_before_send", "state": "DONE"}
        _execute(
            conn, "UPDATE operation_attempts SET request_sent_at=now() WHERE id=%s", (attempt_id,)
        )
        payload = _provider_payload(operation)
        _provider_event(
            conn,
            lease.operation_id,
            attempt_id,
            "REQUEST_SENT",
            payload,
            {"request_hash": operation["request_hash"]},
            trace_id,
        )
        _event(
            conn,
            workflow,
            "ProviderRequestSent",
            operation["intent_revision"],
            lease.operation_id,
            uuid4(),
            {"attempt_id": str(attempt_id)},
            trace_id,
        )
    _crash("AFTER_SEND_MARKER", crash_at)

    response = send_operation(payload)
    _crash("AFTER_PROVIDER_CALL", crash_at)
    with _connection() as conn:
        locator = _one(
            conn, "SELECT workflow_id FROM operations WHERE id=%s", (lease.operation_id,)
        )
        assert locator is not None
        workflow = _workflow(conn, locator["workflow_id"])
        operation = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (lease.operation_id,)
        )
        assert operation is not None
        already_observed = operation["effect_knowledge"] in ("PRESENT", "COMPENSATED")
        if response.status == 200 and response.body is not None:
            _execute(
                conn,
                "UPDATE operation_attempts SET response_received_at=now(),raw_response_json=%s,"
                "normalized_result_json=%s,result_code='ACKNOWLEDGED_UNVERIFIED' WHERE id=%s",
                (Jsonb(response.raw), Jsonb(response.body), attempt_id),
            )
            if not already_observed:
                _execute(
                    conn,
                    "UPDATE operations SET processing_phase='RESPONSE_RECEIVED',"
                    "effect_knowledge='UNKNOWN',response_received_at=now(),"
                    "reconciliation_required=true,version=version+1,updated_at=now() WHERE id=%s",
                    (lease.operation_id,),
                )
            _provider_event(
                conn,
                lease.operation_id,
                attempt_id,
                "RESPONSE_RECEIVED",
                response.raw,
                {"outcome": "UNVERIFIED"},
                trace_id,
            )
            _event(
                conn,
                workflow,
                "ProviderResponseReceived",
                operation["intent_revision"],
                lease.operation_id,
                uuid4(),
                {"attempt_id": str(attempt_id)},
                trace_id,
            )
            _job_done(conn, lease.id)
            if not already_observed:
                _enqueue(conn, lease.operation_id, "RECONCILE_OPERATION")
        else:
            _execute(
                conn,
                "UPDATE operation_attempts SET response_received_at=%s,raw_response_json=%s,"
                "normalized_result_json=%s,result_code='AMBIGUOUS' WHERE id=%s",
                (
                    None if response.transport_error else datetime.now(UTC),
                    Jsonb(response.raw),
                    Jsonb({"outcome": "UNKNOWN"}),
                    attempt_id,
                ),
            )
            if already_observed:
                _job_done(conn, lease.id)
            else:
                _ambiguous_after_possible_send(
                    conn, workflow, operation, lease, trace_id, response.raw, attempt_id
                )
    _crash("AFTER_OUTCOME_RECORDED", crash_at)
    return {
        "job_id": str(lease.id),
        "action": "dispatch",
        "state": "DONE",
        "provider_status": response.status,
        "effect_knowledge": "UNKNOWN",
    }


def _known_effect(
    status: Exchange, resource: Exchange, normalized: dict[str, Any]
) -> tuple[str, dict[str, Any] | None, bool]:
    if status.status == 200 and status.body is not None and status.body.get("authoritative"):
        outcome = status.body.get("outcome")
        if outcome in ("PRESENT", "PARTIAL"):
            facts = status.body.get("facts")
            return outcome, facts if isinstance(facts, dict) else None, True
        if outcome == "ABSENT":
            return "ABSENT", None, True
    if resource.status == 200 and resource.body is not None and resource.body.get("authoritative"):
        desired = normalized["desired_state"]
        matches = [
            item
            for item in resource.body.get("appointments", [])
            if item.get("status") == "CONFIRMED"
            and _same_instant(item.get("starts_at"), desired.get("requested_start"))
            and _same_instant(item.get("ends_at"), desired.get("requested_end"))
        ]
        if len(matches) == 1:
            return "PRESENT", matches[0], True
    return "UNKNOWN", None, False


def _record_effect(
    conn: psycopg.Connection[Any],
    operation: dict[str, Any],
    facts: dict[str, Any],
    trace_id: str,
) -> None:
    existing = _one(
        conn, "SELECT id FROM effect_ledger WHERE operation_id=%s LIMIT 1", (operation["id"],)
    )
    if existing is not None:
        return
    _execute(
        conn,
        "INSERT INTO effect_ledger (operation_id,effect_type,resource_type,resource_id,"
        "before_facts,after_facts,observed_version,evidence_hash,observed_at) "
        "VALUES (%s,%s,'appointment',%s,NULL,%s,%s,%s,now())",
        (
            operation["id"],
            f"PROVIDER_{operation['action_type']}",
            facts["appointment_id"],
            Jsonb(facts),
            str(facts["version"]),
            _hash(facts),
        ),
    )


def _new_linked_operation(
    conn: psycopg.Connection[Any],
    workflow: dict[str, Any],
    parent: dict[str, Any],
    action: str,
    appointment_id: str | None,
    expected_version: int,
    trace_id: str,
    compensation: bool,
) -> UUID:
    existing = _one(
        conn,
        "SELECT id FROM operations WHERE workflow_id=%s AND intent_revision=%s "
        "AND provider_adapter='simulator' AND applicability='CURRENT' "
        "AND id<>%s AND normalized_request_json->>'action'=%s LIMIT 1",
        (workflow["id"], workflow["current_revision"], parent["id"], action),
    )
    if existing is not None:
        value: UUID = existing["id"]
        return value
    desired = workflow["desired_state_json"]
    old = parent["normalized_request_json"]
    normalized = {
        "scenario_id": old["scenario_id"],
        "workflow_id": str(workflow["id"]),
        "intent_revision": workflow["current_revision"],
        "expected_resource_version": expected_version,
        "resource_key": old["resource_key"],
        "desired_state": desired,
        "action": action,
        "appointment_id": appointment_id,
    }
    operation_id = uuid4()
    request_hash = _hash(normalized)
    key = f"linked:{workflow['id']}:{workflow['current_revision']}:{action}"
    _execute(
        conn,
        "INSERT INTO operations (id,workflow_id,intent_revision,parent_operation_id,"
        "supersedes_operation_id,action_type,target_resource_type,target_resource_id,"
        "processing_phase,idempotency_key,request_hash,normalized_request_json,provider_adapter) "
        "VALUES (%s,%s,%s,%s,%s,%s,'appointment',%s,'READY',%s,%s,%s,'simulator')",
        (
            operation_id,
            workflow["id"],
            workflow["current_revision"],
            parent["id"],
            parent["id"],
            "COMPENSATE_CANCEL"
            if compensation
            else (
                "CANCEL_APPOINTMENT"
                if action == "CANCEL"
                else "RESCHEDULE_APPOINTMENT"
                if action == "RESCHEDULE"
                else "CREATE_APPOINTMENT"
            ),
            UUID(appointment_id) if appointment_id else None,
            key,
            request_hash,
            Jsonb(normalized),
        ),
    )
    _enqueue(conn, operation_id, "DISPATCH_OPERATION")
    _event(
        conn,
        workflow,
        "CompensationPlanned" if compensation else "OperationReady",
        workflow["current_revision"],
        operation_id,
        uuid4(),
        {"parent_operation_id": str(parent["id"]), "action": action},
        trace_id,
    )
    return operation_id


def _handoff(
    conn: psycopg.Connection[Any],
    workflow: dict[str, Any],
    operation: dict[str, Any],
    lease: Lease,
    trace_id: str,
    reason: str,
    observations: dict[str, Any],
    *,
    effect_absent: bool = False,
    effect_partial: bool = False,
    effect_present: bool = False,
) -> None:
    known = {"operation_id": str(operation["id"]), "observations": observations}
    unknown = {"effect_outcome": "UNKNOWN"}
    if effect_absent:
        known["effect_outcome"] = "ABSENT"
        unknown = {"final_intent_resolution": "UNRESOLVED"}
    elif effect_partial:
        known["effect_outcome"] = "PARTIAL"
        unknown = {"final_intent_resolution": "UNRESOLVED"}
    elif effect_present:
        known["effect_outcome"] = "PRESENT"
        unknown = {"final_intent_resolution": "UNRESOLVED"}
    _execute(
        conn,
        "INSERT INTO handoffs (workflow_id,resident_id,reason_code,priority,known_facts,"
        "unknown_facts,linked_operation_ids,deadline_at,state) "
        "VALUES (%s,%s,%s,'STANDARD',%s,%s,%s,now()+interval '1 day','OPEN')",
        (
            workflow["id"],
            workflow["resident_id"],
            reason,
            Jsonb(known),
            Jsonb(unknown),
            [operation["id"]],
        ),
    )
    _execute(
        conn,
        "UPDATE workflows SET resolution_status='HANDOFF',updated_at=now() WHERE id=%s",
        (workflow["id"],),
    )
    _execute(
        conn,
        "UPDATE reconciliation_jobs SET state='HANDOFF',lease_owner=NULL,"
        "lease_until=NULL,last_error_json=%s,updated_at=now() WHERE id=%s",
        (Jsonb({"reason": reason}), lease.id),
    )
    _event(
        conn,
        workflow,
        "WorkflowEscalated",
        workflow["current_revision"],
        operation["id"],
        uuid4(),
        {"reason": reason},
        trace_id,
    )


def _reconcile(lease: Lease, trace_id: str, crash_at: str | None) -> dict[str, Any]:
    with _connection() as conn:
        operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (lease.operation_id,))
    assert operation is not None
    normalized = operation["normalized_request_json"]
    scenario_id = UUID(normalized["scenario_id"])
    _crash("BEFORE_LOOKUP", crash_at)
    status = operation_status(scenario_id, lease.operation_id)
    resource = resource_state(scenario_id, lease.operation_id, normalized["resource_key"])
    config = scenario_config(scenario_id)
    _crash("AFTER_LOOKUP", crash_at)
    outcome, facts, authoritative = _known_effect(status, resource, normalized)
    provider_config = config.body.get("config", {}) if config.body else {}
    with _connection() as conn:
        workflow = _workflow(conn, operation["workflow_id"])
        current_op = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (lease.operation_id,)
        )
        assert current_op is not None
        attempt_id = uuid4()
        _execute(
            conn,
            "INSERT INTO operation_attempts (id,operation_id,attempt_number,attempt_type,"
            "request_hash,request_sent_at,response_received_at,raw_response_json,"
            "normalized_result_json,result_code,trace_id) "
            "VALUES (%s,%s,%s,'STATUS_LOOKUP',%s,now(),now(),%s,%s,%s,%s)",
            (
                attempt_id,
                lease.operation_id,
                _attempt_number(conn, lease.operation_id),
                current_op["request_hash"],
                Jsonb({"status": status.raw, "resource": resource.raw, "capability": config.raw}),
                Jsonb({"outcome": outcome, "authoritative": authoritative}),
                outcome,
                trace_id,
            ),
        )
        _provider_event(
            conn,
            lease.operation_id,
            attempt_id,
            "STATUS_LOOKUP",
            status.raw,
            status.body or {"outcome": "UNKNOWN"},
            trace_id,
        )
        _provider_event(
            conn,
            lease.operation_id,
            attempt_id,
            "POSTCONDITION_READ",
            resource.raw,
            resource.body or {"outcome": "UNKNOWN"},
            trace_id,
        )
        if outcome == "PRESENT" and facts is not None:
            _record_effect(conn, current_op, facts, trace_id)
            _execute(
                conn,
                "UPDATE operations SET effect_knowledge='PRESENT',processing_phase='TERMINAL',"
                "target_resource_id=%s,effect_observed_at=now(),resolved_at=now(),"
                "reconciliation_required=false,version=version+1,updated_at=now() WHERE id=%s",
                (UUID(facts["appointment_id"]), lease.operation_id),
            )
            _event(
                conn,
                workflow,
                "ProviderEffectObserved",
                current_op["intent_revision"],
                lease.operation_id,
                uuid4(),
                {"facts_hash": _hash(facts)},
                trace_id,
            )
            _job_done(conn, lease.id)
            if workflow["current_revision"] > current_op["intent_revision"]:
                revision = _one(
                    conn,
                    "SELECT change_class FROM intent_revisions WHERE workflow_id=%s AND revision=%s",
                    (workflow["id"], workflow["current_revision"]),
                )
                assert revision is not None
                transition = revision_transition(
                    revision["change_class"],
                    workflow["desired_state_json"],
                    facts,
                    provider_config.get("supports_reschedule", True),
                )
                reusable_now = (
                    (
                        resource.status == 200
                        and resource.body is not None
                        and resource.body.get("authoritative")
                        and len(resource.body.get("appointments", [])) == 1
                        and revision_transition(
                            revision["change_class"],
                            workflow["desired_state_json"],
                            resource.body["appointments"][0],
                            True,
                        )
                        == "REUSE"
                        and resource.body["appointments"][0].get("status") == "CONFIRMED"
                        and resource.body["appointments"][0].get("appointment_id")
                        == facts["appointment_id"]
                    )
                    if transition == "REUSE"
                    else False
                )
                if transition == "REUSE" and not reusable_now:
                    _handoff(
                        conn,
                        workflow,
                        current_op,
                        lease,
                        trace_id,
                        "REUSE_RESOURCE_NOT_CURRENT",
                        resource.raw,
                        effect_present=True,
                    )
                elif transition == "REUSE":
                    _execute(
                        conn,
                        "UPDATE operations SET applicability='REUSABLE' WHERE id=%s",
                        (current_op["id"],),
                    )
                    _execute(
                        conn,
                        "UPDATE workflows SET resolution_status='RESOLVED',updated_at=now() WHERE id=%s",
                        (workflow["id"],),
                    )
                    _event(
                        conn,
                        workflow,
                        "WorkflowResolved",
                        workflow["current_revision"],
                        current_op["id"],
                        uuid4(),
                        {"resource_version": facts["version"], "reused_effect": True},
                        trace_id,
                    )
                else:
                    _new_linked_operation(
                        conn,
                        workflow,
                        current_op,
                        "RESCHEDULE" if transition == "RESCHEDULE" else "CANCEL",
                        facts["appointment_id"],
                        int(facts["version"]),
                        trace_id,
                        compensation=transition == "COMPENSATE",
                    )
            elif current_op["action_type"] == "COMPENSATE_CANCEL":
                _new_linked_operation(
                    conn, workflow, current_op, "CREATE", None, 0, trace_id, compensation=False
                )
            elif resource.status == 200 and resource.body and resource.body.get("authoritative"):
                desired = workflow["desired_state_json"]
                active = [
                    item
                    for item in resource.body.get("appointments", [])
                    if item.get("status") == "CONFIRMED"
                ]
                matches = [
                    item
                    for item in active
                    if _same_instant(item.get("starts_at"), desired.get("requested_start"))
                    and _same_instant(item.get("ends_at"), desired.get("requested_end"))
                ]
                if len(active) == len(matches) == 1 or (
                    current_op["action_type"] == "CANCEL_APPOINTMENT" and not active
                ):
                    _execute(
                        conn,
                        "UPDATE workflows SET resolution_status='RESOLVED',"
                        "updated_at=now() WHERE id=%s",
                        (workflow["id"],),
                    )
                    _event(
                        conn,
                        workflow,
                        "WorkflowResolved",
                        workflow["current_revision"],
                        lease.operation_id,
                        uuid4(),
                        {"resource_version": facts["version"]},
                        trace_id,
                    )
        elif outcome == "ABSENT" and authoritative:
            write_budget = _one(
                conn,
                "SELECT count(*) AS attempts FROM operation_attempts "
                "WHERE operation_id=%s AND attempt_type='WRITE'",
                (lease.operation_id,),
            )
            assert write_budget is not None
            last_write = _one(
                conn,
                "SELECT raw_response_json FROM operation_attempts "
                "WHERE operation_id=%s AND attempt_type='WRITE' "
                "ORDER BY attempt_number DESC LIMIT 1",
                (lease.operation_id,),
            )
            conflict = bool(
                last_write
                and last_write["raw_response_json"]
                and last_write["raw_response_json"].get("status") == 409
            )
            if conflict:
                _execute(
                    conn,
                    "UPDATE operations SET processing_phase='TERMINAL',effect_knowledge='ABSENT',"
                    "effect_observed_at=now(),resolved_at=now(),reconciliation_required=false,"
                    "version=version+1,updated_at=now() WHERE id=%s",
                    (lease.operation_id,),
                )
                _handoff(
                    conn,
                    workflow,
                    current_op,
                    lease,
                    trace_id,
                    "PROVIDER_CONFLICT",
                    {"status": status.raw, "resource": resource.raw},
                    effect_absent=True,
                )
            elif (
                workflow["current_revision"] == current_op["intent_revision"]
                and provider_config.get("idempotency", False)
                and write_budget["attempts"] < lease.max_attempts
            ):
                _execute(
                    conn,
                    "UPDATE operations SET processing_phase='READY',"
                    "effect_knowledge='ABSENT',updated_at=now() WHERE id=%s",
                    (lease.operation_id,),
                )
                _job_done(conn, lease.id)
                _enqueue(conn, lease.operation_id, "DISPATCH_OPERATION")
                _event(
                    conn,
                    workflow,
                    "SafeRetryScheduled",
                    current_op["intent_revision"],
                    lease.operation_id,
                    uuid4(),
                    {"proof": "authoritative_absence_and_idempotency"},
                    trace_id,
                )
            elif workflow["current_revision"] > current_op["intent_revision"]:
                _execute(
                    conn,
                    "UPDATE operations SET processing_phase='TERMINAL',"
                    "effect_knowledge='ABSENT',reconciliation_required=false,updated_at=now() "
                    "WHERE id=%s",
                    (lease.operation_id,),
                )
                _job_done(conn, lease.id)
                _new_linked_operation(
                    conn, workflow, current_op, "CREATE", None, 0, trace_id, compensation=False
                )
            else:
                _handoff(
                    conn,
                    workflow,
                    current_op,
                    lease,
                    trace_id,
                    "RETRY_NOT_PROVABLY_SAFE_OR_BUDGET_EXHAUSTED",
                    {"status": status.raw, "resource": resource.raw},
                )
        else:
            _execute(
                conn,
                "UPDATE operations SET processing_phase='RECONCILING',"
                "effect_knowledge=%s::effect_knowledge,reconciliation_required=true,"
                "updated_at=now() WHERE id=%s",
                ("PARTIAL" if outcome == "PARTIAL" else "UNKNOWN", lease.operation_id),
            )
            _event(
                conn,
                workflow,
                "ReconciliationPending",
                current_op["intent_revision"],
                lease.operation_id,
                uuid4(),
                {"outcome": outcome},
                trace_id,
            )
            if lease.attempt_count >= lease.max_attempts:
                _handoff(
                    conn,
                    workflow,
                    current_op,
                    lease,
                    trace_id,
                    "RECONCILIATION_BUDGET_EXHAUSTED",
                    {"status": status.raw, "resource": resource.raw},
                    effect_partial=outcome == "PARTIAL",
                )
            else:
                _job_ready(conn, lease.id)
    _crash("AFTER_RECONCILIATION_RECORDED", crash_at)
    return {"job_id": str(lease.id), "action": "reconcile", "outcome": outcome}


def step(
    owner: str = "phase2-worker",
    crash_at: str | None = None,
    operation_id: UUID | None = None,
) -> dict[str, Any]:
    lease = lease_one(owner, operation_id)
    if lease is None:
        return {"action": "idle"}
    _crash("AFTER_LEASE", crash_at)
    trace_id = f"worker:{uuid4()}"
    if lease.job_type == "DISPATCH_OPERATION":
        return _dispatch(lease, trace_id, crash_at)
    if lease.job_type == "RECONCILE_OPERATION":
        return _reconcile(lease, trace_id, crash_at)
    with _connection() as conn:
        _job_done(conn, lease.id)
    return {"job_id": str(lease.id), "action": "unsupported_job", "state": "DONE"}
