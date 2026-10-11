"""Immutable pilot evidence is a regression fixture, never a statistical rerun."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from research.pilot import freeze as freeze_module
from research.pilot.runner import verify_pilot
from research.scenario_dsl.models import stable_hash

ROOT = Path(__file__).resolve().parents[2]


def _closed() -> tuple[Path, Path]:
    directory = ROOT / "artifacts/phase-7-pilot/v1"
    pilots, freezes = (
        sorted(directory.glob("pilot-*.json")),
        sorted(directory.glob("freeze-*.json")),
    )
    assert len(pilots) == len(freezes) == 1, (
        "Closed Phase 7 evidence must ship with regression suite"
    )
    return pilots[0], freezes[0]


def test_closed_pilot_all_instances_and_failures_are_verified() -> None:
    pilot, _ = _closed()
    result = verify_pilot(pilot)
    assert result["independent_scenario_instances"] == 40
    assert result["scenario_versions"] == 45
    assert result["verified_executions"] == 267
    assert result["failure_reviews"] > 0


def test_rehashed_pilot_cannot_omit_case_or_change_analysis() -> None:
    pilot, _ = _closed()
    original = json.loads(pilot.read_text(encoding="utf-8"))
    path = pilot.parent / "test-tampered-pilot.json"
    try:
        changed = deepcopy(original)
        changed["entries"].pop()
        changed["hash"] = stable_hash({k: v for k, v in changed.items() if k != "hash"})
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="omitted"):
            verify_pilot(path)
        changed = deepcopy(original)
        changed["analysis"]["raw_counts"]["P2"]["correction_success"]["numerator"] = 999
        changed["hash"] = stable_hash({k: v for k, v in changed.items() if k != "hash"})
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="analysis or raw counts"):
            verify_pilot(path)
    finally:
        path.unlink(missing_ok=True)


def test_freeze_detects_source_drift_and_rehashed_budget_edit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, freeze = _closed()
    original = json.loads(freeze.read_text(encoding="utf-8"))
    monkeypatch.setattr(freeze_module, "source_inventory", lambda: {"changed.py": "0" * 64})
    with pytest.raises(ValueError, match="protocol drift"):
        freeze_module.verify_freeze(freeze)
    path = freeze.parent / "test-tampered-freeze.json"
    try:
        changed = deepcopy(original)
        changed["protocol"]["budgets"]["reconciliation_max_attempts"] = 999
        changed["hash"] = stable_hash({k: v for k, v in changed.items() if k != "hash"})
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="budget"):
            freeze_module.verify_freeze(path, check_workspace=False)
    finally:
        path.unlink(missing_ok=True)
