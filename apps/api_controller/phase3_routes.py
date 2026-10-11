"""Thin validated HTTP endpoints for Phase 3 evidence and text publication."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from apps.api_controller.phase3_claim_service import (
    authorize,
    permit_detail,
    publish,
    queue,
    safe_language,
)
from apps.api_controller.phase3_models import AuthorizeClaimRequest, PermitCommand, VerifyRequest
from apps.api_controller.phase3_verification_service import issue_verification, receipt_detail

router = APIRouter()


@router.post("/internal/phase3/verifications", status_code=status.HTTP_201_CREATED)
def verify(body: VerifyRequest, request: Request) -> dict[str, object]:
    return issue_verification(body, request.state.trace_id)


@router.get("/v1/receipts/{receipt_id}")
def receipt(receipt_id: UUID) -> dict[str, object]:
    return receipt_detail(receipt_id)


@router.post("/internal/phase3/claims", status_code=status.HTTP_201_CREATED)
def prepare_claim(body: AuthorizeClaimRequest, request: Request) -> dict[str, object]:
    return authorize(body, request.state.trace_id)


@router.post("/internal/phase3/permits/{permit_id}/queue")
def queue_permit(permit_id: UUID, body: PermitCommand, request: Request) -> dict[str, object]:
    return queue(permit_id, body, request.state.trace_id)


@router.post("/internal/phase3/permits/{permit_id}/publish")
def publish_permit(permit_id: UUID, body: PermitCommand, request: Request) -> dict[str, object]:
    return publish(permit_id, body, request.state.trace_id)


@router.get("/v1/permits/{permit_id}")
def permit(permit_id: UUID) -> dict[str, object]:
    return permit_detail(permit_id)


@router.get("/v1/workflows/{workflow_id}/safe-language")
def safe_progress(workflow_id: UUID) -> dict[str, str]:
    return safe_language(workflow_id)
