"""Twelve metadata-only controls. Historical records are never live authorization."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from closed_restart import HERE, NEXT, stage
from controls import Journal, hash_file, read, write_new
from postflight import recover
from storage import OfflineCloud, final_backup, make_backup, upload, verify_continuation_metadata


def metadata(tmp: Path, *, complete: bool = False) -> Path:
    root = tmp / "cal-metadata"
    stage(HERE / "closed-82", root)
    shutil.copyfile(HERE / "closed-82/host-clock.json", root / "host-clock.json")
    receipts = tmp / "historical-public-only"
    shutil.copytree(HERE / "backup-calibration-public", receipts)
    if not complete:
        (receipts / "continuation/CONTINUATION_LAUNCH.json").unlink()
    else:
        # Genuine *historical* readiness, retained byte for byte for closure tests.
        # It cannot authorize this candidate or host. No new readiness is invented.
        shutil.copyfile(
            HERE / "boundary/continuation-readiness.json", root / "continuation-readiness.json"
        )
    config = read(root / "run.json")
    config["receipts"] = str(receipts / "original")
    config["continuation"]["receipts"] = str(receipts / "continuation")
    (root / "run.json").write_text(json.dumps(config))
    (root / "binding-seal.json").write_text(
        json.dumps(
            {"run": hash_file(root / "run.json"), "bindings": hash_file(root / "bindings.json")}
        )
    )
    write_new(
        tmp / "CALIBRATION-ONLY.json",
        {
            "kind": "TEMPORARY_METADATA_NOT_CAMPAIGN_AUTHORIZATION",
            "historical_receipts_not_applicable": True,
            "drivers": 0,
        },
    )
    return root


def roundtrip(root: Path, archive: Path, out: Path) -> Path:
    from handover import ContinuationPolicy

    cloud = OfflineCloud(out / "offline-versioned-copy")
    proof = upload(
        Journal(root),
        cloud,
        ContinuationPolicy.model_validate(read(root / "run.json")["policy"]),
        archive,
    )
    cloud.verify(proof)
    # Actual independent readback consumes the surrogate's stored object, not source archive.
    recovered = recover(proof, out / "readback", local_archive=cloud.root / proof.version_id)
    target = recovered / "slot"
    if (target / "master").exists():
        target = target / "master"
    verify_continuation_metadata(target)
    assert Journal(target).rows() == Journal(root).rows()
    assert len(list((target / "backups").glob("*.json"))) == 82
    assert Journal(target).rows()[82]["execution_id"] == NEXT
    write_new(
        out / "roundtrip.json",
        {
            "status": "PASS",
            "archive_sha256": hash_file(archive),
            "cloud": proof.model_dump(),
            "phase": read(target / "continuation-backup.json")["phase"],
            "BACKED_UP": 82,
            "PLANNED": 1418,
            "drivers": 0,
        },
    )
    return target


def test_prelaunch_roundtrip_without_readiness_or_launch(tmp_path: Path) -> None:
    root = metadata(tmp_path)
    before = Journal(root).rows()
    archive = final_backup(Journal(root), tmp_path / "backup", prelaunch=True)
    recovered = roundtrip(root, archive, tmp_path / "proof")
    assert not (recovered / "continuation-readiness.json").exists()
    assert not (recovered / "public-authority/continuation/CONTINUATION_LAUNCH.json").exists()
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    assert Journal(root).rows() == before


def test_complete_master_roundtrip(tmp_path: Path) -> None:
    root = metadata(tmp_path, complete=True)
    archive = final_backup(Journal(root), tmp_path / "backup")
    recovered = roundtrip(root, archive, tmp_path / "proof")
    assert read(recovered / "continuation-backup.json")["phase"] == "COMPLETE"
    assert (recovered / "continuation-readiness.json").read_bytes() == (
        root / "continuation-readiness.json"
    ).read_bytes()


def test_complete_per_slot_roundtrip(tmp_path: Path) -> None:
    from research.execution_setup.core import Ledger

    root = metadata(tmp_path, complete=True)
    slot = root / "slots/cal-backup-closure"
    Ledger(slot)
    for name in ("qualification-plan.json", "resources.json", "source-seal.json", "config.json"):
        write_new(slot / name, {"kind": "CALIBRATION_METADATA_ONLY"})
    archive = make_backup(slot, tmp_path / "backup", dumps=False)
    roundtrip(root, archive, tmp_path / "proof")


@pytest.mark.parametrize("name", ["restart-boundary.json", "restart-history/summary.json"])
def test_missing_required_restart_metadata_rejected(tmp_path: Path, name: str) -> None:
    root = metadata(tmp_path)
    archive = final_backup(Journal(root), tmp_path / "backup", prelaunch=True)
    recovered = roundtrip(root, archive, tmp_path / "proof")
    (recovered / name).unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_continuation_metadata(recovered)


def test_corrupt_required_history_rejected(tmp_path: Path) -> None:
    root = metadata(tmp_path)
    archive = final_backup(Journal(root), tmp_path / "backup", prelaunch=True)
    recovered = roundtrip(root, archive, tmp_path / "proof")
    (recovered / "restart-history/summary.json").write_text("{}")
    with pytest.raises(ValueError, match="METADATA_DRIFT"):
        verify_continuation_metadata(recovered)


@pytest.mark.parametrize("name", ["continuation-readiness.json", "CONTINUATION_LAUNCH.json"])
def test_normal_backup_rejects_missing_late_metadata(tmp_path: Path, name: str) -> None:
    root = metadata(tmp_path, complete=True)
    target = (
        root / name
        if name == "continuation-readiness.json"
        else Path(read(root / "run.json")["continuation"]["receipts"]) / name
    )
    target.unlink()
    with pytest.raises(FileNotFoundError):
        final_backup(Journal(root), tmp_path / "failed-backup")
    assert list((tmp_path / "failed-backup").glob("final-*"))  # partial retained
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"


def test_prelaunch_rejects_existing_late_records(tmp_path: Path) -> None:
    root = metadata(tmp_path, complete=True)
    with pytest.raises(ValueError, match="MUST_PRECEDE_READINESS_AND_LAUNCH"):
        final_backup(Journal(root), tmp_path / "failed-backup", prelaunch=True)


def test_corrupt_archive_readback_retains_failure(tmp_path: Path) -> None:
    from storage import ObjectProof

    root = metadata(tmp_path)
    archive = final_backup(Journal(root), tmp_path / "backup", prelaunch=True)
    proof = ObjectProof(
        bucket="offline-calibration",
        key="calibration/test",
        version_id="test-version",
        sha256=hash_file(archive),
        bytes=archive.stat().st_size,
    )
    corrupt = tmp_path / "corrupted-copy.tar.gz"
    corrupt.write_bytes(archive.read_bytes()[:-20])
    with pytest.raises(ValueError, match="LOCAL_ARCHIVE_DRIFT"):
        recover(proof, tmp_path / "failed-readback", local_archive=corrupt)
    assert list((tmp_path / "failed-readback").glob("postflight-failure-*.json"))
    assert archive.is_file() and corrupt.is_file()


def test_authorization_failure_precedes_backup_or_readiness(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from handover import ContinuationAuthority
    from prelaunch_backup import run

    root = metadata(tmp_path)
    calls: list[bool] = []

    def deny(self: Any, at: Any = None, *, prelaunch: bool = False) -> str:
        calls.append(prelaunch)
        raise ValueError("MISSING_CALIBRATION_AUTHORIZATION")

    # Only a failing guard is stubbed; no test grants authority or releases a pause.
    monkeypatch.setattr(ContinuationAuthority, "verify", deny)
    with pytest.raises(ValueError, match="MISSING_CALIBRATION_AUTHORIZATION"):
        run(root, tmp_path / "never-created", "prelaunch", OfflineCloud(tmp_path / "offline"))
    assert calls == [True] and not (tmp_path / "never-created").exists()
    assert not (root / "continuation-readiness.json").exists()
    assert not (root / "prelaunch-backup-proof.json").exists()


def test_private_signer_never_copied(tmp_path: Path) -> None:
    root = metadata(tmp_path)
    receipts = Path(read(root / "run.json")["continuation"]["receipts"])
    (receipts / "owner.key").write_bytes(b"CALIBRATION_SENTINEL_NOT_A_SIGNING_KEY")
    archive = final_backup(Journal(root), tmp_path / "backup", prelaunch=True)
    recovered = roundtrip(root, archive, tmp_path / "proof")
    assert not list(recovered.rglob("owner.key"))
    (recovered / "handover.json").unlink()
    with pytest.raises(ValueError, match="REQUIRED_METADATA_MISSING"):
        verify_continuation_metadata(recovered)
