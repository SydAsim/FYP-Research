"""Phase 1 PostgreSQL command handlers. Every handler owns one short transaction."""

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.errors import ExclusionViolation, UniqueViolation
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from apps.api_controller.phase1_models import (
    AcceptRevisionRequest,
    CommitLocalRequest,
    PrepareAppointmentRequest,
    SyntheticFixtureRequest,
)
from packages.domain.phase1 import (
    Applicability,
    EffectKnowledge,
    OperationDimensions,
    ProcessingPhase,
    SpeechEligibility,
    local_commit_dimensions,
    supersede_dimensions,
)


class DomainProblem(Exception):
    def __init__(self, slug: str, title: str, detail: str, status: int = 409) -> None:
        self.slug = slug
        self.title = title
        self.detail = detail
        self.status = status
        super().__init__(detail)


def _connection() -> psycopg.Connection[Any]:
    dsn = os.environ.get(
        "DATABASE_SYNC_URL",
        "postgresql://voice_agent:voice_agent_local@127.0.0.1:5432/voice_agent",
    )
    return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, options="-c timezone=UTC")


def _one(
    conn: psycopg.Connection[Any], sql: str, params: tuple[Any, ...] = ()
) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    return row


def _all(
    conn: psycopg.Connection[Any], sql: str, params: tuple[Any, ...] = ()
) -> list[dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return rows


def _execute(conn: psycopg.Connection[Any], sql: str, params: tuple[Any, ...] = ()) -> None:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)


def _hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(data).hexdigest()


def _command_replay(
    conn: psycopg.Connection[Any], command_id: UUID, command_type: str, request_hash: str
) -> dict[str, Any] | None:
    row = _one(
        conn,
        "SELECT command_type, request_hash, response_json FROM command_receipts WHERE command_id=%s",
        (command_id,),
    )
    if row is None:
        return None
    if row["command_type"] != command_type or row["request_hash"] != request_hash:
        raise DomainProblem(
            "idempotency-conflict",
            "Command identity conflict",
            "Command ID was reused with a changed request",
        )
    response: dict[str, Any] = row["response_json"]
    return response


def _receipt(
    conn: psycopg.Connection[Any],
    command_id: UUID,
    command_type: str,
    workflow_id: UUID,
    request_hash: str,
    response: dict[str, Any],
) -> None:
    _execute(
        conn,
        "INSERT INTO command_receipts (command_id, command_type, workflow_id, request_hash, response_json) "
        "VALUES (%s,%s,%s,%s,%s)",
        (command_id, command_type, workflow_id, request_hash, Jsonb(response)),
    )


def _workflow(conn: psycopg.Connection[Any], workflow_id: UUID) -> dict[str, Any]:
    row = _one(conn, "SELECT * FROM workflows WHERE id=%s FOR UPDATE", (workflow_id,))
    if row is None:
        raise DomainProblem("workflow-not-found", "Workflow not found", "Unknown workflow", 404)
    return row


def _event(
    conn: psycopg.Connection[Any],
    workflow: dict[str, Any],
    name: str,
    revision: int | None,
    operation_id: UUID | None,
    command_id: UUID,
    payload: dict[str, Any],
    trace_id: str,
) -> UUID:
    seq = _one(
        conn,
        "UPDATE workflows SET workflow_sequence=workflow_sequence+1, updated_at=now() "
        "WHERE id=%s RETURNING workflow_sequence",
        (workflow["id"],),
    )
    assert seq is not None
    event_id = uuid4()
    _execute(
        conn,
        "INSERT INTO workflow_events (id,event_name,schema_version,occurred_at,workflow_id,"
        "workflow_sequence,operation_id,intent_revision,correlation_id,trace_id,actor_assumption,payload) "
        "VALUES (%s,%s,1,now(),%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            event_id,
            name,
            workflow["id"],
            seq["workflow_sequence"],
            operation_id,
            revision,
            command_id,
            trace_id,
            str(workflow["actor_id"]),
            Jsonb(payload),
        ),
    )
    _execute(
        conn,
        "INSERT INTO outbox (id,topic,payload) VALUES (%s,%s,%s)",
        (event_id, "workflow.events", Jsonb({"event_id": str(event_id), "event_name": name})),
    )
    return event_id


