"""Six fast boundary/snapshot controls; no imports of application or research drivers."""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from closed145 import check_rows, read, snapshot

HERE = Path(__file__).resolve().parent


def saved() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = read(HERE / "closed-145/read-only-ledger.json")["rows"]
    return rows


def test_exact_boundary() -> None:
    rows = saved()
    check_rows(rows, rows)


@pytest.mark.parametrize("change", ["identity", "backup", "active", "attempt"])
def test_changed_or_active_boundary_rejected(change: str) -> None:
    original = saved()
    rows = copy.deepcopy(original)
    if change == "identity":
        rows[145]["execution_id"] = rows[144]["execution_id"]
    elif change == "backup":
        rows[144]["backup_hash"] = None
    elif change == "active":
        rows[145]["state"] = "RUNNING"
    else:
        rows[145]["attempt"] = 2
    with pytest.raises(ValueError):
        check_rows(rows, original)


def test_consistent_snapshot_and_real_chain_corruption(tmp_path: Path) -> None:
    path = tmp_path / "cal-closed145-ledger.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE notices(n INTEGER,body TEXT,previous TEXT,hash TEXT)")
        db.execute("CREATE TABLE slots(sequence INTEGER,execution_id TEXT)")
        body = json.dumps({"kind": "CALIBRATION_ONLY"})
        digest = hashlib.sha256((body + "GENESIS").encode()).hexdigest()
        db.execute("INSERT INTO notices VALUES(1,?,?,?)", (body, "GENESIS", digest))
        db.execute("INSERT INTO slots VALUES(1,'cal-snapshot-only')")
    rows, notices = snapshot(path)
    assert rows == [{"sequence": 1, "execution_id": "cal-snapshot-only"}]
    assert notices == [{"kind": "CALIBRATION_ONLY"}]
    with sqlite3.connect(path) as db:
        db.execute("UPDATE notices SET hash='corrupt'")
    with pytest.raises(ValueError, match="NOTICE_CHAIN_CORRUPTION"):
        snapshot(path)
