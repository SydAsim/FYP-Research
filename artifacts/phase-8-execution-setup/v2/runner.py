"""Storage v2 entrypoint; reuses the qualified v1 collector and unchanged v4 instrument.

Main admission stays disabled. This adapter only changes research integrity/backup
orchestration. Its own source is copied and hash-registered before any admission.
"""

import gzip
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.execution_setup import cli, worker  # noqa: E402
from research.execution_setup.core import (  # noqa: E402
    Ledger,
    check_inventory,
    digest,
    immutable,
    load,
    now,
)

BLOCK = 75


def compress(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as zipped:
            with source.open("rb") as handle:
                shutil.copyfileobj(handle, zipped, length=1024 * 1024)
        output.flush()
        os.fsync(output.fileno())


class ArchiveLedger(Ledger):
    """Bounded active checks and append-only compressed archives, not app storage."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.verified_n = 0
        self.verified_hash = "GENESIS"
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS archive_cursor (
                    id INTEGER PRIMARY KEY CHECK(id=1), file_rowid INTEGER NOT NULL,
                    event_n INTEGER NOT NULL);
                INSERT OR IGNORE INTO archive_cursor VALUES(1,0,0);
                CREATE TABLE IF NOT EXISTS archive_objects (
                    raw_hash TEXT PRIMARY KEY, compressed_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS archived_executions (
                    execution_id TEXT PRIMARY KEY);
            """)

    def full_verify(self) -> None:
        super().verify()

    def verify(self) -> None:
        rows = self.rows()
        active = [r["execution_id"] for r in rows if r["state"] in ("RUNNING", "CHECKPOINTED")]
        with self.connect() as conn:
            files = conn.execute("SELECT path,hash FROM files").fetchall()
            events = conn.execute(
                "SELECT * FROM events WHERE n>? ORDER BY n", (self.verified_n,)
            ).fetchall()
        # A completed execution is fully audited before archiving and at each 75-slot
        # checkpoint. Do not reread every historical poll in every active minute.
        inventory = {
            r[0]: r[1]
            for r in files
            if not r[0].startswith("executions/")
            or any(r[0].startswith(f"executions/{execution}/") for execution in active)
        }
        check_inventory(inventory, self.root)
        previous = self.verified_hash
        for event in events:
            calculated = hashlib.sha256(
                (event["at"] + event["body"] + previous).encode()
            ).hexdigest()
            if event["previous"] != previous or event["hash"] != calculated:
                raise ValueError("LEDGER_HASH_DRIFT")
            previous = calculated
        if events:
            self.verified_n, self.verified_hash = events[-1]["n"], previous
        for execution in active:
            self.recover_checkpoint(execution)
        closed = sum(r["state"] == "EXPORTED" for r in rows)
        if not active and closed % BLOCK == 0:
            self.full_verify()

    def backup(self, destination: Path) -> Path:
        self.verify()
        with self.connect() as conn:
            archived = {r[0] for r in conn.execute("SELECT execution_id FROM archived_executions")}
            registered = {r[0] for r in conn.execute("SELECT path FROM files")}
        newly_closed = [
            r for r in self.rows() if r["state"] == "EXPORTED" and r["execution_id"] not in archived
        ]
        for row in newly_closed:
            for path in (self.root / "executions" / row["execution_id"]).rglob("*"):
                if path.is_file() and path.name != "runner.lock" and path.suffix != ".tmp":
                    if path.relative_to(self.root).as_posix() not in registered:
                        self.seal(path)
        folder = destination / f"incremental-v2-{uuid4()}"
        folder.mkdir(parents=True, exist_ok=False)
        objects = destination / "objects-v2"
        objects.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT file_rowid,event_n FROM archive_cursor WHERE id=1"
            ).fetchone()
            assert cursor is not None
            files = conn.execute(
                "SELECT rowid,path,hash FROM files WHERE rowid>? ORDER BY rowid", (cursor[0],)
            ).fetchall()
            events = [
                dict(r)
                for r in conn.execute("SELECT * FROM events WHERE n>? ORDER BY n", (cursor[1],))
            ]
        entries = []
        for file in files:
            source = self.root / file["path"]
            if digest(source) != file["hash"]:
                raise ValueError(f"EXPORT_HASH_DRIFT: {source}")
            target = objects / f"{file['hash']}.gz"
            if not target.exists():
                compress(source, target)
            with gzip.open(target, "rb") as handle:
                raw = hashlib.file_digest(handle, "sha256").hexdigest()
            if raw != file["hash"]:
                raise ValueError(f"ARCHIVE_HASH_DRIFT: {target}")
            zipped_hash = digest(target)
            entries.append(
                {
                    "path": file["path"],
                    "raw_hash": raw,
                    "object": target.name,
                    "compressed_hash": zipped_hash,
                }
            )
        rows = self.rows()
        closed = sum(r["state"] == "EXPORTED" for r in rows)
        active = [r for r in rows if r["state"] in ("RUNNING", "CHECKPOINTED")]
        checkpoint = closed % BLOCK == 0 or not any(r["state"] == "PLANNED" for r in rows)
        checkpoint |= any(r["state"] == "CHECKPOINTED" for r in active)
        checkpoint |= any(r["label"] == "DIAGNOSTIC_RERUN" for r in rows)
        active_checkpoints = {
            r["execution_id"]: self.recover_checkpoint(r["execution_id"]) for r in active
        }
        delta = folder / "ledger-delta.json"
        immutable(
            delta,
            {
                "at": now(),
                "version": "storage-v2",
                "slots": rows,
                "events": events,
                "objects": entries,
                "active_checkpoints": active_checkpoints,
                "previous_event_n": cursor[1],
                "main_started": False,
            },
        )
        compress(delta, folder / "ledger-delta.json.gz")
        # Retain the small uncompressed manifest too; never remove original evidence.
        if checkpoint:
            self.full_verify()
            sqlite_path = folder / "ledger.sqlite3"
            with self.connect() as source_db, sqlite3.connect(sqlite_path) as backup_db:
                source_db.backup(backup_db)
            compress(sqlite_path, folder / "ledger.sqlite3.gz")
            resources = self.root / "resources.json"
            if resources.exists():
                config = load(resources)
                for name, user in zip(
                    config["containers"][:2], ("setup_app", "setup_truth"), strict=True
                ):
                    result = subprocess.run(
                        ["docker", "exec", name, "pg_dump", "-U", user, user],
                        capture_output=True,
                        timeout=60,
                    )
                    if result.returncode:
                        immutable(
                            folder / f"{user}-FAILURE.json",
                            {
                                "at": now(),
                                "exit": result.returncode,
                                "stderr": result.stderr.decode(errors="replace"),
                            },
                        )
                        raise RuntimeError(f"Backup failure retained at {folder}")
                    with (folder / f"{user}.sql.gz").open("xb") as handle:
                        with gzip.GzipFile(fileobj=handle, mode="wb", mtime=0) as zipped:
                            zipped.write(result.stdout)
        manifest = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
        immutable(
            folder / "backup-manifest.json",
            {
                "hashes": manifest,
                "full_checkpoint": checkpoint,
                "objects": entries,
                "closed_slots": closed,
                "checkpoint_interval": BLOCK,
            },
        )
        check_inventory(manifest, folder)
        with self.connect() as conn:
            conn.execute(
                "UPDATE archive_cursor SET file_rowid=?,event_n=? WHERE id=1",
                (
                    files[-1]["rowid"] if files else cursor[0],
                    events[-1]["n"] if events else cursor[1],
                ),
            )
            conn.executemany(
                "INSERT INTO archived_executions VALUES (?)",
                [(row["execution_id"],) for row in newly_closed],
            )
        self.event(
            "INCREMENTAL_BACKUP_VERIFIED",
            path=str(folder),
            full_checkpoint=checkpoint,
            new_objects=len(entries),
        )
        return folder


