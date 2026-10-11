"""Permitless B3 outcome speech, confined to synthetic research workflows."""

import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb
from pydantic import Field

from apps.api_controller.phase1_models import StrictModel
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
from apps.api_controller.phase3_verification_service import _evaluate
from apps.api_controller.phase4_audio_service import _wav_facts, fresh_observations
from packages.domain.phase3_verification import ClaimType, Result
from packages.speech_policy.phase3 import render


class B3AudioRequest(StrictModel):
    command_id: UUID
    workflow_id: UUID
    expected_intent_revision: int = Field(ge=1)
    audio_base64: str = Field(min_length=1)
    audio_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    tts_model_id: str = Field(min_length=1)
    tts_config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def _research_only() -> None:
    if os.getenv("EXPERIMENT_MODE") != "true":
        raise DomainProblem("research-disabled", "Research endpoint disabled", "Unavailable", 404)


def _b3_text(conn: Any, workflow: dict[str, Any], revision: int) -> tuple[str, UUID]:
    if workflow["research_arm"] != "B3" or workflow["current_revision"] != revision:
        raise DomainProblem("b3-scope", "B3 scope mismatch", "No current B3 research revision")
    operation = _one(
        conn,
        "SELECT * FROM operations WHERE workflow_id=%s AND intent_revision=%s "
        "AND effect_knowledge='PRESENT' AND applicability='CURRENT' "
        "ORDER BY created_at DESC LIMIT 1",
        (workflow["id"], revision),
    )
    if operation is None:
        raise DomainProblem(
            "b3-effect", "B3 effect unknown", "A current present effect is required"
        )
    claim_type = (
        ClaimType.CURRENT_APPOINTMENT if revision == 1 else ClaimType.RESCHEDULED_APPOINTMENT
    )
    observations = fresh_observations(operation, claim_type)
    evidence = _evaluate(claim_type, workflow, operation, observations, None)
    if evidence.result is not Result.SATISFIED:
        raise DomainProblem(
            "b3-evidence", "B3 evidence unavailable", "Current provider facts do not support speech"
        )
    return render(claim_type, evidence.predicates), operation["id"]


def synthesis_input(workflow_id: UUID, revision: int) -> dict[str, Any]:
    _research_only()
    with _connection() as conn:
        workflow = _workflow(conn, workflow_id)
        text, _ = _b3_text(conn, workflow, revision)
    return {"text": text, "text_hash": _hash(text), "intent_revision": revision}


def _write_b3(body: B3AudioRequest, trace_id: str, state: str) -> dict[str, Any]:
    _research_only()
    if state not in ("GENERATED", "PUBLISHED"):
        raise ValueError("Unsupported B3 research audio state")
    command_type = "stage_b3_audio" if state == "GENERATED" else "publish_b3_audio"
    request_hash = _hash(body.model_dump(mode="json", exclude={"command_id", "audio_base64"}))
    with _connection() as conn:
        workflow = _workflow(conn, body.workflow_id)
        replay = _command_replay(conn, body.command_id, command_type, request_hash)
        if replay is not None:
            return replay
        text, operation_id = _b3_text(conn, workflow, body.expected_intent_revision)
        if _hash(text) != body.text_hash:
            raise DomainProblem("text-hash", "Text hash mismatch", "B3 speech text changed", 422)
        audio, duration, frames, timeline = _wav_facts(body.audio_base64, body.audio_hash, text)
        existing = _one(
            conn,
            "SELECT id FROM audio_segments WHERE workflow_id=%s AND intent_revision=%s "
            "AND research_unpermitted",
            (workflow["id"], body.expected_intent_revision),
        )
        if existing is not None:
            raise DomainProblem(
                "segment-exists", "Audio segment exists", "B3 revision already has audio"
            )
        segment_id = uuid4()
        now = datetime.now(UTC)
        _execute(
            conn,
            "INSERT INTO audio_segments "
            "(id,call_id,workflow_id,intent_revision,segment_class,research_unpermitted,"
            "segment_text,content_hash,audio_data,audio_hash,duration_ms,frame_count,"
            "word_timeline_json,tts_model_id,tts_config_hash,generated_at,published_at,state) "
            "VALUES (%s,%s,%s,%s,'OUTCOME',true,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                segment_id,
                workflow["call_id"],
                workflow["id"],
                body.expected_intent_revision,
                text,
                _hash(text),
                audio,
                body.audio_hash,
                duration,
                frames,
                Jsonb(timeline),
                body.tts_model_id,
                body.tts_config_hash,
                now,
                now if state == "PUBLISHED" else None,
                state,
            ),
        )
        _event(
            conn,
            workflow,
            "ResearchBaselineAudioGenerated"
            if state == "GENERATED"
            else "ResearchBaselineAudioPublished",
            body.expected_intent_revision,
            operation_id,
            body.command_id,
            {
                "segment_id": str(segment_id),
                "audio_hash": body.audio_hash,
                "research_arm": "B3",
                "claim_permit_id": None,
            },
            trace_id,
        )
        response = {
            "segment_id": str(segment_id),
            "state": state,
            "duration_ms": duration,
            "frame_count": frames,
            "text_hash": _hash(text),
            "audio_hash": body.audio_hash,
        }
        _receipt(conn, body.command_id, command_type, workflow["id"], request_hash, response)
        return response


def publish_b3(body: B3AudioRequest, trace_id: str) -> dict[str, Any]:
    return _write_b3(body, trace_id, "PUBLISHED")


def stage_b3(body: B3AudioRequest, trace_id: str) -> dict[str, Any]:
    return _write_b3(body, trace_id, "GENERATED")