def create_fixture(request: SyntheticFixtureRequest) -> dict[str, Any]:
    """Create a bounded synthetic actor, resident, call, ticket and two utterances."""
    if request.research_arm is not None and os.environ.get("EXPERIMENT_MODE") != "true":
        raise DomainProblem(
            "experiment-only",
            "Experiment profile unavailable",
            "Research arms require experiment mode",
            403,
        )
    request_hash = _hash(request.model_dump(mode="json", exclude={"command_id"}))
    fixture_id = uuid4()
    actor_id, property_id, resident_id = uuid4(), uuid4(), uuid4()
    call_id, workflow_id, ticket_id = uuid4(), uuid4(), uuid4()
    utterance_ids = [uuid4(), uuid4()]
    with _connection() as conn:
        _execute(
            conn,
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (str(request.command_id),),
        )
        replay = _command_replay(conn, request.command_id, "create_fixture", request_hash)
        if replay is not None:
            return replay
        _execute(
            conn,
            "INSERT INTO actors (id,subject,display_name) VALUES (%s,%s,%s)",
            (actor_id, f"synthetic:{fixture_id}", "Synthetic Resident"),
        )
        _execute(
            conn,
            "INSERT INTO properties (id,external_ref,display_name,timezone) VALUES (%s,%s,%s,%s)",
            (property_id, f"synthetic:{fixture_id}", "Synthetic Property", request.timezone),
        )
        _execute(
            conn,
            "INSERT INTO residents (id,actor_id,property_id,unit_ref) VALUES (%s,%s,%s,%s)",
            (resident_id, actor_id, property_id, "A-1"),
        )
        _execute(
            conn,
            "INSERT INTO call_sessions (id,actor_id,resident_id,media_status,consent_json,livekit_room) "
            "VALUES (%s,%s,%s,'CREATED',%s,%s)",
            (
                call_id,
                actor_id,
                resident_id,
                Jsonb({"synthetic": True, "consent": True}),
                f"phase1-{fixture_id}",
            ),
        )
        _execute(
            conn,
            "INSERT INTO workflows (id,call_id,actor_id,resident_id,workflow_type,research_arm) "
            "VALUES (%s,%s,%s,%s,'MAINTENANCE_APPOINTMENT',%s)",
            (workflow_id, call_id, actor_id, resident_id, request.research_arm),
        )
        _execute(
            conn,
            "INSERT INTO maintenance_tickets (id,resident_id,property_id,issue_type,description,status) "
            "VALUES (%s,%s,%s,'GENERAL','Synthetic maintenance fixture','OPEN')",
            (ticket_id, resident_id, property_id),
        )
        for utterance_id, transcript in zip(
            utterance_ids, (request.first_transcript, request.second_transcript), strict=True
        ):
            _execute(
                conn,
                "INSERT INTO utterances (id,call_id,speaker,transcript,transcript_version,finalized,content_hash) "
                "VALUES (%s,%s,'USER',%s,1,true,%s)",
                (utterance_id, call_id, transcript, _hash(transcript)),
            )
        response = {
            "call_id": str(call_id),
            "workflow_id": str(workflow_id),
            "ticket_id": str(ticket_id),
            "resident_id": str(resident_id),
            "property_id": str(property_id),
            "resource_key": f"property:{property_id}:maintenance",
            "utterance_ids": [str(value) for value in utterance_ids],
        }
        _receipt(conn, request.command_id, "create_fixture", workflow_id, request_hash, response)
        return response


