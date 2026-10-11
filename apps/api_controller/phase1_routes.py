"""Thin HTTP adapter for the deterministic Phase 1 commands."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from apps.api_controller.phase1_models import (
    AcceptRevisionRequest,
    CommitLocalRequest,
    PrepareAppointmentRequest,
    SyntheticFixtureRequest,
)
from apps.api_controller.phase1_service import (
    accept_revision,
    commit_local,
    create_fixture,
    prepare_appointment,
    workflow_history,
)

router = APIRouter()


@router.post("/internal/phase1/fixtures", status_code=status.HTTP_201_CREATED)
def fixture(body: SyntheticFixtureRequest) -> dict[str, object]:
    return create_fixture(body)


@router.post("/v1/workflows/{workflow_id}/revisions", status_code=status.HTTP_201_CREATED)
def revision(workflow_id: UUID, body: AcceptRevisionRequest, request: Request) -> dict[str, object]:
    return accept_revision(workflow_id, body, request.state.trace_id)


@router.post("/v1/operations/appointments", status_code=status.HTTP_202_ACCEPTED)
def prepare(body: PrepareAppointmentRequest, request: Request) -> dict[str, object]:
    return prepare_appointment(body, request.state.trace_id)


@router.post("/v1/operations/{operation_id}/commit-local")
def commit(operation_id: UUID, body: CommitLocalRequest, request: Request) -> dict[str, object]:
    return commit_local(operation_id, body, request.state.trace_id)


@router.get("/v1/workflows/{workflow_id}/history")
def history(workflow_id: UUID) -> dict[str, object]:
    return workflow_history(workflow_id)
