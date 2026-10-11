"""Generate versioned synthetic speech and record the actual free local cascade."""

import asyncio
import base64
import hashlib
import io
import json
import math
import os
import random
import struct
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.voice_worker.offline_adapters import (
    AppointmentContext,
    LocalEspeakTTS,
    LocalLlamaIntent,
    LocalVoskSTT,
    NeedDetails,
)
from research.scenario_dsl.models import stable_hash

CONDITIONS = (
    "LOCAL_CLEAN",
    "LOCAL_NOISE",
    "LOCAL_OVERLAP",
    "LOCAL_DISFLUENCY",
    "LOCAL_UNCERTAINTY",
    "LOCAL_RECORDED_CLEAN",
)
SOURCE = "Please book maintenance on November fifth twenty twenty six at three P M."


class AcousticEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["phase6-local-acoustic-v1"]
    condition: str
    seed: int
    source_text: str
    input_audio_base64: str
    input_audio_hash: str
    transcript: str
    transcript_hash: str
    status: Literal["READY", "CLARIFICATION"]
    proposal: dict[str, str] | None
    raw_model_output: str | None
    model_output_hash: str | None
    prompt_hash: str | None
    stt_model_id: str
    stt_model_hash: str
    intent_model_id: str
    intent_model_hash: str
    tts_model_id: str
    tts_config_hash: str
    safe_tts_audio_hash: str
    timings_ms: dict[str, float] = Field(min_length=1)
    clarification: str | None

    @model_validator(mode="after")
    def consistent(self) -> "AcousticEvidence":
        audio = base64.b64decode(self.input_audio_base64, validate=True)
        if (
            hashlib.sha256(audio).hexdigest() != self.input_audio_hash
            or hashlib.sha256(self.transcript.encode()).hexdigest() != self.transcript_hash
            or (
                self.raw_model_output is not None
                and hashlib.sha256(self.raw_model_output.encode()).hexdigest()
                != self.model_output_hash
            )
            or (self.status == "READY") != (self.proposal is not None)
            or self.condition not in CONDITIONS
        ):
            raise ValueError("Acoustic evidence is inconsistent")
        if self.status == "READY":
            if self.raw_model_output is None or self.proposal is None or not self.prompt_hash:
                raise ValueError("Ready acoustic evidence lacks its model output")
            raw = json.loads(self.raw_model_output)
            if raw.get("status") != "READY" or datetime.fromisoformat(
                raw["requested_start"]
            ) != datetime.fromisoformat(self.proposal["requested_start"]):
                raise ValueError("Normalized proposal differs from actual model output")
        return self


def _samples(audio: bytes) -> list[int]:
    with wave.open(io.BytesIO(audio), "rb") as reader:
        if (reader.getframerate(), reader.getnchannels(), reader.getsampwidth()) != (16000, 1, 2):
            raise ValueError("Acoustic fixtures require 16 kHz mono PCM16")
        data = reader.readframes(reader.getnframes())
    return list(struct.unpack(f"<{len(data) // 2}h", data))


