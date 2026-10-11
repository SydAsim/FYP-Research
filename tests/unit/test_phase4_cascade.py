"""The strict cascade proposes typed intent and synthesizes only controller text."""

import hashlib
from typing import Any
from uuid import uuid4

import pytest

from apps.voice_worker.cascade import (
    CascadedVoiceAdapter,
    DeterministicToneTTS,
    ScriptedSTT,
    ScriptedTypedIntentLLM,
)
from apps.voice_worker.scheduler import VoiceScheduler
from packages.protocol.voice import VoiceEventType


@pytest.mark.asyncio
async def test_provider_neutral_cascade_normalizes_turn_without_authorizing_outcome() -> None:
    audio = b"prerecorded-wave-fixture"
    transcript = "Actually make it four PM."
    desired = {
        "ticket_id": str(uuid4()),
        "requested_start": "2026-10-01T16:00:00+05:00",
        "requested_end": "2026-10-01T17:00:00+05:00",
        "timezone": "Asia/Karachi",
    }
    adapter = CascadedVoiceAdapter(
        ScriptedSTT(hashlib.sha256(audio).hexdigest(), transcript),
        ScriptedTypedIntentLLM(hashlib.sha256(transcript.encode()).hexdigest(), desired),
    )
    events = await adapter.turn(uuid4(), "p8", audio)
    assert events[0].event_type is VoiceEventType.SPEECH_STARTED
    assert any(item.event_type is VoiceEventType.TRANSCRIPT_FINAL for item in events)
    assert events[-1].event_type is VoiceEventType.TOOL_PROPOSAL_RECEIVED
    assert events[-1].normalized["desired_state"] == desired
    assert all(item.event_type is not VoiceEventType.ASSISTANT_AUDIO_PLAYED for item in events)


class ControllerRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, path: str) -> dict[str, Any]:
        assert "/synthesis-input" in path
        return {
            "text": "Verified appointment at 4 PM.",
            "text_hash": "a" * 64,
            "intent_revision": 2,
        }

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((path, body))
        if path.endswith("/audio-segments"):
            return {"segment_id": str(uuid4()), "audio_hash": body["audio_hash"]}
        if path.endswith("/release"):
            return {"state": "PUBLISHED", "audio_url": "/v1/audio-segments/test/audio"}
        return {"state": "QUEUED"}


def test_scheduler_uses_only_controller_text() -> None:
    controller = ControllerRecorder()
    result = VoiceScheduler(controller, DeterministicToneTTS()).schedule(uuid4(), 2)
    assert result["state"] == "PUBLISHED"
    assert [path.rsplit("/", 1)[-1] for path, _ in controller.calls] == [
        "audio-segments",
        "queue",
        "release",
    ]
    assert controller.calls[0][1]["text_hash"] == "a" * 64
