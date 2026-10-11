"""Semantic refusal discrimination against retained facts; no main commands."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
from controls import Policy, read, utc
from instrument import evidence_for
from refusal import recognize, timing_eligible
from runner import initialize

from research.scenario_dsl.models import stable_hash
from research.study_v4.oracle import revised_evaluate

HERE = Path(__file__).resolve().parent


def original(name: str = "second") -> dict[str, Any]:
    from typing import cast

    return cast(dict[str, Any], read(HERE / f"retained-{name}-original.json"))


@pytest.mark.parametrize("name", ["first", "second"])
def test_originals_keep_business_grades_and_failed_raw_status(name: str) -> None:
    row = original(name)
    row["driver_classification"] = recognize(row)
    assert row["driver_classification"] is not None
    assert timing_eligible(row)
    case, old = evidence_for(row, amended=False)
    _, revised = evidence_for(row)
    anchors = [a.accepted_at for a in old.acceptances if a.revision > 1 and a.accepted_at]
    _, before = revised_evaluate(case, old, challenge_at=max(anchors))
    _, after = revised_evaluate(case, revised, challenge_at=max(anchors))
    assert before.values == after.values == row["analysis_row"]["values"]
    assert after.values["correction_success"] == "TRUE"
    assert after.values["correct_final_update"] == "FALSE"
    assert before.censor_reason == "INFRASTRUCTURE_FAILURE"
    assert after.censor_reason == "NO_SUPPORTED_COMPLETION"
    assert before.duration_seconds == after.duration_seconds == 600
    assert not after.event_observed and row["status"] == "FAILED"


@pytest.mark.parametrize(
    "change",
    [
        "type",
        "status",
        "retryable",
        "receipt",
        "expiry",
        "result",
        "revision",
        "operation",
        "exception",
        "event_hash",
        "observation_hash",
        "query",
        "missing",
        "clean",
        "fault",
        "satisfied_resource",
        "wrong_trace",
        "receipt_version",
    ],
)
def test_proposed_receipt_exception_is_fail_closed(change: str) -> None:
    row = original()
    call = next(c for c in row["http"] if c["path"] == "/internal/phase3/claims")
    verify = next(c for c in row["http"] if c["path"] == "/internal/phase3/verifications")
    if change == "type":
        call["response"]["type"] = "https://example.invalid/problems/stale-intent-revision"
    elif change == "status":
        call["status"] = 500
    elif change == "retryable":
        call["response"]["retryable"] = True
    elif change == "receipt":
        call["request"]["receipt_id"] = "00000000-0000-0000-0000-000000000000"
    elif change == "expiry":
        verify["response"]["valid_until"] = call["sent_at"]
    elif change == "result":
        verify["response"]["result"] = "SATISFIED"
    elif change == "revision":
        call["request"]["expected_intent_revision"] = 1
    elif change == "operation":
        verify["request"]["operation_id"] = "wrong"
    elif change == "exception":
        row["failure"]["type"] = "TimeoutError"
    elif change == "event_hash":
        row["snapshot"]["raw_provider_events"][-1]["content_hash"] = "0" * 64
    elif change == "observation_hash":
        row["snapshot"]["observations"][-1]["raw_hash"] = "0" * 64
    elif change == "query":
        row["snapshot"]["observations"][-1]["query"]["scenario_id"] = "wrong"
    elif change == "missing":
        row["snapshot"]["observations"] = []
    elif change == "clean":
        row["input"]["generator_family"] = "clean-Asia/Karachi-30"
    elif change == "fault":
        row["input"]["provider"]["status_lookup"] = True
    elif change == "wrong_trace":
        verify["trace_id"] = "different"
    elif change == "receipt_version":
        verify["response"]["observed_resource_version"] = "999"
    else:
        # Replace unavailable status evidence with bound authoritative PRESENT facts.
        for o in row["snapshot"]["observations"]:
            if o["source_type"] == "SIMULATOR_OPERATION":
                o["raw"] = {
                    "status": 200,
                    "body": {
                        "authoritative": True,
                        "outcome": "PRESENT",
                        "facts": {"resource_key": row["targets"][-1]["resource_key"], "version": 1},
                    },
                }
                o["raw_hash"] = stable_hash(o["raw"])
    row["failure"]["detail"] = f"HTTP {call['status']}: {call['path']}: {call['response']}"
    assert recognize(row) is None


def test_p1_p2_same_recorded_behavior_receives_identical_values() -> None:
    row = original()
    other = copy.deepcopy(row)
    other["arm"] = "P2"
    for value in (row, other):
        value["driver_classification"] = recognize(value)
        assert value["driver_classification"] is not None
    assert row["driver_classification"] == other["driver_classification"]
    case, evidence = evidence_for(row)
    _, other_evidence = evidence_for(other)
    anchor = evidence.acceptances[-1].accepted_at
    assert (
        revised_evaluate(case, evidence, challenge_at=anchor)[1].values
        == revised_evaluate(case, other_evidence, challenge_at=anchor)[1].values
    )


@pytest.mark.parametrize("missing", ["poll", "anchor", "gap", "drift"])
def test_refusal_does_not_repair_missing_collection_evidence(missing: str) -> None:
    row = original()
    row["driver_classification"] = recognize(row)
    if missing == "poll":
        row["polls"] = []
    elif missing == "anchor":
        row["missing_final_anchor"] = True
    elif missing == "gap":
        row["collection_errors"] = [{"type": "CLOCK_OR_GAP"}]
    else:
        row["source_drift"] = "SOURCE_DRIFT"
    assert not timing_eligible(row)
    assert evidence_for(row)[1].status == "INFRASTRUCTURE_FAILURE"


def test_candidate_cannot_initialize_main(tmp_path: Path) -> None:
    policy = Policy(scope="CAMPAIGN", run_id="blocked-preflight-main", host_started_at=utc())
    with pytest.raises(ValueError, match="MAIN_BLOCKED"):
        initialize(
            tmp_path / "main", tmp_path, tmp_path, policy, tmp_path, tmp_path, tmp_path, tmp_path
        )
    assert not (tmp_path / "main").exists()


def test_backup_failure_cli_leaves_durable_nonresumable_pause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    import runner
    from controls import Journal
    from test_controls import calibration, sample

    root, authority = calibration(tmp_path)
    journal = Journal(root)
    slot = journal.admit(authority, sample(), utc(), 0)
    assert slot
    journal.update(slot["execution_id"], state="EXPORTED")

    def broken_backup(*args: Any, **kwargs: Any) -> None:
        raise ValueError("BACKUP_VERIFICATION_FAILED_CONTROL_ONLY")

    monkeypatch.setattr(runner, "run", broken_backup)
    monkeypatch.setattr(sys, "argv", ["runner", "run", "--root", str(root)])
    with pytest.raises(SystemExit) as stopped:
        runner.main()
    assert stopped.value.code == 1
    assert read(root / "pause.json")["reason"] == "PROTOCOL_STOP"
    # A paused EXPORTED slot may finish its own evidence backup; no new slot is admitted.
    recovered = journal.admit(authority, sample(), utc(), 0)
    assert recovered is not None and recovered["execution_id"] == slot["execution_id"]
    journal.update(slot["execution_id"], state="BACKED_UP", backup_hash="CONTROL_ONLY_PROOF")
    with pytest.raises(ValueError, match="PAUSED_ADMISSIONS"):
        journal.admit(authority, sample(), utc(), 0)
    with pytest.raises(ValueError, match="NO_AUTO_UNPAUSE"):
        journal.resume()
    assert journal.rows()[0]["state"] == "BACKED_UP"
    assert all(r["state"] == "PLANNED" for r in journal.rows()[1:])
