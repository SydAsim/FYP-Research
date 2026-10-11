"""Live P6/P7/P9 B3/P1/P2 paired audio timing runs."""

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
from research.oracle.playout_witness import grade_playout
from research.replay.phase4_p8 import run as run_voice_replay
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
    record_playback,
    record_result,
    timing_evidence,
)
from research.runner.paired import _container_digests, _source_identity
from research.scenario_dsl.models import Barrier, FaultFamily, ScenarioCase, stable_hash

ARMS = (Arm.B3, Arm.P1, Arm.P2)
RUNNER_VERSION = "phase6-p6-p7-p9-playout-paired-v2"


def playout_case(boundary: Barrier) -> ScenarioCase:
    if boundary not in (Barrier.P6, Barrier.P7, Barrier.P9):
        raise ValueError("Audio timing pairing supports P6, P7, or P9")
    data = witness_case().model_dump(mode="json")
    data.update(
        {
            "fixture_version": RUNNER_VERSION,
            "scenario_key": f"maintenance-{boundary.value.lower()}-live-playout",
            "correction_barrier": boundary.value,
            "fault_family": FaultFamily.NONE.value,
            "speech_exposure": "NONE" if boundary in (Barrier.P6, Barrier.P7) else "FULL",
        }
    )
    return ScenarioCase.model_validate(data)


def _client_event(trace: dict[str, Any], segment_id: str, kind: str) -> dict[str, Any]:
    matches = [
        item["request"]
        for item in trace["client_playback_evidence"]
        if item["request"]["segment_id"] == segment_id and item["request"]["event_type"] == kind
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {kind} client event")
    return cast(dict[str, Any], matches[0])


def _record_acks(
    execution_id: UUID, trace: dict[str, Any], case: ScenarioCase
) -> list[PlaybackAck]:
    items: list[PlaybackAck] = []
    stale_id = trace["first_claim"]["scheduled"]["segment_id"]
    if case.correction_barrier is Barrier.P9:
        started = _client_event(trace, stale_id, "STARTED")
        completed = _client_event(trace, stale_id, "COMPLETED")
        items.append(
            PlaybackAck(
                event_id=completed["event_id"],
                claim_type="CURRENT_APPOINTMENT",
                claim_start=case.initial_start,
                intent_revision=1,
                released_at=datetime.fromisoformat(started["client_time"]),
                played_at=datetime.fromisoformat(completed["client_time"]),
                played_ms=completed["played_ms"],
                permit_id=(trace["first_claim"]["permit"] or {}).get("permit_id"),
            )
        )
    corrected_id = trace["corrected_claim"]["scheduled"]["segment_id"]
    started = _client_event(trace, corrected_id, "STARTED")
    completed = _client_event(trace, corrected_id, "COMPLETED")
    items.append(
        PlaybackAck(
            event_id=completed["event_id"],
            claim_type="RESCHEDULED_APPOINTMENT",
            claim_start=case.final_start,
            intent_revision=2,
            released_at=datetime.fromisoformat(started["client_time"]),
            played_at=datetime.fromisoformat(completed["client_time"]),
            played_ms=completed["played_ms"],
            permit_id=(trace["corrected_claim"]["permit"] or {}).get("permit_id"),
        )
    )
    for item in items:
        record_playback(execution_id, item, case.audio_hash)
    return playback_for(execution_id)


def _execute(run_id: UUID, case_id: UUID, case: ScenarioCase, arm: Arm) -> dict[str, Any]:
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    boundary = case.correction_barrier
    placement = schedule(case)
    barrier_id: UUID | None = None
    source_event_id: str | None = None
    try:

        def at_barrier(event: dict[str, Any]) -> None:
            nonlocal barrier_id, source_event_id
            expected = {
                Barrier.P6: "GENERATED",
                Barrier.P7: "PUBLISHED",
                Barrier.P9: "COMPLETED",
            }[boundary]
            if event["event_type"] != expected:
                raise AssertionError("Live playout reached the wrong boundary event")
            source_event_id = event["event_id"]
            controller = NamedBarrierController(execution_id, {boundary})
            with ThreadPoolExecutor(max_workers=1) as pool:
                paused = pool.submit(controller.reach, boundary, source_event_id)
                barrier_id = controller.wait_reached(boundary)
                controller.release(boundary)
                if paused.result(timeout=40) != barrier_id:
                    raise AssertionError("Playout barrier reach/release identity changed")

        if arm in (Arm.B0, Arm.B1, Arm.B2):
            from research.runner.baseline_audio import run_baseline_audio

            trace = run_baseline_audio(execution_id, case, arm, at_barrier)
        else:
            trace = run_voice_replay(
                research_arm=cast(Literal["B3", "P1", "P2"], arm.value),
                boundary=boundary,
                on_barrier=at_barrier,
            )
        if barrier_id is None or source_event_id is None:
            raise AssertionError("Playout barrier was not reached")
        bind_execution(
            execution_id,
            UUID(trace["scenario_id"]),
            UUID(trace["workflow_id"]),
            placement.hash,
            datetime.fromisoformat(trace["correction_scripted_at"]),
        )
        acks = _record_acks(execution_id, trace, case)
        result = grade_playout(trace, case)
        record_result(execution_id, case, trace["simulator_truth_log"], result)
        return {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": trace["scenario_id"],
            "workflow_id": trace["workflow_id"],
            "fault_placement_hash": placement.hash,
            "fault_occurrence_id": None,
            "barrier_source_event_id": source_event_id,
            "playback_acks": [ack.model_dump(mode="json") for ack in acks],
            "timing_evidence": timing_evidence(execution_id),
            "trace": trace,
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        raise


def run_playout_paired(
    boundary: Barrier,
    output_dir: Path = Path("artifacts") / "phase-6-replays",
    arms: tuple[Arm, ...] = ARMS,
) -> dict[str, Any]:
    case = playout_case(boundary)
    placement = schedule(case)
    source_commit, tree_hash = _source_identity()
    manifest: dict[str, Any] = {
        "name": f"Phase 6 paired {boundary.value} B3/P1/P2 playout",
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
        "paired_summary": paired_counts(rows, "safe_resolution"),
        "executions": executions,
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{boundary.value.lower()}-paired-{run_id}.json"
    if path.exists():
        raise FileExistsError("A frozen playout bundle cannot be overwritten")
    path.write_text(json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "run_id": str(run_id),
        "bundle_path": str(path.resolve()),
        "bundle_hash": bundle["bundle_hash"],
        "paired_summary": bundle["paired_summary"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a paired P6, P7, or P9 audio boundary")
    parser.add_argument("boundary", choices=("P6", "P7", "P9"))
    args = parser.parse_args()
    print(json.dumps(run_playout_paired(Barrier(args.boundary)), indent=2))