def accept_revision(
    workflow_id: UUID, request: AcceptRevisionRequest, trace_id: str
) -> dict[str, Any]:
    request_hash = _hash(request.model_dump(mode="json", exclude={"command_id"}))
    with _connection() as conn:
        workflow = _workflow(conn, workflow_id)
        replay = _command_replay(conn, request.command_id, "accept_revision", request_hash)
        if replay is not None:
            return replay
        current = workflow["current_revision"]
        if current != request.expected_revision:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                f"Expected revision {request.expected_revision} but revision {current} is current.",
            )
        if (current == 0) != (request.change_class == "INITIAL"):
            raise DomainProblem(
                "invalid-change-class",
                "Invalid change class",
                "INITIAL is valid only for revision 1",
            )
        ticket = _one(
            conn,
            "SELECT id FROM maintenance_tickets WHERE id=%s AND resident_id=%s",
            (request.desired_state.ticket_id, workflow["resident_id"]),
        )
        if ticket is None:
            raise DomainProblem(
                "ticket-scope",
                "Ticket scope mismatch",
                "Ticket does not belong to the workflow resident",
            )
        source = _one(
            conn,
            "SELECT id FROM utterances WHERE id=%s AND call_id=%s AND transcript_version=%s AND finalized=true",
            (
                request.candidate_source.utterance_id,
                workflow["call_id"],
                request.candidate_source.transcript_version,
            ),
        )
        if source is None:
            raise DomainProblem(
                "source-scope",
                "Candidate source mismatch",
                "Finalized utterance provenance is invalid",
            )
        if request.desired_state.appointment_id is not None:
            appointment = _one(
                conn,
                "SELECT id FROM appointments WHERE id=%s AND ticket_id=%s AND resident_id=%s",
                (request.desired_state.appointment_id, ticket["id"], workflow["resident_id"]),
            )
            if appointment is None:
                raise DomainProblem(
                    "appointment-scope",
                    "Appointment scope mismatch",
                    "Appointment is outside this ticket",
                )
        revision = current + 1
        desired = request.desired_state.model_dump(mode="json")
        _execute(
            conn,
            "INSERT INTO intent_revisions (workflow_id,revision,parent_revision,change_class,"
            "desired_state_json,structured_intent_json,source_utterance_id,source_span_json,"
            "model_id,prompt_hash,accepted_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                workflow_id,
                revision,
                current or None,
                request.change_class,
                Jsonb(desired),
                Jsonb({"type": "appointment", "desired": desired}),
                request.candidate_source.utterance_id,
                Jsonb(
                    {
                        "audio_start_ms": request.candidate_source.audio_start_ms,
                        "audio_end_ms": request.candidate_source.audio_end_ms,
                        "transcript_version": request.candidate_source.transcript_version,
                    }
                ),
                request.candidate_source.model,
                request.candidate_source.prompt_hash,
                str(workflow["actor_id"]),
            ),
        )
        _execute(
            conn,
            "UPDATE workflows SET current_revision=%s,desired_state_json=%s,version=version+1,updated_at=now() WHERE id=%s",
            (revision, Jsonb(desired), workflow_id),
        )
        for op in _all(
            conn,
            "SELECT * FROM operations WHERE workflow_id=%s AND intent_revision<%s "
            "AND applicability IN ('CURRENT','REUSABLE') ORDER BY id FOR UPDATE",
            (workflow_id, revision),
        ):
            dimensions = OperationDimensions(
                ProcessingPhase(op["processing_phase"]),
                EffectKnowledge(op["effect_knowledge"]),
                Applicability(op["applicability"]),
                SpeechEligibility(op["speech_eligibility"]),
            )
            dispatched_external = (
                op["provider_adapter"] == "simulator" and op["dispatch_recorded_at"] is not None
            )
            if dispatched_external:
                updated = OperationDimensions(
                    ProcessingPhase.RECONCILING,
                    dimensions.effect
                    if dimensions.effect in (EffectKnowledge.PRESENT, EffectKnowledge.PARTIAL)
                    else EffectKnowledge.UNKNOWN,
                    Applicability.SUPERSEDED,
                    SpeechEligibility.BLOCKED,
                )
            else:
                updated = supersede_dimensions(dimensions)
            _execute(
                conn,
                "UPDATE operations SET processing_phase=%s::processing_phase,"
                "effect_knowledge=%s::effect_knowledge,applicability=%s::applicability,"
                "speech_eligibility=%s::speech_eligibility,reconciliation_required=%s,"
                "version=version+1,updated_at=now() WHERE id=%s",
                (
                    updated.processing.value,
                    updated.effect.value,
                    updated.applicability.value,
                    updated.speech.value,
                    dispatched_external,
                    op["id"],
                ),
            )
            if dispatched_external:
                _execute(
                    conn,
                    "INSERT INTO reconciliation_jobs (operation_id,job_type) "
                    "VALUES (%s,'RECONCILE_OPERATION') ON CONFLICT DO NOTHING",
                    (op["id"],),
                )
                _event(
                    conn,
                    workflow,
                    "ReconciliationScheduled",
                    revision,
                    op["id"],
                    request.command_id,
                    {"reason": "accepted_correction"},
                    trace_id,
                )
            elif op["provider_adapter"] == "simulator":
                _execute(
                    conn,
                    "UPDATE reconciliation_jobs SET state='DONE',lease_owner=NULL,lease_until=NULL,"
                    "updated_at=now() WHERE operation_id=%s AND job_type='DISPATCH_OPERATION' "
                    "AND state IN ('READY','LEASED')",
                    (op["id"],),
                )
                _event(
                    conn,
                    workflow,
                    "OperationCancelledBeforeDispatch",
                    revision,
                    op["id"],
                    request.command_id,
                    {},
                    trace_id,
                )
            _event(
                conn,
                workflow,
                "OperationSuperseded",
                revision,
                op["id"],
                request.command_id,
                {
                    "previous_revision": op["intent_revision"],
                    "effect_knowledge": updated.effect.value,
                },
                trace_id,
            )
        accepted_event_id = _event(
            conn,
            workflow,
            "IntentRevisionAccepted",
            revision,
            None,
            request.command_id,
            {
                "revision": revision,
                "change_class": request.change_class,
                "desired_state_hash": _hash(desired),
            },
            trace_id,
        )
        for old_receipt in _all(
            conn,
            "UPDATE verification_receipts SET invalidated_at=now(),invalidating_event_id=%s "
            "WHERE workflow_id=%s AND intent_revision<%s AND invalidated_at IS NULL "
            "RETURNING id,operation_id,intent_revision",
            (accepted_event_id, workflow_id, revision),
        ):
            _event(
                conn,
                workflow,
                "ReceiptInvalidated",
                revision,
                old_receipt["operation_id"],
                request.command_id,
                {"receipt_id": str(old_receipt["id"]), "reason": "new_accepted_revision"},
                trace_id,
            )
        for old_permit in _all(
            conn,
            "UPDATE claim_permits SET state='INVALIDATED',invalidated_at=now(),"
            "invalidating_event_id=%s,version=version+1 WHERE workflow_id=%s "
            "AND intent_revision<%s AND state IN ('AUTHORIZED','QUEUED') "
            "RETURNING id,claim_id,intent_revision",
            (accepted_event_id, workflow_id, revision),
        ):
            claim_operation = _one(
                conn, "SELECT operation_id FROM claims WHERE id=%s", (old_permit["claim_id"],)
            )
            _event(
                conn,
                workflow,
                "ClaimPermitInvalidated",
                revision,
                claim_operation["operation_id"] if claim_operation else None,
                request.command_id,
                {"permit_id": str(old_permit["id"]), "reason": "new_accepted_revision"},
                trace_id,
            )
        from apps.api_controller.phase4_playback_service import on_revision_accepted

        on_revision_accepted(
            conn,
            {**workflow, "current_revision": revision, "desired_state_json": desired},
            revision,
            request.command_id,
            trace_id,
        )
        row = _one(
            conn,
            "SELECT accepted_at FROM intent_revisions WHERE workflow_id=%s AND revision=%s",
            (workflow_id, revision),
        )
        assert row is not None
        response = {
            "workflow_id": str(workflow_id),
            "revision": revision,
            "desired_state": desired,
            "accepted_at": row["accepted_at"].isoformat(),
        }
        _receipt(conn, request.command_id, "accept_revision", workflow_id, request_hash, response)
        return response


