"""Offline integrity and independent-oracle verification for the P8 paired run."""

import argparse
import json
from pathlib import Path
from typing import Any

from research.analysis.metrics import metric_rows, paired_counts
from research.barriers.schedule import schedule
from research.oracle.p8_witness import grade_p8_paired
from research.replay.baseline_audio_evidence import verify_baseline_audio
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash


def verify_p8_paired(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    body = {key: value for key, value in bundle.items() if key != "bundle_hash"}
    if stable_hash(body) != bundle["bundle_hash"]:
        raise ValueError("P8 paired bundle hash differs")
    manifest = bundle["manifest"]
    if stable_hash(manifest) != bundle["manifest_hash"]:
        raise ValueError("P8 paired manifest hash differs")
    case = ScenarioCase.model_validate(manifest["scenario"])
    if case.correction_barrier is not Barrier.P8 or case.fixture_hash != manifest["fixture_hash"]:
        raise ValueError("P8 paired fixture differs")
    placement = schedule(case)
    frozen_schedule = manifest["fault_schedule"]
    if frozen_schedule["hash"] != placement.hash:
        raise ValueError("P8 fault placement differs")
    executions = bundle["executions"]
    expected_arms = (
        set(manifest["arms"])
        if manifest["runner_version"] == "phase6-p8-b3-p1-p2-paired-v2"
        else {"P1", "P2"}
    )
    if {item["arm"] for item in executions} != expected_arms or len(executions) != len(
        expected_arms
    ):
        raise ValueError("P8 paired arms differ")
    if bundle["execution_count"] != len(expected_arms) or bundle["independent_scenario_count"] != 1:
        raise ValueError("P8 paired execution or scenario count differs")
    rows: list[dict[str, Any]] = []
    for execution in executions:
        trace = execution["trace"]
        if execution["arm"] in ("B0", "B1", "B2"):
            verify_baseline_audio(execution, case)
            result = grade_p8_paired(trace, case)
            if result != execution["oracle_result"] or metric_rows(result) != execution["metrics"]:
                raise ValueError("Baseline P8 oracle or metrics differ")
            rows.append(
                {
                    "scenario_key": case.scenario_key,
                    "arm": execution["arm"],
                    "metrics": {
                        item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                    },
                }
            )
            continue
        if trace["research_arm"] != execution["arm"]:
            raise ValueError("P8 workflow arm differs")
        if trace["prerecorded_audio_sha256"] != case.audio_hash:
            raise ValueError("P8 correction audio hash differs")
        if trace["correction"]["audio_hash"] != case.audio_hash:
            raise ValueError("P8 arm did not receive the same correction audio")
        if execution["fault_placement_hash"] != placement.hash:
            raise ValueError("P8 arm received different fault placement")
        progress = [
            item["request"]
            for item in trace["client_playback_evidence"]
            if item["request"]["event_type"] == "PROGRESS"
        ]
        if len(progress) != 1 or (progress[0]["played_ms"], progress[0]["last_frame"]) != (
            frozen_schedule["played_ms"],
            frozen_schedule["last_frame"],
        ):
            raise ValueError("P8 client did not reach the frozen partial span")
        timing = execution["timing_evidence"]
        if len(timing["barriers"]) != 1 or len(timing["faults"]) != 1:
            raise ValueError("P8 barrier or fault count differs")
        barrier = timing["barriers"][0]
        fault = timing["faults"][0]
        if (
            barrier["barrier_name"] != "P8"
            or barrier["state"] != "RELEASED"
            or barrier["source_event_id"] != progress[0]["event_id"]
            or fault["actual_event_id"] != barrier["id"]
            or fault["fault_type"] != "PARTIAL_PLAYBACK"
            or fault["scheduled_target"]
            != {
                key: frozen_schedule[key] for key in ("barrier", "fault", "request_index", "target")
            }
        ):
            raise ValueError("P8 fault was not linked to the client progress barrier")
        if len(execution["playback_acks"]) != 2:
            raise ValueError("P8 client playback evidence is incomplete")
        if execution["playback_acks"][0]["event_id"] != progress[0]["event_id"]:
            raise ValueError("P8 stored playback differs from client progress")
        completed = [
            item["request"]
            for item in trace["client_playback_evidence"]
            if item["request"]["event_type"] == "COMPLETED"
        ]
        if (
            len(completed) != 1
            or execution["playback_acks"][1]["event_id"] != completed[0]["event_id"]
        ):
            raise ValueError("P8 stored playback differs from completed correction")
        repair_events = [
            event
            for event in trace["normalized_timeline"]
            if event["event_name"] == "RepairRequired"
        ]
        if execution["arm"] in ("B3", "P1") and (
            repair_events or trace["repair_played"] is not None
        ):
            raise ValueError("Baseline unexpectedly used the P2 repair mechanism")
        if execution["arm"] == "B3":
            for claim_key in ("first_claim", "corrected_claim"):
                if (
                    trace[claim_key]["permit"] is not None
                    or trace[claim_key]["receipt"] is not None
                ):
                    raise ValueError("B3 unexpectedly used a claim permit or verification receipt")
            if not all(
                trace[key]["research_unpermitted"] for key in ("stale_segment", "corrected_segment")
            ):
                raise ValueError("B3 audio was not marked as unpermitted research speech")
        if execution["arm"] == "P2" and (
            len(repair_events) != 1 or trace["repair_played"]["state"] != "REPAIR_PLAYED"
        ):
            raise ValueError("P2 repair mechanism was not completed")
        result = grade_p8_paired(trace, case)
        if result != execution["oracle_result"] or metric_rows(result) != execution["metrics"]:
            raise ValueError("P8 independent oracle or metric rows differ")
        rows.append(
            {
                "scenario_key": case.scenario_key,
                "arm": execution["arm"],
                "metrics": {
                    item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                },
            }
        )
    if paired_counts(rows, "played_span_repair_complete") != bundle["paired_summary"]:
        raise ValueError("P8 paired summary differs")
    return {
        "run_id": bundle["run_id"],
        "bundle_hash": bundle["bundle_hash"],
        "verified_executions": len(expected_arms),
        "independent_scenarios": 1,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a frozen P8 paired replay")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_p8_paired(args.path), indent=2))
