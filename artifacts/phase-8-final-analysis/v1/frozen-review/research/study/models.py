"""Strict review-design and offline evidence contracts, separate from v1/v2."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from research.arms import Arm
from research.provider_simulator.models import ScenarioConfig
from research.scenario_dsl.models import stable_hash

VERSION = "phase8-study-design-v3"
Status = Literal["TRUE", "FALSE", "UNKNOWN", "NOT_APPLICABLE"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Stratum(StrEnum):
    CLEAN = "CLEAN"
    AMBIGUITY = "HIDDEN_COMMIT"
    EXPOSURE = "PLAYOUT"
    BOUNDARY = "OTHER_BOUNDARY"


class Intent(Strict):
    revision: int = Field(ge=1, le=3)
    start: datetime
    end: datetime
    timezone: str
    transcript: str = Field(min_length=1)

    @model_validator(mode="after")
    def schedule(self) -> "Intent":
        zone = ZoneInfo(self.timezone)
        if self.start.tzinfo is None or self.end.tzinfo is None or self.end <= self.start:
            raise ValueError("Offset timestamps and positive appointment duration required")
        if any(t.utcoffset() != t.astimezone(zone).utcoffset() for t in (self.start, self.end)):
            raise ValueError("Appointment offset must match original IANA zone")
        return self


class StudyCase(Strict):
    version: Literal["phase8-study-design-v3"] = "phase8-study-design-v3"
    case_id: str
    stratum: Stratum
    cluster_id: str
    generator_family: str
    member: int = Field(ge=0, le=9)
    cluster_representative: bool
    seed: int
    resource_binding: Literal["NEW_SYNTHETIC_PROPERTY_MAINTENANCE"]
    initial_state: Literal["EMPTY_RESOURCE"]
    issue: str
    intents: list[Intent] = Field(min_length=1, max_length=3)
    correction_barrier: str
    fault_schedule: list[str]
    provider: ScenarioConfig
    speech_exposure: str
    media: Literal["SCRIPTED_TONE_PROTOCOL_PROXY"]
    speaker_id: None = None
    recording_id: None = None
    primary_arms: list[Arm]
    secondary_arms: list[Arm]
    arm_order: list[Arm]
    observation_budget_seconds: int = Field(ge=1)

    @model_validator(mode="after")
    def coherent(self) -> "StudyCase":
        if self.cluster_representative != (self.member == 0):
            raise ValueError(
                "Member zero is the predeclared representative, never outcome-selected"
            )
        if [i.revision for i in self.intents] != list(range(1, len(self.intents) + 1)):
            raise ValueError("Intent revisions must be sequential")
        if self.stratum is Stratum.CLEAN and len(self.intents) != 1:
            raise ValueError("Clean task has exactly one intent")
        if self.stratum is not Stratum.CLEAN and len(self.intents) < 2:
            raise ValueError("Revision task requires externally specified correction")
        if self.primary_arms != [Arm.B3, Arm.P1, Arm.P2]:
            raise ValueError("Primary comparison arms must be explicit and consistent")
        if set(self.arm_order) != set(self.primary_arms + self.secondary_arms):
            raise ValueError("Arm order must contain each applicable arm once")
        if len(self.arm_order) != len(set(self.arm_order)):
            raise ValueError("Duplicate execution arm")
        return self

    @property
    def fixture_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))

    @property
    def fault_label(self) -> str:
        parts = [f"{f.kind}:{f.stage}:{f.request_index}" for f in self.provider.faults]
        return "+".join(parts + self.fault_schedule) or "NONE"

    @property
    def semantic_hash(self) -> str:
        body = self.model_dump(mode="json")
        for key in (
            "case_id",
            "cluster_id",
            "member",
            "seed",
            "arm_order",
            "cluster_representative",
        ):
            body.pop(key)
        return stable_hash(body)


class Acceptance(Strict):
    revision: int = Field(ge=1)
    scripted_at: datetime
    accepted_at: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    actual_timezone: str | None

    @field_validator("scripted_at", "accepted_at", "actual_start", "actual_end")
    @classmethod
    def offset(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Event timestamps need UTC offsets")
        return value


class Evidence(Strict):
    classification: Literal["VALIDATION_ONLY", "CAMPAIGN"]
    case_id: str
    arm: Arm
    attempt: int = Field(ge=1)
    execution_id: str
    fixture_hash: str
    started_at: datetime
    ended_at: datetime
    status: Literal["COMPLETED", "TIMEOUT", "INFRASTRUCTURE_FAILURE", "EVIDENCE_INVALID"]
    resource_key: str
    acceptances: list[Acceptance]
    # Provider/segment/ACK records are raw JSON boundaries, validated by the adapter.
    truth: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    playback: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    truth_complete: bool
    publication_journal_complete: bool
    playback_journal_complete: bool
    independent_truth_source: Literal["SIMULATOR_APPEND_ONLY_ORACLE_EXPORT"]
    raw_trace_hash: str
    error: dict[str, Any] | None = None
    repair_obligations: list[dict[str, Any]] | None = None
    repair_journal_complete: bool = False

    @model_validator(mode="after")
    def clocks(self) -> "Evidence":
        if self.started_at.tzinfo is None or self.ended_at.tzinfo is None:
            raise ValueError("Observation window needs UTC offsets")
        if self.ended_at < self.started_at:
            raise ValueError("Observation ended before it began")
        return self


class AnalysisRow(Strict):
    classification: Literal["VALIDATION_ONLY", "CAMPAIGN"]
    case_id: str
    cluster_id: str
    generator_family: str
    stratum: Stratum
    member: int
    cluster_representative: bool
    arm: Arm
    attempt: int
    execution_id: str
    values: dict[str, Status]
    duration_seconds: float | None = Field(ge=0, allow_inf_nan=False)
    event_observed: bool | None
    censor_reason: str | None
    oracle_hash: str
    phase: str
    fault: str
    revision_type: Literal["NONE", "PARAMETER_CORRECTION"]
    action_class: Literal["CREATE", "CREATE_RESCHEDULE", "CREATE_CANCEL_CREATE"]
    speaker_id: str | None = None
    recording_id: str | None = None

    @model_validator(mode="after")
    def timing(self) -> "AnalysisRow":
        if (self.duration_seconds is None) != (self.event_observed is None):
            raise ValueError("A missing time cannot be an observed event or a timed censor")
        if self.event_observed and self.censor_reason is not None:
            raise ValueError("An event cannot also be censored")
        return self
