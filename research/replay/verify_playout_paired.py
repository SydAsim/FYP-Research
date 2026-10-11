"""Offline integrity and independent grading for P6/P7/P9 paired replays."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from research.analysis.metrics import metric_rows, paired_counts
from research.barriers.schedule import schedule
from research.oracle.playout_witness import grade_playout
from research.replay.baseline_audio_evidence import verify_baseline_audio
from research.runner.playout_paired import RUNNER_VERSION
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash


def verify_playout_paired(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"})
        != bundle["bundle_hash"]
    ):
        raise ValueError("Playout bundle hash differs")
    manifest = bundle["manifest"]
    if stable_hash(manifest) != bundle["manifest_hash"]:
        raise ValueError("Playout manifest hash differs")
    old_version = "phase6-p7-p9-playout-paired-v1"
    if manifest["runner_version"] not in (RUNNER_VERSION, old_version):
        raise ValueError("Playout runner version differs")
    case = ScenarioCase.model_validate(manifest["scenario"])
    boundary = case.correction_barrier
    if (
        boundary not in (Barrier.P6, Barrier.P7, Barrier.P9)
        or case.fixture_hash != manifest["fixture_hash"]
    ):
        raise ValueError("Playout scenario differs")
    placement = schedule(case)
    if manifest["fault_schedule"]["hash"] != placement.hash:
        raise ValueError("Playout fault placement differs")
    executions = bundle["executions"]
    if (
        len(executions) != bundle["execution_count"]
        or len(executions) != len(manifest["arms"])
        or {item["arm"] for item in executions} != set(manifest["arms"])
        or bundle["independent_scenario_count"] != 1
    ):
        raise ValueError("Playout arm or scenario count differs")
    rows: list[dict[str, Any]] = []
    for execution in executions:
        trace = execution["trace"]
        arm = execution["arm"]
        if arm in ("B0", "B1", "B2"):
            verify_baseline_audio(execution, case)
            result = grade_playout(trace, case)
            if result != execution["oracle_result"] or metric_rows(result) != execution["metrics"]:
                raise ValueError("Baseline playout oracle or metrics differ")
            rows.append(
                {
                    "scenario_key": case.scenario_key,
                    "arm": arm,
                    "metrics": {
                        item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                    },
                }
            )
            continue
        if trace["research_arm"] != arm or trace["boundary"] != boundary.value:
            raise ValueError("Playout workflow arm or boundary differs")
        if (
            trace["prerecorded_audio_sha256"] != case.audio_hash
            or trace["correction"]["audio_hash"] != case.audio_hash
            or execution["fault_placement_hash"] != placement.hash
        ):
            raise ValueError("Playout fixture or placement differs")
        if execution["fault_occurrence_id"] is not None or execution["timing_evidence"]["faults"]:
            raise ValueError("No fault is scheduled for this playout boundary")
        barrier_rows = execution["timing_evidence"]["barriers"]
        if len(barrier_rows) != 1:
            raise ValueError("Playout boundary was not reached exactly once")
        barrier_row = barrier_rows[0]
        stale_id = trace["first_claim"]["scheduled"]["segment_id"]
        initial_events = [
            item["request"]
            for item in trace["client_playback_evidence"]
            if item["request"]["segment_id"] == stale_id
        ]
        if boundary in (Barrier.P6, Barrier.P7):
            expected_source = stale_id
            if initial_events or trace["stale_segment"]["state"] != "CANCELLED":
                raise ValueError("Stale audio was not cancelled before playout")
            stage_time_field = "generated_at" if boundary is Barrier.P6 else "published_at"
            source_time = datetime.fromisoformat(trace["stale_segment"][stage_time_field])
            if boundary is Barrier.P6 and trace["stale_segment"]["published_at"] is not None:
                raise ValueError("P6 audio was published before correction")
        else:
            completions = [item for item in initial_events if item["event_type"] == "COMPLETED"]
            if len(completions) != 1 or trace["stale_segment"]["state"] != "COMPLETED":
                raise ValueError("P9 stale audio did not complete before correction")
            expected_source = completions[0]["event_id"]
            source_time = datetime.fromisoformat(completions[0]["client_time"])
        if (
            barrier_row["barrier_name"] != boundary.value
            or barrier_row["state"] != "RELEASED"
            or barrier_row["source_event_id"] != expected_source
            or execution["barrier_source_event_id"] != expected_source
        ):
            raise ValueError("Playout barrier was not tied to the exposure event")
        if not (
            source_time
            <= datetime.fromisoformat(barrier_row["reached_at"])
            <= datetime.fromisoformat(trace["correction_scripted_at"])
        ):
            raise ValueError("Playout barrier timing differs from the exposure event")
        expected_acks = 1 if boundary in (Barrier.P6, Barrier.P7) else 2
        if len(execution["playback_acks"]) != expected_acks:
            raise ValueError("Playout client acknowledgement count differs")
        completed_ids = {
            item["request"]["event_id"]
            for item in trace["client_playback_evidence"]
            if item["request"]["event_type"] == "COMPLETED"
        }
        if {item["event_id"] for item in execution["playback_acks"]} != completed_ids:
            raise ValueError("Stored playout acknowledgements differ from client completion")
        expected_permits = {
            (trace[key]["permit"] or {}).get("permit_id")
            for key in (
                ("corrected_claim",)
                if boundary in (Barrier.P6, Barrier.P7)
                else ("first_claim", "corrected_claim")
            )
        }
        if {item["permit_id"] for item in execution["playback_acks"]} != expected_permits:
            raise ValueError("Stored playout permit evidence differs from the arm")
        repair_events = [
            event
            for event in trace["normalized_timeline"]
            if event["event_name"] == "RepairRequired"
        ]
        if boundary is Barrier.P9 and arm == "P2":
            if len(repair_events) != 1 or trace["repair_played"]["state"] != "REPAIR_PLAYED":
                raise ValueError("P9 P2 played-span repair was not completed")
        elif repair_events or trace["repair_played"] is not None:
            raise ValueError("Playout baseline unexpectedly created repair")
        if arm == "B3":
            if any(trace[key]["permit"] is not None for key in ("first_claim", "corrected_claim")):
                raise ValueError("B3 unexpectedly used a permit")
            if not all(
                trace[key]["research_unpermitted"] for key in ("stale_segment", "corrected_segment")
            ):
                raise ValueError("B3 audio was not marked as research-only")
        elif any(trace[key]["permit"] is None for key in ("first_claim", "corrected_claim")):
            raise ValueError("Permit arm did not use permits")
        result = grade_playout(
            trace,
            case,
            oracle_version=(
                "phase6-p7-p9-client-truth-v1"
                if manifest["runner_version"] == old_version
                else "phase6-p6-p7-p9-client-truth-v2"
            ),
        )
        if result != execution["oracle_result"] or metric_rows(result) != execution["metrics"]:
            raise ValueError("Playout independent oracle or metrics differ")
        rows.append(
            {
                "scenario_key": case.scenario_key,
                "arm": arm,
                "metrics": {
                    item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                },
            }
        )
    if paired_counts(rows, "safe_resolution") != bundle["paired_summary"]:
        raise ValueError("Playout paired summary differs")
    return {
        "run_id": bundle["run_id"],
        "bundle_hash": bundle["bundle_hash"],
        "boundary": boundary.value,
        "verified_executions": len(executions),
        "independent_scenarios": 1,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a frozen P6, P7, or P9 paired replay")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_playout_paired(args.path), indent=2))
