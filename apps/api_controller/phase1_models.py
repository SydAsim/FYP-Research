"""Validated Phase 1 HTTP command schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SyntheticFixtureRequest(StrictModel):
    command_id: UUID
    timezone: str = "Asia/Karachi"
    first_transcript: str = "Please book maintenance at 3 PM."
    second_transcript: str = "Actually, make that 4 PM."
    research_arm: Literal["B3", "P1", "P2"] | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA time zone") from exc
        return value


class CandidateSource(StrictModel):
    utterance_id: UUID
    model: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=1)
    transcript_version: int = Field(ge=1)
    audio_start_ms: int | None = Field(default=None, ge=0)
    audio_end_ms: int | None = Field(default=None, ge=0)


class DesiredAppointment(StrictModel):
    ticket_id: UUID
    appointment_id: UUID | None = None
    requested_start: datetime
    requested_end: datetime
    timezone: str

    @model_validator(mode="after")
    def validate_time(self) -> "DesiredAppointment":
        if self.requested_start.tzinfo is None or self.requested_end.tzinfo is None:
            raise ValueError("Appointment times must include UTC offsets")
        if self.requested_end <= self.requested_start:
            raise ValueError("Appointment end must follow start")
        try:
            zone = ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA time zone") from exc
        for value in (self.requested_start, self.requested_end):
            if value.utcoffset() != value.astimezone(zone).utcoffset():
                raise ValueError("Timestamp offset does not match the IANA time zone")
        return self


class AcceptRevisionRequest(StrictModel):
    command_id: UUID
    expected_revision: int = Field(ge=0)
    change_class: str = Field(
        pattern="^(INITIAL|PARAMETER_CORRECTION|REPLACEMENT|RETRACTION|ADDITIVE_COMPATIBLE|CONFLICTING_CHANGE)$"
    )
    desired_state: DesiredAppointment
    candidate_source: CandidateSource


class PrepareAppointmentRequest(StrictModel):
    command_id: UUID
    workflow_id: UUID
    expected_intent_revision: int = Field(ge=1)
    expected_resource_version: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)


class CommitLocalRequest(StrictModel):
    command_id: UUID