def main() -> None:
    # Each worker is its own OS process, so research class substitution cannot
    # change application modules, another execution, or an existing Codex process.
    vars(cli)["Ledger"] = ArchiveLedger
    vars(worker)["Ledger"] = ArchiveLedger
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        root = Path(sys.argv[sys.argv.index("--root") + 1])
        if digest(root / "entrypoint-storage-v2.py") != digest(Path(__file__)):
            raise ValueError("STORAGE_WORKER_SOURCE_DRIFT")
        sys.argv.pop(1)
        worker.main()
        return
    root = Path(sys.argv[sys.argv.index("--root") + 1])
    if len(sys.argv) > 1 and sys.argv[1] != "init":
        ledger = ArchiveLedger(root)
        entry = root / "entrypoint-storage-v2.py"
        if not entry.exists():
            with entry.open("xb") as handle:
                handle.write(Path(__file__).read_bytes())
            ledger.seal(entry)
            ledger.event(
                "STORAGE_V2_PACKAGE_DECLARED",
                source_hash=digest(entry),
                checkpoint_slots=BLOCK,
                original_outcomes_preserved=True,
            )
        elif digest(entry) != digest(Path(__file__)):
            raise ValueError("STORAGE_SOURCE_DRIFT")
        if sys.argv[1] == "verify":
            ledger.full_verify()
    original_popen = subprocess.Popen

    def launch(command: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(command, list) and command[1:3] == ["-m", "research.execution_setup.worker"]:
            command = [command[0], str(Path(__file__).resolve()), "worker", *command[3:]]
        return original_popen(command, *args, **kwargs)

    subprocess.Popen = launch  # type: ignore[misc,assignment]  # isolated subprocess boundary
    cli.main()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if "--root" in sys.argv:
            failed_root = Path(sys.argv[sys.argv.index("--root") + 1])
            failed_ledger = Ledger(failed_root)
            failed_ledger.event("STORAGE_V2_FAILURE", detail=str(error))
            from research.execution_setup.core import atomic

            atomic(failed_root / "pause.json", {"reason": str(error), "at": now()})
        raise
