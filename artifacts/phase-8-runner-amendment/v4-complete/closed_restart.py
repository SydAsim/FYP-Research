"""Reviewed 120-original metadata continuation, including stopped-host reuse."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from controls import Journal, hash_file, read, write_new

HERE = Path(__file__).resolve().parent
COUNT = 120
IDENTITY = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
NEXT = "01a11705-11f1-75f4-b64e-8f0a3679518b"
PARENT_FREEZE = "3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46"


def boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    pinned = read(HERE / "closed-120/ledger-read-only.json")["rows"]
    if len(rows) != 1500 or len(saved) != 1500:
        raise ValueError("EXACT_1500_IDENTITIES_REQUIRED")
    for actual, original, schedule in zip(rows, pinned, saved, strict=True):
        if any(actual[k] != original[k] for k in IDENTITY) or any(
            actual[k] != schedule[k] for k in IDENTITY if k != "execution_id"
        ):
            raise ValueError("CLOSED120_IDENTITY_OR_ORDER_DRIFT")
    if rows[:COUNT] != pinned[:COUNT]:
        raise ValueError("CLOSED120_ORIGINAL_STATUS_OR_BACKUP_DRIFT")
    if any(
        r["state"] != "PLANNED"
        or any(r[k] is not None for k in ("deadline", "backup_hash", "error"))
        for r in rows[COUNT:]
    ):
        raise ValueError("CLOSED120_ACTIVE_OR_CHANGED_SLOT")
    if rows[COUNT]["execution_id"] != NEXT or rows[COUNT]["arm"] != "P1":
        raise ValueError("NEXT_SEQUENCE121_DRIFT")


def master_check(master: Path) -> list[dict[str, Any]]:
    from handover import original_policy, ro_rows

    for name, digest in read(HERE / "closed-120-members.json").items():
        target = (master / name).resolve()
        if master.resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("CLOSED120_MEMBER_DRIFT: " + name)
    rows = ro_rows(master)
    boundary(rows, read(HERE / "closed-120/ledger-read-only.json")["rows"])
    original_policy(read(master / "run.json")["policy"])
    if read(master / "pause.json")["reason"] != "WALL_CLOCK_BACKWARD_STOP_ADMISSIONS":
        raise ValueError("EXACT_REVIEWED_STOP_REQUIRED")
    for row in rows[:COUNT]:
        receipt = master / "backups" / (row["execution_id"] + ".json")
        proof = read(receipt)
        raw = read(master / "exports" / f"{row['sequence']:04d}" / "export.json")
        if (
            hash_file(receipt) != row["backup_hash"]
            or proof["execution_id"] != row["execution_id"]
            or proof["sha256"] != proof["cloud"]["sha256"]
            or not proof["cloud"]["version_id"]
            or any(raw[k] != row[k] for k in ("execution_id", "arm", "attempt", "fixture_hash"))
        ):
            raise ValueError("CLOSED120_INCOMPLETE_BACKUP_OR_EXPORT")
    return rows


def stage(master: Path, destination: Path) -> dict[str, Any]:
    master_check(master)
    if destination.exists():
        raise ValueError("FRESH_METADATA_ROOT_ONLY")
    destination.mkdir(parents=True)
    # Preserve legacy 38-original history and timing sidecars byte for byte.
    for name in (
        "campaign.sqlite3",
        "bindings.json",
        "cloud.json",
        "handover.json",
        "saved-identities.json",
        "historical-evidence.tar.gz",
    ):
        shutil.copyfile(master / name, destination / name)
    shutil.copytree(master / "backups", destination / "backups")
    shutil.copytree(master, destination / "restart-history")
    config = read(master / "run.json")
    config.update(
        source="/opt/fyp-phase8-continuation-v9",
        manifest="/opt/fyp-phase8-continuation-v9/artifacts/phase-8-review-freeze/v2/review-inventory.json",
        backup="/var/lib/p8-continuation-v9/backup",
        operational_limits_sha256="b0349d0814cb519445a40cf430ee3f4aad50cf2d326509f96d6b59f36b4c44eb",
        continuation={
            "manifest": "artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json",
            "receipts": "/var/lib/fyp-owner/continuation-v9-receipts",
        },
    )
    # Original backup paths remain valid on the retained root; never restore SQL.
    write_new(destination / "run.json", config)
    write_new(
        destination / "binding-seal.json",
        {
            "run": hash_file(destination / "run.json"),
            "bindings": hash_file(destination / "bindings.json"),
        },
    )
    record = {
        "version": "phase85-continuation-v9",
        "backed_up": COUNT,
        "planned": 1380,
        "next_execution_id": NEXT,
        "parent_freeze_sha256": PARENT_FREEZE,
        "history_files": read(HERE / "closed-120-members.json"),
        "driver_calls": 0,
        "live_application_state_restored": False,
        "clock_reset": False,
    }
    write_new(destination / "restart-boundary.json", record)
    journal = Journal(destination)
    journal.verify()
    journal.event(
        "CLOSED_120_METADATA_IMPORT", proof=hash_file(destination / "restart-boundary.json")
    )
    journal.event(
        "BINDINGS_SEALED",
        run=hash_file(destination / "run.json"),
        bindings=hash_file(destination / "bindings.json"),
    )
    journal.pause("CONTINUATION_REVIEW_REQUIRED")
    verify(destination)
    return record


def verify(root: Path) -> None:
    from handover import ro_rows

    record = read(root / "restart-boundary.json")
    if (
        record["parent_freeze_sha256"] != PARENT_FREEZE
        or record["backed_up"] != COUNT
        or record["planned"] != 1380
        or record["next_execution_id"] != NEXT
        or record["history_files"] != read(HERE / "closed-120-members.json")
    ):
        raise ValueError("CLOSED120_HANDOVER_BINDING_DRIFT")
    history = root / "restart-history"
    for name, digest in record["history_files"].items():
        target = (history / name).resolve()
        if history.resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("CLOSED120_HISTORY_DRIFT")
    rows = ro_rows(root)
    saved = read(history / "ledger-read-only.json")["rows"]
    if (
        len(rows) != 1500
        or rows[:COUNT] != saved[:COUNT]
        or any(any(a[k] != b[k] for k in IDENTITY) for a, b in zip(rows, saved, strict=True))
    ):
        raise ValueError("CLOSED120_LIVE_IDENTITY_OR_ORIGINAL_DRIFT")

    def notices(folder: Path) -> list[tuple[Any, ...]]:
        with sqlite3.connect(
            (folder / "campaign.sqlite3").resolve().as_uri() + "?mode=ro", uri=True
        ) as db:
            db.execute("BEGIN")
            return db.execute("SELECT * FROM notices ORDER BY n").fetchall()

    historical = notices(history)
    if notices(root)[: len(historical)] != historical:
        raise ValueError("CLOSED120_NOTICE_PREFIX_DRIFT")
    for row in saved[:COUNT]:
        if hash_file(root / "backups" / (row["execution_id"] + ".json")) != row["backup_hash"]:
            raise ValueError("CLOSED120_BACKUP_RECEIPT_DRIFT")


def imported(root: Path, execution_id: str) -> bool:
    if not (root / "restart-boundary.json").exists():
        return False
    return execution_id in {
        r["execution_id"]
        for r in read(root / "restart-history/ledger-read-only.json")["rows"][:COUNT]
    }