def prepare_appointment(request: PrepareAppointmentRequest, trace_id: str) -> dict[str, Any]:
    with _connection() as conn:
        workflow = _workflow(conn, request.workflow_id)
        revision = _one(
            conn,
            "SELECT desired_state_json FROM intent_revisions WHERE workflow_id=%s AND revision=%s",
            (request.workflow_id, request.expected_intent_revision),
        )
        if revision is None:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                "Operation revision is not accepted",
            )
        desired = revision["desired_state_json"]
        normalized = {
            "workflow_id": str(request.workflow_id),
            "intent_revision": request.expected_intent_revision,
            "expected_resource_version": request.expected_resource_version,
            "desired_state": desired,
        }
        request_hash = _hash(normalized)
        replay = _command_replay(conn, request.command_id, "prepare_appointment", request_hash)
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
                    "Key was reused with a changed request",
                )
            response = {
                "operation_id": str(existing["id"]),
                "processing_phase": existing["processing_phase"],
                "effect_knowledge": existing["effect_knowledge"],
            }
            _receipt(
                conn,
                request.command_id,
                "prepare_appointment",
                request.workflow_id,
                request_hash,
                response,
            )
            return response
        appointment_id = desired.get("appointment_id")
        if appointment_id:
            resource = _one(
                conn,
                "SELECT version FROM appointments WHERE id=%s AND ticket_id=%s FOR UPDATE",
                (UUID(appointment_id), UUID(desired["ticket_id"])),
            )
        else:
            resource = _one(
                conn,
                "SELECT version FROM maintenance_tickets WHERE id=%s AND resident_id=%s FOR UPDATE",
                (UUID(desired["ticket_id"]), workflow["resident_id"]),
            )
        if resource is None or resource["version"] != request.expected_resource_version:
            raise DomainProblem(
                "stale-resource-version", "Stale resource version", "Resource version has changed"
            )
        operation_id = uuid4()
        _execute(
            conn,
            "INSERT INTO operations (id,workflow_id,intent_revision,action_type,target_resource_type,"
            "target_resource_id,processing_phase,idempotency_key,request_hash,normalized_request_json,provider_adapter) "
            "VALUES (%s,%s,%s,%s,%s,%s,'READY',%s,%s,%s,'local_postgres')",
            (
                operation_id,
                request.workflow_id,
                request.expected_intent_revision,
                "RESCHEDULE_APPOINTMENT" if appointment_id else "CREATE_APPOINTMENT",
                "appointment" if appointment_id else "ticket",
                UUID(appointment_id) if appointment_id else UUID(desired["ticket_id"]),
                request.idempotency_key,
                request_hash,
                Jsonb(normalized),
            ),
        )
        _event(
            conn,
            workflow,
            "LocalOperationPrepared",
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
            "prepare_appointment",
            request.workflow_id,
            request_hash,
            response,
        )
        return response


