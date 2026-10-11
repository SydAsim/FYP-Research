"""Independent P6/P7/P9 witness from client playout and simulator truth."""

from datetime import datetime
from typing import Any

from research.oracle.grade import PlaybackAck, grade
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash

ORACLE_VERSION = "phase6-p6-p7-p9-client-truth-v2"


def _event(trace: dict[str, Any], segment_id: str, kind: str) -> dict[str, Any]:
    matches = [
        item
        for item in trace["client_playback_evidence"]
        if item["request"]["segment_id"] == segment_id and item["request"]["event_type"] == kind
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {kind} client event for {segment_id}")
    item = matches[0]
    if (
        item["response"]["event_id"] != item["request"]["event_id"]
        or item["response"]["segment_id"] != segment_id
    ):
        raise ValueError("Playback acknowledgement differs from the client request")
    return dict(item["request"])


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Playback time requires an offset")
    return parsed


def _claim_text(case: ScenarioCase, *, final: bool) -> str:
    start = case.final_start if final else case.initial_start
    time = f"{start.hour % 12 or 12}:{start.minute:02d} "
    time += "AM" if start.hour < 12 else "PM"
    lead = (
        "Your maintenance appointment has been moved to "
        if final
        else "Your maintenance appointment is confirmed for "
    )
    return f"{lead}{time} on {start.date().isoformat()} ({case.timezone})."


def grade_playout(
    trace: dict[str, Any], case: ScenarioCase, *, oracle_version: str = ORACLE_VERSION
) -> dict[str, Any]:
    if case.correction_barrier not in (Barrier.P6, Barrier.P7, Barrier.P9):
        raise ValueError("Playout witness requires P6, P7, or P9")
    if trace["boundary"] != case.correction_barrier.value:
        raise ValueError("Trace boundary differs from the frozen scenario")
    stale_id = trace["first_claim"]["scheduled"]["segment_id"]
    corrected_id = trace["corrected_claim"]["scheduled"]["segment_id"]
    correction_at = _time(trace["correction_scripted_at"])
    corrected_start = _event(trace, corrected_id, "STARTED")
    corrected_done = _event(trace, corrected_id, "COMPLETED")
    if (
        not correction_at
        <= _time(corrected_start["client_time"])
        <= _time(corrected_done["client_time"])
    ):
        raise ValueError("Corrected audio was not heard after the correction")
    if any(
        item["request"]["segment_id"] == stale_id for item in trace["client_playback_evidence"]
    ) and case.correction_barrier in (Barrier.P6, Barrier.P7):
        raise ValueError("Unpublished or unplayed stale audio has a client acknowledgement")
    first_text = trace["stale_segment"]["segment_text"]
    if (
        first_text != _claim_text(case, final=False)
        or stable_hash(first_text) != trace["first_claim"]["scheduled"]["text_hash"]
    ):
        raise ValueError("Initial audio differs from the frozen claim")
    acks: list[PlaybackAck] = []
    full_stale = False
    if case.correction_barrier is Barrier.P9:
        stale_start = _event(trace, stale_id, "STARTED")
        stale_done = _event(trace, stale_id, "COMPLETED")
        if (
            not _time(stale_start["client_time"])
            <= _time(stale_done["client_time"])
            <= correction_at
        ):
            raise ValueError("P9 stale audio did not complete before correction")
        stale = trace["first_claim"]["scheduled"]
        full_stale = (
            stale_done["played_ms"] == stale["duration_ms"]
            and stale_done["last_frame"] == stale["frame_count"]
            and stale_done["last_word_index"] == len(trace["stale_segment"]["word_timeline_json"])
        )
        acks.append(
            PlaybackAck(
                event_id=stale_done["event_id"],
                claim_type="CURRENT_APPOINTMENT",
                claim_start=case.initial_start,
                intent_revision=1,
                released_at=_time(stale_start["client_time"]),
                played_at=_time(stale_done["client_time"]),
                played_ms=stale_done["played_ms"],
            )
        )
    corrected = trace["corrected_claim"]["scheduled"]
    detail = trace["corrected_segment"]
    final_claim = _claim_text(case, final=True)
    repair_claim = "Correction: my earlier confirmation was outdated. " + final_claim
    spoken = detail["segment_text"]
    text_matches = (
        spoken == final_claim or (case.correction_barrier is Barrier.P9 and spoken == repair_claim)
    ) and stable_hash(spoken) == corrected["text_hash"] == detail["content_hash"]
    explicit_repair = spoken == repair_claim and text_matches
    full_corrected = (
        corrected_done["played_ms"] == corrected["duration_ms"]
        and corrected_done["last_frame"] == corrected["frame_count"]
        and corrected_done["last_word_index"] == len(detail["word_timeline_json"])
    )
    acks.append(
        PlaybackAck(
            event_id=corrected_done["event_id"],
            claim_type="RESCHEDULED_APPOINTMENT",
            claim_start=case.final_start if text_matches else case.initial_start,
            intent_revision=2,
            released_at=_time(corrected_start["client_time"]),
            played_at=_time(corrected_done["client_time"]),
            played_ms=corrected_done["played_ms"],
        )
    )
    truth = grade(case, trace["simulator_truth_log"], acks, correction_at)
    repair_complete = (
        case.correction_barrier is Barrier.P9
        and explicit_repair
        and full_stale
        and full_corrected
        and text_matches
        and truth["correction_success"]
        and not truth["unsupported_confirmation"]
    )
    result: dict[str, Any] = {
        "oracle_version": oracle_version,
        "correction_success": truth["correction_success"],
        "unsupported_confirmation": truth["unsupported_confirmation"],
        "duplicate_effect": truth["duplicate_effect"],
        "outcome_coverage": truth["outcome_coverage"] and full_corrected and text_matches,
        "safe_resolution": truth["safe_resolution"]
        and full_corrected
        and text_matches
        and (case.correction_barrier in (Barrier.P6, Barrier.P7) or repair_complete),
        "stale_audio_fully_acknowledged": full_stale,
        "corrected_audio_fully_acknowledged": full_corrected,
        "corrected_audio_states_final_intent": text_matches,
        "truth_result_hash": truth["result_hash"],
    }
    if case.correction_barrier is Barrier.P9:
        result["played_span_repair_complete"] = repair_complete
    result["result_hash"] = stable_hash(result)
    return result
