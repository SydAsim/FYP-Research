"""Validated deterministic provider simulator inputs."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Visibility(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class FaultKind(StrEnum):
    DROP_RESPONSE = "DROP_RESPONSE"
    DELAY = "DELAY"
    DUPLICATE = "DUPLICATE"
    REORDER = "REORDER"
    RETURN_5XX = "RETURN_5XX"
    CRASH = "CRASH"
    PARTIAL_EFFECT = "PARTIAL_EFFECT"
    CONFLICTING_CHANGE = "CONFLICTING_CHANGE"


class BarrierName(StrEnum):
    BEFORE_COMMIT = "BEFORE_COMMIT"
    AFTER_COMMIT_BEFORE_RESPONSE = "AFTER_COMMIT_BEFORE_RESPONSE"
    AFTER_RESPONSE = "AFTER_RESPONSE"


class FaultRule(StrictModel):
    request_index: int = Field(ge=1)
    stage: BarrierName
    kind: FaultKind


class ScenarioConfig(StrictModel):
    idempotency: bool = True
    status_lookup: bool = True
    resource_lookup: bool = True
    visibility: Visibility = Visibility.IMMEDIATE
    visibility_reads: int = Field(default=0, ge=0)
    supports_reschedule: bool = True
    held_barriers: list[str] = Field(default_factory=list)
    faults: list[FaultRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_barriers(self) -> "ScenarioConfig":
        for item in self.held_barriers:
            stage, separator, index = item.partition(":")
            if (
                not separator
                or stage not in BarrierName._value2member_map_
                or not index.isdigit()
                or int(index) < 1
            ):
                raise ValueError("Held barriers must be STAGE:positive-request-index")
        for fault in self.faults:
            if fault.kind in (FaultKind.DELAY, FaultKind.REORDER):
                if f"{fault.stage.value}:{fault.request_index}" not in self.held_barriers:
                    raise ValueError("DELAY and REORDER require their named held barrier")
        return self


class ProviderAction(StrEnum):
    CREATE = "CREATE"
    RESCHEDULE = "RESCHEDULE"
    CANCEL = "CANCEL"


class ProviderOperation(StrictModel):
    scenario_id: UUID
    operation_id: UUID
    idempotency_key: str = Field(min_length=1)
    request_hash: str = Field(min_length=1)
    action: ProviderAction
    resource_key: str = Field(min_length=1)
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    timezone: str | None = None
    appointment_id: UUID | None = None
    expected_resource_version: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_action(self) -> "ProviderOperation":
        if self.action in (ProviderAction.CREATE, ProviderAction.RESCHEDULE):
            if self.requested_start is None or self.requested_end is None or self.timezone is None:
                raise ValueError("Create/reschedule require start, end and IANA zone")
            if self.requested_start.tzinfo is None or self.requested_end.tzinfo is None:
                raise ValueError("Appointment times must have UTC offsets")
            if self.requested_end <= self.requested_start:
                raise ValueError("Appointment end must follow start")
            try:
                zone = ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("Unknown IANA zone") from exc
            if any(
                value.utcoffset() != value.astimezone(zone).utcoffset()
                for value in (self.requested_start, self.requested_end)
            ):
                raise ValueError("Timestamp offset does not match IANA zone")
        if (
            self.action in (ProviderAction.RESCHEDULE, ProviderAction.CANCEL)
            and self.appointment_id is None
        ):
            raise ValueError("Reschedule/cancel require appointment_id")
        return self
