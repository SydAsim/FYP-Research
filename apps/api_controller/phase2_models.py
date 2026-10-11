"""Validated Phase 2 external-operation commands."""

from uuid import UUID

from pydantic import Field

from apps.api_controller.phase1_models import StrictModel


class PrepareExternalAppointmentRequest(StrictModel):
    command_id: UUID
    workflow_id: UUID
    scenario_id: UUID
    expected_intent_revision: int = Field(ge=1)
    expected_resource_version: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1)
