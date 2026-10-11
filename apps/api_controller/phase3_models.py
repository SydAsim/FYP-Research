"""Validated research commands for verification and text publication."""

from uuid import UUID

from pydantic import Field

from apps.api_controller.phase1_models import StrictModel
from packages.domain.phase3_verification import ClaimType


class VerifyRequest(StrictModel):
    command_id: UUID
    operation_id: UUID
    expected_intent_revision: int = Field(ge=1)
    claim_type: ClaimType


class AuthorizeClaimRequest(StrictModel):
    command_id: UUID
    receipt_id: UUID
    expected_intent_revision: int = Field(ge=1)


class PermitCommand(StrictModel):
    command_id: UUID
    expected_intent_revision: int = Field(ge=1)
