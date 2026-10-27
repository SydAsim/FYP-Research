"""Exact closed1297 metadata gate; no application restore or outcome changes."""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any

from closed145 import snapshot
from controls import hash_file, read, write_new

FIELDS = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
COUNT = 1297
NEXT = "01a11705-11f4-7c05-9897-af35348a8028"
MASTER = "98b581a9b3868d51f2bb8fafb1dde510c174970089bae488a1aea3677b61effe"
PAUSE = "7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8"
REL = "restart-history/continuation-v12-boundary/closed1297.json"


def check_rows(rows: list[dict[str, Any]], saved: list[dict[str, Any]], *, closed: bool = True) -> None:
    if len(rows) != 1500 or len(saved) != 1500 or len({r["execution_id"] for r in rows}) != 1500:
        raise ValueError("CLOSED1297_EXACT_IDENTITIES_REQUIRED")
    for i, (current, prior) in enumerate(zip(rows, saved, strict=True)):
        if current["sequence"] != i + 1 or current["attempt"] != 1 or any(current[k] != prior[k] for k in FIELDS):
            raise ValueError("CLOSED1297_IDENTITY_ORDER_ATTEMPT_DRIFT")
    if rows[:COUNT] != saved[:COUNT] or any(r["state"] != "BACKED_UP" or not r["backup_hash"] or not r["deadline"] for r in rows[:COUNT]):
        raise ValueError("CLOSED1297_ORIGINAL_DRIFT")
    if closed and any(r["state"] != "PLANNED" or any(r[k] is not None for k in ("deadline", "backup_hash", "error")) for r in rows[COUNT:]):
        raise ValueError("CLOSED1297_ACTIVE_OR_CHANGED_PENDING")
    if rows[COUNT]["execution_id"] != NEXT or rows[COUNT]["arm"] != "B3":
        raise ValueError("CLOSED1297_NEXT1298_DRIFT")


def prepare(root: Path, archive: Path) -> dict[str, Any]:
    from storage import verify_local

    verify_local(archive, MASTER)
    folder = root / "restart-history/continuation-v12-boundary"
    folder.mkdir(mode=0o700, exist_ok=False)
    with tarfile.open(archive) as tf:
        manifest = json.load(tf.extractfile("slot/manifest.json"))
        item = tf.getmember("slot/campaign.sqlite3")
        if not item.isfile() or item.size > 128 * 1024**2:
            raise ValueError("BOUNDARY_SQLITE_SIZE")
        data = tf.extractfile(item).read()
    if hashlib.sha256(data).hexdigest() != manifest["files"]["campaign.sqlite3"]:
        raise ValueError("BOUNDARY_SQLITE_HASH")
    with (folder / "campaign.sqlite3").open("xb") as f:
        f.write(data)
    baseline, notices = snapshot(folder / "campaign.sqlite3")
    rows, current = snapshot(root / "campaign.sqlite3")
    check_rows(rows, baseline)
    if current[:len(notices)] != notices or hash_file(root / "pause.json") != PAUSE:
        raise ValueError("BOUNDARY_NOTICE_OR_PAUSE_DRIFT")
    body = {"master_sha256": MASTER, "rows": baseline, "notices_count": len(notices), "last_notice": notices[-1], "pause_sha256": PAUSE, "sqlite_sha256": hashlib.sha256(data).hexdigest()}
    write_new(root / REL, body)
    return body


def verify(root: Path, *, closed: bool = False) -> dict[str, Any]:
    config = read(root / "run.json")
    record = root / REL
    if hash_file(record) != config["continuation"]["closed1297_sha256"]:
        raise ValueError("CLOSED1297_COMMITMENT_DRIFT")
    baseline = read(record)
    if baseline["master_sha256"] != MASTER or baseline["pause_sha256"] != PAUSE:
        raise ValueError("CLOSED1297_PARENT_DRIFT")
    rows, notices = snapshot(root / "campaign.sqlite3")
    check_rows(rows, baseline["rows"], closed=closed)
    n = baseline["notices_count"]
    if len(notices) < n or notices[n - 1] != baseline["last_notice"]:
        raise ValueError("CLOSED1297_NOTICE_PREFIX_DRIFT")
    for row in rows[:COUNT]:
        p = root / "backups" / (row["execution_id"] + ".json")
        proof = read(p)
        if hash_file(p) != row["backup_hash"] or proof["execution_id"] != row["execution_id"] or proof["sha256"] != proof["cloud"]["sha256"] or not proof["cloud"]["version_id"]:
            raise ValueError("CLOSED1297_BACKUP_REFERENCE_DRIFT")
    if closed and hash_file(root / "pause.json") != PAUSE:
        raise ValueError("CLOSED1297_PAUSE_DRIFT")
    return {"backed_up": COUNT, "planned": 1500 - COUNT, "next": rows[COUNT], "closed1297_sha256": hash_file(record)}
