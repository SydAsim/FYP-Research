"""Validated browser-facing Phase 5 request bodies."""

from uuid import UUID

from pydantic import Field, model_validator

from apps.api_controller.phase1_models import StrictModel


class CreateCallRequest(StrictModel):
    consent: bool
    resident_id: UUID
    experiment_run_id: UUID | None = None


class CreateNoteRequest(StrictModel):
    command_id: UUID
    resident_id: UUID
    category: str = Field(
        pattern="^(SCHEDULING_PREFERENCE|ACCESS_INSTRUCTION|MAINTENANCE_CONTEXT|COMMUNICATION_PREFERENCE|FOLLOW_UP)$"
    )
    note_text: str = Field(min_length=1, max_length=2000)
    expected_resident_version: int = Field(ge=0)


class HandoffCommand(StrictModel):
    command_id: UUID
    expected_state: str = Field(pattern="^(OPEN|ACKNOWLEDGED)$")
    note: str | None = Field(default=None, max_length=2000)
    administrative_closure: bool = False


class ExperimentDraftRequest(StrictModel):
    command_id: UUID
    name: str = Field(min_length=3, max_length=120)
    fixture_version: str = Field(min_length=1, max_length=120)
    final_intent: str = Field(min_length=3, max_length=500)
    correction_phase: str = Field(pattern=r"^P[0-9]$")
    provider_behavior: str = Field(
        pattern="^(VISIBLE_COMMIT|HIDDEN_COMMIT|REFUSAL|UNKNOWN_TIMEOUT)$"
    )
    fault_family: str = Field(pattern="^(NONE|RESPONSE_LOSS|DELAY|REDIS_LOSS|PARTIAL_PLAYBACK)$")
    arms: list[str] = Field(min_length=1, max_length=6)
    seeds: list[int] = Field(min_length=1, max_length=100)
    oracle_required: bool = True
    model_profile: str = Field(min_length=1, max_length=120)

    @model_validator(mode="after")
    def validate_research_scope(self) -> "ExperimentDraftRequest":
        if not self.oracle_required:
            raise ValueError("Independent oracle is required")
        if any(arm not in {"B0", "B1", "B2", "B3", "P1", "P2"} for arm in self.arms):
            raise ValueError("Unknown system arm")
        if len(self.arms) != len(set(self.arms)) or len(self.seeds) != len(set(self.seeds)):
            raise ValueError("Arms and seeds must be unique")
        if any(
            word in self.final_intent.casefold() for word in ("allergy", "medical", "emergency")
        ):
            raise ValueError("Final intent is outside maintenance scope")
        return self
