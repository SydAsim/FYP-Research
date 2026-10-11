"""Provider-neutral cascaded voice worker and deterministic research adapters."""

import asyncio
import base64
import binascii
import hashlib
import os
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import Field

from apps.api_controller.phase1_models import DesiredAppointment, StrictModel
from apps.voice_worker.cascade import (
    CascadedVoiceAdapter,
    DeterministicToneTTS,
    ScriptedSTT,
    ScriptedTypedIntentLLM,
)
from apps.voice_worker.live_agent import LiveRoomAgent
from apps.voice_worker.livekit_transport import LiveKitTransport
from apps.voice_worker.offline_adapters import LocalVoskSTT
from apps.voice_worker.scheduler import HttpControllerPort, VoiceScheduler
from packages.observability.logging import configure_logging
from packages.protocol.voice import VoiceEventType

configure_logging("voice-worker")
app = FastAPI(title="Commit-Aware Voice Worker", docs_url=None, redoc_url=None)
_rooms: dict[UUID, LiveRoomAgent] = {}
_room_lock = asyncio.Lock()
_offline_stt: LocalVoskSTT | None = None


@app.middleware("http")
async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.trace_id = str(uuid4())
    response = await call_next(request)
    response.headers["x-trace-id"] = request.state.trace_id
    return response


