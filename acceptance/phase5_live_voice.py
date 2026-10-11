"""Exercise two real PCM speech turns through LiveKit and the local worker."""

import asyncio
import hashlib
import json
import os
import wave
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from uuid import uuid4
from zoneinfo import ZoneInfo

from livekit import rtc

ROOT = Path(__file__).resolve().parents[1]
API = os.environ.get("PHASE5_API_URL", "http://127.0.0.1:8000")


def request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"content-type": "application/json"}
    if path == "/v1/calls" and method == "POST":
        headers["Idempotency-Key"] = str(uuid4())
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    with urlopen(
        Request(API + path, data=encoded, headers=headers, method=method), timeout=20
    ) as response:
        payload: dict[str, Any] = json.load(response)
    return payload


async def wait_for(predicate: Any, label: str, seconds: int = 90) -> Any:
    deadline = asyncio.get_running_loop().time() + seconds
    while asyncio.get_running_loop().time() < deadline:
        result = predicate()
        if result:
            return result
        await asyncio.sleep(0.5)
    raise AssertionError(f"Timed out waiting for {label}")


async def speak(source: rtc.AudioSource, filename: str) -> str:
    path = ROOT / "tests" / "audio" / filename
    audio = path.read_bytes()
    with wave.open(str(path), "rb") as reader:
        assert (reader.getframerate(), reader.getnchannels(), reader.getsampwidth()) == (
            16000,
            1,
            2,
        )
        while frame := reader.readframes(320):
            if len(frame) < 640:
                frame += bytes(640 - len(frame))
            await source.capture_frame(rtc.AudioFrame(frame, 16000, 1, 320))
            await asyncio.sleep(0.02)
    for _ in range(50):
        await source.capture_frame(rtc.AudioFrame(bytes(640), 16000, 1, 320))
        await asyncio.sleep(0.02)
    return hashlib.sha256(audio).hexdigest()


async def main() -> None:
    fixture = request(
        "POST",
        "/internal/phase1/fixtures",
        {
            "command_id": str(uuid4()),
            "timezone": "Asia/Karachi",
            "first_transcript": "Book maintenance on October third twenty twenty six at three P M.",
            "second_transcript": "Actually change it to four o'clock in the afternoon.",
        },
    )
    call_id = fixture["call_id"]
    workflow_id = fixture["workflow_id"]
    resident_id = fixture["resident_id"]
    media = request("GET", f"/v1/calls/{call_id}/media-token")
    assert media["voice_agent_status"] == "READY", media

    room = rtc.Room()
    source = rtc.AudioSource(16000, 1, queue_size_ms=20)
    track = rtc.LocalAudioTrack.create_audio_track("acceptance-microphone", source)
    await room.connect(media["livekit_url"], media["livekit_token"])
    await room.local_participant.publish_track(track)
    try:
        first_audio_hash = await speak(source, "phase5-booking.wav")

        def first_booking() -> dict[str, Any] | None:
            call = request("GET", f"/v1/calls/{call_id}")
            if call["workflows"][0]["current_revision"] != 1:
                return None
            detail = request("GET", f"/v1/residents/{resident_id}")
            matches = [
                row
                for row in detail["appointments"]
                if row["source_workflow_id"] == workflow_id and row["status"] == "CONFIRMED"
            ]
            return matches[0] if matches else None

        first = await wait_for(first_booking, "first verified local booking")
        local_zone = ZoneInfo("Asia/Karachi")
        assert datetime.fromisoformat(first["starts_at"]).astimezone(local_zone).hour == 15
        await wait_for(
            lambda: len(request("GET", f"/v1/calls/{call_id}/timeline")["segments"]) >= 1,
            "first speech segment",
        )

        second_audio_hash = await speak(source, "phase5-correction.wav")

        def corrected_booking() -> dict[str, Any] | None:
            call = request("GET", f"/v1/calls/{call_id}")
            if call["workflows"][0]["current_revision"] != 2:
                return None
            detail = request("GET", f"/v1/residents/{resident_id}")
            matches = [
                row
                for row in detail["appointments"]
                if row["id"] == first["id"] and row["status"] == "CONFIRMED"
            ]
            return matches[0] if matches and matches[0]["version"] > first["version"] else None

        corrected = await wait_for(corrected_booking, "spoken correction")
        assert datetime.fromisoformat(corrected["starts_at"]).astimezone(local_zone).hour == 16
        timeline = await wait_for(
            lambda: (
                item
                if len((item := request("GET", f"/v1/calls/{call_id}/timeline"))["segments"]) >= 2
                and all(segment["published_at"] for segment in item["segments"])
                else None
            ),
            "published corrected speech segment",
        )
        assert all(row["tts_model_id"] == "espeak-ng-en-us" for row in timeline["segments"])
        assert not any(
            row["event_type"] in ("AgentTurnFailed", "AgentTurnUnknown")
            for row in timeline["voice_events"]
        )
        assert [row["result"] for row in timeline["receipts"]] == [
            "SATISFIED",
            "SATISFIED",
        ]
        assert len(timeline["utterances"]) >= 4
        proposals = [
            row for row in timeline["voice_events"] if row["event_type"] == "ToolProposalReceived"
        ]
        assert len(proposals) >= 2
        report = {
            "call_id": call_id,
            "workflow_id": workflow_id,
            "first_appointment_id": first["id"],
            "first_start": first["starts_at"],
            "corrected_start": corrected["starts_at"],
            "first_audio_sha256": first_audio_hash,
            "correction_audio_sha256": second_audio_hash,
            "segment_ids": [row["id"] for row in timeline["segments"]],
            "published_segments": [
                {
                    "id": row["id"],
                    "intent_revision": row["intent_revision"],
                    "claim_permit_id": row["claim_permit_id"],
                    "published_at": row["published_at"],
                    "text": row["segment_text"],
                }
                for row in timeline["segments"]
            ],
            "satisfied_receipts": [
                {
                    "id": row["id"],
                    "intent_revision": row["intent_revision"],
                    "claim_type": row["claim_type"],
                    "observed_resource_version": row["observed_resource_version"],
                }
                for row in timeline["receipts"]
            ],
            "utterance_ids": [row["id"] for row in timeline["utterances"]],
            "checked_at_utc": datetime.now(UTC).isoformat(),
        }
        destination = ROOT / "artifacts" / "phase-5-live-voice.json"
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        await room.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
