"""Durable audio preparation and release behind current claim evidence."""

import base64
import binascii
import hashlib
import io
import wave
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

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
from apps.api_controller.phase3_claim_service import _check_receipt, publish
from apps.api_controller.phase3_models import PermitCommand
from apps.api_controller.phase3_verification_service import (
    Observation,
    _evaluate,
    _external_observations,
    _local_effect_observation,
    _local_observation,
)
from apps.api_controller.phase4_models import PrepareSegmentRequest, SegmentCommand
from packages.domain.phase3_verification import ClaimType, Result
from packages.speech_policy.phase3 import render
from packages.speech_policy.phase4 import AudioState, SegmentClass, repair_capable, repair_text


def _locator(conn: Any, segment_id: UUID) -> dict[str, Any]:
    row = _one(conn, "SELECT workflow_id,call_id FROM audio_segments WHERE id=%s", (segment_id,))
    if row is None:
        raise DomainProblem("segment-not-found", "Audio segment not found", "Unknown segment", 404)
    return row


def _permit_rows(
    conn: Any, permit_id: UUID
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    permit = _one(conn, "SELECT * FROM claim_permits WHERE id=%s FOR UPDATE", (permit_id,))
    if permit is None:
        raise DomainProblem("permit-not-found", "Permit not found", "Unknown permit", 404)
    claim = _one(conn, "SELECT * FROM claims WHERE id=%s", (permit["claim_id"],))
    receipt = _one(conn, "SELECT * FROM verification_receipts WHERE id=%s", (permit["receipt_id"],))
    assert claim is not None and receipt is not None
    return permit, claim, receipt


def _expected_text(conn: Any, claim: dict[str, Any], obligation_id: UUID | None) -> str:
    text = render(ClaimType(claim["claim_type"]), claim["semantic_predicates_json"])
    if obligation_id is None:
        return text
    workflow = _one(conn, "SELECT research_arm FROM workflows WHERE id=%s", (claim["workflow_id"],))
    if workflow is None or not repair_capable(workflow["research_arm"]):
        raise DomainProblem(
            "repair-capability", "Repair capability disabled", "Arm cannot deliver durable repair"
        )
    obligation = _one(conn, "SELECT * FROM repair_obligations WHERE id=%s", (obligation_id,))
    if obligation is None or obligation["workflow_id"] != claim["workflow_id"]:
        raise DomainProblem("repair-scope", "Repair scope mismatch", "Unknown repair obligation")
    if obligation["state"] not in ("OPEN", "REPAIR_AUTHORIZED"):
        raise DomainProblem("repair-state", "Repair state conflict", "Repair is not open")
    if obligation["triggering_revision"] != claim["intent_revision"]:
        raise DomainProblem(
            "repair-revision", "Repair revision mismatch", "Corrected claim is stale"
        )
    return repair_text(text)


def fresh_observations(operation: dict[str, Any], claim_type: ClaimType) -> list[Observation]:
    if operation["provider_adapter"] == "simulator":
        return _external_observations(operation, claim_type)
    return []


def check_fresh(
    conn: Any,
    workflow: dict[str, Any],
    operation: dict[str, Any],
    permit: dict[str, Any],
    claim: dict[str, Any],
    receipt: dict[str, Any],
    observations: list[Observation],
) -> None:
    claim_type = ClaimType(claim["claim_type"])
    if claim_type is ClaimType.HANDOFF_CREATED:
        handoff = _one(
            conn,
            "SELECT * FROM handoffs WHERE workflow_id=%s "
            "AND state IN ('OPEN','ACKNOWLEDGED') ORDER BY created_at DESC LIMIT 1",
            (workflow["id"],),
        )
    else:
        handoff = None
    if operation["provider_adapter"] == "local_postgres":
        observations.append(_local_observation(conn, workflow))
        if claim_type is ClaimType.RESCHEDULED_APPOINTMENT:
            observations.append(_local_effect_observation(conn, operation))
    fresh = _evaluate(claim_type, workflow, operation, observations, handoff)
    if fresh.result is not Result.SATISFIED or fresh.predicates != receipt["predicates_json"]:
        raise DomainProblem(
            "fresh-evidence-required",
            "Fresh evidence required",
            "Current source facts do not support audio playback",
        )
    _check_receipt(workflow, permit, claim, receipt, datetime.now(UTC), fresh.resource_version)


def synthesis_input(permit_id: UUID, obligation_id: UUID | None = None) -> dict[str, Any]:
    with _connection() as conn:
        locator = _one(conn, "SELECT workflow_id FROM claim_permits WHERE id=%s", (permit_id,))
        if locator is None:
            raise DomainProblem("permit-not-found", "Permit not found", "Unknown permit", 404)
        workflow = _workflow(conn, locator["workflow_id"])
        permit, claim, receipt = _permit_rows(conn, permit_id)
        if permit["state"] != "QUEUED":
            raise DomainProblem("permit-state", "Permit state conflict", "Queue the permit first")
        _check_receipt(
            workflow,
            permit,
            claim,
            receipt,
            datetime.now(UTC),
            receipt["observed_resource_version"],
        )
        text = _expected_text(conn, claim, obligation_id)
        return {
            "text": text,
            "text_hash": _hash(text),
            "permit_id": str(permit_id),
            "intent_revision": workflow["current_revision"],
        }


def _wav_facts(
    encoded: str, expected_hash: str, text: str
) -> tuple[bytes, int, int, list[dict[str, Any]]]:
    try:
        audio = base64.b64decode(encoded, validate=True)
        with wave.open(io.BytesIO(audio), "rb") as reader:
            rate, channels, width, frames = (
                reader.getframerate(),
                reader.getnchannels(),
                reader.getsampwidth(),
                reader.getnframes(),
            )
    except (ValueError, EOFError, wave.Error, binascii.Error) as exc:
        raise DomainProblem(
            "invalid-audio", "Invalid audio", "Expected valid WAV bytes", 422
        ) from exc
    if hashlib.sha256(audio).hexdigest() != expected_hash:
        raise DomainProblem("audio-hash", "Audio hash mismatch", "Audio bytes changed", 422)
    if rate != 16000 or channels != 1 or width != 2 or not (1 <= frames <= 480000):
        raise DomainProblem(
            "audio-format",
            "Unsupported audio format",
            "Use mono 16 kHz 16-bit WAV no longer than 30 seconds",
            422,
        )
    duration = (frames * 1000 + rate - 1) // rate
    words = text.split()
    timeline = [
        {
            "word": word,
            "start_ms": duration * i // len(words),
            "end_ms": duration * (i + 1) // len(words),
        }
        for i, word in enumerate(words)
    ]
    return audio, duration, frames, timeline


def prepare_segment(body: PrepareSegmentRequest, trace_id: str) -> dict[str, Any]:
    request_hash = _hash(body.model_dump(mode="json", exclude={"command_id", "audio_base64"}))
    with _connection() as conn:
        locator = _one(conn, "SELECT workflow_id FROM claim_permits WHERE id=%s", (body.permit_id,))
        if locator is None:
            raise DomainProblem("permit-not-found", "Permit not found", "Unknown permit", 404)
        workflow = _workflow(conn, locator["workflow_id"])
        permit, claim, receipt = _permit_rows(conn, body.permit_id)
        replay = _command_replay(conn, body.command_id, "prepare_audio", request_hash)
        if replay is not None:
            return replay
        if (
            workflow["current_revision"] != body.expected_intent_revision
            or permit["state"] != "QUEUED"
        ):
            raise DomainProblem(
                "stale-audio", "Stale audio", "Permit is not queued for this revision"
            )
        _check_receipt(
            workflow,
            permit,
            claim,
            receipt,
            datetime.now(UTC),
            receipt["observed_resource_version"],
        )
        text = _expected_text(conn, claim, body.repair_obligation_id)
        if _hash(text) != body.text_hash:
            raise DomainProblem(
                "text-hash", "Text hash mismatch", "TTS input was not authorized", 422
            )
        audio, duration, frames, timeline = _wav_facts(body.audio_base64, body.audio_hash, text)
        existing = _one(
            conn, "SELECT id FROM audio_segments WHERE claim_permit_id=%s", (body.permit_id,)
        )
        if existing is not None:
            raise DomainProblem(
                "segment-exists", "Audio segment exists", "Permit already has audio"
            )
        segment_id = uuid4()
        segment_class = SegmentClass.REPAIR if body.repair_obligation_id else SegmentClass.OUTCOME
        _execute(
            conn,
            "INSERT INTO audio_segments "
            "(id,call_id,workflow_id,intent_revision,claim_id,claim_permit_id,"
            "repair_obligation_id,segment_class,segment_text,content_hash,audio_data,"
            "audio_hash,duration_ms,frame_count,word_timeline_json,tts_model_id,"
            "tts_config_hash,generated_at,state) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),'GENERATED')",
            (
                segment_id,
                workflow["call_id"],
                workflow["id"],
                workflow["current_revision"],
                claim["id"],
                permit["id"],
                body.repair_obligation_id,
                segment_class.value,
                text,
                _hash(text),
                audio,
                body.audio_hash,
                duration,
                frames,
                Jsonb(timeline),
                body.tts_model_id,
                body.tts_config_hash,
            ),
        )
        if body.repair_obligation_id:
            _execute(
                conn,
                "UPDATE repair_obligations SET state='REPAIR_AUTHORIZED',"
                "repair_claim_id=%s,updated_at=now() WHERE id=%s AND state='OPEN'",
                (claim["id"], body.repair_obligation_id),
            )
        _event(
            conn,
            workflow,
            "AudioGenerated",
            workflow["current_revision"],
            claim["operation_id"],
            body.command_id,
            {
                "segment_id": str(segment_id),
                "audio_hash": body.audio_hash,
                "segment_class": segment_class.value,
            },
            trace_id,
        )
        response = {
            "segment_id": str(segment_id),
            "state": AudioState.GENERATED.value,
            "duration_ms": duration,
            "frame_count": frames,
            "word_count": len(timeline),
            "audio_hash": body.audio_hash,
        }
        _receipt(conn, body.command_id, "prepare_audio", workflow["id"], request_hash, response)
        return response


def queue_segment(segment_id: UUID, body: SegmentCommand, trace_id: str) -> dict[str, Any]:
    request_hash = _hash({"segment_id": str(segment_id), "revision": body.expected_intent_revision})
    with _connection() as conn:
        locator = _locator(conn, segment_id)
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, body.command_id, "queue_audio", request_hash)
        if replay is not None:
            return replay
        segment = _one(conn, "SELECT * FROM audio_segments WHERE id=%s FOR UPDATE", (segment_id,))
        assert segment is not None
        permit, claim, receipt = _permit_rows(conn, segment["claim_permit_id"])
        if (
            segment["state"] != AudioState.GENERATED
            or body.expected_intent_revision != workflow["current_revision"]
        ):
            raise DomainProblem("stale-audio", "Stale audio", "Generated segment cannot be queued")
        _check_receipt(
            workflow,
            permit,
            claim,
            receipt,
            datetime.now(UTC),
            receipt["observed_resource_version"],
        )
        _execute(
            conn,
            "UPDATE audio_segments SET state='QUEUED',queued_at=now() WHERE id=%s",
            (segment_id,),
        )
        _event(
            conn,
            workflow,
            "AssistantAudioQueued",
            workflow["current_revision"],
            claim["operation_id"],
            body.command_id,
            {"segment_id": str(segment_id)},
            trace_id,
        )
        response = {"segment_id": str(segment_id), "state": AudioState.QUEUED.value}
        _receipt(conn, body.command_id, "queue_audio", workflow["id"], request_hash, response)
        return response


