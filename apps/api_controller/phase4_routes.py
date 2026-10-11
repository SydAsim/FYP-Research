"""Validated Phase 4 voice and playback HTTP boundaries."""

from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from apps.api_controller.phase4_audio_service import (
    prepare_segment,
    queue_segment,
    release_segment,
    segment_audio,
    segment_detail,
    synthesis_input,
)
from apps.api_controller.phase4_models import (
    AcceptVoiceProposalRequest,
    MediaEndRequest,
    PlaybackEventRequest,
    PrepareSegmentRequest,
    SegmentCommand,
    VoiceEventRequest,
)
from apps.api_controller.phase4_playback_service import (
    end_media,
    record_playback,
    repair_detail,
    resume_segment,
)
from apps.api_controller.phase4_voice_service import accept_voice_proposal, record_voice_event

router = APIRouter()


@router.post("/internal/phase4/calls/{call_id}/voice-events", status_code=status.HTTP_201_CREATED)
def voice_event(call_id: UUID, body: VoiceEventRequest, request: Request) -> dict[str, object]:
    return record_voice_event(call_id, body, request.state.trace_id)


@router.post(
    "/internal/phase4/workflows/{workflow_id}/accept-proposal", status_code=status.HTTP_201_CREATED
)
def accept_proposal(
    workflow_id: UUID, body: AcceptVoiceProposalRequest, request: Request
) -> dict[str, object]:
    return accept_voice_proposal(workflow_id, body, request.state.trace_id)


@router.get("/internal/phase4/permits/{permit_id}/synthesis-input")
def text_for_tts(permit_id: UUID, repair_obligation_id: UUID | None = None) -> dict[str, object]:
    return synthesis_input(permit_id, repair_obligation_id)


@router.post("/internal/phase4/audio-segments", status_code=status.HTTP_201_CREATED)
def prepare_audio(body: PrepareSegmentRequest, request: Request) -> dict[str, object]:
    return prepare_segment(body, request.state.trace_id)


@router.post("/internal/phase4/audio-segments/{segment_id}/queue")
def queue_audio(segment_id: UUID, body: SegmentCommand, request: Request) -> dict[str, object]:
    return queue_segment(segment_id, body, request.state.trace_id)


@router.post("/internal/phase4/audio-segments/{segment_id}/release")
def release_audio(segment_id: UUID, body: SegmentCommand, request: Request) -> dict[str, object]:
    return release_segment(segment_id, body, request.state.trace_id)


@router.post("/internal/phase4/audio-segments/{segment_id}/resume")
def resume_audio(segment_id: UUID, body: SegmentCommand, request: Request) -> dict[str, object]:
    return resume_segment(segment_id, body, request.state.trace_id)


@router.get("/v1/audio-segments/{segment_id}")
def get_segment(segment_id: UUID) -> dict[str, object]:
    return segment_detail(segment_id)


@router.get("/v1/audio-segments/{segment_id}/audio")
def get_audio(segment_id: UUID) -> Response:
    return Response(segment_audio(segment_id), media_type="audio/wav")


@router.post("/v1/calls/{call_id}/playback-events", status_code=status.HTTP_202_ACCEPTED)
def playback(call_id: UUID, body: PlaybackEventRequest, request: Request) -> dict[str, object]:
    return record_playback(call_id, body, request.state.trace_id)


@router.post("/v1/calls/{call_id}/end")
def end_call_media(call_id: UUID, body: MediaEndRequest, request: Request) -> dict[str, object]:
    return end_media(call_id, body, request.state.trace_id)


@router.get("/v1/repairs/{obligation_id}")
def get_repair(obligation_id: UUID) -> dict[str, object]:
    return repair_detail(obligation_id)
