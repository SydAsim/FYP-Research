"""Fifteen SQLite-only controls: coherent read snapshots and unchanged rejection."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sqlite3
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Literal, cast

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import controls as amended  # noqa: E402

spec = importlib.util.spec_from_file_location("legacy_controls_v3", HERE.parent / "v3/controls.py")
assert spec is not None and spec.loader is not None
legacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = legacy
spec.loader.exec_module(legacy)
LegacyJournal = cast(type[amended.Journal], legacy.Journal)
EXECUTION = "sqlite-control-original-01"
DEADLINE = "2026-10-08T13:45:53.962738+00:00"
Boundary = Literal["deadline", "backup"]


def seed(root: Path, kind: Boundary = "backup", mode: str = "WAL") -> amended.Journal:
    journal = amended.Journal(root)
    with journal.connect() as db:
        assert db.execute(f"PRAGMA journal_mode={mode}").fetchone()[0].upper() == mode
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "INSERT INTO slots VALUES(1,'sqlite-control','CONTROL',1,?,'fixture',"
            "'RUNNING',NULL,NULL,NULL)",
            (EXECUTION,),
        )
        journal.event_in(
            db,
            "ADMITTED",
            execution_id=EXECUTION,
            state="RUNNING",
            deadline=None,
            backup_hash=None,
        )
    if kind == "backup":
        journal.update(EXECUTION, state="EXPORTED", deadline=DEADLINE)
    return journal


def commit(journal: amended.Journal, kind: Boundary) -> None:
    if kind == "deadline":
        journal.update(EXECUTION, deadline=DEADLINE)
    else:
        journal.update(EXECUTION, state="BACKED_UP", backup_hash="a" * 64)


def install_boundary(
    reader: amended.Journal,
    monkeypatch: pytest.MonkeyPatch,
    writer: Callable[[], None],
) -> tuple[list[sqlite3.Connection], list[str]]:
    connections: list[sqlite3.Connection] = []
    events: list[str] = []

    def connect() -> sqlite3.Connection:
        db = sqlite3.connect(reader.path, timeout=0)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")

        def barrier(statement: str) -> None:
            if statement.startswith("SELECT * FROM slots WHERE") and not events:
                events.append("NOTICES_READ_BEFORE_SLOT_QUERY")
                try:
                    writer()
                    events.append("WRITER_COMMITTED")
                except sqlite3.OperationalError as error:
                    events.append(str(error))

        db.set_trace_callback(barrier)
        connections.append(db)
        return db

    monkeypatch.setattr(reader, "connect", connect)
    return connections, events


@pytest.mark.parametrize("kind", ["deadline", "backup"])
def test_legacy_false_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: Boundary
) -> None:
    writer = seed(tmp_path, kind, mode="DELETE" if kind == "backup" else "WAL")
    reader = LegacyJournal(tmp_path)
    connections, events = install_boundary(reader, monkeypatch, lambda: commit(writer, kind))
    with pytest.raises(ValueError, match="^LEDGER_TRANSITION_DRIFT$"):
        reader.verify()
    assert events == ["NOTICES_READ_BEFORE_SLOT_QUERY", "WRITER_COMMITTED"]
    for db in connections:
        db.close()
    # The same committed ledger is genuinely consistent when read without interleaving.
    LegacyJournal(tmp_path).verify()


@pytest.mark.parametrize("kind", ["deadline", "backup"])
def test_revised_consistent_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: Boundary
) -> None:
    writer = seed(tmp_path, kind)
    reader = amended.Journal(tmp_path)
    connections, events = install_boundary(reader, monkeypatch, lambda: commit(writer, kind))
    reader.verify()
    assert events == ["NOTICES_READ_BEFORE_SLOT_QUERY", "WRITER_COMMITTED"]
    assert all(not db.in_transaction for db in connections)
    for db in connections:
        db.close()
    amended.Journal(tmp_path).verify()
    row = amended.Journal(tmp_path).rows()[0]
    assert row["deadline"] == DEADLINE
    assert row["backup_hash"] == ("a" * 64 if kind == "backup" else None)


def test_rollback_journal_commit_waits_for_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = seed(tmp_path, mode="DELETE")
    reader = amended.Journal(tmp_path)

    def attempted_commit() -> None:
        with sqlite3.connect(writer.path, timeout=0) as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE slots SET state='BACKED_UP',backup_hash=?", ("a" * 64,))
            writer.event_in(
                db,
                "TRANSITION",
                execution_id=EXECUTION,
                state="BACKED_UP",
                deadline=DEADLINE,
                backup_hash="a" * 64,
            )

    connections, events = install_boundary(reader, monkeypatch, attempted_commit)
    reader.verify()
    assert events == ["NOTICES_READ_BEFORE_SLOT_QUERY", "database is locked"]
    assert writer.rows()[0]["state"] == "EXPORTED"
    for db in connections:
        db.close()
    commit(writer, "backup")
    amended.Journal(tmp_path).verify()


def test_valid_ledger(tmp_path: Path) -> None:
    seed(tmp_path).verify()


@pytest.mark.parametrize(
    "corruption", ["state", "deadline", "backup_hash", "notice_hash", "missing_notice", "file"]
)
def test_genuine_corruption_rejected(tmp_path: Path, corruption: str) -> None:
    journal = seed(tmp_path, mode="DELETE")
    commit(journal, "backup")
    if corruption == "file":
        journal.path.write_bytes(b"GENUINELY DAMAGED SQLITE HEADER")
        with pytest.raises(sqlite3.DatabaseError):
            amended.Journal(tmp_path).verify()
        return
    with journal.connect() as db:
        if corruption in {"state", "deadline", "backup_hash"}:
            db.execute(f"UPDATE slots SET {corruption}='corrupted'")
        elif corruption == "notice_hash":
            db.execute("UPDATE notices SET hash='corrupted' WHERE n=(SELECT max(n) FROM notices)")
        else:
            db.execute("DELETE FROM notices WHERE n=(SELECT max(n) FROM notices)")
    expected = "LEDGER_HASH_DRIFT" if corruption == "notice_hash" else "LEDGER_TRANSITION_DRIFT"
    with pytest.raises(ValueError, match=f"^{expected}$"):
        journal.verify()
    # A failing verifier also releases the read transaction rather than pinning a lock.
    with journal.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE slots SET error='control-observation'")


def test_uncommitted_write_not_visible(tmp_path: Path) -> None:
    journal = seed(tmp_path)
    db = journal.connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE slots SET state='corrupted'")
        amended.Journal(tmp_path).verify()
        db.rollback()
    finally:
        db.close()
    journal.verify()


def test_newly_committed_corruption_detected_next_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    writer = seed(tmp_path)
    reader = amended.Journal(tmp_path)

    def corrupt() -> None:
        with writer.connect() as db:
            db.execute("UPDATE slots SET state='corrupted'")

    connections, events = install_boundary(reader, monkeypatch, corrupt)
    reader.verify()  # Consistent snapshot preceding the genuinely corrupt commit.
    assert events == ["NOTICES_READ_BEFORE_SLOT_QUERY", "WRITER_COMMITTED"]
    for db in connections:
        db.close()
    with pytest.raises(ValueError, match="^LEDGER_TRANSITION_DRIFT$"):
        amended.Journal(tmp_path).verify()


def test_retained_boundary_on_disposable_copy(tmp_path: Path) -> None:
    source = Path("E:/FYP Project/p8-observation-20261008-1/x/inspection")
    original_hash = amended.hash_file(source / "campaign.sqlite3")
    shutil.copyfile(source / "campaign.sqlite3", tmp_path / "campaign.sqlite3")
    journal = amended.Journal(tmp_path)
    journal.verify()
    rows = journal.rows()
    assert Counter(r["state"] for r in rows) == {"BACKED_UP": 38, "PLANNED": 1462}
    assert len(rows) == 1500
    fields = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
    saved = amended.read(source / "saved-identities.json")["rows"]
    assert [tuple(r[k] for k in fields) for r in rows] == [
        tuple(r[k] for k in fields) for r in saved
    ]
    assert rows[38]["execution_id"] == "01a11705-11f0-73c0-af15-dd9f1d590b08"
    assert rows[38]["arm"] == "B3" and rows[38]["attempt"] == 1
    details = json.loads((source / "completed-details.json").read_text())
    assert len(details) == 38
    for item in details:
        export = source / "exports" / f"{item['sequence']:04d}" / "export.json"
        assert amended.hash_file(export) == item["export_sha256"]
    assert amended.hash_file(source / "campaign.sqlite3") == original_hash
