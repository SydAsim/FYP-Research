"""Live P8 B3/P1/P2 repair ablation with an explicit client-progress barrier."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID, uuid4

from research.analysis.metrics import metric_rows, paired_counts
from research.arms import PROFILES, Arm
from research.barriers.control import NamedBarrierController
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck
from research.oracle.p8_witness import grade_p8_paired
from research.replay.phase4_p8 import run as run_phase4_p8
from research.replay.phase6_p8_witness import witness_case
from research.run_store import (
    MIGRATION_VERSION,
    bind_execution,
    create_case,
    create_execution,
    create_run,
    fail_execution,
    finish_run,
    playback_for,
    record_fault,
    record_playback,
    record_result,
    timing_evidence,
)
from research.runner.paired import _container_digests, _source_identity
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash

ARMS = (Arm.B3, Arm.P1, Arm.P2)
RUNNER_VERSION = "phase6-p8-b3-p1-p2-paired-v2"


def _client_event(trace: dict[str, Any], segment_id: str, kind: str) -> dict[str, Any]:
    events = [
        item["request"]
        for item in trace["client_playback_evidence"]
        if item["request"]["segment_id"] == segment_id and item["request"]["event_type"] == kind
    ]
    if len(events) != 1:
        raise AssertionError(f"Expected one {kind} event for {segment_id}")
    return cast(dict[str, Any], events[0])


def _record_client_acks(
    execution_id: UUID, trace: dict[str, Any], case: ScenarioCase
) -> list[PlaybackAck]:
    stale_id = trace["first_claim"]["scheduled"]["segment_id"]
    corrected_id = trace["corrected_claim"]["scheduled"]["segment_id"]
    stale_started = _client_event(trace, stale_id, "STARTED")
    stale_progress = _client_event(trace, stale_id, "PROGRESS")
    corrected_started = _client_event(trace, corrected_id, "STARTED")
    corrected_completed = _client_event(trace, corrected_id, "COMPLETED")
    acks = [
        PlaybackAck(
            event_id=stale_progress["event_id"],
            claim_type="CURRENT_APPOINTMENT",
            claim_start=case.initial_start,
            intent_revision=1,
            released_at=datetime.fromisoformat(stale_started["client_time"]),
            played_at=datetime.fromisoformat(stale_progress["client_time"]),
            played_ms=stale_progress["played_ms"],
            permit_id=(trace["first_claim"]["permit"] or {}).get("permit_id"),
        ),
        PlaybackAck(
            event_id=corrected_completed["event_id"],
            claim_type="RESCHEDULED_APPOINTMENT",
            claim_start=case.final_start,
            intent_revision=2,
            released_at=datetime.fromisoformat(corrected_started["client_time"]),
            played_at=datetime.fromisoformat(corrected_completed["client_time"]),
            played_ms=corrected_completed["played_ms"],
            permit_id=(trace["corrected_claim"]["permit"] or {}).get("permit_id"),
        ),
    ]
    for ack in acks:
        record_playback(execution_id, ack, case.audio_hash)
    return playback_for(execution_id)


def _execute(
    run_id: UUID,
    case_id: UUID,
    case: ScenarioCase,
    arm: Arm,
) -> dict[str, Any]:
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
    barrier_id: UUID | None = None
    try:

        def at_progress(event: dict[str, Any]) -> None:
            nonlocal barrier_id
            if event["played_ms"] != 500 or event["last_frame"] != 8000:
                raise AssertionError("P8 did not reach the frozen partial-playback span")
            controller = NamedBarrierController(execution_id, {Barrier.P8})
            with ThreadPoolExecutor(max_workers=1) as pool:
                paused = pool.submit(controller.reach, Barrier.P8, event["event_id"])
                barrier_id = controller.wait_reached(Barrier.P8)
                controller.release(Barrier.P8)
                if paused.result(timeout=40) != barrier_id:
                    raise AssertionError("P8 barrier reach/release identity changed")

        if arm in (Arm.B0, Arm.B1, Arm.B2):
            from research.runner.baseline_audio import run_baseline_audio

            trace = run_baseline_audio(execution_id, case, arm, at_progress)
        else:
            trace = run_phase4_p8(
                research_arm=cast(Literal["B3", "P1", "P2"], arm.value),
                on_p8_progress=at_progress,
            )
        if barrier_id is None:
            raise AssertionError("P8 client progress barrier was never reached")
        target = {
            "barrier": placement.barrier.value,
            "fault": placement.fault.value,
            "request_index": placement.request_index,
            "target": placement.target,
        }
        fault_id = record_fault(
            execution_id, Barrier.P8.value, placement.fault.value, target, barrier_id
        )
        bind_execution(
            execution_id,
            UUID(trace["scenario_id"]),
            UUID(trace["workflow_id"]),
            placement.hash,
            datetime.fromisoformat(trace["correction_scripted_at"]),
        )
        acks = _record_client_acks(execution_id, trace, case)
        result = grade_p8_paired(trace, case)
        record_result(execution_id, case, trace["simulator_truth_log"], result)
        return {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": trace["scenario_id"],
            "workflow_id": trace["workflow_id"],
            "fault_occurrence_id": str(fault_id),
            "fault_placement_hash": placement.hash,
            "playback_acks": [ack.model_dump(mode="json") for ack in acks],
            "timing_evidence": timing_evidence(execution_id),
            "trace": trace,
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        raise


def run_p8_paired(
    output_dir: Path = Path("artifacts") / "phase-6-replays", arms: tuple[Arm, ...] = ARMS
) -> dict[str, Any]:
    case = witness_case()
    placement = schedule(case)
    source_commit, tree_hash = _source_identity()
    manifest: dict[str, Any] = {
        "name": "Phase 6 paired P8 B3/P1/P2 repair ablation",
        "runner_version": RUNNER_VERSION,
        "scenario": case.model_dump(mode="json"),
        "fixture_hash": case.fixture_hash,
        "audio_hash": case.audio_hash,
        "source_commit": source_commit,
        "source_tree_hash": tree_hash,
        "container_digests": _container_digests(),
        "migration_version": MIGRATION_VERSION,
        "model_profile": "phase4-scripted-stt-and-intent",
        "fault_schedule": {
            "barrier": placement.barrier.value,
            "fault": placement.fault.value,
            "request_index": placement.request_index,
            "target": placement.target,
            "hash": placement.hash,
            "played_ms": 500,
            "last_frame": 8000,
        },
        "arms": {
            arm.value: {
                key: value.value if isinstance(value, Arm) else value
                for key, value in vars(PROFILES[arm]).items()
            }
            for arm in arms
        },
    }
    run_id, manifest_hash, frozen_manifest = create_run(manifest, source_commit)
    case_id = create_case(run_id, case, manifest["fault_schedule"])
    executions = [_execute(run_id, case_id, case, arm) for arm in arms]
    finish_run(run_id)
    rows = [
        {
            "scenario_key": case.scenario_key,
            "arm": item["arm"],
            "metrics": {row["metric_name"]: row["numeric_value"] for row in item["metrics"]},
        }
        for item in executions
    ]
    bundle = {
        "run_id": str(run_id),
        "case_id": str(case_id),
        "manifest": frozen_manifest,
        "manifest_hash": manifest_hash,
        "execution_count": len(executions),
        "independent_scenario_count": 1,
        "paired_summary": paired_counts(rows, "played_span_repair_complete"),
        "executions": executions,
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"p8-paired-{run_id}.json"
    if path.exists():
        raise FileExistsError("A frozen P8 paired bundle cannot be overwritten")
    path.write_text(json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "run_id": str(run_id),
        "bundle_path": str(path.resolve()),
        "bundle_hash": bundle["bundle_hash"],
        "paired_summary": bundle["paired_summary"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run paired B3/P1/P2 P8 repair ablation")
    parser.parse_args()
    print(json.dumps(run_p8_paired(), indent=2))
