"""Verify isolated baseline audio against raw provider and client observations."""

from typing import Any

from research.barriers.schedule import schedule
from research.runner.baseline_audio import segment
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash


def verify_baseline_audio(execution: dict[str, Any], case: ScenarioCase) -> None:
    trace = execution["trace"]
    if (
        trace["research_arm"] != execution["arm"]
        or trace["boundary"] != case.correction_barrier.value
        or trace["prerecorded_audio_sha256"] != case.audio_hash
        or trace["correction"]["audio_hash"] != case.audio_hash
        or trace["repair_played"] is not None
        or trace["exposure_scope"] != "scripted_client_acknowledgements_not_physical_hearing"
    ):
        raise ValueError("Baseline audio scope, fixture, or arm differs")
    for key, final in (("first_claim", False), ("corrected_claim", True)):
        saved = trace[key]
        expected = segment(case, final=final)
        if saved["permit"] is not None or saved["receipt"] is not None:
            raise ValueError("Baseline audio used a proposed claim mechanism")
        if any(
            saved["scheduled"][key] != value
            for key, value in expected.items()
            if key != "segment_id"
        ):
            raise ValueError("Baseline generated audio differs from the shared TTS adapter")
    events = trace["baseline_events"]
    for ordinal, event in enumerate(events, 1):
        if event["ordinal"] != ordinal or event["content_hash"] != stable_hash(
            {
                "event_kind": event["event_kind"],
                "raw": event["raw_json"],
                "normalized": event["normalized_json"],
            }
        ):
            raise ValueError("Baseline audio raw event integrity differs")
    writes = [row["raw_json"] for row in events if row["event_kind"] == "REQUEST_SENT"]
    actions = [row["action"] for row in writes]
    expected_actions = (
        ["CREATE", "RESCHEDULE"] if execution["arm"] == "B2" else ["CREATE", "CANCEL", "CREATE"]
    )
    if actions != expected_actions or actions != [
        row["action"] for row in trace["simulator_truth_log"]
    ]:
        raise ValueError("Baseline audio writes differ from independent commits")
    if [row["operation_id"] for row in writes] != [
        str(row["operation_id"]) for row in trace["simulator_truth_log"]
    ]:
        raise ValueError("Baseline audio provider operations differ")
    raw_client = [row["raw_json"] for row in events if row["event_kind"] == "CLIENT_PLAYBACK"]
    if raw_client != [row["request"] for row in trace["client_playback_evidence"]]:
        raise ValueError("Baseline client playback differs from durable raw observations")
    placement = schedule(case)
    timing = execution["timing_evidence"]
    barriers = timing["barriers"]
    if len(barriers) != 1 or execution["fault_placement_hash"] != placement.hash:
        raise ValueError("Baseline audio named boundary differs")
    barrier = barriers[0]
    source = trace["first_claim"]["scheduled"]["segment_id"]
    if case.correction_barrier in (Barrier.P8, Barrier.P9):
        event_type = "PROGRESS" if case.correction_barrier is Barrier.P8 else "COMPLETED"
        source = next(row["event_id"] for row in raw_client if row["event_type"] == event_type)
    if (
        barrier["source_event_id"] != source
        or barrier["state"] != "RELEASED"
        or barrier["barrier_name"] != case.correction_barrier.value
    ):
        raise ValueError("Baseline audio barrier was not linked to its actual client event")
    if case.correction_barrier is Barrier.P8:
        faults = timing["faults"]
        if len(faults) != 1 or faults[0]["actual_event_id"] != barrier["id"]:
            raise ValueError("Baseline partial playback fault differs")
    elif timing["faults"] or execution["fault_occurrence_id"] is not None:
        raise ValueError("Baseline unexpected playout fault")
    ack_events = [
        row["event_id"] for row in raw_client if row["event_type"] in ("PROGRESS", "COMPLETED")
    ]
    if [row["event_id"] for row in execution["playback_acks"]] != ack_events:
        raise ValueError("Baseline stored playback acknowledgement differs")
