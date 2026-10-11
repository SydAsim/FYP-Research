"""PostgreSQL-authoritative playback acknowledgement and stale-span repair."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from apps.api_controller.phase1_service import (
    DomainProblem,
    _command_replay,
    _connection,
    _event,
    _execute,
    _hash,
    _one,
    _receipt,
    _workflow,
)
from apps.api_controller.phase4_audio_service import (
    _locator,
    _permit_rows,
    check_fresh,
    fresh_observations,
)
from apps.api_controller.phase4_models import (
    MediaEndRequest,
    PlaybackEventRequest,
    PlaybackType,
    SegmentCommand,
)
from packages.domain.phase3_verification import ClaimType
from packages.speech_policy.phase4 import (
    AudioState,
    Exposure,
    SegmentClass,
    exposed_span,
    needs_repair,
    repair_capable,
    validate_progress,
)


def _ensure_repair(
    conn: Any,
    workflow: dict[str, Any],
    segment: dict[str, Any],
    triggering_revision: int,
    correlation_id: UUID,
    trace_id: str,
) -> UUID | None:
    if not repair_capable(workflow.get("research_arm")) or not needs_repair(
        segment, triggering_revision, workflow["desired_state_json"]
    ):
        return None
    span = exposed_span(segment)
    existing = _one(
        conn,
        "SELECT id,played_span_json FROM repair_obligations "
        "WHERE stale_segment_id=%s AND triggering_revision=%s FOR UPDATE",
        (segment["id"], triggering_revision),
    )
    if existing is not None:
        previous = existing["played_span_json"]
        if span["last_frame"] > previous["last_frame"]:
            _execute(
                conn,
                "UPDATE repair_obligations SET played_span_json=%s,updated_at=now() WHERE id=%s",
                (Jsonb(span), existing["id"]),
            )
            _event(
                conn,
                workflow,
                "RepairExposureUpdated",
                triggering_revision,
                None,
                correlation_id,
                {"repair_obligation_id": str(existing["id"]), "played_span": span},
                trace_id,
            )
        return UUID(str(existing["id"]))
    obligation_id = uuid4()
    _execute(
        conn,
        "INSERT INTO repair_obligations "
        "(id,workflow_id,stale_claim_id,stale_segment_id,triggering_revision,"
        "played_span_json,required_predicates_json,state,deadline_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,'OPEN',%s)",
        (
            obligation_id,
            workflow["id"],
            segment["claim_id"],
            segment["id"],
            triggering_revision,
            Jsonb(span),
            Jsonb(
                {
                    "current_revision": triggering_revision,
                    "correction_of_claim_id": str(segment["claim_id"]),
                }
            ),
            datetime.now(UTC) + timedelta(hours=1),
        ),
    )
    _event(
        conn,
        workflow,
        "RepairRequired",
        triggering_revision,
        None,
        correlation_id,
        {
            "repair_obligation_id": str(obligation_id),
            "stale_segment_id": str(segment["id"]),
            "played_span": span,
        },
        trace_id,
    )
    return obligation_id


def on_revision_accepted(
    conn: Any,
    workflow: dict[str, Any],
    new_revision: int,
    correlation_id: UUID,
    trace_id: str,
) -> None:
    """Called inside the revision transaction after the workflow row is locked."""
    if repair_capable(workflow.get("research_arm")):
        # A pending obligation remains durable, but its corrected target must follow
        # the latest accepted intent. Old repair audio cannot satisfy the new target.
        retargeted = conn.execute(
            "UPDATE repair_obligations SET triggering_revision=%s,state='OPEN',"
            "repair_claim_id=NULL,delivery_lease_owner=NULL,delivery_lease_until=NULL,"
            "required_predicates_json=jsonb_set(required_predicates_json,'{current_revision}',"
            "to_jsonb(%s::integer)),updated_at=now() WHERE workflow_id=%s "
            "AND triggering_revision<%s AND state IN ('OPEN','REPAIR_AUTHORIZED') RETURNING id",
            (new_revision, new_revision, workflow["id"], new_revision),
        ).fetchall()
        for obligation in retargeted:
            _event(
                conn,
                workflow,
                "RepairRetargeted",
                new_revision,
                None,
                correlation_id,
                {"repair_obligation_id": str(obligation["id"])},
                trace_id,
            )
    segments = conn.execute(
        "SELECT * FROM audio_segments WHERE workflow_id=%s AND intent_revision<%s "
        "AND state IN ('GENERATED','QUEUED','PUBLISHED','STARTED','STOPPED','COMPLETED') "
        "ORDER BY id FOR UPDATE",
        (workflow["id"], new_revision),
    ).fetchall()
    for segment in segments:
        updated = dict(segment)
        acknowledged = Exposure(
            segment["last_played_ms"], segment["last_frame"], segment["last_word_index"]
        ).acknowledged
        if segment["state"] != AudioState.COMPLETED:
            next_state = (
                AudioState.STOPPED
                if acknowledged or segment["state"] in (AudioState.STARTED, AudioState.STOPPED)
                else AudioState.CANCELLED
            )
            _execute(
                conn,
                "UPDATE audio_segments SET state=%s,stopped_at=now(),"
                "cancelled_at=now() WHERE id=%s",
                (next_state.value, segment["id"]),
            )
            updated["state"] = next_state.value
            _event(
                conn,
                workflow,
                "AssistantAudioStopped",
                new_revision,
                None,
                correlation_id,
                {
                    "segment_id": str(segment["id"]),
                    "reason": "accepted_revision",
                    "last_frame": segment["last_frame"],
                    "last_word_index": segment["last_word_index"],
                },
                trace_id,
            )
        _ensure_repair(conn, workflow, updated, new_revision, correlation_id, trace_id)


def _replay(conn: Any, call_id: UUID, body: PlaybackEventRequest) -> dict[str, Any] | None:
    row = _one(conn, "SELECT * FROM playback_events WHERE id=%s", (body.event_id,))
    if row is None:
        return None
    if (
        row["call_id"] != call_id
        or row["segment_id"] != body.segment_id
        or row["event_type"] != body.event_type.value
        or row["played_ms"] != body.played_ms
        or row["last_frame"] != body.last_frame
        or row["last_word_index"] != body.last_word_index
        or row["client_time"] != body.client_time
    ):
        raise DomainProblem(
            "event-id-conflict",
            "Event ID conflict",
            "Playback event ID was reused with changed facts",
        )
    return dict(row["response_json"])


def record_playback(call_id: UUID, body: PlaybackEventRequest, trace_id: str) -> dict[str, Any]:
    with _connection() as conn:
        replay = _replay(conn, call_id, body)
        if replay is not None:
            return replay
        locator = _locator(conn, body.segment_id)
        if locator["call_id"] != call_id:
            raise DomainProblem(
                "call-scope", "Call scope mismatch", "Segment belongs to another call"
            )
        segment = _one(
            conn, "SELECT claim_permit_id FROM audio_segments WHERE id=%s", (body.segment_id,)
        )
        assert segment is not None
        permit_id = segment["claim_permit_id"]
        operation = None
        claim_type = None
        if body.event_type is PlaybackType.STARTED and permit_id:
            claim = _one(
                conn,
                "SELECT c.* FROM claims c JOIN claim_permits p ON p.claim_id=c.id WHERE p.id=%s",
                (permit_id,),
            )
            assert claim is not None
            operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (claim["operation_id"],))
            assert operation is not None
            claim_type = ClaimType(claim["claim_type"])
    observations = fresh_observations(operation, claim_type) if operation and claim_type else []
    with _connection() as conn:
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _replay(conn, call_id, body)
        if replay is not None:
            return replay
        segment = _one(
            conn, "SELECT * FROM audio_segments WHERE id=%s FOR UPDATE", (body.segment_id,)
        )
        assert segment is not None
        current = Exposure(
            segment["last_played_ms"], segment["last_frame"], segment["last_word_index"]
        )
        incoming = Exposure(body.played_ms, body.last_frame, body.last_word_index)
        try:
            validate_progress(
                Exposure(0, 0, 0),
                incoming,
                segment["duration_ms"],
                segment["frame_count"],
                len(segment["word_timeline_json"]),
            )
        except ValueError as exc:
            raise DomainProblem(
                "invalid-playback-span", "Invalid playback span", str(exc), 422
            ) from exc
        # Client-time ordering differs from delivery ordering. Retain every raw ACK,
        # while cumulative durable exposure never moves backward on delayed delivery.
        incoming = Exposure(
            max(current.played_ms, incoming.played_ms),
            max(current.last_frame, incoming.last_frame),
            max(current.last_word_index, incoming.last_word_index),
        )
        state = AudioState(segment["state"])
        event_name: str | None = None
        if body.event_type is PlaybackType.STARTED:
            if (
                state is not AudioState.PUBLISHED
                or workflow["current_revision"] != segment["intent_revision"]
            ):
                raise DomainProblem("stale-audio", "Stale audio", "Segment cannot start")
            if segment["claim_permit_id"]:
                permit, claim, receipt = _permit_rows(conn, segment["claim_permit_id"])
                current_op = _one(
                    conn, "SELECT * FROM operations WHERE id=%s", (claim["operation_id"],)
                )
                assert current_op is not None
                check_fresh(conn, workflow, current_op, permit, claim, receipt, observations)
            state = AudioState.STARTED
            _execute(
                conn,
                "UPDATE audio_segments SET state='STARTED',started_at=now() WHERE id=%s",
                (segment["id"],),
            )
            event_name = "PlaybackStarted"
        elif body.event_type is PlaybackType.PROGRESS:
            if state not in (AudioState.STARTED, AudioState.STOPPED, AudioState.COMPLETED):
                raise DomainProblem(
                    "playback-state", "Playback state conflict", "No segment was started"
                )
        elif body.event_type is PlaybackType.INTERRUPTED:
            if state not in (AudioState.PUBLISHED, AudioState.STARTED, AudioState.STOPPED):
                raise DomainProblem(
                    "playback-state", "Playback state conflict", "Nothing to interrupt"
                )
            state = AudioState.STOPPED
            _execute(
                conn,
                "UPDATE audio_segments SET state='STOPPED',stopped_at=now() WHERE id=%s",
                (segment["id"],),
            )
            event_name = "PlaybackInterrupted"
        elif body.event_type is PlaybackType.COMPLETED:
            if state not in (AudioState.STARTED, AudioState.STOPPED, AudioState.COMPLETED):
                raise DomainProblem(
                    "playback-state", "Playback state conflict", "No segment was started"
                )
            if (
                body.played_ms < segment["duration_ms"]
                or body.last_frame < segment["frame_count"]
                or body.last_word_index < len(segment["word_timeline_json"])
            ):
                raise DomainProblem(
                    "incomplete-playback",
                    "Incomplete playback",
                    "Completion must acknowledge the full segment",
                    422,
                )
            if (
                workflow["current_revision"] == segment["intent_revision"]
                and state is AudioState.STARTED
            ):
                state = AudioState.COMPLETED
                _execute(
                    conn,
                    "UPDATE audio_segments SET state='COMPLETED',completed_at=now() WHERE id=%s",
                    (segment["id"],),
                )
            event_name = "PlaybackCompleted"
        elif body.event_type in (PlaybackType.RECEIVED, PlaybackType.QUEUED):
            if state not in (
                AudioState.PUBLISHED,
                AudioState.STARTED,
                AudioState.STOPPED,
                AudioState.COMPLETED,
            ):
                raise DomainProblem(
                    "playback-state", "Playback state conflict", "Audio was not released"
                )
        _execute(
            conn,
            "UPDATE audio_segments SET last_played_ms=%s,last_frame=%s,"
            "last_word_index=%s WHERE id=%s",
            (incoming.played_ms, incoming.last_frame, incoming.last_word_index, segment["id"]),
        )
        segment.update(
            {
                "last_played_ms": incoming.played_ms,
                "last_frame": incoming.last_frame,
                "last_word_index": incoming.last_word_index,
                "state": state.value,
            }
        )
        obligation_id = _ensure_repair(
            conn, workflow, segment, workflow["current_revision"], body.event_id, trace_id
        )
        if (
            state is AudioState.COMPLETED
            and segment["segment_class"] == SegmentClass.REPAIR
            and segment["repair_obligation_id"]
        ):
            satisfied = _one(
                conn,
                "UPDATE repair_obligations SET state='REPAIR_PLAYED',"
                "satisfied_at=now(),updated_at=now() WHERE id=%s AND state='REPAIR_AUTHORIZED' "
                "AND repair_claim_id=%s AND triggering_revision=%s RETURNING id",
                (
                    segment["repair_obligation_id"],
                    segment["claim_id"],
                    workflow["current_revision"],
                ),
            )
            if satisfied:
                _event(
                    conn,
                    workflow,
                    "RepairSatisfied",
                    workflow["current_revision"],
                    None,
                    body.event_id,
                    {
                        "repair_obligation_id": str(segment["repair_obligation_id"]),
                        "segment_id": str(segment["id"]),
                    },
                    trace_id,
                )
        if event_name is not None:
            _event(
                conn,
                workflow,
                event_name,
                workflow["current_revision"],
                None,
                body.event_id,
                {
                    "segment_id": str(segment["id"]),
                    "played_ms": incoming.played_ms,
                    "last_frame": incoming.last_frame,
                    "last_word_index": incoming.last_word_index,
                },
                trace_id,
            )
        response = {
            "event_id": str(body.event_id),
            "segment_id": str(segment["id"]),
            "state": state.value,
            "repair_obligation_id": str(obligation_id) if obligation_id else None,
        }
        _execute(
            conn,
            "INSERT INTO playback_events "
            "(id,segment_id,call_id,event_type,played_ms,last_frame,last_word_index,"
            "client_time,response_json) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                body.event_id,
                segment["id"],
                call_id,
                body.event_type.value,
                body.played_ms,
                body.last_frame,
                body.last_word_index,
                body.client_time,
                Jsonb(response),
            ),
        )
        return response


def resume_segment(segment_id: UUID, body: SegmentCommand, trace_id: str) -> dict[str, Any]:
    request_hash = _hash({"segment_id": str(segment_id), "revision": body.expected_intent_revision})
    with _connection() as conn:
        locator = _locator(conn, segment_id)
        replay = _command_replay(conn, body.command_id, "resume_audio", request_hash)
        if replay is not None:
            return replay
        segment = _one(conn, "SELECT * FROM audio_segments WHERE id=%s", (segment_id,))
        assert segment is not None
        claim = _one(conn, "SELECT * FROM claims WHERE id=%s", (segment["claim_id"],))
        assert claim is not None
        operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (claim["operation_id"],))
        assert operation is not None
    observations = fresh_observations(operation, ClaimType(claim["claim_type"]))
    with _connection() as conn:
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, body.command_id, "resume_audio", request_hash)
        if replay is not None:
            return replay
        segment = _one(conn, "SELECT * FROM audio_segments WHERE id=%s FOR UPDATE", (segment_id,))
        assert segment is not None
        if (
            segment["state"] != AudioState.STOPPED
            or segment["intent_revision"] != workflow["current_revision"]
            or body.expected_intent_revision != workflow["current_revision"]
        ):
            raise DomainProblem("stale-audio", "Stale audio", "Interrupted segment cannot resume")
        permit, claim, receipt = _permit_rows(conn, segment["claim_permit_id"])
        current_op = _one(conn, "SELECT * FROM operations WHERE id=%s", (claim["operation_id"],))
        assert current_op is not None
        check_fresh(conn, workflow, current_op, permit, claim, receipt, observations)
        _execute(
            conn,
            "UPDATE audio_segments SET state='PUBLISHED',stopped_at=NULL WHERE id=%s",
            (segment_id,),
        )
        _event(
            conn,
            workflow,
            "SpeechResumed",
            workflow["current_revision"],
            None,
            body.command_id,
            {"segment_id": str(segment_id), "resume_frame": segment["last_frame"]},
            trace_id,
        )
        response = {
            "segment_id": str(segment_id),
            "state": "PUBLISHED",
            "resume_frame": segment["last_frame"],
        }
        _receipt(conn, body.command_id, "resume_audio", workflow["id"], request_hash, response)
        return response


def repair_detail(obligation_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        row = _one(conn, "SELECT * FROM repair_obligations WHERE id=%s", (obligation_id,))
    if row is None:
        raise DomainProblem(
            "repair-not-found", "Repair not found", "Unknown repair obligation", 404
        )
    return row


def end_media(call_id: UUID, body: MediaEndRequest, trace_id: str) -> dict[str, Any]:
    request_hash = _hash({"call_id": str(call_id)})
    with _connection() as conn:
        workflow_row = _one(
            conn, "SELECT id FROM workflows WHERE call_id=%s ORDER BY id LIMIT 1", (call_id,)
        )
        if workflow_row is None:
            raise DomainProblem("call-not-found", "Call not found", "Unknown call", 404)
        workflow = _workflow(conn, workflow_row["id"])
        replay = _command_replay(conn, body.command_id, "end_media", request_hash)
        if replay is not None:
            return replay
        call = _one(conn, "SELECT * FROM call_sessions WHERE id=%s FOR UPDATE", (call_id,))
        assert call is not None
        if call["media_status"] != "ENDED":
            _execute(
                conn,
                "UPDATE call_sessions SET media_status='ENDED',ended_at=now() WHERE id=%s",
                (call_id,),
            )
            _event(
                conn,
                workflow,
                "CallMediaEnded",
                workflow["current_revision"],
                None,
                body.command_id,
                {"call_id": str(call_id)},
                trace_id,
            )
        response = {
            "call_id": str(call_id),
            "media_status": "ENDED",
            "workflow_id": str(workflow["id"]),
        }
        _receipt(conn, body.command_id, "end_media", workflow["id"], request_hash, response)
        return response
