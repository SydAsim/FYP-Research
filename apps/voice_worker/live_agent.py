"""Join one LiveKit call and run the strict local cascaded voice path."""

import asyncio
import hashlib
import io
import math
import os
import wave
from collections import deque
from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any
from urllib.error import URLError
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import structlog
from livekit import rtc

from apps.voice_worker.cascade import CascadedVoiceAdapter
from apps.voice_worker.livekit_transport import LiveKitTransport
from apps.voice_worker.offline_adapters import (
    AppointmentContext,
    LocalEspeakTTS,
    LocalLlamaIntent,
    LocalVoskSTT,
    NeedDetails,
)
from apps.voice_worker.scheduler import HttpControllerPort, VoiceScheduler
from packages.protocol.voice import VoiceEventType

logger = structlog.get_logger(__name__)


def pcm_wav(samples: bytes) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(samples)
    return output.getvalue()


class TurnSegmenter:
    """Bounded energy endpointing; it has no authority over business state."""

    def __init__(self) -> None:
        self.leading: deque[bytes] = deque(maxlen=10)
        self.frames: list[bytes] = []
        self.silent_frames = 0
        self.voiced_frames = 0

    def push(self, pcm: bytes) -> bytes | None:
        if len(pcm) < 2:
            return None
        samples = memoryview(pcm).cast("h")
        rms = math.isqrt(sum(sample * sample for sample in samples) // len(samples))
        speaking = rms >= 450
        if not self.frames:
            self.leading.append(pcm)
            if not speaking:
                return None
            self.frames.extend(self.leading)
            self.leading.clear()
        else:
            self.frames.append(pcm)
        self.voiced_frames += int(speaking)
        self.silent_frames = 0 if speaking else self.silent_frames + 1
        if self.silent_frames < 35 and len(self.frames) < 750:
            return None
        result = b"".join(self.frames) if self.voiced_frames >= 15 else None
        self.frames = []
        self.silent_frames = 0
        self.voiced_frames = 0
        return result

    def finish(self) -> bytes | None:
        result = b"".join(self.frames) if self.voiced_frames >= 15 else None
        self.frames = []
        self.silent_frames = 0
        self.voiced_frames = 0
        return result


class LiveRoomAgent:
    def __init__(
        self,
        call_id: UUID,
        workflow_id: UUID,
        room_token: str,
        controller: HttpControllerPort,
        stt: LocalVoskSTT,
    ) -> None:
        self.call_id = call_id
        self.workflow_id = workflow_id
        self.room_token = room_token
        self.controller = controller
        self.stt = stt
        self.transport = LiveKitTransport(controller)
        self.turn_lock = asyncio.Lock()
        self.tasks: set[asyncio.Task[None]] = set()
        self.connected = False

    async def start(self) -> None:
        self.transport.room.on("track_subscribed", self._on_track)
        await self.transport.connect(os.environ["LIVEKIT_URL"], self.room_token)
        self.connected = True

    async def close(self) -> None:
        for task in list(self.tasks):
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        await self.transport.close()
        self.connected = False

    def _on_track(
        self,
        track: rtc.Track,
        _publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        if not isinstance(track, rtc.RemoteAudioTrack):
            return
        if participant.identity != f"caller-{self.call_id}":
            return
        self._spawn(self._listen(track))

    def _spawn(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task: asyncio.Task[None] = asyncio.create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _listen(self, track: rtc.Track) -> None:
        segmenter = TurnSegmenter()
        try:
            async for frame in self.transport.microphone_frames(track):
                turn = segmenter.push(frame)
                if turn is not None:
                    self._spawn(self._process(pcm_wav(turn)))
            remaining = segmenter.finish()
            if remaining is not None:
                self._spawn(self._process(pcm_wav(remaining)))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._record_status(
                str(uuid4()),
                VoiceEventType.AGENT_TURN_FAILED,
                "Microphone stream stopped unexpectedly.",
                type(exc).__name__,
            )

    def _context(self) -> tuple[AppointmentContext, int, int]:
        call = self.controller.get(f"/v1/calls/{self.call_id}")
        workflows = call["workflows"]
        workflow = next((item for item in workflows if item["id"] == str(self.workflow_id)), None)
        if workflow is None or call["call"]["media_status"] == "ENDED":
            raise ValueError("Call is no longer active")
        resident = self.controller.get(f"/v1/residents/{call['call']['resident_id']}")
        current = workflow.get("desired_state_json") or {}
        tickets = resident["tickets"]
        if current:
            ticket = next((row for row in tickets if row["id"] == current["ticket_id"]), None)
        elif len(tickets) == 1:
            ticket = tickets[0]
        else:
            raise NeedDetails("Please choose which maintenance request to schedule.")
        if ticket is None:
            raise ValueError("The call has no eligible maintenance ticket")
        appointments = [
            row
            for row in resident["appointments"]
            if row.get("source_workflow_id") == str(self.workflow_id)
            and row.get("status") == "CONFIRMED"
        ]
        if len(appointments) > 1:
            raise ValueError("The workflow has more than one active appointment")
        appointment = appointments[0] if appointments else None
        current_start = datetime.fromisoformat(current["requested_start"]) if current else None
        current_end = datetime.fromisoformat(current["requested_end"]) if current else None
        context = AppointmentContext(
            UUID(ticket["id"]),
            UUID(appointment["id"]) if appointment else None,
            resident["resident"]["timezone"],
            current_start,
            current_end,
        )
        resource_version = int(appointment["version"] if appointment else ticket["version"])
        return context, int(workflow["current_revision"]), resource_version

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self.controller.post, path, body)

    async def _record_status(
        self,
        turn_key: str,
        kind: VoiceEventType,
        message: str,
        reason: str,
        provider_output: str | None = None,
    ) -> None:
        source_event_id = f"{turn_key}:{kind.value}"
        await self._post(
            f"/internal/phase4/calls/{self.call_id}/voice-events",
            {
                "event_id": str(
                    uuid5(NAMESPACE_URL, f"voice-event:{self.call_id}:{source_event_id}")
                ),
                "source_event_id": source_event_id,
                "event_type": kind.value,
                "occurred_at": datetime.now(UTC).isoformat(),
                "raw": {
                    "reason": reason,
                    "provider_output": provider_output,
                    "provider_output_hash": (
                        hashlib.sha256(provider_output.encode()).hexdigest()
                        if provider_output is not None
                        else None
                    ),
                },
                "normalized": {"message": message},
            },
        )

    async def _process(self, audio: bytes) -> None:
        async with self.turn_lock:
            turn_key = str(uuid4())
            trace = {"call_id": str(self.call_id), "workflow_id": str(self.workflow_id)}
            try:
                context, expected_revision, resource_version = await asyncio.to_thread(
                    self._context
                )
                llm = LocalLlamaIntent(os.environ["LOCAL_LLM_URL"], context)
                adapter = CascadedVoiceAdapter(self.stt, llm)
                try:
                    events = await adapter.turn(self.call_id, turn_key, audio)
                except NeedDetails as exc:
                    try:
                        transcript = await self.stt.transcribe(audio)
                    except NeedDetails:
                        transcript = None
                    if transcript:
                        final_source = f"{turn_key}:final"
                        await self._post(
                            f"/internal/phase4/calls/{self.call_id}/voice-events",
                            {
                                "event_id": str(
                                    uuid5(
                                        NAMESPACE_URL,
                                        f"voice-event:{self.call_id}:{final_source}",
                                    )
                                ),
                                "source_event_id": final_source,
                                "event_type": VoiceEventType.TRANSCRIPT_FINAL.value,
                                "occurred_at": datetime.now(UTC).isoformat(),
                                "raw": {
                                    "provider_text": transcript,
                                    "stt_model_id": self.stt.model_id,
                                },
                                "normalized": {
                                    "transcript": transcript,
                                    "transcript_hash": hashlib.sha256(
                                        transcript.encode()
                                    ).hexdigest(),
                                },
                            },
                        )
                    await self._record_status(
                        turn_key,
                        VoiceEventType.CLARIFICATION_REQUIRED,
                        str(exc),
                        "missing_schedule_detail",
                        llm.raw_output,
                    )
                    return
                for event in events:
                    await self._post(
                        f"/internal/phase4/calls/{self.call_id}/voice-events",
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
                    event
                    for event in events
                    if event.event_type is VoiceEventType.TOOL_PROPOSAL_RECEIVED
                )

                def command(step: str) -> str:
                    return str(uuid5(NAMESPACE_URL, f"live:{self.call_id}:{turn_key}:{step}"))

                accepted = await self._post(
                    f"/internal/phase4/workflows/{self.workflow_id}/accept-proposal",
                    {
                        "command_id": command("accept"),
                        "source_event_id": proposal.source_event_id,
                        "expected_revision": expected_revision,
                        "change_class": (
                            "INITIAL" if expected_revision == 0 else "PARAMETER_CORRECTION"
                        ),
                    },
                )
                revision = int(accepted["revision"])
                prepared = await self._post(
                    "/v1/operations/appointments",
                    {
                        "command_id": command("prepare"),
                        "workflow_id": str(self.workflow_id),
                        "expected_intent_revision": revision,
                        "expected_resource_version": resource_version,
                        "idempotency_key": f"live:{self.call_id}:{turn_key}",
                    },
                )
                operation_id = prepared["operation_id"]
                await self._post(
                    f"/v1/operations/{operation_id}/commit-local",
                    {"command_id": command("commit")},
                )
                receipt = await self._post(
                    "/internal/phase3/verifications",
                    {
                        "command_id": command("verify"),
                        "operation_id": operation_id,
                        "expected_intent_revision": revision,
                        "claim_type": (
                            "CURRENT_APPOINTMENT" if revision == 1 else "RESCHEDULED_APPOINTMENT"
                        ),
                    },
                )
                if receipt["result"] != "SATISFIED":
                    await self._record_status(
                        turn_key,
                        VoiceEventType.AGENT_TURN_FAILED,
                        "The appointment is still being checked.",
                        "verification_inconclusive",
                    )
                    return
                permit = await self._post(
                    "/internal/phase3/claims",
                    {
                        "command_id": command("claim"),
                        "receipt_id": receipt["receipt_id"],
                        "expected_intent_revision": revision,
                    },
                )
                await self._post(
                    f"/internal/phase3/permits/{permit['permit_id']}/queue",
                    {"command_id": command("queue"), "expected_intent_revision": revision},
                )
                scheduler = VoiceScheduler(self.controller, LocalEspeakTTS())
                await asyncio.to_thread(scheduler.schedule, UUID(permit["permit_id"]), revision)
            except asyncio.CancelledError:
                raise
            except (TimeoutError, URLError) as exc:
                logger.exception(
                    "live_agent_turn_unknown",
                    **trace,
                    trace_id=turn_key,
                    error_type=type(exc).__name__,
                )
                try:
                    await self._record_status(
                        turn_key,
                        VoiceEventType.AGENT_TURN_UNKNOWN,
                        "The outcome is unclear. Check the current appointment "
                        "before trying again.",
                        type(exc).__name__,
                    )
                except Exception:
                    logger.exception("live_agent_unknown_event_failed", **trace, trace_id=turn_key)
            except Exception as exc:
                logger.exception(
                    "live_agent_turn_failed",
                    **trace,
                    trace_id=turn_key,
                    error_type=type(exc).__name__,
                )
                try:
                    await self._record_status(
                        turn_key,
                        VoiceEventType.AGENT_TURN_FAILED,
                        "The request could not be completed. Please check the call trace.",
                        type(exc).__name__,
                    )
                except Exception:
                    logger.exception("live_agent_failure_event_failed", **trace)
