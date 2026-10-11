"""Persist raw and normalized voice events; accept only validated typed proposals."""

from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from psycopg.types.json import Jsonb
from pydantic import ValidationError

from apps.api_controller.phase1_models import AcceptRevisionRequest
from apps.api_controller.phase1_service import (
    DomainProblem,
    _connection,
    _event,
    _execute,
    _hash,
    _one,
    _workflow,
    accept_revision,
)
from apps.api_controller.phase4_models import (
    AcceptVoiceProposalRequest,
    VoiceEventRequest,
    VoiceToolProposal,
)
from packages.protocol.voice import VoiceEventType


def record_voice_event(call_id: UUID, body: VoiceEventRequest, trace_id: str) -> dict[str, Any]:
    fingerprint = _hash(
        {
            "type": body.event_type.value,
            "raw": body.raw,
            "normalized": body.normalized,
            "occurred_at": body.occurred_at.isoformat(),
        }
    )
    with _connection() as conn:
        workflow_row = _one(
            conn, "SELECT id FROM workflows WHERE call_id=%s ORDER BY id LIMIT 1", (call_id,)
        )
        if workflow_row is None:
            raise DomainProblem("call-not-found", "Call not found", "Unknown call", 404)
        workflow = _workflow(conn, workflow_row["id"])
        existing = _one(
            conn,
            "SELECT * FROM voice_events WHERE id=%s OR (call_id=%s AND source_event_id=%s)",
            (body.event_id, call_id, body.source_event_id),
        )
        if existing is not None:
            if (
                existing["id"] != body.event_id
                or existing["call_id"] != call_id
                or existing["content_hash"] != fingerprint
            ):
                raise DomainProblem(
                    "voice-event-conflict",
                    "Voice event conflict",
                    "Voice event identity was reused with changed content",
                )
            utterance_id: UUID | None = None
            if body.event_type is VoiceEventType.TRANSCRIPT_FINAL:
                utterance_id = uuid5(
                    NAMESPACE_URL, f"voice-utterance:{call_id}:{body.source_event_id}"
                )
            return {
                "event_id": str(body.event_id),
                "event_type": body.event_type.value,
                "utterance_id": utterance_id,
            }
        utterance_id = None
        if body.event_type is VoiceEventType.TRANSCRIPT_FINAL:
            transcript = body.normalized.get("transcript")
            if not isinstance(transcript, str) or not transcript.strip():
                raise DomainProblem(
                    "invalid-transcript",
                    "Invalid transcript",
                    "TranscriptFinal needs nonempty transcript",
                    422,
                )
            utterance_id = uuid5(NAMESPACE_URL, f"voice-utterance:{call_id}:{body.source_event_id}")
            _execute(
                conn,
                "INSERT INTO utterances "
                "(id,call_id,speaker,transcript,transcript_version,finalized,content_hash) "
                "VALUES (%s,%s,'USER',%s,1,true,%s)",
                (utterance_id, call_id, transcript, _hash(transcript)),
            )
        elif body.event_type is VoiceEventType.TOOL_PROPOSAL_RECEIVED:
            try:
                VoiceToolProposal.model_validate(body.normalized)
            except ValidationError as exc:
                raise DomainProblem(
                    "invalid-proposal",
                    "Invalid proposal",
                    "Typed intent proposal failed validation",
                    422,
                ) from exc
        _execute(
            conn,
            "INSERT INTO voice_events "
            "(id,call_id,source_event_id,event_type,raw_json,normalized_json,"
            "content_hash,occurred_at,trace_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                body.event_id,
                call_id,
                body.source_event_id,
                body.event_type.value,
                Jsonb(body.raw),
                Jsonb(body.normalized),
                fingerprint,
                body.occurred_at,
                trace_id,
            ),
        )
        _event(
            conn,
            workflow,
            body.event_type.value,
            workflow["current_revision"] or None,
            None,
            body.event_id,
            {
                "source_event_id": body.source_event_id,
                "normalized_hash": _hash(body.normalized),
                "utterance_id": str(utterance_id) if utterance_id else None,
            },
            trace_id,
        )
        return {
            "event_id": str(body.event_id),
            "event_type": body.event_type.value,
            "utterance_id": str(utterance_id) if utterance_id else None,
        }


def accept_voice_proposal(
    workflow_id: UUID,
    body: AcceptVoiceProposalRequest,
    trace_id: str,
) -> dict[str, Any]:
    with _connection() as conn:
        workflow = _one(conn, "SELECT call_id FROM workflows WHERE id=%s", (workflow_id,))
        if workflow is None:
            raise DomainProblem("workflow-not-found", "Workflow not found", "Unknown workflow", 404)
        proposal_event = _one(
            conn,
            "SELECT * FROM voice_events WHERE call_id=%s AND source_event_id=%s AND event_type=%s",
            (
                workflow["call_id"],
                body.source_event_id,
                VoiceEventType.TOOL_PROPOSAL_RECEIVED.value,
            ),
        )
        if proposal_event is None:
            raise DomainProblem(
                "proposal-not-found",
                "Proposal not found",
                "Typed proposal event is not recorded",
                404,
            )
        proposal = VoiceToolProposal.model_validate(proposal_event["normalized_json"])
    accepted = AcceptRevisionRequest(
        command_id=body.command_id,
        expected_revision=body.expected_revision,
        change_class=body.change_class,
        desired_state=proposal.desired_state,
        candidate_source=proposal.candidate_source,
    )
    return accept_revision(workflow_id, accepted, trace_id)
