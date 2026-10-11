"""Provider-neutral normalized voice event envelope."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class VoiceEventType(StrEnum):
    SPEECH_STARTED = "SpeechStarted"
    TRANSCRIPT_DELTA = "TranscriptDelta"
    TRANSCRIPT_FINAL = "TranscriptFinal"
    POSSIBLE_END_OF_TURN = "PossibleEndOfTurn"
    CONFIRMED_END_OF_TURN = "ConfirmedEndOfTurn"
    SPEECH_RESUMED = "SpeechResumed"
    INTERRUPTION_CANDIDATE = "InterruptionCandidate"
    INTERRUPTION_ACCEPTED = "InterruptionAccepted"
    ASSISTANT_AUDIO_GENERATED = "AssistantAudioGenerated"
    ASSISTANT_AUDIO_QUEUED = "AssistantAudioQueued"
    ASSISTANT_AUDIO_PLAYED = "AssistantAudioPlayed"
    ASSISTANT_AUDIO_STOPPED = "AssistantAudioStopped"
    TOOL_PROPOSAL_RECEIVED = "ToolProposalReceived"
    CLARIFICATION_REQUIRED = "ClarificationRequired"
    AGENT_TURN_FAILED = "AgentTurnFailed"
    AGENT_TURN_UNKNOWN = "AgentTurnUnknown"


@dataclass(frozen=True)
class VoiceEvent:
    event_id: UUID
    call_id: UUID
    source_event_id: str
    event_type: VoiceEventType
    occurred_at: datetime
    normalized: dict[str, Any]
    raw: dict[str, Any]


@dataclass(frozen=True)
class TypedIntentProposal:
    desired_state: dict[str, str]
    transcript_hash: str
    model_id: str
    prompt_hash: str
    raw_output: str | None = None
