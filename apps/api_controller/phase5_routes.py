"""Thin browser-facing HTTP boundary for Phase 5 read models."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder

from apps.api_controller.phase1_service import DomainProblem
from apps.api_controller.phase5_models import (
    CreateCallRequest,
    CreateNoteRequest,
    ExperimentDraftRequest,
    HandoffCommand,
)
from apps.api_controller.phase5_service import (
    appointment_detail,
    call_detail,
    call_media_token,
    call_summary,
    call_timeline,
    create_call,
    create_experiment_draft,
    create_note,
    dashboard,
    evaluation_run,
    evaluation_runs,
    list_appointments,
    list_calls,
    list_handoffs,
    list_notes,
    list_residents,
    public_config,
    resident_detail,
    settings,
    update_handoff,
)

router = APIRouter()


def _page(response: Response, result: tuple[list[dict[str, Any]], int]) -> Any:
    rows, total = result
    response.headers["x-total-count"] = str(total)
    return jsonable_encoder(rows)


@router.get("/v1/public/config")
def get_public_config() -> Any:
    return public_config()


@router.post("/v1/calls", status_code=status.HTTP_201_CREATED)
def post_call(
    body: CreateCallRequest,
    request: Request,
    idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")],
) -> Any:
    return create_call(body, idempotency_key, request.state.trace_id)


@router.get("/v1/calls")
def get_calls(
    response: Response, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)
) -> Any:
    return _page(response, list_calls(limit, offset))


@router.get("/v1/calls/{call_id}")
def get_call(call_id: UUID) -> Any:
    return jsonable_encoder(call_detail(call_id))


@router.get("/v1/calls/{call_id}/media-token")
def get_call_media_token(call_id: UUID) -> Any:
    return call_media_token(call_id)


@router.get("/v1/calls/{call_id}/summary")
def get_call_summary(call_id: UUID) -> Any:
    return jsonable_encoder(call_summary(call_id))


@router.get("/v1/calls/{call_id}/timeline")
def get_call_timeline(call_id: UUID) -> Any:
    return jsonable_encoder(call_timeline(call_id))


@router.get("/v1/appointments")
def get_appointments(
    response: Response,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Literal["HELD", "CONFIRMED", "CANCELLED", "COMPLETED"] | None = Query(
        None, alias="status"
    ),
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
) -> Any:
    if (from_at is not None and from_at.tzinfo is None) or (
        to_at is not None and to_at.tzinfo is None
    ):
        raise DomainProblem(
            "timezone-required", "Time zone required", "Date filters need a UTC offset", 422
        )
    if from_at is not None and to_at is not None and to_at <= from_at:
        raise DomainProblem(
            "invalid-date-range", "Invalid date range", "The end must follow the start", 422
        )
    return _page(response, list_appointments(limit, offset, status_filter, from_at, to_at))


@router.get("/v1/appointments/{appointment_id}")
def get_appointment(appointment_id: UUID) -> Any:
    return jsonable_encoder(appointment_detail(appointment_id))


@router.get("/v1/residents")
def get_residents(
    response: Response, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)
) -> Any:
    return _page(response, list_residents(limit, offset))


@router.get("/v1/residents/{resident_id}")
def get_resident(resident_id: UUID) -> Any:
    return jsonable_encoder(resident_detail(resident_id))


@router.get("/v1/notes")
def get_notes(
    response: Response, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)
) -> Any:
    return _page(response, list_notes(limit, offset))


@router.post("/v1/notes", status_code=status.HTTP_201_CREATED)
def post_note(body: CreateNoteRequest) -> Any:
    return create_note(body)


@router.get("/v1/handoffs")
def get_handoffs(
    response: Response, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)
) -> Any:
    return _page(response, list_handoffs(limit, offset))


@router.post("/v1/handoffs/{handoff_id}/acknowledge")
def acknowledge_handoff(handoff_id: UUID, body: HandoffCommand, request: Request) -> Any:
    return update_handoff(handoff_id, body, "ACKNOWLEDGED", request.state.trace_id)


@router.post("/v1/handoffs/{handoff_id}/resolve")
def resolve_handoff(handoff_id: UUID, body: HandoffCommand, request: Request) -> Any:
    return update_handoff(handoff_id, body, "RESOLVED", request.state.trace_id)


@router.get("/v1/dashboard/summary")
def get_dashboard() -> Any:
    return jsonable_encoder(dashboard())


@router.get("/v1/evaluation/runs")
def get_evaluation_runs(
    response: Response, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)
) -> Any:
    return _page(response, evaluation_runs(limit, offset))


@router.post("/v1/evaluation/runs", status_code=status.HTTP_201_CREATED)
def post_evaluation_draft(body: ExperimentDraftRequest) -> Any:
    return create_experiment_draft(body)


@router.get("/v1/evaluation/runs/{run_id}")
def get_evaluation_run(run_id: UUID) -> Any:
    return jsonable_encoder(evaluation_run(run_id))


@router.get("/v1/settings")
def get_settings() -> Any:
    return settings()
