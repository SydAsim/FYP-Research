"""Conditional frame, identified contrasts and observable recovery credit."""

import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from research.arms import Arm
from research.remedies.runner import Trial
from research.study_v4.analysis import (
    RECOVERY_FAMILIES,
    batch_sensitivity,
    clean_gate,
    marginal_model,
)
from research.study_v4.calibration import CalibrationTrial
from research.study_v4.design import ALLOCATION, materialize
from research.study_v4.oracle import adapt_calibration, revised_evaluate
from research.study_v4.pipeline import pipeline
from research.study_v4.qualification import qualify
from research.study_v4.runtime import Runtime
from research.study_v4.window import observe
from tests.unit.test_phase8_study import row


def test_fixed_frame_input_draws_and_separate_calibration() -> None:
    main = materialize()
    calibration = materialize(calibration=True)
    assert len(main) == 500 and Counter(c.stratum for c in main) == ALLOCATION
    assert len({c.semantic_hash for c in main}) == 500
    assert not {c.semantic_hash for c in main} & {c.semantic_hash for c in calibration}
    assert len(calibration) == 50 and sum(len(c.arm_order) for c in main) == 1500
    assert all(c.secondary_arms == [] for c in main)


def test_calibration_rejects_main_before_any_network(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="main input"):
        CalibrationTrial(Runtime(tmp_path / "logs"), materialize()[0], Arm.B3, tmp_path)


def test_model_known_contrast_uses_all_inputs_not_member_zero() -> None:
    cases = materialize()
    rows = [row(c, a, "TRUE" if a is Arm.P2 else "FALSE") for c in cases for a in c.primary_arms]
    result = marginal_model(cases, rows, "correction_success")
    contrast = result["standardized_contrasts"][1]
    assert contrast["identified"] and contrast["difference"] == 1
    assert sum(c["complete_pairs"] for c in contrast["components"]) == 200
    assert contrast["conservative_95_interval"][0] < 1
    sensitivity = batch_sensitivity(cases, rows)
    assert len(sensitivity["estimates"]) == 20
    assert all(e["difference"] == 1 for e in sensitivity["estimates"])


def test_missingness_does_not_manufacture_a_model_fit() -> None:
    result = marginal_model(materialize(), [], "correction_success")
    for contrast in result["standardized_contrasts"]:
        assert not contrast["identified"] and contrast["difference"] is None
        assert contrast["missingness_bounds"] == [-1, 1]


def completed_trace(family: str = "full-before-correction") -> dict:
    for manifest in Path("artifacts/phase-8-study-design/v4/calibration").glob("*/manifest.json"):
        for entry in json.loads(manifest.read_text(encoding="utf-8"))["executions"]:
            trace = json.loads(Path(entry["path"]).read_text(encoding="utf-8"))
            if trace["input"]["generator_family"] == family and trace["arm"] == "B3":
                return dict(trace)
    raise AssertionError("Separate live calibration fixture is required")


@pytest.mark.parametrize("arm", [Arm.B3, Arm.P1, Arm.P2])
def test_ordinary_update_delivery_is_label_invariant(arm: Arm) -> None:
    trace = completed_trace()
    case, evidence = adapt_calibration(trace)
    anchor = evidence.acceptances[-1].accepted_at
    baseline, _ = revised_evaluate(case, evidence, challenge_at=anchor)
    relabeled, _ = revised_evaluate(
        case, evidence.model_copy(update={"arm": arm}), challenge_at=anchor
    )
    assert relabeled["values"] == baseline["values"]
    assert baseline["values"]["corrective_delivery_after_challenge"] == "TRUE"


def test_missing_completion_and_short_window_are_unknown() -> None:
    case, evidence = adapt_calibration(completed_trace())
    incomplete = evidence.model_copy(
        update={
            "playback": [p for p in evidence.playback if p["request"]["event_type"] != "COMPLETED"]
        }
    )
    grade, _ = revised_evaluate(case, incomplete, challenge_at=evidence.acceptances[-1].accepted_at)
    assert grade["values"]["corrective_delivery_after_challenge"] == "UNKNOWN"