def _problem(request: Request, status: int, slug: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://example.invalid/problems/{slug}",
            "title": slug.replace("-", " ").title(),
            "status": status,
            "detail": detail,
            "instance": str(request.url.path),
            "trace_id": request.state.trace_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_problem(request: Request, exc: HTTPException) -> JSONResponse:
    return _problem(request, exc.status_code, "voice-request", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, _exc: RequestValidationError) -> JSONResponse:
    return _problem(request, 422, "invalid-request", "Voice command did not match its schema")


@app.exception_handler(ValueError)
async def rejected_voice_command(request: Request, exc: ValueError) -> JSONResponse:
    return _problem(request, 409, "voice-command-rejected", str(exc))


class ReplayTurnRequest(StrictModel):
    call_id: UUID
    workflow_id: UUID
    turn_key: str = Field(min_length=1)
    audio_base64: str = Field(min_length=1)
    transcript: str = Field(min_length=1)
    desired_state: DesiredAppointment
    expected_revision: int = Field(ge=0)
    change_class: str = Field(
        pattern="^(INITIAL|PARAMETER_CORRECTION|REPLACEMENT|RETRACTION|ADDITIVE_COMPATIBLE|CONFLICTING_CHANGE)$"
    )
    interrupted_segment_id: UUID | None = None


class ScheduleRequest(StrictModel):
    permit_id: UUID
    expected_intent_revision: int = Field(ge=1)
    repair_obligation_id: UUID | None = None


class B3ScheduleRequest(StrictModel):
    workflow_id: UUID
    expected_intent_revision: int = Field(ge=1)


class LiveKitPublishRequest(StrictModel):
    segment_id: UUID
    expected_intent_revision: int = Field(ge=1)
    room_token: str = Field(min_length=1)


class JoinLiveRoomRequest(StrictModel):
    call_id: UUID
    workflow_id: UUID
    room_token: str = Field(min_length=1)


def _experiment_only() -> None:
    if os.getenv("EXPERIMENT_MODE") != "true":
        raise HTTPException(status_code=404, detail="Research endpoint disabled")


def _controller() -> HttpControllerPort:
    return HttpControllerPort(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "voice-worker"}


def _local_models_ready() -> bool:
    if os.environ.get("VOICE_PROFILE") != "local_cascade" or shutil.which("espeak-ng") is None:
        return False
    model_path = Path(os.environ.get("VOSK_MODEL_PATH", "/models/vosk-model-small-en-us-0.15"))
    if not (model_path / "am" / "final.mdl").is_file():
        return False
    base_url = os.environ.get("LOCAL_LLM_URL")
    if not base_url:
        return False
    try:
        with urlopen(f"{base_url.rstrip('/')}/health", timeout=2) as response:
            return bool(response.status == 200)
    except (URLError, TimeoutError, OSError):
        return False


@app.get("/health/ready")
async def local_voice_ready() -> dict[str, str]:
    return {"status": "READY" if await asyncio.to_thread(_local_models_ready) else "UNAVAILABLE"}


@app.post("/internal/phase5/rooms/join")
async def join_live_room(body: JoinLiveRoomRequest) -> dict[str, str]:
    _experiment_only()
    if not await asyncio.to_thread(_local_models_ready):
        raise HTTPException(status_code=503, detail="Local voice models are unavailable")
    global _offline_stt
    async with _room_lock:
        prior = _rooms.get(body.call_id)
        if prior is not None and prior.transport.room.isconnected():
            return {"status": "READY", "call_id": str(body.call_id)}
        if prior is not None:
            await prior.close()
        if _offline_stt is None:
            model_path = Path(os.environ["VOSK_MODEL_PATH"])
            _offline_stt = await asyncio.to_thread(LocalVoskSTT, model_path)
        agent = LiveRoomAgent(
            body.call_id, body.workflow_id, body.room_token, _controller(), _offline_stt
        )
        try:
            await agent.start()
        except Exception as exc:
            await agent.close()
            raise HTTPException(status_code=503, detail="Voice agent could not join media") from exc
        _rooms[body.call_id] = agent
    return {"status": "READY", "call_id": str(body.call_id)}


@app.on_event("shutdown")
async def close_live_rooms() -> None:
    for agent in list(_rooms.values()):
        await agent.close()
    _rooms.clear()


@app.post("/internal/phase4/cascade/replay")
async def replay_turn(body: ReplayTurnRequest, request: Request) -> dict[str, object]:
    _experiment_only()
    try:
        audio = base64.b64decode(body.audio_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=422, detail="Invalid prerecorded audio") from exc
    digest = hashlib.sha256(audio).hexdigest()
    transcript_hash = hashlib.sha256(body.transcript.encode("utf-8")).hexdigest()
    adapter = CascadedVoiceAdapter(
        ScriptedSTT(digest, body.transcript),
        ScriptedTypedIntentLLM(transcript_hash, body.desired_state.model_dump(mode="json")),
    )
    controller = _controller()
    if body.interrupted_segment_id is not None:
        segment = await asyncio.to_thread(
            controller.get, f"/v1/audio-segments/{body.interrupted_segment_id}"
        )
        if segment["workflow_id"] != str(body.workflow_id) or segment["state"] != "STOPPED":
            raise ValueError("Interruption requires an acknowledged stopped segment")
    events = await adapter.turn(body.call_id, body.turn_key, audio, body.interrupted_segment_id)
    for event in events:
        await asyncio.to_thread(
            controller.post,
            f"/internal/phase4/calls/{body.call_id}/voice-events",
            {
                "event_id": str(event.event_id),
                "source_event_id": event.source_event_id,
                "event_type": event.event_type.value,
                "occurred_at": event.occurred_at.isoformat(),
                "raw": event.raw,
                "normalized": event.normalized,
            },
        )
    proposal = next(
        event for event in events if event.event_type is VoiceEventType.TOOL_PROPOSAL_RECEIVED
    )
    accepted = await asyncio.to_thread(
        controller.post,
        f"/internal/phase4/workflows/{body.workflow_id}/accept-proposal",
        {
            "command_id": str(uuid5(NAMESPACE_URL, f"accept-voice:{body.call_id}:{body.turn_key}")),
            "source_event_id": proposal.source_event_id,
            "expected_revision": body.expected_revision,
            "change_class": body.change_class,
        },
    )
    return {
        "call_id": str(body.call_id),
        "workflow_id": str(body.workflow_id),
        "revision": accepted["revision"],
        "audio_hash": digest,
        "transcript_hash": transcript_hash,
        "event_count": len(events),
        "trace_id": request.state.trace_id,
    }


@app.post("/internal/phase4/cascade/schedule")
async def schedule_claim(body: ScheduleRequest) -> dict[str, object]:
    _experiment_only()
    scheduler = VoiceScheduler(_controller(), DeterministicToneTTS())
    return await asyncio.to_thread(
        scheduler.schedule, body.permit_id, body.expected_intent_revision, body.repair_obligation_id
    )


@app.post("/internal/phase6/claim/stage")
async def stage_claim(body: ScheduleRequest) -> dict[str, object]:
    _experiment_only()
    scheduler = VoiceScheduler(_controller(), DeterministicToneTTS())
    return await asyncio.to_thread(
        scheduler.stage_claim,
        body.permit_id,
        body.expected_intent_revision,
        body.repair_obligation_id,
    )


@app.post("/internal/phase6/b3/schedule")
async def schedule_b3(body: B3ScheduleRequest) -> dict[str, object]:
    _experiment_only()
    scheduler = VoiceScheduler(_controller(), DeterministicToneTTS())
    return await asyncio.to_thread(
        scheduler.schedule_b3, body.workflow_id, body.expected_intent_revision
    )


@app.post("/internal/phase6/b3/stage")
async def stage_b3(body: B3ScheduleRequest) -> dict[str, object]:
    _experiment_only()
    scheduler = VoiceScheduler(_controller(), DeterministicToneTTS())
    return await asyncio.to_thread(
        scheduler.stage_b3, body.workflow_id, body.expected_intent_revision
    )


@app.post("/internal/phase4/livekit/publish")
async def publish_livekit(body: LiveKitPublishRequest) -> dict[str, object]:
    _experiment_only()
    transport = LiveKitTransport(_controller())
    try:
        await transport.connect(os.getenv("LIVEKIT_URL", "ws://127.0.0.1:7880"), body.room_token)
        return await transport.publish_segment(body.segment_id, body.expected_intent_revision)
    finally:
        await transport.close()