def commit_local(operation_id: UUID, request: CommitLocalRequest, trace_id: str) -> dict[str, Any]:
    # The initial operation lookup is non-locking; all mutation locks workflow first.
    with _connection() as conn:
        locator = _one(conn, "SELECT workflow_id FROM operations WHERE id=%s", (operation_id,))
        if locator is None:
            raise DomainProblem(
                "operation-not-found", "Operation not found", "Unknown operation", 404
            )
        workflow = _workflow(conn, locator["workflow_id"])
        request_hash = _hash({"operation_id": str(operation_id)})
        replay = _command_replay(conn, request.command_id, "commit_local", request_hash)
        if replay is not None:
            return replay
        op = _one(conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (operation_id,))
        assert op is not None
        if workflow["current_revision"] != op["intent_revision"]:
            raise DomainProblem(
                "stale-intent-revision", "Stale intent revision", "Operation revision is obsolete"
            )
        try:
            local_commit_dimensions(
                OperationDimensions(
                    ProcessingPhase(op["processing_phase"]),
                    EffectKnowledge(op["effect_knowledge"]),
                    Applicability(op["applicability"]),
                    SpeechEligibility(op["speech_eligibility"]),
                )
            )
        except ValueError as exc:
            raise DomainProblem(
                "illegal-operation-transition", "Illegal operation transition", str(exc)
            ) from exc
        normalized = op["normalized_request_json"]
        desired = normalized["desired_state"]
        expected_version = normalized["expected_resource_version"]
        appointment_id = desired.get("appointment_id")
        before: dict[str, Any] | None = None
        if appointment_id:
            appointment = _one(
                conn, "SELECT * FROM appointments WHERE id=%s FOR UPDATE", (UUID(appointment_id),)
            )
            if appointment is None or appointment["version"] != expected_version:
                raise DomainProblem(
                    "stale-resource-version",
                    "Stale resource version",
                    "Appointment version has changed",
                )
            if appointment["status"] not in ("HELD", "CONFIRMED"):
                raise DomainProblem(
                    "inactive-appointment",
                    "Inactive appointment",
                    "Appointment cannot be rescheduled",
                )
            before = {
                "starts_at": appointment["starts_at"].isoformat(),
                "ends_at": appointment["ends_at"].isoformat(),
                "version": appointment["version"],
            }
            resource_id = appointment["id"]
            _execute(
                conn,
                "UPDATE appointments SET starts_at=%s,ends_at=%s,timezone=%s,requested_local_start=%s,"
                "source_workflow_id=%s,source_intent_revision=%s,version=version+1,updated_at=now() WHERE id=%s",
                (
                    desired["requested_start"],
                    desired["requested_end"],
                    desired["timezone"],
                    desired["requested_start"],
                    workflow["id"],
                    op["intent_revision"],
                    resource_id,
                ),
            )
            effect_type = "APPOINTMENT_RESCHEDULED"
        else:
            ticket = _one(
                conn,
                "SELECT * FROM maintenance_tickets WHERE id=%s FOR UPDATE",
                (UUID(desired["ticket_id"]),),
            )
            if ticket is None or ticket["version"] != expected_version:
                raise DomainProblem(
                    "stale-resource-version", "Stale resource version", "Ticket version has changed"
                )
            resource_id = uuid4()
            _execute(
                conn,
                "INSERT INTO appointments (id,ticket_id,resident_id,resource_key,starts_at,ends_at,"
                "timezone,requested_local_start,status,source_workflow_id,source_intent_revision) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'CONFIRMED',%s,%s)",
                (
                    resource_id,
                    ticket["id"],
                    ticket["resident_id"],
                    f"property:{ticket['property_id']}:maintenance",
                    desired["requested_start"],
                    desired["requested_end"],
                    desired["timezone"],
                    desired["requested_start"],
                    workflow["id"],
                    op["intent_revision"],
                ),
            )
            _execute(
                conn,
                "UPDATE maintenance_tickets SET status='SCHEDULED',version=version+1,updated_at=now() WHERE id=%s",
                (ticket["id"],),
            )
            effect_type = "APPOINTMENT_CREATED"
        appointment_after = _one(conn, "SELECT * FROM appointments WHERE id=%s", (resource_id,))
        assert appointment_after is not None
        after = {
            "starts_at": appointment_after["starts_at"].isoformat(),
            "ends_at": appointment_after["ends_at"].isoformat(),
            "version": appointment_after["version"],
        }
        _execute(
            conn,
            "INSERT INTO effect_ledger (operation_id,effect_type,resource_type,resource_id,before_facts,"
            "after_facts,observed_version,evidence_hash,observed_at) VALUES (%s,%s,'appointment',%s,%s,%s,%s,%s,now())",
            (
                operation_id,
                effect_type,
                str(resource_id),
                Jsonb(before) if before else None,
                Jsonb(after),
                str(after["version"]),
                _hash(after),
            ),
        )
        _execute(
            conn,
            "UPDATE operations SET processing_phase='TERMINAL',effect_knowledge='PRESENT',"
            "target_resource_type='appointment',target_resource_id=%s,effect_observed_at=now(),"
            "resolved_at=now(),version=version+1,updated_at=now() WHERE id=%s",
            (resource_id, operation_id),
        )
        _event(
            conn,
            workflow,
            "LocalEffectCommitted",
            op["intent_revision"],
            operation_id,
            request.command_id,
            {
                "effect_type": effect_type,
                "appointment_id": str(resource_id),
                "resource_version": after["version"],
            },
            trace_id,
        )
        response = {
            "operation_id": str(operation_id),
            "appointment_id": str(resource_id),
            "processing_phase": "TERMINAL",
            "effect_knowledge": "PRESENT",
            "appointment_version": after["version"],
        }
        _receipt(conn, request.command_id, "commit_local", workflow["id"], request_hash, response)
        return response


