"""Prepare stable external operation identity without calling a provider."""

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
from apps.api_controller.phase2_models import PrepareExternalAppointmentRequest


def prepare_external(request: PrepareExternalAppointmentRequest, trace_id: str) -> dict[str, Any]:
    with _connection() as conn:
        workflow = _workflow(conn, request.workflow_id)
        revision = _one(
            conn,
            "SELECT desired_state_json FROM intent_revisions WHERE workflow_id=%s AND revision=%s",
            (request.workflow_id, request.expected_intent_revision),
        )
        if revision is None:
            raise DomainProblem(
                "stale-intent-revision", "Stale intent revision", "Revision was not accepted"
            )
        desired = revision["desired_state_json"]
        ticket = _one(
            conn,
            "SELECT property_id FROM maintenance_tickets WHERE id=%s AND resident_id=%s",
            (UUID(desired["ticket_id"]), workflow["resident_id"]),
        )
        if ticket is None:
            raise DomainProblem(
                "ticket-scope", "Ticket scope mismatch", "Ticket is outside the workflow"
            )
        normalized = {
            "scenario_id": str(request.scenario_id),
            "workflow_id": str(request.workflow_id),
            "intent_revision": request.expected_intent_revision,
            "expected_resource_version": request.expected_resource_version,
            "resource_key": f"property:{ticket['property_id']}:maintenance",
            "desired_state": desired,
            "action": "CREATE" if not desired.get("appointment_id") else "RESCHEDULE",
        }
        request_hash = _hash(normalized)
        replay = _command_replay(conn, request.command_id, "prepare_external", request_hash)
        if replay is not None:
            return replay
        if workflow["current_revision"] != request.expected_intent_revision:
            raise DomainProblem(
                "stale-intent-revision", "Stale intent revision", "Operation revision is obsolete"
            )
        existing = _one(
            conn,
            "SELECT id,request_hash,processing_phase,effect_knowledge "
            "FROM operations WHERE idempotency_key=%s",
            (request.idempotency_key,),
        )
        if existing is not None:
            if existing["request_hash"] != request_hash:
                raise DomainProblem(
                    "idempotency-conflict",
                    "Idempotency key conflict",
                    "Key was reused with changed request",
                )
            response = {
                "operation_id": str(existing["id"]),
                "processing_phase": existing["processing_phase"],
                "effect_knowledge": existing["effect_knowledge"],
            }
            _receipt(
                conn,
                request.command_id,
                "prepare_external",
                request.workflow_id,
                request_hash,
                response,
            )
            return response
        operation_id = uuid4()
        _execute(
            conn,
            "INSERT INTO operations (id,workflow_id,intent_revision,action_type,target_resource_type,"
            "target_resource_id,processing_phase,idempotency_key,request_hash,normalized_request_json,"
            "provider_adapter) VALUES (%s,%s,%s,%s,'appointment',%s,'READY',%s,%s,%s,'simulator')",
            (
                operation_id,
                request.workflow_id,
                request.expected_intent_revision,
                "CREATE_APPOINTMENT"
                if normalized["action"] == "CREATE"
                else "RESCHEDULE_APPOINTMENT",
                UUID(desired["appointment_id"]) if desired.get("appointment_id") else None,
                request.idempotency_key,
                request_hash,
                Jsonb(normalized),
            ),
        )
        _execute(
            conn,
            "INSERT INTO reconciliation_jobs (operation_id,job_type) VALUES (%s,'DISPATCH_OPERATION')",
            (operation_id,),
        )
        _event(
            conn,
            workflow,
            "OperationReady",
            request.expected_intent_revision,
            operation_id,
            request.command_id,
            {"request_hash": request_hash},
            trace_id,
        )
        response = {
            "operation_id": str(operation_id),
            "processing_phase": "READY",
            "effect_knowledge": "NOT_ATTEMPTED",
        }
        _receipt(
            conn,
            request.command_id,
            "prepare_external",
            request.workflow_id,
            request_hash,
            response,
        )
        return response


def operation_detail(operation_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (operation_id,))
        if operation is None:
            raise DomainProblem(
                "operation-not-found", "Operation not found", "Unknown operation", 404
            )
        attempts = _all(
            conn,
            "SELECT id,attempt_number,attempt_type,request_hash,request_sent_at,"
            "response_received_at,raw_response_json,normalized_result_json,result_code,trace_id "
            "FROM operation_attempts WHERE operation_id=%s ORDER BY attempt_number",
            (operation_id,),
        )
        events = _all(
            conn,
            "SELECT id,event_kind,raw_json,normalized_json,content_hash,trace_id,occurred_at "
            "FROM provider_events WHERE operation_id=%s ORDER BY occurred_at,id",
            (operation_id,),
        )
        jobs = _all(
            conn,
            "SELECT id,job_type,state,attempt_count,max_attempts,next_run_at,lease_owner,"
            "lease_until,last_error_json FROM reconciliation_jobs WHERE operation_id=%s "
            "ORDER BY created_at,id",
            (operation_id,),
        )
    return {"operation": operation, "attempts": attempts, "provider_events": events, "jobs": jobs}
