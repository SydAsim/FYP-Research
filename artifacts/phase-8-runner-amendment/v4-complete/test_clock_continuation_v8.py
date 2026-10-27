"""Eighteen finite offline controls; temporary metadata only, zero drivers."""

from __future__ import annotations

import copy
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import clock_sampling as clocks
import pytest
import runner
from closed_restart import HERE, NEXT, boundary, stage, verify
from controls import Journal, Policy, hash_file, read, write_new
from postflight import recover
from storage import OfflineCloud, final_backup, upload, verify_continuation_metadata

EPOCH = datetime(2026, 10, 7, 15, 24, 23, 810674, tzinfo=UTC)
POLICY = Policy.model_validate(read(HERE / "original-launch-policy.json"))


def reading(seconds: float, mono: float, width: float = 0) -> clocks.Sample:
    return clocks.Sample(EPOCH + timedelta(seconds=seconds), mono - width / 2, mono + width / 2)


def anchor() -> dict[str, Any]:
    return clocks.anchor_record(reading(0, 100), "cal-boot")


def clock_root(tmp: Path) -> Path:
    root = tmp / "cal-clock-v8"
    journal = Journal(root)
    write_new(root / "host-clock.json", anchor())
    journal.event("HOST_CLOCK_SEALED", hash=hash_file(root / "host-clock.json"))
    return root


def test_clock_01_bracket_order_and_midpoint() -> None:
    events: list[str] = []
    values = iter([100.0, 100.02])

    def mono() -> float:
        events.append("mono")
        return next(values)

    def wall() -> datetime:
        events.append("wall")
        return EPOCH

    got = clocks.sample(wall, mono)
    assert events == ["mono", "wall", "mono"] and got.midpoint == pytest.approx(100.01)
    assert got.record()["uncertainty_seconds"] == pytest.approx(0.01)


def test_clock_02_metadata_delay_precedes_pair(tmp_path: Path, monkeypatch: Any) -> None:
    root = clock_root(tmp_path)
    phases: list[str] = []
    real_read = runner.read

    def delayed_metadata(path: Path) -> Any:
        phases.append("metadata-done-after-eight-synthetic-seconds")
        return real_read(path)

    def paired() -> clocks.Sample:
        assert phases == ["metadata-done-after-eight-synthetic-seconds", "boot-done"]
        return reading(108, 208, 0.002)

    def boot() -> str:
        phases.append("boot-done")
        return "cal-boot"

    monkeypatch.setattr(runner, "read", delayed_metadata)
    monkeypatch.setattr(runner, "sample", paired)
    monkeypatch.setattr("research.execution_linux_v1.platform.boot_id", boot)
    runner.verify_clock(root, POLICY)


def test_clock_03_excess_uncertainty_stops() -> None:
    with pytest.raises(ValueError, match="CLOCK_SAMPLE_UNCERTAIN"):
        clocks.check(POLICY, anchor(), reading(10, 110, 0.051), "cal-boot")


def test_clock_04_negative_bracket_stops() -> None:
    with pytest.raises(ValueError, match="MONOTONIC_CLOCK_DRIFT"):
        clocks.quality(clocks.Sample(EPOCH, 101, 100))


def test_clock_05_nonfinite_stops() -> None:
    with pytest.raises(ValueError, match="CLOCK_SAMPLE_INVALID"):
        clocks.quality(clocks.Sample(EPOCH, float("nan"), 100))


def test_clock_06_exact_five_seconds_unchanged() -> None:
    clocks.check(POLICY, anchor(), reading(95, 200), "cal-boot")
    with pytest.raises(ValueError, match="WALL_CLOCK_BACKWARD"):
        clocks.check(POLICY, anchor(), reading(94.999999, 200), "cal-boot")


def test_clock_07_genuine_rollback_stops() -> None:
    with pytest.raises(ValueError, match="WALL_CLOCK_BACKWARD"):
        clocks.check(POLICY, anchor(), reading(94, 200), "cal-boot")


