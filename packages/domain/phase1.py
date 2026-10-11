"""Pure Phase 1 domain vocabulary and legal local-operation transitions."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ProcessingPhase(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    DISPATCH_RECORDED = "DISPATCH_RECORDED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    VERIFYING = "VERIFYING"
    RECONCILING = "RECONCILING"
    COMPENSATING = "COMPENSATING"
    TERMINAL = "TERMINAL"


class EffectKnowledge(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    COMPENSATED = "COMPENSATED"


class Applicability(StrEnum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    REUSABLE = "REUSABLE"
    INCOMPATIBLE = "INCOMPATIBLE"


class SpeechEligibility(StrEnum):
    BLOCKED = "BLOCKED"
    PROGRESS_ONLY = "PROGRESS_ONLY"
    CLAIM_PERMITTED = "CLAIM_PERMITTED"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"


class VerificationResult(StrEnum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


class AppointmentStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class Workflow:
    id: UUID
    call_id: UUID
    current_revision: int
    version: int


@dataclass(frozen=True)
class IntentRevision:
    workflow_id: UUID
    revision: int
    parent_revision: int | None
    source_utterance_id: UUID
    accepted_at: datetime


@dataclass(frozen=True)
class OperationDimensions:
    processing: ProcessingPhase
    effect: EffectKnowledge
    applicability: Applicability
    speech: SpeechEligibility


@dataclass(frozen=True)
class Ticket:
    id: UUID
    resident_id: UUID
    property_id: UUID
    version: int


@dataclass(frozen=True)
class Appointment:
    id: UUID
    ticket_id: UUID
    starts_at: datetime
    ends_at: datetime
    version: int
    status: AppointmentStatus


def local_commit_dimensions(current: OperationDimensions) -> OperationDimensions:
    if current != OperationDimensions(
        ProcessingPhase.READY,
        EffectKnowledge.NOT_ATTEMPTED,
        Applicability.CURRENT,
        SpeechEligibility.BLOCKED,
    ):
        raise ValueError("Local commit requires a current, unattempted READY operation")
    return OperationDimensions(
        ProcessingPhase.TERMINAL,
        EffectKnowledge.PRESENT,
        Applicability.CURRENT,
        SpeechEligibility.BLOCKED,
    )


def supersede_dimensions(current: OperationDimensions) -> OperationDimensions:
    if current.effect is EffectKnowledge.NOT_ATTEMPTED:
        return OperationDimensions(
            ProcessingPhase.TERMINAL,
            EffectKnowledge.ABSENT,
            Applicability.SUPERSEDED,
            SpeechEligibility.BLOCKED,
        )
    if current.effect is EffectKnowledge.PRESENT:
        return OperationDimensions(
            ProcessingPhase.TERMINAL,
            EffectKnowledge.PRESENT,
            Applicability.SUPERSEDED,
            SpeechEligibility.BLOCKED,
        )
    raise ValueError("An ambiguous effect needs reconciliation before a terminal transition")