def build_audio(condition: str, seed: int, tts: LocalEspeakTTS) -> bytes:
    if condition == "LOCAL_RECORDED_CLEAN":
        source = Path(__file__).parents[1] / "fixtures" / "audio" / "clean_booking.wav"
        with wave.open(str(source), "rb") as reader:
            if reader.getnchannels() != 1 or reader.getsampwidth() != 2:
                raise ValueError("Recorded speech must be mono PCM16")
            rate = reader.getframerate()
            frames = reader.readframes(reader.getnframes())
        original = list(struct.unpack(f"<{len(frames) // 2}h", frames))
        samples = []
        for index in range(int(len(original) * 16000 / rate)):
            position = index * rate / 16000
            left = int(position)
            right = min(left + 1, len(original) - 1)
            samples.append(
                round(original[left] + (original[right] - original[left]) * (position - left))
            )
        output = io.BytesIO()
        with wave.open(output, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        return output.getvalue()
    text = (
        SOURCE
        if condition != "LOCAL_DISFLUENCY"
        else (
            "Um, please book maintenance, uh, on November fifth twenty twenty six, "
            "at, um, three P M."
        )
    )
    samples = _samples(tts.synthesize(text))
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    rng = random.Random(seed)
    if condition in ("LOCAL_NOISE", "LOCAL_UNCERTAINTY"):
        deviation = rms * (0.1 if condition == "LOCAL_NOISE" else 3)
        samples = [
            max(-32768, min(32767, round(value + rng.gauss(0, deviation)))) for value in samples
        ]
    if condition == "LOCAL_OVERLAP":
        other = _samples(tts.synthesize("Hello, can you hear me? I need help."))
        offset = 4800
        for index, value in enumerate(other):
            if index + offset < len(samples):
                samples[index + offset] = max(
                    -32768, min(32767, round(samples[index + offset] + value * 0.3))
                )
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return output.getvalue()


async def capture(
    condition: str, seed: int, stt: LocalVoskSTT, model_hashes: dict[str, str]
) -> dict[str, Any]:
    tts = LocalEspeakTTS()
    audio = build_audio(condition, seed, tts)
    transcript = ""
    proposal = None
    clarification = None
    context = AppointmentContext(UUID(int=1), None, "Asia/Karachi", None, None)
    intent = LocalLlamaIntent(os.environ["LOCAL_LLM_URL"], context)
    timings: dict[str, float] = {}
    started = time.perf_counter()
    try:
        transcript = await stt.transcribe(audio)
        timings["stt"] = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        proposal = await intent.propose(transcript)
    except NeedDetails as exc:
        clarification = str(exc)
    timings["intent_or_clarification"] = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    # This measurement emits only non-decisive progress/clarification text.
    safe_audio = tts.synthesize(
        clarification or "I am checking the appointment. It is not confirmed yet."
    )
    timings["safe_tts"] = (time.perf_counter() - started) * 1000
    return AcousticEvidence(
        version="phase6-local-acoustic-v1",
        condition=condition,
        seed=seed,
        source_text=SOURCE,
        input_audio_base64=base64.b64encode(audio).decode(),
        input_audio_hash=hashlib.sha256(audio).hexdigest(),
        transcript=transcript,
        transcript_hash=hashlib.sha256(transcript.encode()).hexdigest(),
        status="READY" if proposal else "CLARIFICATION",
        proposal={
            key: value
            for key, value in proposal.desired_state.items()
            if key not in ("ticket_id", "appointment_id")
        }
        if proposal
        else None,
        raw_model_output=intent.raw_output,
        model_output_hash=hashlib.sha256(intent.raw_output.encode()).hexdigest()
        if intent.raw_output
        else None,
        prompt_hash=proposal.prompt_hash if proposal else None,
        stt_model_id=stt.model_id,
        stt_model_hash=model_hashes["stt"],
        intent_model_id=intent.model_id,
        intent_model_hash=model_hashes["intent"],
        tts_model_id=tts.model_id,
        tts_config_hash=tts.config_hash,
        safe_tts_audio_hash=hashlib.sha256(safe_audio).hexdigest(),
        timings_ms=timings,
        clarification=clarification,
    ).model_dump(mode="json")


async def main() -> None:
    request = json.load(sys.stdin)
    model_path = Path(os.environ["VOSK_MODEL_PATH"])
    stt = LocalVoskSTT(model_path)
    hashes = {
        "stt": stable_hash(
            {
                str(path.relative_to(model_path)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in model_path.rglob("*")
                if path.is_file()
            }
        ),
        "intent": hashlib.sha256(
            Path("/models/qwen2.5-0.5b-instruct-q4_k_m.gguf").read_bytes()
        ).hexdigest(),
    }
    evidence = [
        await capture(condition, request["seed"] + index, stt, hashes)
        for index, condition in enumerate(request["conditions"])
    ]
    print(json.dumps(evidence))


if __name__ == "__main__":
    asyncio.run(main())
