"""Finite storage qualification, using artificial records rather than main inputs."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from research.execution_setup.core import immutable, load

spec = importlib.util.spec_from_file_location("storage_v2", Path(__file__).with_name("runner.py"))
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def ledger(root: Path, count: int = 76) -> Any:
    value = module.ArchiveLedger(root)
    with value.connect() as conn:
        conn.executemany(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) "
            "VALUES (?,?,'B3','PLANNED',1,'STORAGE_CALIBRATION_ONLY')",
            [(i, f"cal-storage-v2-{i}") for i in range(1, count + 1)],
        )
    return value


def test_incremental_objects_not_cumulative_raw_archive(tmp_path: Path) -> None:
    value = ledger(tmp_path / "live")
    folders = []
    for index in range(1, 4):
        path = value.root / f"calibration-only-{index}.json"
        immutable(path, {"payload": "x" * 65536, "index": index})
        value.seal(path)
        value.event("STORAGE_RECORD", index=index)
        with value.connect() as conn:
            conn.execute(
                "UPDATE slots SET state='EXPORTED',execution_id=? WHERE sequence=?",
                (f"cal-storage-execution-{index}", index),
            )
        folders.append(value.backup(tmp_path / "archive"))
    assert len(list((tmp_path / "archive/objects-v2").glob("*.gz"))) == 3
    assert all(not load(folder / "backup-manifest.json")["full_checkpoint"] for folder in folders)
    assert [len(load(folder / "ledger-delta.json")["objects"]) for folder in folders] == [1, 1, 1]
    value.full_verify()


def test_corrupt_object_stops_and_original_remains(tmp_path: Path) -> None:
    value = ledger(tmp_path / "live")
    path = value.root / "same.json"
    immutable(path, {"data": "keep"})
    value.seal(path)
    value.backup(tmp_path / "archive")
    blob = next((tmp_path / "archive/objects-v2").glob("*.gz"))
    blob.write_bytes(b"corrupt")
    # Same bytes registered under a new name force validation of the reused object.
    other = value.root / "same-new-path.json"
    other.write_bytes(path.read_bytes())
    value.seal(other)
    with pytest.raises((OSError, ValueError)):
        value.backup(tmp_path / "archive")
    assert load(path) == {"data": "keep"}
    assert len(list((tmp_path / "archive").glob("incremental-v2-*"))) == 2


def test_full_audit_detects_historical_drift(tmp_path: Path) -> None:
    value = ledger(tmp_path / "live")
    path = value.root / "executions/cal-storage-execution-1/export.json"
    immutable(path, {"status": "FAILED"})
    value.seal(path)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="HASH_DRIFT"):
        value.full_verify()


def test_final_checkpoint_snapshot_restores(tmp_path: Path) -> None:
    value = ledger(tmp_path / "live", 1)
    with value.connect() as conn:
        conn.execute("UPDATE slots SET state='EXPORTED',execution_id='cal-storage-final'")
    folder = value.backup(tmp_path / "archive")
    assert load(folder / "backup-manifest.json")["full_checkpoint"]
    restored = module.ArchiveLedger(folder)
    assert restored.rows() == value.rows()
    restored.full_verify()
