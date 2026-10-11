"""Independent P8 witness grade from client acknowledgements and simulator truth."""

from datetime import datetime
from typing import Any, cast

from research.oracle.grade import PlaybackAck, grade
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash

WITNESS_ORACLE_VERSION = "phase6-p8-client-truth-v1"
PAIRED_ORACLE_VERSION = "phase6-p8-paired-truth-v1"


def _event(trace: dict[str, Any], segment_id: str, kind: str) -> dict[str, Any]:
    matches = [
        item
        for item in trace["client_playback_evidence"]
        if item["request"]["segment_id"] == segment_id and item["request"]["event_type"] == kind
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {kind} client event for segment {segment_id}")
    item = matches[0]
    if (
        item["response"]["event_id"] != item["request"]["event_id"]
        or item["response"]["segment_id"] != segment_id
    ):
        raise ValueError("Playback response does not acknowledge its client request")
    return cast(dict[str, Any], item["request"])


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("P8 witness timestamps require an offset")
    return parsed


def grade_p8_witness(trace: dict[str, Any], case: ScenarioCase) -> dict[str, Any]:
    """Grade what the client acknowledged, without using controller repair state."""
    if case.correction_barrier is not Barrier.P8:
        raise ValueError("P8 witness requires the P8 fixture")
    stale_id = trace["first_claim"]["scheduled"]["segment_id"]
    corrected_id = trace["corrected_claim"]["scheduled"]["segment_id"]
    started = _event(trace, stale_id, "STARTED")
    progress = _event(trace, stale_id, "PROGRESS")
    interrupted = _event(trace, stale_id, "INTERRUPTED")
    corrected_started = _event(trace, corrected_id, "STARTED")
    completed = _event(trace, corrected_id, "COMPLETED")
    correction_at = _time(trace["correction_scripted_at"])
    if not (
        _time(started["client_time"])
        <= _time(progress["client_time"])
        <= _time(interrupted["client_time"])
        <= correction_at
        <= _time(corrected_started["client_time"])
        <= _time(completed["client_time"])
    ):
        raise ValueError("P8 playback and correction order is inconsistent")
    stale = trace["first_claim"]["scheduled"]
    corrected = trace["corrected_claim"]["scheduled"]
    partial = (
        0 < progress["played_ms"] < stale["duration_ms"]
        and 0 < progress["last_frame"] < stale["frame_count"]
        and interrupted["played_ms"] == progress["played_ms"]
        and interrupted["last_frame"] == progress["last_frame"]
        and interrupted["last_word_index"] == progress["last_word_index"]
    )
    full_correction = (
        completed["played_ms"] == corrected["duration_ms"]
        and completed["last_frame"] == corrected["frame_count"]
        and completed["last_word_index"] == len(trace["corrected_segment"]["word_timeline_json"])
    )
    expected_time = (
        f"{case.final_start.hour % 12 or 12}:{case.final_start.minute:02d} "
        f"{'AM' if case.final_start.hour < 12 else 'PM'}"
    )
    expected_day = case.final_start.date().isoformat()
    corrected_text = trace["corrected_segment"]["segment_text"]
    claim_text = (
        f"Your maintenance appointment has been moved to {expected_time} "
        f"on {expected_day} ({case.timezone})."
    )
    arm = trace.get("research_arm")
    expected_text = (
        "Correction: my earlier confirmation was outdated. " + claim_text
        if arm not in ("B0", "B1", "B2", "B3", "P1")
        else claim_text
    )
    spoken_final_intent = (
        corrected_text == expected_text
        and stable_hash(corrected_text)
        == corrected["text_hash"]
        == trace["corrected_segment"]["content_hash"]
    )
    acknowledgements = [
        PlaybackAck(
            event_id=progress["event_id"],
            claim_type="CURRENT_APPOINTMENT",
            claim_start=case.initial_start,
            intent_revision=1,
            released_at=_time(started["client_time"]),
            played_at=_time(progress["client_time"]),
            played_ms=progress["played_ms"],
        ),
        PlaybackAck(
            event_id=completed["event_id"],
            claim_type="RESCHEDULED_APPOINTMENT",
            claim_start=case.final_start if spoken_final_intent else case.initial_start,
            intent_revision=2,
            released_at=_time(corrected_started["client_time"]),
            played_at=_time(completed["client_time"]),
            played_ms=completed["played_ms"],
        ),
    ]
    truth_result = grade(case, trace["simulator_truth_log"], acknowledgements, correction_at)
    result = {
        "oracle_version": WITNESS_ORACLE_VERSION,
        "partial_stale_span_acknowledged": partial,
        "partial_played_ms": progress["played_ms"],
        "partial_last_frame": progress["last_frame"],
        "corrected_audio_fully_acknowledged": full_correction,
        "corrected_audio_states_final_intent": spoken_final_intent,
        "correction_success": truth_result["correction_success"],
        "unsupported_confirmation": truth_result["unsupported_confirmation"],
        "played_span_repair_complete": (
            arm not in ("B0", "B1", "B2", "B3", "P1")
            and partial
            and full_correction
            and spoken_final_intent
            and truth_result["correction_success"]
            and not truth_result["unsupported_confirmation"]
        ),
        "truth_result_hash": truth_result["result_hash"],
    }
    result["result_hash"] = stable_hash(result)
    return result


def grade_p8_paired(trace: dict[str, Any], case: ScenarioCase) -> dict[str, Any]:
    """Add the research endpoints while preserving the earlier witness format."""
    witness = grade_p8_witness(trace, case)
    operation_ids = [str(item["operation_id"]) for item in trace["simulator_truth_log"]]
    duplicate = len(operation_ids) != len(set(operation_ids))
    result = {
        **{key: value for key, value in witness.items() if key != "result_hash"},
        "oracle_version": PAIRED_ORACLE_VERSION,
        "duplicate_effect": duplicate,
        "outcome_coverage": (
            witness["correction_success"]
            and witness["corrected_audio_fully_acknowledged"]
            and witness["corrected_audio_states_final_intent"]
        ),
        "safe_resolution": (
            witness["correction_success"]
            and not witness["unsupported_confirmation"]
            and not duplicate
            and witness["played_span_repair_complete"]
        ),
    }
    result["result_hash"] = stable_hash(result)
    return result
