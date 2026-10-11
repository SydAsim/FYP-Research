"""Execute a selected frozen pilot fixture in empty isolated PostgreSQL services."""

import json
import sys
from pathlib import Path
from typing import Any

from research.analysis.latency import paired_latency
from research.analysis.metrics import paired_counts
from research.arms import Arm
from research.pilot.freeze import source_inventory
from research.replay.verify_phase6 import verify_bundle
from research.run_store import create_case, create_run, finish_run
from research.runner.paired import _execute_one
from research.scenario_dsl.models import ScenarioCase, stable_hash


def reproduce(request: dict[str, Any]) -> dict[str, Any]:
    if source_inventory() != request["source_inventory"]:
        raise ValueError("Clean runtime source differs from frozen archive")
    original = request["bundle"]
    # Independent verification runs without relying on the original controller database.
    original_path = Path("/evidence/original.json")
    original_path.write_text(json.dumps(original), encoding="utf-8")
    verify_bundle(original_path)
    from research.run_store import connection

    with connection() as conn:
        counts = {
            table: conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]  # type: ignore[index]
            for table in ("evaluation_runs", "workflows", "operations")
        }
    if any(counts.values()):
        raise ValueError("Clean reproduction requires empty workflow/research databases")
    manifest = {
        k: v for k, v in original["manifest"].items() if k not in ("run_id", "frozen_at_utc")
    }
    manifest["name"] = "Phase 7 clean environment reproduction"
    manifest["container_digests"] = request["container_digests"]
    case = ScenarioCase.model_validate(manifest["scenario"])
    arms = tuple(Arm(a) for a in manifest["arms"])
    run_id, manifest_hash, frozen = create_run(manifest, manifest["source_commit"])
    case_id = create_case(run_id, case, manifest["fault_schedule"])
    executions = [_execute_one(run_id, case_id, case, arm) for arm in arms]
    finish_run(run_id)
    paired = paired_counts(
        [
            {
                "scenario_key": case.scenario_key,
                "arm": e["arm"],
                "metrics": {m["metric_name"]: m["numeric_value"] for m in e["metrics"]},
            }
            for e in executions
        ],
        "correction_success",
    )
    replay: dict[str, Any] = {
        "run_id": str(run_id),
        "case_id": str(case_id),
        "manifest": frozen,
        "manifest_hash": manifest_hash,
        "execution_count": len(executions),
        "independent_scenario_count": 1,
        "paired_summary": paired,
        "executions": executions,
        "latency_summary": {
            arm.value: paired_latency(
                [
                    {
                        "scenario_key": case.scenario_key,
                        "arm": e["arm"],
                        **e["correction_to_outcome_latency"],
                    }
                    for e in executions
                ],
                "B3",
                arm.value,
            )
            for arm in arms
            if arm is not Arm.B3
        },
    }
    replay["bundle_hash"] = stable_hash(replay)
    path = Path("/evidence/reproduced.json")
    path.write_text(json.dumps(replay, indent=2, default=str) + "\n", encoding="utf-8")
    verified = verify_bundle(path)
    expected = {e["arm"]: e["metrics"] for e in original["executions"]}
    actual = {e["arm"]: e["metrics"] for e in executions}
    if actual != expected:
        raise ValueError(
            "Clean independent replay did not reproduce the selected binary metric rows"
        )
    result = {
        "version": "phase7-clean-reproduction-v1",
        "empty_before": counts,
        "original_bundle_hash": original["bundle_hash"],
        "source_inventory_hash": stable_hash(request["source_inventory"]),
        "reproduced_bundle_hash": replay["bundle_hash"],
        "verified": verified,
        "metric_rows_match": True,
        "metric_rows": actual,
        "comparison_scope": (
            "Exact binary row reproduction; timing and generated IDs are new observations"
        ),
    }
    result["hash"] = stable_hash(result)
    Path("/evidence/result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(reproduce(json.load(sys.stdin)), indent=2))
