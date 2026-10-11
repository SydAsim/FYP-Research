"""Finite evidence-discrimination and analysis parity checks; no main driver."""

from pathlib import Path
from typing import Any

import pytest
from controls import Policy, read, utc
from instrument import evidence_for
from refusal import recognize, timing_eligible, validate_classification
from runner import HERE, initialize

from research.scenario_dsl.models import stable_hash
from research.study_v4.oracle import revised_evaluate


def original() -> dict[str, Any]:
    from typing import cast

    return cast(dict[str, Any], read(HERE / "retained-first-original.json"))


def failure_sync(row: dict[str, Any]) -> None:
    call = next(c for c in row["http"] if c["path"] == "/internal/phase6/b3/schedule")
    row["failure"]["detail"] = f"HTTP {call['status']}: {call['path']}: {call['response']}"


@pytest.mark.parametrize(
    "change",
    [
        "other409",
        "500",
        "retryable",
        "malformed",
        "revision",
        "arm",
        "exception",
        "missing_fact",
        "wrong_resource",
        "wrong_operation",
        "altered_raw",
        "unavailable_resource",
        "unbound_response",
        "missing_failure",
        "available_status",
        "missing_cause",
    ],
)
def test_only_specific_evidenced_refusal_is_recognized(change: str) -> None:
    row = original()
    call = next(c for c in row["http"] if c["path"] == "/internal/phase6/b3/schedule")
    wrapper = call["response"]
    if change == "other409":
        wrapper["detail"] = "Stale intent revision"
    elif change == "500":
        call["status"] = 500
    elif change == "retryable":
        wrapper["detail"] = wrapper["detail"].replace('"retryable":false', '"retryable":true')
    elif change == "malformed":
        wrapper["detail"] += " garbage"
    elif change == "revision":
        call["request"]["expected_intent_revision"] = 3
    elif change == "arm":
        row["arm"] = "P1"
    elif change == "exception":
        row["failure"]["type"] = "TimeoutError"
    elif change == "missing_failure":
        del row["failure"]
    elif change == "missing_cause":
        row["input"]["provider"]["status_lookup"] = True
    elif change == "unbound_response":
        wrapper["instance"] = "/different"
    else:
        obs = row["snapshot"]["observations"]
        if change == "missing_fact":
            obs.pop()
        elif change == "wrong_resource":
            obs[-3]["raw"]["body"]["appointments"][0]["status"] = "CANCELLED"
            obs[-3]["raw_hash"] = stable_hash(obs[-3]["raw"])
        elif change == "wrong_operation":
            obs[-1]["query"]["operation_id"] = "unrelated"
        elif change == "altered_raw":
            obs[-1]["raw"]["body"]["detail"] = "Altered"
        elif change == "unavailable_resource":
            obs[-3]["raw"]["status"] = 501
            obs[-3]["raw_hash"] = stable_hash(obs[-3]["raw"])
        elif change == "available_status":
            obs[-1]["raw"] = {"status": 200, "body": {"outcome": "PRESENT"}}
            obs[-1]["raw_hash"] = stable_hash(obs[-1]["raw"])
    if "failure" in row:
        failure_sync(row)
    assert recognize(row) is None


def test_retained_first_original_parity_and_full_window_censor() -> None:
    row = original()
    proof = recognize(row)
    assert proof is not None and proof["retryable"] is False
    row["driver_classification"] = proof
    assert validate_classification(row) and timing_eligible(row)
    old_case, old_evidence = evidence_for(row, amended=False)
    new_case, new_evidence = evidence_for(row)
    accepted = [a.accepted_at for a in old_evidence.acceptances if a.revision > 1 and a.accepted_at]
    challenge = max(accepted) if accepted else None
    old_grade, old = revised_evaluate(old_case, old_evidence, challenge_at=challenge)
    new_grade, new = revised_evaluate(new_case, new_evidence, challenge_at=challenge)
    # Correct final communication stays FALSE; absence of speech is not a success.
    assert old.values == new.values == row["analysis_row"]["values"]
    assert new.values["correction_success"] == "TRUE"
    assert new.values["correct_final_update"] == "FALSE"
    assert old.duration_seconds == new.duration_seconds == 600
    assert old.event_observed is new.event_observed is False
    assert old.censor_reason == "INFRASTRUCTURE_FAILURE"
    assert new.censor_reason == "NO_SUPPORTED_COMPLETION"
    assert row["status"] == "FAILED" and old_grade != new_grade


@pytest.mark.parametrize("missing", ["poll", "anchor", "gap", "drift"])
def test_incomplete_refusal_never_earns_complete_timing(missing: str) -> None:
    row = original()
    row["driver_classification"] = recognize(row)
    if missing == "poll":
        row["polls"] = row["polls"][:-1]
    elif missing == "anchor":
        row["missing_final_anchor"] = True
    elif missing == "gap":
        row["collection_errors"] = [{"type": "CLOCK_OR_GAP"}]
    else:
        row["source_drift"] = "SOURCE_DRIFT"
    assert not timing_eligible(row)
    assert evidence_for(row)[1].status == "INFRASTRUCTURE_FAILURE"


def test_classification_tamper_is_a_defect() -> None:
    row = original()
    row["driver_classification"] = recognize(row)
    row["driver_classification"]["retryable"] = True
    with pytest.raises(ValueError, match="CLASSIFICATION_EVIDENCE_DRIFT"):
        evidence_for(row)


def test_unclassified_other_refusal_keeps_original_failure() -> None:
    row = original()
    assert evidence_for(row)[1].status == "INFRASTRUCTURE_FAILURE"


def test_candidate_never_admits_main_even_with_old_authorization(tmp_path: Path) -> None:
    policy = Policy(scope="CAMPAIGN", run_id="blocked-amendment-main", host_started_at=utc())
    with pytest.raises(ValueError, match="AMENDMENT_REVIEW_REQUIRED_MAIN_BLOCKED"):
        initialize(
            tmp_path / "blocked",
            tmp_path,
            tmp_path / "manifest",
            policy,
            tmp_path / "receipts",
            tmp_path / "key",
            tmp_path / "schedule",
            tmp_path / "backup",
        )
    assert not (tmp_path / "blocked").exists()


def test_plan_finite_and_calibration_separated() -> None:
    bank = read(HERE / "calibration-inputs.json")["calibration_inputs"]
    plan = read(HERE / "calibration-plan.json")
    assert len(bank) == plan["planned_live_executions"] == 4
    assert {c["case_id"] for c in bank} == {c["id"] for c in plan["cases"]}
    assert all(c["observation_budget_seconds"] == 600 for c in bank)
    assert all(c["case_id"].startswith("cal-v4-") for c in bank)
    assert plan["cloud_budget_usd"] == 0 and plan["concurrency"] == 1
