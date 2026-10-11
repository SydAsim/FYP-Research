"""Strict, hashed scenario language shared by every research arm."""

import hashlib
import json
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator


def stable_hash(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Barrier(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"
    P6 = "P6"
    P7 = "P7"
    P8 = "P8"
    P9 = "P9"


class FaultFamily(StrEnum):
    NONE = "NONE"
    RESPONSE_LOSS = "RESPONSE_LOSS"
    DELAY = "DELAY"
    PROVIDER_REFUSAL = "PROVIDER_REFUSAL"
    PROVIDER_CONFLICT = "PROVIDER_CONFLICT"
    PARTIAL_EFFECT = "PARTIAL_EFFECT"
    REDIS_LOSS = "REDIS_LOSS"
    PARTIAL_PLAYBACK = "PARTIAL_PLAYBACK"


class ProviderCapability(StrEnum):
    ATOMIC_RESCHEDULE = "ATOMIC_RESCHEDULE_STATUS_AND_RESOURCE_LOOKUP"
    COMPENSATE_CANCEL_CREATE = "CANCEL_CREATE_STATUS_AND_RESOURCE_LOOKUP"

    @property
    def supports_reschedule(self) -> bool:
        return self is ProviderCapability.ATOMIC_RESCHEDULE


class ProviderVisibility(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    DELAYED_TWO_READS = "DELAYED_TWO_READS"
    UNAVAILABLE = "UNAVAILABLE"
    STALE_TWO_READS = "STALE_TWO_READS"

    @property
    def simulator_visibility(self) -> str:
        if self is ProviderVisibility.UNAVAILABLE:
            return "UNAVAILABLE"
        if self is ProviderVisibility.STALE_TWO_READS:
            return "STALE"
        return "DELAYED" if self is ProviderVisibility.DELAYED_TWO_READS else "IMMEDIATE"

    @property
    def visibility_reads(self) -> int:
        return (
            2
            if self in (ProviderVisibility.DELAYED_TWO_READS, ProviderVisibility.STALE_TWO_READS)
            else 0
        )


class ScenarioCase(StrictModel):
    fixture_version: str = Field(min_length=1)
    scenario_key: str = Field(min_length=1)
    revision_type: str
    action_semantics: str
    workflow_shape: str
    acoustic_condition: str
    provider_capability: ProviderCapability
    visibility: ProviderVisibility
    speech_exposure: str
    fault_family: FaultFamily
    correction_barrier: Barrier
    seed: int
    initial_start: datetime
    final_start: datetime
    timezone: str
    initial_transcript: str = Field(min_length=1)
    correction_transcript: str = Field(min_length=1)
    audio_hash: str = Field(pattern="^[0-9a-f]{64}$")
    repetition: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def valid_schedule(self) -> "ScenarioCase":
        zone = ZoneInfo(self.timezone)
        if self.initial_start.tzinfo is None or self.final_start.tzinfo is None:
            raise ValueError("Scenario starts must carry UTC offsets")
        if any(
            value.utcoffset() != value.astimezone(zone).utcoffset()
            for value in (self.initial_start, self.final_start)
        ):
            raise ValueError("Scenario start offset must match IANA zone")
        if self.initial_start == self.final_start and self.revision_type not in (
            "RETRACTION",
            "ADDITIVE_COMPATIBLE",
        ):
            raise ValueError("Correction scenarios need a changed final intent")
        if (
            self.fault_family is FaultFamily.RESPONSE_LOSS
            and self.correction_barrier is not Barrier.P3
        ):
            raise ValueError("Post-commit response loss belongs at P3")
        if (
            self.fault_family is FaultFamily.PARTIAL_PLAYBACK
            and self.correction_barrier is not Barrier.P8
        ):
            raise ValueError("Partial playback belongs at P8")
        if self.fault_family is FaultFamily.DELAY and self.correction_barrier is not Barrier.P2:
            raise ValueError("Pre-commit provider delay belongs at P2")
        if (
            self.fault_family is FaultFamily.PROVIDER_REFUSAL
            and self.correction_barrier is not Barrier.P2
        ):
            raise ValueError("Pre-commit provider refusal belongs at P2")
        if self.visibility is ProviderVisibility.UNAVAILABLE and (
            self.correction_barrier is not Barrier.P3
            or self.fault_family is not FaultFamily.RESPONSE_LOSS
        ):
            raise ValueError("Unavailable evidence case requires hidden-commit response loss at P3")
        if self.fault_family is FaultFamily.PROVIDER_CONFLICT and (
            self.correction_barrier is not Barrier.P5
            or self.visibility is not ProviderVisibility.IMMEDIATE
            or not self.provider_capability.supports_reschedule
        ):
            raise ValueError("Provider conflict requires immediate atomic reschedule after P5")
        if (
            self.fault_family is FaultFamily.PARTIAL_EFFECT
            and self.correction_barrier is not Barrier.P2
        ):
            raise ValueError("Partial provider effect belongs at P2")
        if (
            self.fault_family is FaultFamily.REDIS_LOSS
            and self.correction_barrier is not Barrier.P3
        ):
            raise ValueError("Redis loss recovery case belongs at P3")
        return self

    @property
    def fixture_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))

    @property
    def final_intent(self) -> dict[str, str]:
        if self.revision_type == "RETRACTION":
            return {"appointment_status": "CANCELLED", "timezone": self.timezone}
        return {
            "requested_start": self.final_start.isoformat(),
            "requested_end": (self.final_start + timedelta(hours=1)).isoformat(),
            "timezone": self.timezone,
        }


class CleanScenarioCase(StrictModel):
    """One accepted intent and one CREATE, without a correction boundary."""

    fixture_version: str = Field(min_length=1)
    scenario_key: str = Field(min_length=1)
    seed: int
    final_start: datetime
    timezone: str
    transcript: str = Field(min_length=1)
    audio_hash: str = Field(pattern="^[0-9a-f]{64}$")
    acoustic_condition: str
    provider_capability: ProviderCapability
    visibility: ProviderVisibility
    repetition: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def valid_start(self) -> "CleanScenarioCase":
        zone = ZoneInfo(self.timezone)
        if self.final_start.tzinfo is None:
            raise ValueError("Clean task start must carry a UTC offset")
        if self.final_start.utcoffset() != self.final_start.astimezone(zone).utcoffset():
            raise ValueError("Clean task start offset must match IANA zone")
        return self

    @property
    def fixture_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))

    @property
    def final_intent(self) -> dict[str, str]:
        return {
            "requested_start": self.final_start.isoformat(),
            "requested_end": (self.final_start + timedelta(hours=1)).isoformat(),
            "timezone": self.timezone,
        }
