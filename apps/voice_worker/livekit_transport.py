"""LiveKit media carrier; PostgreSQL-backed controller gates every speech segment."""

import asyncio
import hashlib
import io
import json
import wave
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from livekit import rtc

from apps.voice_worker.scheduler import HttpControllerPort


class LiveKitTransport:
    """Carry audio and segment control packets without granting claim authority."""

    def __init__(self, controller: HttpControllerPort) -> None:
        self.controller = controller
        self.room = rtc.Room()
        self.source = rtc.AudioSource(16000, 1, queue_size_ms=20)
        self.track = rtc.LocalAudioTrack.create_audio_track("verified-assistant", self.source)
        self.connected = False

    async def connect(self, url: str, token: str) -> None:
        await self.room.connect(url, token)
        await self.room.local_participant.publish_track(self.track)
        self.connected = True

    async def close(self) -> None:
        self.source.clear_queue()
        if self.connected:
            await self.room.disconnect()
            self.connected = False

    async def _packet(self, kind: str, segment_id: UUID, **facts: object) -> None:
        packet = json.dumps(
            {"kind": kind, "segment_id": str(segment_id), **facts}, separators=(",", ":")
        )
        await self.room.local_participant.publish_data(
            packet, reliable=True, topic="commit-aware-audio"
        )

    async def publish_segment(self, segment_id: UUID, expected_revision: int) -> dict[str, Any]:
        if not self.connected:
            raise RuntimeError("LiveKit room is not connected")
        path = f"/v1/audio-segments/{segment_id}"
        detail = await asyncio.to_thread(self.controller.get, path)
        if detail.get("research_unpermitted"):
            raise ValueError("Research baseline audio cannot be transported to a live room")
        if detail["state"] != "STARTED" or detail["intent_revision"] != expected_revision:
            raise ValueError("Segment has not passed its current playback gate")
        audio = await asyncio.to_thread(
            self.controller.get_bytes, f"/v1/audio-segments/{segment_id}/audio"
        )
        if hashlib.sha256(audio).hexdigest() != detail["audio_hash"]:
            raise ValueError("Released audio hash differs from durable segment")
        with wave.open(io.BytesIO(audio), "rb") as reader:
            if (
                reader.getframerate(),
                reader.getnchannels(),
                reader.getsampwidth(),
            ) != (16000, 1, 2):
                raise ValueError("Released audio is not mono PCM16 at 16 kHz")
            await self._packet(
                "segment-start",
                segment_id,
                audio_hash=detail["audio_hash"],
                intent_revision=expected_revision,
            )
            sent_frames = 0
            while sent_frames < detail["frame_count"]:
                current = await asyncio.to_thread(self.controller.get, path)
                if current["state"] != "STARTED" or current["intent_revision"] != expected_revision:
                    self.source.clear_queue()
                    await self._packet("segment-stopped", segment_id, sent_frames=sent_frames)
                    return {"state": "STOPPED", "sent_frames": sent_frames}
                chunk = reader.readframes(min(320, detail["frame_count"] - sent_frames))
                if not chunk:
                    raise ValueError("Released WAV ended before recorded frame count")
                frames = len(chunk) // 2
                await self.source.capture_frame(rtc.AudioFrame(chunk, 16000, 1, frames))
                sent_frames += frames
        await self.source.wait_for_playout()
        await self._packet("segment-sent", segment_id, sent_frames=sent_frames)
        return {"state": "SENT", "sent_frames": sent_frames}

    async def microphone_frames(self, track: rtc.Track) -> AsyncIterator[bytes]:
        """Yield caller PCM frames for a provider-neutral STT adapter."""
        stream = rtc.AudioStream(track, sample_rate=16000, num_channels=1, frame_size_ms=20)
        async for event in stream:
            yield bytes(event.frame.data)
