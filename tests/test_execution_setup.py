"""Recovery and integrity tests exercise observable failure modes, not timing sleeps."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from research.arms import Arm
from research.execution_setup.cli import diagnostic
from research.execution_setup.core import PREFIX, ROOT, Ledger, check_inventory, immutable, load
from research.execution_setup.resources import GIB, admission
from research.execution_setup.runtime import Runtime
from research.execution_setup.timing import paired_latency, timing_report
from research.execution_setup.worker import Trial, fixed_deadline, recover_trial
from research.study.models import AnalysisRow, StudyCase


def case(index: int = 1) -> StudyCase:
    bank = load(ROOT / "research/fixtures/phase8_design_v4/inputs.json")
    item = next(c for c in bank["calibration_inputs"] if c["stratum"] == "CLEAN")
    return StudyCase.model_validate({**item, "case_id": f"{PREFIX}{index:04d}"})


def planned(root: Path) -> Ledger:
    ledger = Ledger(root)
    with ledger.connect() as conn:
        conn.execute(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) "
            "VALUES (1,?,'B3','PLANNED',1,'ORIGINAL_PLANNED')",
            (case().case_id,),
        )
    return ledger


def test_same_execution_and_original_deadline(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    first = ledger.admit()
    assert first is not None
    ledger.update(first["execution_id"], deadline="2030-01-01T00:10:00+00:00", state="CHECKPOINTED")
    resumed = ledger.admit()
    assert resumed is not None and resumed["execution_id"] == first["execution_id"]
    with pytest.raises(ValueError, match="deadline"):
        ledger.update(first["execution_id"], deadline="2030-01-01T00:20:00+00:00")


def test_no_main_admission(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    with ledger.connect() as conn:
        conn.execute("UPDATE slots SET case_id='p8v4-0001'")
    with pytest.raises(ValueError, match="MAIN_CAMPAIGN_GUARD"):
        ledger.admit()
    assert ledger.rows()[0]["execution_id"] is None


def test_original_retained_diagnostic_separate(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    first = ledger.admit()
    assert first
    ledger.update(first["execution_id"], state="EXPORTED", export_hash="failed-original")
    diagnostic(tmp_path, first["execution_id"])
    rows = ledger.rows()
    assert rows[0]["export_hash"] == "failed-original"
    assert rows[1]["label"] == "DIAGNOSTIC_RERUN" and rows[1]["attempt"] == 2
    assert rows[1]["original_id"] == first["execution_id"]
    with pytest.raises(ValueError, match="cannot be replaced"):
        ledger.update(first["execution_id"], state="RUNNING")


def test_export_tamper_and_immutable_collision(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path)
    path = tmp_path / "export.json"
    immutable(path, {"failure": "retained"})
    ledger.seal(path)
    with pytest.raises(FileExistsError):
        immutable(path, {"success": True})
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="HASH_DRIFT"):
        ledger.verify()


def test_event_chain_tamper(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path)
    ledger.event("FAILURE", detail="keep me")
    with ledger.connect() as conn:
        conn.execute("UPDATE events SET body='{}'")
    with pytest.raises(ValueError, match="LEDGER_HASH_DRIFT"):
        ledger.verify()


def test_backup_hashes_and_sqlite_snapshot(tmp_path: Path) -> None:
    ledger = planned(tmp_path / "live")
    immutable(ledger.root / "trace.json", {"ack": "missing"})
    ledger.seal(ledger.root / "trace.json")
    ledger.event("TEST")
    backup = ledger.backup(tmp_path / "separate")
    check_inventory(load(backup / "backup-manifest.json")["hashes"], backup)
    restored = Ledger(backup)
    restored.verify()
    assert restored.rows() == ledger.rows()


def test_source_drift_rejected(tmp_path: Path) -> None:
    file = tmp_path / "contract.json"
    file.write_text("original", encoding="utf-8")
    import hashlib

    inventory = {file.name: hashlib.sha256(file.read_bytes()).hexdigest()}
    file.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="HASH_DRIFT"):
        check_inventory(inventory, tmp_path)


def test_checkpoint_transaction_survives_missing_convenience_file(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    slot = ledger.admit()
    assert slot
    ledger.checkpoint(slot["execution_id"], {"issued_request": "original", "deadline": "fixed"})
    assert not (tmp_path / "checkpoint.json").exists()
    assert ledger.recover_checkpoint(slot["execution_id"])["deadline"] == "fixed"
    ledger.verify()


def test_checkpoint_payload_tamper_stops_recovery(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    slot = ledger.admit()
    assert slot
    ledger.checkpoint(slot["execution_id"], {"issued_request": "original"})
    with ledger.connect() as conn:
        conn.execute("UPDATE checkpoints SET body='{}'")
    with pytest.raises(ValueError, match="CHECKPOINT_HASH_DRIFT"):
        ledger.verify()


def test_missing_final_anchor_grades_unknown_using_revised_instrument() -> None:
    from research.execution_setup.worker import evidence_for
    from research.study_v4.oracle import revised_evaluate

    qualification = load(ROOT / "artifacts/phase-8-study-design/v4/calibration-qualification.json")
    trace = load(ROOT / qualification["all_attempts"][0]["path"])
    trace["attempt"] = 1
    trace["external_requests"] = []
    c, evidence = evidence_for(trace)
    grade, timing = revised_evaluate(c, evidence, challenge_at=None)
    assert grade["values"]["unsupported_exposed_claim"] in ("TRUE", "UNKNOWN")
    assert timing.duration_seconds is None and timing.censor_reason == "MISSING_EXTERNAL_ANCHOR"


def test_missing_final_anchor_not_invented() -> None:
    start = datetime.now(UTC)
    deadline, missing = fixed_deadline({"started_at": start.isoformat()})
    assert missing and datetime.fromisoformat(deadline) == start + timedelta(seconds=600)
    kept = {"started_at": start.isoformat(), "original_deadline": deadline}
    assert fixed_deadline(kept)[0] == deadline


def test_interrupted_driver_resume_does_not_reissue(tmp_path: Path) -> None:
    ledger = planned(tmp_path)
    slot = ledger.admit()
    assert slot
    runtime = Mock(spec=Runtime)
    trial = Trial(runtime, case(), slot, ledger)
    resumed = recover_trial(runtime, slot, ledger)
    assert resumed.id == trial.id and resumed.row["failure"]["type"] == "INTERRUPTED_DRIVER"
    runtime.start_all.assert_not_called()
    runtime.restart_worker.assert_not_called()


def test_request_anchor_persisted_before_transport_failure(
    tmp_path: Path, monkeypatch: Any
) -> None:
    ledger = planned(tmp_path)
    slot = ledger.admit()
    assert slot
    trial = Trial(Mock(spec=Runtime), case(), slot, ledger)
    from research.study_v4.calibration import CalibrationTrial

    def fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        saved = load(trial.path)
        assert saved["external_requests"][0]["command_id"] == "original-command"
        assert ledger.rows()[0]["deadline"] == saved["original_deadline"]
        raise TimeoutError("Ambiguous transport")

    monkeypatch.setattr(CalibrationTrial, "request", fail)
    with pytest.raises(TimeoutError):
        trial.request(
            "http://127.0.0.1",
            "POST",
            "/v1/workflows/example/revisions",
            {"expected_revision": 0, "command_id": "original-command"},
        )


@pytest.mark.parametrize("concurrency,available,system", [(2, 2, 20), (1, 1, 20), (1, 4, 4)])
def test_resource_guards(concurrency: int, available: int, system: int) -> None:
    with pytest.raises(RuntimeError, match="RESOURCE_STOP"):
        admission(
            {
                "available_memory_bytes": available * GIB,
                "system_free_bytes": system * GIB,
                "output_free_bytes": 100 * GIB,
                "backup_free_bytes": 100 * GIB,
            },
            concurrent=concurrency,
        )


def row(
    c: StudyCase, arm: Arm, duration: float | None, observed: bool | None, attempt: int = 1
) -> AnalysisRow:
    return AnalysisRow(
        classification="VALIDATION_ONLY",
        case_id=c.case_id,
        cluster_id=c.cluster_id,
        generator_family=c.generator_family,
        stratum=c.stratum,
        member=c.member,
        cluster_representative=c.cluster_representative,
        arm=arm,
        attempt=attempt,
        execution_id=f"{c.case_id}:{arm}:{attempt}",
        values={},
        duration_seconds=duration,
        event_observed=observed,
        censor_reason=None if observed else "ADMINISTRATIVE_TIMEOUT",
        oracle_hash="test",
        phase=c.correction_barrier,
        fault=c.fault_label,
        revision_type="NONE",
        action_class="CREATE",
    )


def test_latency_input_clusters_not_recipe_labels() -> None:
    cases = [case(i) for i in range(1, 9)]
    # All have the SAME fixed recipe. Eight independently drawn inputs remain eight units.
    rows = [
        r
        for i, c in enumerate(cases)
        for r in (row(c, Arm.B3, 10 + i, True), row(c, Arm.P2, 9 + 2 * i, True))
    ]
    result = paired_latency(cases, rows, repetitions=200)
    assert result["planned_inputs"] == 8
    assert result["interval_95"][0] < result["interval_95"][1]
    assert result == paired_latency(cases, list(reversed(rows)), repetitions=200)


def test_latency_censor_not_completion_missing_not_zero_rerun_not_replacement() -> None:
    c = case()
    rows = [row(c, Arm.B3, 10, True), row(c, Arm.P2, 600, False), row(c, Arm.P2, 1, True, 2)]
    result = paired_latency([c], rows, repetitions=10)
    assert result["restricted_mean_difference_seconds"] == 590
    assert result["censored_arm_records"] == 1
    missing = paired_latency([c], [row(c, Arm.B3, 10, True), row(c, Arm.P2, None, None)])
    assert missing["interval_95"] is None and missing["missing_input_ids"] == [c.case_id]
    early = paired_latency([c], [row(c, Arm.B3, 10, True), row(c, Arm.P2, 40, False)])
    assert early["interval_95"] is None


def test_aft_pipeline_and_campaign_guard() -> None:
    cases = [case(i) for i in range(1, 25)]
    rows = [
        row(c, arm, float(10 + i % 7 + j * 2 + (i * j) % 3), True)
        for i, c in enumerate(cases)
        for j, arm in enumerate((Arm.B3, Arm.P1, Arm.P2))
    ]
    result = timing_report(cases, rows, repetitions=20, aft_repetitions=8)
    assert result["aft"]["status"] == "CONVERGED"
    assert result["aft_input_cluster_bootstrap"]["completed_draws"] == 8
    with pytest.raises(ValueError, match="Main analysis"):
        timing_report(cases, [rows[0].model_copy(update={"classification": "CAMPAIGN"})])
