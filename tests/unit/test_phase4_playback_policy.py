"""Pure acknowledgement and repair predicates."""

import pytest

from packages.speech_policy.phase4 import (
    Exposure,
    exposed_span,
    needs_repair,
    repair_text,
    validate_progress,
)


def test_progress_is_monotonic_and_bounded() -> None:
    validate_progress(Exposure(100, 1600, 1), Exposure(500, 8000, 3), 1000, 16000, 5)
    with pytest.raises(ValueError, match="backward"):
        validate_progress(Exposure(500, 8000, 3), Exposure(499, 8000, 3), 1000, 16000, 5)
    with pytest.raises(ValueError, match="exceeds"):
        validate_progress(Exposure(0, 0, 0), Exposure(1001, 16000, 5), 1000, 16000, 5)


def test_only_acknowledged_stale_decisive_span_needs_repair() -> None:
    segment = {
        "segment_class": "OUTCOME",
        "intent_revision": 1,
        "last_played_ms": 500,
        "last_frame": 8000,
        "last_word_index": 3,
        "word_timeline_json": [
            {"word": "Your", "end_ms": 100},
            {"word": "appointment", "end_ms": 200},
            {"word": "is", "end_ms": 300},
            {"word": "confirmed", "end_ms": 400},
        ],
        "content_hash": "text",
        "audio_hash": "audio",
    }
    assert not needs_repair(segment, 2)
    assert needs_repair({**segment, "last_word_index": 4}, 2)
    assert exposed_span(segment)["words"] == ["Your", "appointment", "is"]
    assert not needs_repair(
        {**segment, "last_played_ms": 0, "last_frame": 0, "last_word_index": 0}, 2
    )
    assert not needs_repair({**segment, "segment_class": "PROGRESS"}, 2)
    assert not needs_repair(segment, 1)


def test_repair_template_requires_corrected_claim() -> None:
    assert repair_text("The appointment is now 4 PM.").startswith("Correction:")
    with pytest.raises(ValueError, match="verified"):
        repair_text("  ")
