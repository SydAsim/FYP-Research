"""Validated voice, audio scheduling, and client exposure commands."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field, field_validator

from apps.api_controller.phase1_models import CandidateSource, DesiredAppointment, StrictModel
from packages.protocol.voice import VoiceEventType


class VoiceEventRequest(StrictModel):
    event_id: UUID
    source_event_id: str = Field(min_length=1)
    event_type: VoiceEventType
    occurred_at: datetime
    raw: dict[str, object]
    normalized: dict[str, object]

    @field_validator("occurred_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Voice event time needs a UTC offset")
        return value


class PrepareSegmentRequest(StrictModel):
    command_id: UUID
    permit_id: UUID
    expected_intent_revision: int = Field(ge=1)
    audio_base64: str = Field(min_length=1)
    audio_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    tts_model_id: str = Field(min_length=1)
    tts_config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    repair_obligation_id: UUID | None = None


class SegmentCommand(StrictModel):
    command_id: UUID
    expected_intent_revision: int = Field(ge=1)


class PlaybackType(StrEnum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    INTERRUPTED = "INTERRUPTED"
    COMPLETED = "COMPLETED"


class PlaybackEventRequest(StrictModel):
    event_id: UUID
    segment_id: UUID
    event_type: PlaybackType
    client_time: datetime
    played_ms: int = Field(default=0, ge=0)
    last_frame: int = Field(default=0, ge=0)
    last_word_index: int = Field(default=0, ge=0)

    @field_validator("client_time")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Client time needs a UTC offset")
        return value


class MediaEndRequest(StrictModel):
    command_id: UUID


class VoiceToolProposal(StrictModel):
    desired_state: DesiredAppointment
    candidate_source: CandidateSource


class AcceptVoiceProposalRequest(StrictModel):
    command_id: UUID
    source_event_id: str = Field(min_length=1)
    expected_revision: int = Field(ge=0)
    change_class: str = Field(
        pattern="^(INITIAL|PARAMETER_CORRECTION|REPLACEMENT|RETRACTION|ADDITIVE_COMPATIBLE|CONFLICTING_CHANGE)$"
    )
