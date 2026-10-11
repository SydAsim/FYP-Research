"""Thin Phase 2 operation HTTP adapter."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from apps.api_controller.phase2_models import PrepareExternalAppointmentRequest
from apps.api_controller.phase2_service import operation_detail, prepare_external

router = APIRouter()


@router.post("/internal/phase2/operations", status_code=status.HTTP_202_ACCEPTED)
def prepare(body: PrepareExternalAppointmentRequest, request: Request) -> dict[str, object]:
    return prepare_external(body, request.state.trace_id)


@router.get("/v1/operations/{operation_id}")
def detail(operation_id: UUID) -> dict[str, object]:
    return operation_detail(operation_id)
