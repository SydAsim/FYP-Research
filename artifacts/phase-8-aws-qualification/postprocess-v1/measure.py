"""Read-only calibration summaries and independent regrading, never main analysis."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.execution_setup.core import digest, immutable, load  # noqa: E402
from research.execution_setup.resources import cpu_fraction, tree_bytes  # noqa: E402
from research.execution_setup.worker import evidence_for  # noqa: E402
from research.study_v4.oracle import revised_evaluate  # noqa: E402


def execution(path: Path) -> dict[str, Any]:
    trace = load(path)
    polls = [load(path.parent / "polls" / Path(p["path"]).name) for p in trace["polls"]]
    hosts = [p["host"] for p in polls]
    deadline = datetime.fromisoformat(trace["original_deadline"])
    times = [datetime.fromisoformat(p["at"]) for p in polls]
    case, evidence = evidence_for(trace)
    accepted = [a.accepted_at for a in evidence.acceptances if a.revision > 1 and a.accepted_at]
    grade, row = revised_evaluate(case, evidence, challenge_at=max(accepted) if accepted else None)
    if grade != trace["revised_grade"] or row.model_dump(mode="json") != trace["analysis_row"]:
        raise ValueError("REPLAY_GRADE_DRIFT: do not replace original")
    return {
        "trace": str(path.resolve()),
        "export_sha256": digest(path),
        "execution_id": trace["execution_id"],
        "arm": trace["arm"],
        "case_id": case.case_id,
        "recipe": case.generator_family,
        "attempt_label": trace["attempt_label"],
        "original_id": trace["original_id"],
        "driver_status": trace["status"],
        "failure": trace.get("failure"),
        "missing_final_anchor": trace["missing_final_anchor"],
        "deadline": trace["original_deadline"],
        "last_poll_start": polls[-1]["at"],
        "last_poll_end": polls[-1]["ended_at"],
        "post_cutoff_snapshot_start": times[-1] >= deadline,
        "cutoff_start_overshoot_seconds": (times[-1] - deadline).total_seconds(),
        "elapsed_seconds": (
            datetime.fromisoformat(trace["finished_at"])
            - datetime.fromisoformat(trace["started_at"])
        ).total_seconds(),
        "poll_count": len(polls),
        "maximum_start_gap_seconds": max(
            ((b - a).total_seconds() for a, b in zip(times, times[1:], strict=False)), default=0
        ),
        "sampled_peak_used_memory_bytes": max(h["used_memory_bytes"] for h in hosts),
        "sampled_minimum_available_memory_bytes": min(h["available_memory_bytes"] for h in hosts),
        "minimum_disk_free_bytes": min(h["system_free_bytes"] for h in hosts),
        "maximum_cpu_load_fraction": max(
            (h["cpu_load_fraction"] for h in hosts if h.get("cpu_load_fraction") is not None),
            default=None,
        ),
        "cpu_scope": hosts[-1].get("cpu_scope"),
        "memory_scope": hosts[-1].get("memory_scope"),
        "database_start": trace["resource_start"],
        "database_end": trace["resource_end"],
        "execution_directory_bytes": tree_bytes(path.parent),
        "export_bytes": path.stat().st_size,
        "oracle_replay": "IDENTICAL",
        "grade_values": grade["values"],
        "repair_mechanism": grade.get("repair_mechanism"),
        "voice_evidence": "SCRIPTED_TONE_ACK_PROTOCOL_ONLY",
        "unsafe_attempt": trace.get("unsafe_attempt"),
    }


def summarize(root: Path) -> dict[str, Any]:
    rows = [execution(p) for p in sorted(root.rglob("export.json"))]
    parallel = root / "fyp-p82-v2/parallel-v2"
    samples = [load(p) for p in sorted((parallel / "samples").glob("*.json"))]
    loads = [cpu_fraction(a, b) for a, b in zip(samples, samples[1:], strict=False)]
    return {
        "classification": "CALIBRATION_NOT_MAIN",
        "main_started": False,
        "main_inferential_inputs": 0,
        "executions": rows,
        "sampled_parallel_host": {
            "samples": len(samples),
            "peak_used_memory_bytes": max((s["used_memory_bytes"] for s in samples), default=None),
            "minimum_available_memory_bytes": min(
                (s["available_memory_bytes"] for s in samples), default=None
            ),
            "maximum_cpu_fraction": max((v for v in loads if v is not None), default=None),
        },
        "retained_directory_bytes": tree_bytes(root),
        "scope_note": "Calibration repetitions do not enlarge N; no arm superiority inference",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    immutable(args.output, summarize(args.root))
