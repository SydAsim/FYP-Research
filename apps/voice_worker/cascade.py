"""Strict cascaded research path: STT, typed intent proposal, deterministic TTS."""

import hashlib
import io
import math
import struct
import wave
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from packages.protocol.voice import TypedIntentProposal, VoiceEvent, VoiceEventType


class STTAdapter(Protocol):
    async def transcribe(self, wav_audio: bytes) -> str: ...


class TypedIntentLLM(Protocol):
    async def propose(self, transcript: str) -> TypedIntentProposal: ...


class TTSAdapter(Protocol):
    model_id: str
    config_hash: str

    def synthesize(self, text: str) -> bytes: ...


class VoiceAdapter(Protocol):
    async def turn(
        self,
        call_id: UUID,
        turn_key: str,
        wav_audio: bytes,
        interrupted_segment_id: UUID | None = None,
    ) -> list[VoiceEvent]: ...


@dataclass(frozen=True)
class ScriptedSTT:
    audio_hash: str
    transcript: str

    async def transcribe(self, wav_audio: bytes) -> str:
        if hashlib.sha256(wav_audio).hexdigest() != self.audio_hash:
            raise ValueError("Prerecorded audio hash mismatch")
        return self.transcript


@dataclass(frozen=True)
class ScriptedTypedIntentLLM:
    transcript_hash: str
    desired_state: dict[str, str]
    model_id: str = "scripted-typed-intent-v1"
    prompt_hash: str = hashlib.sha256(b"phase4-scripted-intent-prompt-v1").hexdigest()

    async def propose(self, transcript: str) -> TypedIntentProposal:
        digest = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
        if digest != self.transcript_hash:
            raise ValueError("Transcript hash mismatch for typed intent")
        return TypedIntentProposal(
            dict(self.desired_state), digest, self.model_id, self.prompt_hash
        )


class CascadedVoiceAdapter:
    """Normalizes provider events; it cannot authorize a business or speech claim."""

    def __init__(self, stt: STTAdapter, llm: TypedIntentLLM) -> None:
        self.stt = stt
        self.llm = llm

    async def turn(
        self,
        call_id: UUID,
        turn_key: str,
        wav_audio: bytes,
        interrupted_segment_id: UUID | None = None,
    ) -> list[VoiceEvent]:
        audio_hash = hashlib.sha256(wav_audio).hexdigest()
        transcript = await self.stt.transcribe(wav_audio)
        transcript_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()
        proposal = await self.llm.propose(transcript)
        if proposal.transcript_hash != transcript_hash:
            raise ValueError("Intent proposal did not bind to finalized transcript")
        events: list[VoiceEvent] = []

        def emit(
            kind: VoiceEventType, suffix: str, normalized: dict[str, object], raw: dict[str, object]
        ) -> None:
            source_event_id = f"{turn_key}:{suffix}"
            events.append(
                VoiceEvent(
                    uuid5(NAMESPACE_URL, f"voice-event:{call_id}:{source_event_id}"),
                    call_id,
                    source_event_id,
                    kind,
                    datetime.now(UTC),
                    normalized,
                    raw,
                )
            )

        emit(
            VoiceEventType.SPEECH_STARTED,
            "speech",
            {"audio_hash": audio_hash},
            {
                "adapter": type(self.stt).__name__,
                "stt_model_id": getattr(self.stt, "model_id", "scripted-stt"),
                "audio_hash": audio_hash,
            },
        )
        if interrupted_segment_id is not None:
            emit(
                VoiceEventType.INTERRUPTION_CANDIDATE,
                "interrupt-candidate",
                {"segment_id": str(interrupted_segment_id)},
                {"source": "caller-speech-during-assistant-audio"},
            )
            emit(
                VoiceEventType.INTERRUPTION_ACCEPTED,
                "interrupt-accepted",
                {"segment_id": str(interrupted_segment_id)},
                {"decision": "caller-correction"},
            )
        words = transcript.split()
        for index in range(len(words)):
            emit(
                VoiceEventType.TRANSCRIPT_DELTA,
                f"delta:{index}",
                {"text": " ".join(words[: index + 1]), "version": index + 1},
                {"provider_delta": words[index]},
            )
        emit(
            VoiceEventType.POSSIBLE_END_OF_TURN,
            "possible-end",
            {},
            {
                "reason": (
                    "prerecorded_audio_end"
                    if isinstance(self.stt, ScriptedSTT)
                    else "live_energy_endpoint"
                )
            },
        )
        emit(
            VoiceEventType.CONFIRMED_END_OF_TURN,
            "confirmed-end",
            {},
            {
                "reason": (
                    "scripted_endpoint"
                    if isinstance(self.stt, ScriptedSTT)
                    else "live_energy_endpoint"
                )
            },
        )
        final_source = f"{turn_key}:final"
        utterance_id = uuid5(NAMESPACE_URL, f"voice-utterance:{call_id}:{final_source}")
        emit(
            VoiceEventType.TRANSCRIPT_FINAL,
            "final",
            {"transcript": transcript, "transcript_hash": transcript_hash},
            {"provider_text": transcript, "audio_hash": audio_hash},
        )
        emit(
            VoiceEventType.TOOL_PROPOSAL_RECEIVED,
            "proposal",
            {
                "desired_state": proposal.desired_state,
                "candidate_source": {
                    "utterance_id": str(utterance_id),
                    "model": proposal.model_id,
                    "prompt_hash": proposal.prompt_hash,
                    "transcript_version": 1,
                },
            },
            {
                "model_id": proposal.model_id,
                "prompt_hash": proposal.prompt_hash,
                "transcript_hash": transcript_hash,
                "provider_output": proposal.raw_output,
                "provider_output_hash": (
                    hashlib.sha256(proposal.raw_output.encode("utf-8")).hexdigest()
                    if proposal.raw_output is not None
                    else None
                ),
            },
        )
        return events


class DeterministicToneTTS:
    """Synthetic test adapter; production TTS implements the same text-in/WAV-out port."""

    model_id = "deterministic-tone-tts-v1"
    config_hash = hashlib.sha256(b"16kHz-mono-pcm16-tone-v1").hexdigest()

    def synthesize(self, text: str) -> bytes:
        words = text.split()
        if not words:
            raise ValueError("TTS text cannot be empty")
        sample_rate = 16000
        samples = min(30 * sample_rate, max(1, len(words)) * 180 * sample_rate // 1000)
        pitch = 320 + int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:2], 16)
        output = io.BytesIO()
        with wave.open(output, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(sample_rate)
            frame = bytearray()
            for index in range(samples):
                value = int(1500 * math.sin(2 * math.pi * pitch * index / sample_rate))
                frame.extend(struct.pack("<h", value))
            writer.writeframes(bytes(frame))
        return output.getvalue()