def release_segment(segment_id: UUID, body: SegmentCommand, trace_id: str) -> dict[str, Any]:
    request_hash = _hash({"segment_id": str(segment_id), "revision": body.expected_intent_revision})
    with _connection() as conn:
        locator = _locator(conn, segment_id)
        replay = _command_replay(conn, body.command_id, "release_audio", request_hash)
        if replay is not None:
            return replay
        segment = _one(conn, "SELECT * FROM audio_segments WHERE id=%s", (segment_id,))
        assert segment is not None
        if segment["state"] != AudioState.QUEUED:
            raise DomainProblem("segment-state", "Audio state conflict", "Segment is not queued")
    publication_command = uuid5(NAMESPACE_URL, f"phase4-audio-release:{body.command_id}")
    publication = publish(
        segment["claim_permit_id"],
        PermitCommand(
            command_id=publication_command, expected_intent_revision=body.expected_intent_revision
        ),
        trace_id,
    )
    with _connection() as conn:
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, body.command_id, "release_audio", request_hash)
        if replay is not None:
            return replay
        current = _one(conn, "SELECT * FROM audio_segments WHERE id=%s FOR UPDATE", (segment_id,))
        assert current is not None
        expected_text = publication["text"]
        if current["segment_class"] == SegmentClass.REPAIR:
            expected_text = repair_text(expected_text)
        if (
            current["state"] != AudioState.QUEUED
            or workflow["current_revision"] != body.expected_intent_revision
            or current["segment_text"] != expected_text
        ):
            raise DomainProblem(
                "stale-audio", "Stale audio", "Audio release lost its current claim"
            )
        _execute(
            conn,
            "UPDATE audio_segments SET state='PUBLISHED',published_at=now() WHERE id=%s",
            (segment_id,),
        )
        _event(
            conn,
            workflow,
            "AudioPublished",
            workflow["current_revision"],
            None,
            body.command_id,
            {"segment_id": str(segment_id), "audio_hash": current["audio_hash"]},
            trace_id,
        )
        response = {
            "segment_id": str(segment_id),
            "state": AudioState.PUBLISHED.value,
            "audio_url": f"/v1/audio-segments/{segment_id}/audio",
            "duration_ms": current["duration_ms"],
            "frame_count": current["frame_count"],
        }
        _receipt(conn, body.command_id, "release_audio", workflow["id"], request_hash, response)
        return response


def segment_detail(segment_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        row = _one(conn, "SELECT * FROM audio_segments WHERE id=%s", (segment_id,))
    if row is None:
        raise DomainProblem("segment-not-found", "Audio segment not found", "Unknown segment", 404)
    row.pop("audio_data", None)
    return row


def segment_audio(segment_id: UUID) -> bytes:
    with _connection() as conn:
        row = _one(
            conn,
            "SELECT s.state,s.audio_data,s.intent_revision,s.research_unpermitted,"
            "w.current_revision "
            "FROM audio_segments s JOIN workflows w ON w.id=s.workflow_id WHERE s.id=%s",
            (segment_id,),
        )
    if row is None:
        raise DomainProblem("segment-not-found", "Audio segment not found", "Unknown segment", 404)
    if row["research_unpermitted"]:
        raise DomainProblem(
            "research-audio-only", "Research audio only", "Baseline audio is not live-playable", 404
        )
    if (
        row["state"] not in (AudioState.PUBLISHED, AudioState.STARTED)
        or row["intent_revision"] != row["current_revision"]
    ):
        raise DomainProblem(
            "audio-not-published", "Audio not published", "Segment is not currently playable"
        )
    return bytes(row["audio_data"])
