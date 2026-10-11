"""Live PostgreSQL evidence and missing-review detection for the pilot wrapper."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from research.analysis.completion_metrics import secondary_metrics, timeline_snapshot
from research.pilot.runner import inspect_failure, verify_entry
from research.runner.paired import run_paired
from research.scenario_dsl.catalog import PARTIAL_COVERING
from research.scenario_dsl.models import stable_hash


def test_pilot_keeps_partial_failure_and_rejects_omitted_review(tmp_path: Path) -> None:
    case = PARTIAL_COVERING[0]
    item = {
        "scenario_id": case.scenario_key,
        "template_id": case.scenario_key,
        "variant": "PRIMARY",
        "kind": "provider",
        "case": case.model_dump(mode="json"),
        "arms": ["B3", "P1", "P2"],
        "voice_evidence": None,
    }
    result = run_paired(case, output_dir=tmp_path)
    path = Path(result["bundle_path"])
    bundle = json.loads(path.read_text(encoding="utf-8"))
    entry = {"path": path.name, "bundle_hash": bundle["bundle_hash"], "secondary_evidence": []}
    for row in bundle["executions"]:
        timeline = timeline_snapshot(row["workflow_id"])
        entry["secondary_evidence"].append(
            {
                "execution_id": row["execution_id"],
                "timeline": timeline,
                "timeline_hash": stable_hash(timeline),
                "metrics": secondary_metrics(row, timeline),
                "failure_review": inspect_failure(row, item["case"], "provider"),
            }
        )
    observed = verify_entry(entry, tmp_path, item)
    assert len(observed) == 3
    assert all(r["values"]["correction_success"] == 0 for r in observed)
    assert all(r["values"]["safe_resolution"] == 1 for r in observed)
    changed = deepcopy(entry)
    changed["secondary_evidence"][0]["failure_review"] = None
    with pytest.raises(ValueError, match="failure inspection"):
        verify_entry(changed, tmp_path, item)
    changed = deepcopy(entry)
    changed["secondary_evidence"][0]["timeline"]["workflow_id"] = "another-workflow"
    with pytest.raises(ValueError, match="another execution"):
        verify_entry(changed, tmp_path, item)