def workflow_history(workflow_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        workflow = _one(conn, "SELECT * FROM workflows WHERE id=%s", (workflow_id,))
        if workflow is None:
            raise DomainProblem("workflow-not-found", "Workflow not found", "Unknown workflow", 404)
        revisions = _all(
            conn,
            "SELECT revision,change_class,desired_state_json,accepted_at FROM intent_revisions "
            "WHERE workflow_id=%s ORDER BY revision",
            (workflow_id,),
        )
        operations = _all(
            conn,
            "SELECT id,intent_revision,processing_phase,effect_knowledge,applicability,"
            "speech_eligibility,target_resource_id FROM operations WHERE workflow_id=%s ORDER BY created_at,id",
            (workflow_id,),
        )
        effects = _all(
            conn,
            "SELECT e.operation_id,e.effect_type,e.before_facts,e.after_facts,e.resource_id "
            "FROM effect_ledger e JOIN operations o ON o.id=e.operation_id "
            "WHERE o.workflow_id=%s ORDER BY e.created_at,e.id",
            (workflow_id,),
        )
        appointments = _all(
            conn,
            "SELECT id,starts_at,ends_at,status,version,source_intent_revision "
            "FROM appointments WHERE source_workflow_id=%s ORDER BY created_at,id",
            (workflow_id,),
        )
        events = _all(
            conn,
            "SELECT workflow_sequence,event_name,intent_revision,payload FROM workflow_events "
            "WHERE workflow_id=%s ORDER BY workflow_sequence",
            (workflow_id,),
        )
    return {
        "workflow_id": str(workflow_id),
        "current_revision": workflow["current_revision"],
        "desired_state": workflow["desired_state_json"],
        "revisions": revisions,
        "operations": operations,
        "effects": effects,
        "appointments": appointments,
        "events": events,
        "read_at": datetime.now(UTC).isoformat(),
    }


def translate_integrity_error(exc: psycopg.IntegrityError) -> DomainProblem:
    if isinstance(exc, ExclusionViolation):
        return DomainProblem(
            "appointment-overlap",
            "Appointment overlap",
            "An active appointment already occupies this resource and time",
        )
    if isinstance(exc, UniqueViolation):
        return DomainProblem(
            "unique-conflict",
            "Unique constraint conflict",
            "A conflicting command or resource already exists",
        )
    return DomainProblem(
        "database-constraint",
        "Database constraint conflict",
        "The requested domain mutation violates a database constraint",
    )
