"""Pure operation transition checks independent of PostgreSQL."""

import pytest

from packages.domain.phase1 import (
    Applicability,
    EffectKnowledge,
    OperationDimensions,
    ProcessingPhase,
    SpeechEligibility,
    local_commit_dimensions,
    supersede_dimensions,
)


def test_local_commit_remains_speech_blocked() -> None:
    ready = OperationDimensions(
        ProcessingPhase.READY,
        EffectKnowledge.NOT_ATTEMPTED,
        Applicability.CURRENT,
        SpeechEligibility.BLOCKED,
    )
    committed = local_commit_dimensions(ready)
    assert committed.effect is EffectKnowledge.PRESENT
    assert committed.speech is SpeechEligibility.BLOCKED
    assert supersede_dimensions(committed).effect is EffectKnowledge.PRESENT


def test_unknown_cannot_be_marked_terminal_absent() -> None:
    ambiguous = OperationDimensions(
        ProcessingPhase.READY,
        EffectKnowledge.UNKNOWN,
        Applicability.CURRENT,
        SpeechEligibility.BLOCKED,
    )
    with pytest.raises(ValueError, match="reconciliation"):
        supersede_dimensions(ambiguous)
