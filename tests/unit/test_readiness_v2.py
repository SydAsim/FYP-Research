"""Construct properties independent of arm identity or controller representation."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from packages.speech_policy.phase4 import decisive_exposure, incompatible_exposure, repair_capable
from research.oracle.readiness_v2 import RevisionTarget, grade_observable, repair_telemetry, support


def evidence() -> tuple[
    list[RevisionTarget],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    zero = datetime(2026, 10, 4, tzinfo=UTC)

    def at(seconds: float) -> str:
        return (zero + timedelta(seconds=seconds)).isoformat()

    targets = [
        RevisionTarget(
            revision=i,
            scripted_at=at(0 if i == 1 else 4.5),
            accepted_at=at(0 if i == 1 else 5),
            requested_start=f"2026-11-01T{hour}:00:00+05:00",
            requested_end=f"2026-11-01T{hour + 1}:00:00+05:00",
            timezone="Asia/Karachi",
            resource_key="maintenance",
        )
        for i, hour in ((1, 15), (2, 16))
    ]
    facts = [
        {
            "appointment_id": "a",
            "resource_key": "maintenance",
            "status": "CONFIRMED",
            "starts_at": t.requested_start.isoformat(),
            "ends_at": t.requested_end.isoformat(),
            "timezone": t.timezone,
            "version": i,
        }
        for i, t in enumerate(targets)
    ]
    commits = [
        {"sequence": i + 1, "committed_at": at(1 if i == 0 else 6), "after_facts": f}
        for i, f in enumerate(facts)
    ]
    observations = [
        {
            "source_type": "SIMULATOR_RESOURCE",
            "source_identifier": "maintenance",
            "available_at": at(1.5 if i == 0 else 6.5),
            "raw": {"status": 200, "body": {"authoritative": True, "appointments": [f]}},
        }
        for i, f in enumerate(facts)
    ]
    segments = []
    playback = []
    for i, _t in enumerate(targets):
        text = (
            f"Your maintenance appointment is confirmed for {3 + i}:00 PM "
            "on 2026-11-01 (Asia/Karachi)."
        )
        if i:
            text = "Correction: my earlier confirmation was outdated. " + text
        words = text.split()
        segment = {
            "id": str(i),
            "published_at": at(2 if i == 0 else 7),
            "segment_text": text,
            "duration_ms": 100 * len(words),
            "frame_count": 1600 * len(words),
            "word_timeline_json": [
                {"word": w, "end_ms": 100 * (n + 1)} for n, w in enumerate(words)
            ],
        }
        segments.append(segment)
        for kind, time in (("STARTED", 2.5 if i == 0 else 7.5), ("COMPLETED", 4 if i == 0 else 9)):
            playback.append(
                {
                    "request": {
                        "segment_id": str(i),
                        "event_type": kind,
                        "client_time": at(time),
                        "played_ms": 0 if kind == "STARTED" else segment["duration_ms"],
                        "last_frame": 0 if kind == "STARTED" else segment["frame_count"],
                        "last_word_index": 0 if kind == "STARTED" else len(words),
                    },
                    "status": 202,
                }
            )
    return targets, commits, segments, playback, observations


@pytest.mark.parametrize("label", ["B0", "B1", "B2", "B3", "P1", "P2", "OTHER"])
def test_label_and_internal_representation_do_not_change_outcomes(label: str) -> None:
    original = evidence()
    changed = deepcopy(original)
    for segment in changed[2]:
        segment.update(
            research_arm=label,
            claim_permit_id="arbitrary",
            repair_obligation_id="arbitrary",
            controller_receipt={"result": "VIOLATED"},
        )
    assert grade_observable(*changed) == grade_observable(*original)
    assert grade_observable(*changed)["explicit_retraction"] == "TRUE"
    assert repair_telemetry([]) != repair_telemetry([{"state": "REPAIR_PLAYED"}])


def test_correct_update_and_explicit_retraction_are_separate() -> None:
    inputs = evidence()
    segment = inputs[2][1]
    segment["segment_text"] = segment["segment_text"].removeprefix(
        "Correction: my earlier confirmation was outdated. "
    )
    result = grade_observable(*inputs)
    assert result["final_business_state_correct"]
    assert result["correct_final_update"] == "TRUE"
    assert result["explicit_retraction"] == "FALSE"


def test_true_claim_without_available_observation_is_unknown_support() -> None:
    targets, commits, segments, playback, _ = evidence()
    result = grade_observable(targets, commits, segments, playback, [])
    assert result["unknown_claim_support"]
    assert result["correct_final_update"] != "TRUE"


def test_missing_completion_is_unknown_and_cannot_complete_update() -> None:
    targets, commits, segments, playback, observations = evidence()
    playback.pop()
    result = grade_observable(targets, commits, segments, playback, observations)
    assert result["playback_evidence_unknown"]
    assert result["correct_final_update"] == result["explicit_retraction"] == "UNKNOWN"


def test_intro_control_does_not_expose_decisive_content_or_require_retraction() -> None:
    inputs = evidence()
    old = inputs[2][0]
    ack = inputs[3][1]["request"]
    ack.update(event_type="INTERRUPTED", last_word_index=2, played_ms=200, last_frame=3200)
    proxy = {**old, "last_word_index": 2, "last_played_ms": 200, "last_frame": 3200}
    assert decisive_exposure(proxy) is False
    result = grade_observable(*inputs)
    assert result["claims"][0]["decisive_exposure"] == "FALSE"
    assert result["explicit_retraction"] == "NOT_APPLICABLE"


def test_delayed_delivery_uses_exposure_time_and_accepted_anchor() -> None:
    inputs = evidence()
    inputs[3][1]["server_received_at"] = "2026-10-04T00:00:10+00:00"
    before = grade_observable(*inputs)
    assert before["incompatible_stale_exposure"] == "FALSE"
    inputs[3][1]["request"]["client_time"] = "2026-10-04T00:00:05.500000+00:00"
    after = grade_observable(*inputs)
    assert after["incompatible_stale_exposure"] == "TRUE"
    assert after["unsupported_exposed_claim"] == "FALSE"  # true/evidenced before commit 6s


def test_new_version_requires_new_applicable_observation() -> None:
    inputs = evidence()
    inputs[1].insert(
        1,
        {
            "sequence": 2,
            "committed_at": "2026-10-04T00:00:03+00:00",
            "after_facts": {**inputs[1][0]["after_facts"], "version": 9},
        },
    )
    inputs[1][-1]["sequence"] = 3
    result = grade_observable(*inputs)
    assert result["claims"][0]["truth_at_playback"] == "TRUE"
    assert result["claims"][0]["evidence_at_playback"] == "FALSE"


def test_confirmation_verb_alone_does_not_expose_an_incompatible_time() -> None:
    inputs = evidence()
    old = inputs[2][0]
    proxy = {**old, "last_word_index": 5, "last_played_ms": 500, "last_frame": 8000}
    assert decisive_exposure(proxy) is True
    assert incompatible_exposure(proxy, inputs[0][-1].model_dump(mode="json")) is False
    # New ordinary evidence confirms the booking exists; no old time was yet exposed.
    assert support(
        inputs[1], inputs[4], inputs[0][0].requested_start.astimezone(
            ZoneInfo("Asia/Karachi")
        ), datetime(2026, 10, 4, 0, 0, 8, tzinfo=UTC), "maintenance",
        text=old["segment_text"], through=5,
    ) == ("TRUE", "TRUE")
    proxy.update(last_word_index=8, last_played_ms=800, last_frame=12800)
    assert incompatible_exposure(proxy, inputs[0][-1].model_dump(mode="json")) is True


def test_missing_alignment_is_unknown_even_with_terminal_ack() -> None:
    inputs = evidence()
    inputs[2][0]["word_timeline_json"] = []
    result = grade_observable(*inputs)
    assert result["claims"][0]["decisive_exposure"] == "UNKNOWN"


def test_moved_claim_needs_observed_reschedule_not_just_current_booking() -> None:
    inputs = evidence()
    inputs[2][1]["segment_text"] = inputs[2][1]["segment_text"].replace(
        "is confirmed for", "has been moved to"
    )
    result = grade_observable(*inputs)
    assert result["claims"][1]["truth_at_publication"] == "FALSE"
    assert result["claims"][1]["evidence_at_publication"] == "UNKNOWN"


@pytest.mark.parametrize("arm", ["B0", "B1", "B2", "B3", "P1"])
def test_repair_is_only_product_or_p2_capability(arm: str) -> None:
    assert not repair_capable(arm)
    assert repair_capable("P2") and repair_capable(None)
