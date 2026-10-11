"""Research-only B3 audio boundary."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from apps.api_controller.phase6_b3_audio import (
    B3AudioRequest,
    publish_b3,
    stage_b3,
    synthesis_input,
)

router = APIRouter()


@router.get("/internal/phase6/b3/workflows/{workflow_id}/synthesis-input")
def b3_synthesis_input(workflow_id: UUID, revision: int) -> dict[str, object]:
    return synthesis_input(workflow_id, revision)


@router.post("/internal/phase6/b3/audio-segments", status_code=status.HTTP_201_CREATED)
def b3_publish(body: B3AudioRequest, request: Request) -> dict[str, object]:
    return publish_b3(body, request.state.trace_id)


@router.post("/internal/phase6/b3/audio-segments/stage", status_code=status.HTTP_201_CREATED)
def b3_stage(body: B3AudioRequest, request: Request) -> dict[str, object]:
    return stage_b3(body, request.state.trace_id)
