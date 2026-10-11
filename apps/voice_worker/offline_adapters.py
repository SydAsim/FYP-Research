"""No-key cascaded adapters. Model output is a proposal, never an authority."""

import asyncio
import hashlib
import importlib
import io
import json
import re
import struct
import subprocess
import wave
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from apps.api_controller.phase1_models import DesiredAppointment
from packages.protocol.voice import TypedIntentProposal


class NeedDetails(ValueError):
    """The caller has not supplied enough grounded scheduling information."""


@dataclass(frozen=True)
class AppointmentContext:
    ticket_id: UUID
    appointment_id: UUID | None
    timezone: str
    current_start: datetime | None
    current_end: datetime | None


class LocalVoskSTT:
    model_id = "vosk-model-small-en-us-0.15"

    def __init__(self, model_path: Path) -> None:
        if not (model_path / "am" / "final.mdl").is_file():
            raise FileNotFoundError(f"Vosk model is missing at {model_path}")
        vosk = importlib.import_module("vosk")
        vosk.SetLogLevel(-1)
        self._vosk: Any = vosk
        self._model: Any = vosk.Model(str(model_path))

    def _transcribe(self, wav_audio: bytes) -> str:
        with wave.open(io.BytesIO(wav_audio), "rb") as reader:
            if (reader.getframerate(), reader.getnchannels(), reader.getsampwidth()) != (
                16000,
                1,
                2,
            ):
                raise ValueError("Caller audio must be mono PCM16 WAV at 16 kHz")
            recognizer = self._vosk.KaldiRecognizer(self._model, 16000)
            while chunk := reader.readframes(4000):
                recognizer.AcceptWaveform(chunk)
            result: dict[str, object] = json.loads(recognizer.FinalResult())
        transcript = result.get("text")
        if not isinstance(transcript, str) or not transcript.strip():
            raise NeedDetails("I could not hear a clear request. Please try again.")
        return transcript.strip()

    async def transcribe(self, wav_audio: bytes) -> str:
        return await asyncio.to_thread(self._transcribe, wav_audio)


class ExtractedStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(pattern="^(READY|NEED_DETAILS)$")
    requested_start: str


MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "january february march april may june july august september october november december"
        ).split(),
        1,
    )
}
NUMBERS = {
    word: value
    for value, word in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve "
        "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty "
        "twenty-one twenty-two twenty-three twenty-four twenty-five twenty-six "
        "twenty-seven twenty-eight twenty-nine thirty thirty-one".split()
    )
}
ORDINALS = {
    word: index
    for index, word in enumerate(
        "first second third fourth fifth sixth seventh eighth ninth tenth eleventh "
        "twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth "
        "nineteenth twentieth twenty-first twenty-second twenty-third twenty-fourth "
        "twenty-fifth twenty-sixth twenty-seventh twenty-eighth twenty-ninth "
        "thirtieth thirty-first".split(),
        1,
    )
}


def _spoken_year(words: list[str]) -> int | None:
    if words and re.fullmatch(r"20\d\d", words[0]):
        return int(words[0])
    if words[:2] == ["two", "thousand"]:
        tail = words[2:]
        if tail and tail[0] == "and":
            tail = tail[1:]
        if tail and tail[0] == "twenty":
            return 2020 + NUMBERS.get(tail[1], 0) if len(tail) > 1 else 2020
        return 2000 + NUMBERS.get(tail[0], 0) if tail else 2000
    if words[:2] == ["twenty", "twenty"]:
        return 2020 + NUMBERS.get(words[2], 0) if len(words) > 2 else 2020
    return None


def _grounded_start(transcript: str, context: AppointmentContext) -> datetime:
    """Independent lexical guard for dates and times before model output is accepted."""
    lowered = transcript.casefold()
    words = re.findall(r"\d{4}-\d{2}-\d{2}|\d+(?::\d+)?(?:st|nd|rd|th)?|[a-z]+", lowered)
    zone = ZoneInfo(context.timezone)
    day: date | None = None
    for token in words:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
            day = date.fromisoformat(token)
            break
    if day is None and "tomorrow" in words:
        day = datetime.now(zone).date() + timedelta(days=1)
    if day is None and "today" in words:
        day = datetime.now(zone).date()
    if day is None:
        for index, token in enumerate(words):
            if token not in MONTHS or index + 1 >= len(words):
                continue
            day_word = words[index + 1]
            if day_word in ("twenty", "thirty") and index + 2 < len(words):
                day_word = f"{day_word}-{words[index + 2]}"
                year_words = words[index + 3 :]
            else:
                year_words = words[index + 2 :]
            day_number = ORDINALS.get(day_word)
            numeric_day = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", day_word)
            if day_number is None and numeric_day:
                day_number = int(numeric_day.group(1))
            year = _spoken_year(year_words)
            if day_number is not None and year is not None:
                try:
                    day = date(year, MONTHS[token], day_number)
                except ValueError as exc:
                    raise NeedDetails("Please say a valid appointment date.") from exc
            break
    if day is None and context.current_start is not None:
        day = context.current_start.astimezone(zone).date()
    if day is None:
        raise NeedDetails("Please include the appointment date and year.")

    period = None
    has_spelled_pm = any(words[index : index + 2] == ["p", "m"] for index in range(len(words)))
    has_spelled_am = any(words[index : index + 2] == ["a", "m"] for index in range(len(words)))
    if "afternoon" in words or "evening" in words or "pm" in words or has_spelled_pm:
        period = "pm"
    elif "morning" in words or "am" in words or has_spelled_am:
        period = "am"
    if period is None:
        raise NeedDetails("Please say AM or PM for the appointment time.")
    hour: int | None = None
    minute = 0
    for index, token in enumerate(words):
        if token in MONTHS or token in ("twenty", "thirty"):
            continue
        candidate = NUMBERS.get(token)
        if candidate is None and re.fullmatch(r"\d{1,2}(?::\d{2})?", token):
            parts = token.split(":")
            candidate = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        if candidate is None or not 1 <= candidate <= 12:
            continue
        following = words[index + 1 : index + 5]
        has_period = any(
            part in ("pm", "am", "afternoon", "evening", "morning", "clock") for part in following
        )
        has_spelled_period = following[:2] in (["p", "m"], ["a", "m"])
        if has_period or has_spelled_period:
            hour = candidate
    if hour is None or minute > 59:
        raise NeedDetails("Please repeat the appointment time with AM or PM.")
    if period == "pm" and hour != 12:
        hour += 12
    if period == "am" and hour == 12:
        hour = 0
    grounded = datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
    if grounded <= datetime.now(zone):
        raise NeedDetails("Please choose a future appointment date and time.")
    return grounded


