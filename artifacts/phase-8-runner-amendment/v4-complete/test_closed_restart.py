from __future__ import annotations

import copy
import sqlite3
from pathlib import Path

import pytest
from closed_restart import HERE, NEXT, boundary, master_check, stage, verify
from controls import Journal, hash_file, read

MASTER = HERE / "closed-82"


def test_closed82_stage_preserves_all_identities_notices_and_sidecars(tmp_path: Path) -> None:
    from handover import verify_imported_first

    root = tmp_path / "cal-closed82"
    result = stage(MASTER, root)
    verify_imported_first(root)
    assert result["driver_calls"] == 0 and result["planned"] == 1418
    rows = Journal(root).rows()
    assert rows[82]["execution_id"] == NEXT and rows[82]["state"] == "PLANNED"
    assert hash_file(root / "historical-evidence.tar.gz") == hash_file(
        MASTER / "historical-evidence.tar.gz"
    )
    assert read(root / "run.json")["policy"] == read(MASTER / "run.json")["policy"]
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    assert (root / "restart-history/pause.json").read_bytes() == (
        MASTER / "pause.json"
    ).read_bytes()


@pytest.mark.parametrize("alteration", ["active", "identity", "backup"])
def test_closed82_rejects_changed_boundary(alteration: str) -> None:
    rows = copy.deepcopy(read(MASTER / "ledger-read-only.json")["rows"])
    saved = read(MASTER / "ledger-read-only.json")["rows"]
    if alteration == "active":
        rows[82]["state"] = "RUNNING"
    elif alteration == "identity":
        rows[82]["execution_id"] = rows[83]["execution_id"]
    else:
        rows[81]["backup_hash"] = None
    with pytest.raises(ValueError):
        boundary(rows, saved)


def test_closed82_rejects_notice_and_receipt_drift(tmp_path: Path) -> None:
    root = tmp_path / "cal-closed82-drift"
    stage(MASTER, root)
    with sqlite3.connect(root / "campaign.sqlite3") as db:
        db.execute("UPDATE notices SET body='{}' WHERE n=1")
    with pytest.raises(ValueError):
        verify(root)
    root2 = tmp_path / "cal-closed82-receipt"
    stage(MASTER, root2)
    path = root2 / "backups" / (Journal(root2).rows()[81]["execution_id"] + ".json")
    path.write_text("{}")
    with pytest.raises(ValueError, match="BACKUP_RECEIPT_DRIFT"):
        verify(root2)


def test_closed82_requires_empty_destination(tmp_path: Path) -> None:
    master_check(MASTER)
    root = tmp_path / "cal-existing"
    root.mkdir()
    with pytest.raises(ValueError, match="FRESH_METADATA_ROOT_ONLY"):
        stage(MASTER, root)