def test_clock_08_wrong_boot_stops() -> None:
    with pytest.raises(ValueError, match="HOST_REBOOT_UNQUALIFIED"):
        clocks.check(POLICY, anchor(), reading(100, 200), "other-boot")


def test_clock_09_counter_before_anchor_stops() -> None:
    with pytest.raises(ValueError, match="MONOTONIC_CLOCK_DRIFT"):
        clocks.check(POLICY, anchor(), reading(10, 99), "cal-boot")


def test_clock_10_absolute_deadline_unchanged() -> None:
    with pytest.raises(ValueError, match="HOST_360H_LIMIT"):
        clocks.check(POLICY, anchor(), reading(360 * 3600, 360 * 3600 + 100), "cal-boot")
    assert POLICY.stop_at.isoformat() == "2026-10-22T15:24:23.810674+00:00"


def test_clock_11_anchor_same_pair_and_quality() -> None:
    got = clocks.anchor_record(reading(0, 100, 0.002), "cal-boot")
    assert got["sampling_method"] == clocks.METHOD
    assert got["monotonic_before"] == 99.999 and got["monotonic_after"] == 100.001
    clocks.check(POLICY, got, reading(100, 200, 0.002), "cal-boot")
    with pytest.raises(ValueError, match="CLOCK_SAMPLE_UNCERTAIN"):
        clocks.anchor_record(reading(0, 100, 0.1), "cal-boot")
    with pytest.raises(ValueError, match="BRACKETED_BOOT_ANCHOR_REQUIRED"):
        clocks.check(
            POLICY,
            {k: got[k] for k in ("boot_id", "wall", "monotonic")},
            reading(100, 200),
            "cal-boot",
        )


