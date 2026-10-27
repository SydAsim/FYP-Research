"""Fourteen bounded metadata checks; no drivers or application state restoration."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import pytest
from closed_prefix import COUNT, HERE, NEXT, archive_proof, boundary, imported, stage, verify
from controls import Journal, hash_file, read
from handover import ContinuationReceipt
from imported_analysis import imported_row
from pydantic import ValidationError


@pytest.fixture(scope="session")
def staged(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("cal-v4-metadata") / "import"
    stage(HERE / "boundary", root)
    return root


def clone(staged: Path, target: Path) -> Path:
    target.mkdir()
    for name in (
        "campaign.sqlite3",
        "saved-identities.json",
        "handover.json",
        "historical-evidence.tar.gz",
        "run.json",
        "bindings.json",
        "binding-seal.json",
        "cloud.json",
        "pause.json",
    ):
        shutil.copyfile(staged / name, target / name)
    shutil.copytree(staged / "backups", target / "backups")
    return target


def test_actual_import_packed_recovery_and_preserved_analysis(staged: Path, tmp_path: Path) -> None:
    root = clone(staged, tmp_path / "recovered")
    verify(root)
    rows = Journal(root).rows()
    assert len(rows) == 1500
    assert sum(r["state"] == "BACKED_UP" for r in rows) == 38
    assert sum(r["state"] == "PLANNED" for r in rows) == 1462
    assert rows[38]["execution_id"] == NEXT and rows[38]["arm"] == "B3"
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    for slot in rows[:COUNT]:
        row, provenance = imported_row(root, slot["execution_id"])
        trace = read(
            root / "historical/boundary/exports" / f"{slot['sequence']:04d}" / "export.json"
        )
        assert row.execution_id == slot["execution_id"]
        assert provenance["export_hash"] == hash_file(
            root / "historical/boundary/exports" / f"{slot['sequence']:04d}" / "export.json"
        )
        assert provenance["replacement_or_driver_replay"] is False
        if slot["sequence"] > 2:
            assert row.model_dump(mode="json") == trace["analysis_row"]
        else:
            assert trace["status"] == "FAILED"


@pytest.mark.parametrize("field", ["execution_id", "attempt", "sequence"])
def test_reject_changed_identities(field: str) -> None:
    saved = read(HERE / "saved-boundary.json")["rows"]
    rows = copy.deepcopy(saved)
    rows[38][field] = "altered" if field == "execution_id" else 99
    with pytest.raises(ValueError, match="IDENTITY_ORDER_OR_ATTEMPT"):
        boundary(rows, saved)


@pytest.mark.parametrize("state", ["RUNNING", "EXPORTED"])
def test_reject_active_slot_import(state: str) -> None:
    saved = read(HERE / "saved-boundary.json")["rows"]
    rows = copy.deepcopy(saved)
    rows[38]["state"] = state
    with pytest.raises(ValueError, match="ACTIVE_OR_CHANGED_SLOT"):
        boundary(rows, saved)


def test_missing_complete_backup(tmp_path: Path) -> None:
    proof = copy.deepcopy(read(HERE / "retained-slot-proofs.json")[2])
    proof["archive"] = str(tmp_path / "absent.tar.gz")
    with pytest.raises(FileNotFoundError):
        archive_proof(HERE / "boundary", proof)


def test_missing_postgres_dump_is_rejected(tmp_path: Path) -> None:
    proof = copy.deepcopy(read(HERE / "retained-slot-proofs.json")[2])
    manifest = {"postgres_dumps": True, "files": {"setup_app.sql.gz": "0" * 64}}
    raw = json.dumps(manifest).encode()
    member = tmp_path / "manifest.json"
    member.write_bytes(raw)
    archive = tmp_path / "incomplete.tar.gz"
    with tarfile.open(archive, "x:gz") as target:
        target.add(member, arcname="slot/manifest.json")
    proof.update(
        archive=str(archive),
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        members=manifest["files"],
    )
    proof["cloud"].update(bytes=archive.stat().st_size, sha256=hash_file(archive))
    master = tmp_path / "master"
    receipt_file = master / "backups" / (proof["identity"]["execution_id"] + ".json")
    receipt_file.parent.mkdir(parents=True)
    receipt_file.write_text(
        json.dumps(
            {
                "execution_id": proof["identity"]["execution_id"],
                "cloud": proof["cloud"],
                "sha256": proof["cloud"]["sha256"],
            }
        )
    )
    proof["receipt_sha256"] = hash_file(receipt_file)
    with pytest.raises(ValueError, match="INCOMPLETE_POSTGRES_BACKUP"):
        archive_proof(master, proof)


def test_altered_export_is_rejected(tmp_path: Path) -> None:
    from closed_prefix import verify_master

    master = tmp_path / "boundary"
    shutil.copytree(HERE / "boundary", master)
    (master / "exports/0038/export.json").write_text("{}")
    with pytest.raises(ValueError, match="AUTHORITATIVE_BOUNDARY_MEMBER_DRIFT"):
        verify_master(master)


def test_historical_notice_corruption_is_rejected(staged: Path, tmp_path: Path) -> None:
    root = clone(staged, tmp_path / "notice")
    with Journal(root).connect() as db:
        db.execute("UPDATE notices SET body='corrupted' WHERE n=1")
    with pytest.raises(ValueError, match="IMPORTED_LEDGER_CHAIN_DRIFT"):
        verify(root)


def test_altered_backup_receipt_is_rejected(staged: Path, tmp_path: Path) -> None:
    root = clone(staged, tmp_path / "receipt")
    (root / "backups" / (NEXT + ".json")).write_text("{}")
    first = read(HERE / "retained-slot-proofs.json")[0]["identity"]["execution_id"]
    (root / "backups" / (first + ".json")).write_text("{}")
    with pytest.raises(ValueError, match="IMPORTED_BACKUP_DRIFT"):
        verify(root)


def test_later_closed_slot_preserves_imported_prefix(staged: Path, tmp_path: Path) -> None:
    root = clone(staged, tmp_path / "later")
    journal = Journal(root)
    # Synthetic metadata on a disposable copy; no runner admission or driver.
    # PLANNED -> RUNNING belongs to admission, not Journal.update.
    with journal.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE slots SET state='RUNNING' WHERE execution_id=?", (NEXT,))
        journal.event_in(
            db, "ADMITTED", execution_id=NEXT, state="RUNNING", deadline=None, backup_hash=None
        )
    journal.update(NEXT, deadline="2026-10-08T23:00:00+00:00")
    journal.update(NEXT, state="EXPORTED")
    journal.update(NEXT, state="BACKED_UP", backup_hash="f" * 64)
    journal.verify()
    verify(root)
    assert journal.rows()[38]["state"] == "BACKED_UP"


def test_retirement_eligibility_uses_only_reviewed_imports(staged: Path) -> None:
    rows = Journal(staged).rows()
    assert all(imported(staged, r["execution_id"]) for r in rows[:38])
    assert not imported(staged, NEXT)
    assert not imported(staged, "unknown")


def test_parent_v3_receipt_cannot_authorize_v4() -> None:
    # Pinned public receipt is historical evidence, never a new authorization.
    raw: dict[str, Any] = read(HERE / "parent-provenance/CONTINUATION_ACCEPTED.json")
    with pytest.raises(ValidationError):
        ContinuationReceipt.model_validate(raw)