def test_completed_driver_does_not_certify_hook() -> None:
    trace = completed_trace("redis-loss")
    trace["status"] = "COMPLETED"
    trace["barriers"] = []
    assert qualify(trace, [])["status"] == "NEEDS_QUALIFICATION"
    assert "restart-before-repair" in RECOVERY_FAMILIES


def test_main_ledger_unstarted() -> None:
    slots = json.loads(Path("artifacts/phase-8-study-design/v4/main-slots.json").read_text())
    assert len(slots) == 1500 and all(s["status"] == "NOT_STARTED" for s in slots)
    assert all(s["execution_id"] is None for s in slots)


def test_nonprogressing_drain_has_a_bounded_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    trial = object.__new__(Trial)
    trial.id = "validation-budget-only"
    trial.row = {"classification": "ARTIFICIAL_ADAPTER_VALIDATION"}
    calls = []
    monkeypatch.setattr(trial, "history", lambda: {"operations": [{"id": "busy-operation"}]})

    def busy(*args: object, **kwargs: object) -> dict:
        calls.append(kwargs)
        return {"action": "busy"}

    monkeypatch.setattr(trial, "post", busy)
    with pytest.raises(TimeoutError, match="30 drain passes"):
        trial.drain()
    assert len(calls) == 30


def test_clean_gate_uses_three_hundred_and_blocks_missingness() -> None:
    cases = materialize()
    rows = [
        row(c, a, "TRUE", endpoint="clean_task_success")
        for c in cases
        if c.stratum.value == "CLEAN"
        for a in c.primary_arms
    ]
    gate = clean_gate(cases, rows)
    assert gate["planned_n"] == gate["complete_pairs"] == 300
    assert gate["criterion_met_descriptive"]
    assert not clean_gate(cases, [])["criterion_met_descriptive"]


def test_integrated_oracle_pipeline_and_campaign_lock() -> None:
    case, evidence = adapt_calibration(completed_trace())
    result = pipeline([case], [evidence])
    assert result["grades"][0]["values"]["corrective_delivery_after_challenge"] == "TRUE"
    assert result["analysis"]["secondary_family"]["count"] == 10
    with pytest.raises(ValueError, match="no reviewed freeze"):
        pipeline([case], [evidence.model_copy(update={"classification": "CAMPAIGN"})])


def test_after_deadline_ack_cannot_complete_corrective_delivery() -> None:
    case, original = adapt_calibration(completed_trace())
    evidence = original.model_copy(deep=True)
    cap = evidence.acceptances[-1].scripted_at + timedelta(seconds=600)
    evidence.ended_at = cap + timedelta(seconds=2)
    for playback in evidence.playback:
        if playback["request"]["event_type"] == "COMPLETED":
            playback["server_received_at"] = (cap + timedelta(seconds=1)).isoformat()
    grade, _ = revised_evaluate(case, evidence, challenge_at=evidence.acceptances[-1].accepted_at)
    assert grade["values"]["corrective_delivery_after_challenge"] == "UNKNOWN"


def test_recovery_does_not_credit_publication_after_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial = object.__new__(Trial)
    trial.row = {"input": {"case_id": "cal-v4-edge"}}
    future = datetime.now(UTC) + timedelta(seconds=30)
    monkeypatch.setattr(trial, "save", lambda: None)
    monkeypatch.setattr(
        trial, "snapshot", lambda: {"obligations": [], "playback_rows": [], "published_at": future}
    )
    result = observe(trial, 0, "CLOCK_BOUNDARY", lambda s, cutoff: s["published_at"] <= cutoff)
    assert result["outcome"] == "ADMINISTRATIVE_TIMEOUT"