class LocalLlamaIntent:
    """Ask a local LLM for time only; bind ticket and appointment in code."""

    model_id = "qwen2.5-0.5b-instruct-q4_k_m"
    prompt_version = "phase5-local-intent-v2"

    def __init__(self, endpoint: str, context: AppointmentContext) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.context = context
        self.raw_output: str | None = None

    def _complete(self, transcript: str, grounded: datetime) -> tuple[str, str]:
        spoken_for_model = transcript.replace("'", " ")
        prompt = (
            f"{self.prompt_version}. Caller transcript: {spoken_for_model!r}. "
            f"The verified appointment start derived from those words is {grounded.isoformat()}. "
            "Return JSON with status READY and requested_start copied exactly from the "
            "verified appointment start. Do not claim an action completed."
        )
        schema = ExtractedStart.model_json_schema()
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": "Copy the verified ISO datetime into JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object", "schema": schema},
            "temperature": 0,
            "max_tokens": 120,
            "stream": False,
        }
        request = Request(
            f"{self.endpoint}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=90) as response:
            body: dict[str, Any] = json.load(response)
        raw = body["choices"][0]["message"]["content"]
        if not isinstance(raw, str):
            raise ValueError("Local intent model returned no text")
        return prompt, raw

    async def propose(self, transcript: str) -> TypedIntentProposal:
        if re.search(r"\b(cancel|delete|remove)\b", transcript.casefold()):
            raise NeedDetails("Please use the scheduling screen for cancellations.")
        grounded = _grounded_start(transcript, self.context)
        prompt, raw = await asyncio.to_thread(self._complete, transcript, grounded)
        self.raw_output = raw
        extracted = ExtractedStart.model_validate_json(raw)
        if extracted.status != "READY" or not extracted.requested_start:
            raise NeedDetails("Please say the appointment date and time.")
        try:
            start = datetime.fromisoformat(extracted.requested_start)
        except ValueError as exc:
            raise NeedDetails("Please say the date and time again.") from exc
        zone = ZoneInfo(self.context.timezone)
        if start.tzinfo is None:
            start = start.replace(tzinfo=zone)
        start = start.astimezone(zone)
        if start != grounded:
            raise NeedDetails(
                "Please repeat the date and time; the local model disagreed "
                "with the caller's words."
            )
        duration = (
            self.context.current_end - self.context.current_start
            if self.context.current_start and self.context.current_end
            else timedelta(hours=1)
        )
        desired = DesiredAppointment(
            ticket_id=self.context.ticket_id,
            appointment_id=self.context.appointment_id,
            requested_start=start,
            requested_end=start + duration,
            timezone=self.context.timezone,
        )
        return TypedIntentProposal(
            desired.model_dump(mode="json"),
            hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
            self.model_id,
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            raw,
        )


class LocalEspeakTTS:
    """Small offline speech renderer; output matches the verified 16 kHz carrier."""

    model_id = "espeak-ng-en-us"
    config_hash = hashlib.sha256(b"espeak-ng-en-us-155wpm-linear16k-v1").hexdigest()

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise ValueError("TTS text cannot be empty")
        generated = subprocess.run(
            ["espeak-ng", "--stdout", "--stdin", "-v", "en-us", "-s", "155"],
            input=text.encode("utf-8"),
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
        with wave.open(io.BytesIO(generated), "rb") as reader:
            if reader.getnchannels() != 1 or reader.getsampwidth() != 2:
                raise ValueError("eSpeak generated an unsupported audio format")
            source_rate = reader.getframerate()
            source = reader.readframes(reader.getnframes())
        samples = struct.unpack(f"<{len(source) // 2}h", source)
        target_count = int(len(samples) * 16000 / source_rate)
        resampled = bytearray(target_count * 2)
        for index in range(target_count):
            source_index = min(len(samples) - 1, int(index * source_rate / 16000))
            struct.pack_into("<h", resampled, index * 2, samples[source_index])
        output = io.BytesIO()
        with wave.open(output, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(resampled)
        return output.getvalue()
