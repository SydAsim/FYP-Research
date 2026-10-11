"""The saved Phase 6 closure is independently reproducible without running services."""

import json
from pathlib import Path

import pytest

from research.runner.completion import verify_completion
from research.scenario_dsl.models import stable_hash

SAVED = (
    Path(__file__).parents[2] / "artifacts" / "phase-6-completion" / "completion-fcbd40b83dc7.json"
)


@pytest.mark.parametrize(
    "filename", ["completion-fcbd40b83dc7.json", "completion-0ce13a086fe0.json"]
)
def test_saved_phase6_closure_reproduces_all_execution_and_coverage_counts(filename: str) -> None:
    result = verify_completion(SAVED.with_name(filename))
    assert result["paired_fixture_count"] == 43
    assert result["verified_executions"] == 256
    assert not result["phase7_started"]


@pytest.mark.parametrize("tamper", ["omit_mandatory", "change_metric", "swap_workflow"])
def test_closed_replay_rejects_semantic_tampering_after_rehash(tamper: str, tmp_path: Path) -> None:
    bundle = json.loads(SAVED.read_text(encoding="utf-8"))
    if tamper == "omit_mandatory":
        bundle["entries"] = [e for e in bundle["entries"] if e["label"] != "P8"]
        expected = "mandatory"
    elif tamper == "change_metric":
        metric = bundle["entries"][0]["secondary_evidence"][0]["metrics"]
        metric["stale_confirmation_rate"]["numerator"] = 999
        metric["hash"] = stable_hash({k: v for k, v in metric.items() if k != "hash"})
        expected = "secondary metric"
    else:
        evidence = bundle["entries"][0]["secondary_evidence"][0]
        evidence["timeline"]["workflow_id"] = "00000000-0000-0000-0000-000000000000"
        evidence["timeline_hash"] = stable_hash(evidence["timeline"])
        expected = "another workflow"
    bundle["hash"] = stable_hash({k: v for k, v in bundle.items() if k != "hash"})
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        verify_completion(path)


def test_ready_acoustic_proposal_cannot_diverge_from_the_actual_model_output() -> None:
    from research.runner.acoustic_source import AcousticEvidence

    closure = json.loads(SAVED.read_text(encoding="utf-8"))
    entry = next(e for e in closure["entries"] if e["label"] == "LOCAL_RECORDED_CLEAN")
    child = json.loads((Path(__file__).parents[2] / entry["path"]).read_text(encoding="utf-8"))
    voice = child["manifest"]["voice_evidence"]
    assert AcousticEvidence.model_validate(voice).status == "READY"
    voice["proposal"]["requested_start"] = "2026-11-06T15:00:00+05:00"
    with pytest.raises(ValueError, match="actual model output"):
        AcousticEvidence.model_validate(voice)


def test_honest_handoff_is_safe_but_does_not_receive_task_or_outcome_credit() -> None:
    closure = json.loads(
        SAVED.with_name("completion-0ce13a086fe0.json").read_text(encoding="utf-8")
    )
    entry = next(
        e for e in closure["entries"] if e["label"] == "maintenance-p2-partial-provider-effect-17"
    )
    child = json.loads((Path(__file__).parents[2] / entry["path"]).read_text(encoding="utf-8"))
    for row, proof in zip(child["executions"], entry["secondary_evidence"], strict=True):
        if row["arm"] not in ("B3", "P1", "P2"):
            continue
        assert proof["metrics"]["safe_resolution_policy"]["honest_durable_handoff"]
        assert proof["metrics"]["safe_resolution_policy"]["value"]
        assert not row["oracle_result"]["correction_success"]
        assert not row["oracle_result"]["outcome_coverage"]