def test_clock_12_rejection_actual_operands_durable(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    root = clock_root(tmp_path)
    monkeypatch.setattr(runner, "sample", lambda: reading(94, 200, 0.002))
    monkeypatch.setattr("research.execution_linux_v1.platform.boot_id", lambda: "cal-boot")
    with pytest.raises(ValueError, match="WALL_CLOCK_BACKWARD"):
        runner.verify_clock(root, POLICY)
    journal = Journal(root)
    journal.pause("WALL_CLOCK_BACKWARD_STOP_ADMISSIONS")
    journal.verify()
    with journal.connect() as db:
        notices = [json.loads(r[0]) for r in db.execute("SELECT body FROM notices ORDER BY n")]
    failure = next(n for n in notices if n["kind"] == "HOST_CLOCK_REJECTED")
    details = failure["measurement"]
    assert details["wall_elapsed_seconds"] == 94
    assert details["monotonic_elapsed_seconds"] == 100
    assert details["wall_minus_monotonic_seconds"] == -6
    assert details["comparison_rhs_seconds"] == 95
    assert details["sample"]["monotonic_before"] == 199.999
    assert details["combined_sampling_uncertainty_seconds"] == pytest.approx(0.001)
    assert read(root / "pause.json")["reason"] == failure["reason"]
    logged = json.loads(capsys.readouterr().out)
    assert logged["result"] == failure["reason"] and logged["anchor_sha256"] == hash_file(
        root / "host-clock.json"
    )


@pytest.fixture(scope="module")
def imported(tmp_path_factory: Any) -> Path:
    root = tmp_path_factory.mktemp("cal-v8-boundary") / "run"
    stage(HERE / "closed-120", root)
    return root


def test_boundary_01_exact_closed_handover(imported: Path) -> None:
    from handover import verify_imported_first

    verify_imported_first(imported)
    rows = Journal(imported).rows()
    assert (
        len(rows) == 1500
        and rows[:120] == read(HERE / "closed-120/ledger-read-only.json")["rows"][:120]
    )
    assert rows[120]["execution_id"] == NEXT and rows[120]["arm"] == "P1"
    assert sum(r["state"] == "PLANNED" for r in rows) == 1380
    assert read(imported / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    assert (
        read(imported / "restart-history/pause.json")["reason"]
        == "WALL_CLOCK_BACKWARD_STOP_ADMISSIONS"
    )


def test_boundary_02_altered_identity_rejected(imported: Path) -> None:
    rows = copy.deepcopy(Journal(imported).rows())
    rows[120]["attempt"] = 2
    with pytest.raises(ValueError, match="IDENTITY_OR_ORDER_DRIFT"):
        boundary(rows, read(HERE / "closed-120/ledger-read-only.json")["rows"])


def test_boundary_03_active_pending_rejected(imported: Path) -> None:
    rows = copy.deepcopy(Journal(imported).rows())
    rows[120]["state"] = "RUNNING"
    with pytest.raises(ValueError, match="ACTIVE_OR_CHANGED_SLOT"):
        boundary(rows, read(HERE / "closed-120/ledger-read-only.json")["rows"])


def test_boundary_04_incomplete_receipt_rejected(imported: Path) -> None:
    path = imported / "backups" / (Journal(imported).rows()[119]["execution_id"] + ".json")
    original = path.read_bytes()
    try:
        path.write_text("{}")
        with pytest.raises(ValueError, match="BACKUP_RECEIPT_DRIFT"):
            verify(imported)
    finally:
        path.write_bytes(original)


def backup_test(imported: Path, tmp: Path, complete: bool) -> Path:
    root = tmp / "cal-v8-backup"
    shutil.copytree(imported, root)
    # Existing *historical* v7 records test copying only. No signature is issued
    # and no authority verifier/admission is bypassed or invoked as successful.
    shutil.copyfile(HERE / "closed-120/host-clock.json", root / "host-clock.json")
    receipts = tmp / "historical-public"
    shutil.copytree(HERE / "closed-120/public-authority", receipts)
    if complete:
        shutil.copyfile(
            HERE / "closed-120/continuation-readiness.json", root / "continuation-readiness.json"
        )
    else:
        (receipts / "continuation/CONTINUATION_LAUNCH.json").unlink()
    config = read(root / "run.json")
    config["receipts"] = str(receipts / "original")
    config["continuation"]["receipts"] = str(receipts / "continuation")
    (root / "run.json").write_text(json.dumps(config))
    archive = final_backup(Journal(root), tmp / "backup", prelaunch=not complete)
    from handover import ContinuationPolicy

    cloud = OfflineCloud(tmp / "independent-stored-copy")
    proof = upload(
        Journal(root), cloud, ContinuationPolicy.model_validate(config["policy"]), archive
    )
    cloud.verify(proof)
    recovered = (
        recover(proof, tmp / "readback", local_archive=cloud.root / proof.version_id) / "slot"
    )
    verify_continuation_metadata(recovered)
    assert Journal(recovered).rows() == Journal(imported).rows()
    assert len(list((recovered / "backups").glob("*.json"))) == 120
    write_new(
        tmp / "roundtrip.json",
        {
            "status": "PASS",
            "phase": "COMPLETE" if complete else "PRELAUNCH",
            "bytes": archive.stat().st_size,
            "sha256": hash_file(archive),
            "BACKED_UP": 120,
            "PLANNED": 1380,
            "driver_calls": 0,
            "historical_records_not_launch_authority": True,
        },
    )
    return recovered


def test_boundary_05_prelaunch_backup_roundtrip(imported: Path, tmp_path: Path) -> None:
    root = backup_test(imported, tmp_path, False)
    assert not (root / "continuation-readiness.json").exists()
    original = (root / "restart-boundary.json").read_bytes()
    (root / "restart-boundary.json").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_continuation_metadata(root)
    (root / "restart-boundary.json").write_bytes(original)
    verify_continuation_metadata(root)


def test_boundary_06_complete_backup_roundtrip(imported: Path, tmp_path: Path) -> None:
    root = backup_test(imported, tmp_path, True)
    assert read(root / "continuation-backup.json")["phase"] == "COMPLETE"
    path = root / "restart-history/pause.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="METADATA_DRIFT"):
        verify_continuation_metadata(root)
