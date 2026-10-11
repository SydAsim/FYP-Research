"""Durable research ledger, immutable records and admission guards (not app state)."""

import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
VERSION = "phase8-execution-setup-v1"
PREFIX = "cal-v4-setup-v1-"


def now() -> str:
    return datetime.now(UTC).isoformat()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def immutable(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return digest(path)


def source_inventory() -> dict[str, str]:
    files = [ROOT / p for p in ("AGENTS.md", "README.md", "pyproject.toml", "uv.lock")]
    excluded = {
        "node_modules",
        ".next",
        "__pycache__",
        "test-results",
        "playwright-report",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "coverage",
    }
    for directory in ("apps", "packages", "research", "tests", "database", "contracts", "docs"):
        for folder, subdirectories, names in os.walk(ROOT / directory):
            subdirectories[:] = [name for name in subdirectories if name not in excluded]
            files.extend(Path(folder) / name for name in names if not name.endswith(".pyc"))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}


def check_inventory(inventory: dict[str, str], base: Path = ROOT) -> None:
    for relative, expected in inventory.items():
        path = base / relative
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"HASH_DRIFT: {path}")


def check_source(directory: Path) -> None:
    expected = load(directory / "source-seal.json")
    if source_inventory() != expected:
        raise ValueError("SOURCE_HASH_DRIFT_OR_ADDED_SOURCE")


def preserve(directory: Path) -> None:
    previous = ROOT / "artifacts/phase-8-execution-plan/v1/preserved-files-before.json"
    inventory: dict[str, str] = load(previous)
    check_inventory(inventory)
    # Preserve the prior execution plan too, including its descriptive timing proposal.
    for p in previous.parent.rglob("*"):
        if p.is_file():
            inventory[p.relative_to(ROOT).as_posix()] = digest(p)
    immutable(directory / "historical-hashes-before.json", inventory)


class Ledger:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.db = root / "ledger.sqlite3"
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS slots (
                  sequence INTEGER PRIMARY KEY, case_id TEXT NOT NULL, arm TEXT NOT NULL,
                  execution_id TEXT UNIQUE, state TEXT NOT NULL, deadline TEXT,
                  attempt INTEGER NOT NULL, label TEXT NOT NULL, original_id TEXT,
                  export_hash TEXT, error TEXT);
                CREATE TABLE IF NOT EXISTS events (
                  n INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                  body TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS checkpoints (
                  execution_id TEXT PRIMARY KEY, body TEXT NOT NULL, hash TEXT NOT NULL);
            """)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db, timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def event(self, kind: str, **facts: Any) -> None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT hash FROM events ORDER BY n DESC LIMIT 1").fetchone()
            previous = prior[0] if prior else "GENESIS"
            at, body = now(), json.dumps({"kind": kind, **facts}, sort_keys=True, default=str)
            hashed = hashlib.sha256((at + body + previous).encode()).hexdigest()
            conn.execute(
                "INSERT INTO events(at,body,previous,hash) VALUES (?,?,?,?)",
                (at, body, previous, hashed),
            )

    def rows(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM slots ORDER BY sequence")]

    def checkpoint(self, execution: str, value: dict[str, Any]) -> None:
        body = json.dumps(value, indent=2, default=str) + "\n"
        hashed = hashlib.sha256(body.encode()).hexdigest()
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute("SELECT hash FROM events ORDER BY n DESC LIMIT 1").fetchone()
            previous = prior[0] if prior else "GENESIS"
            at = now()
            event = json.dumps(
                {"kind": "CHECKPOINT", "execution_id": execution, "hash": hashed}, sort_keys=True
            )
            chain = hashlib.sha256((at + event + previous).encode()).hexdigest()
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints VALUES (?,?,?)", (execution, body, hashed)
            )
            conn.execute(
                "INSERT INTO events(at,body,previous,hash) VALUES (?,?,?,?)",
                (at, event, previous, chain),
            )

    def recover_checkpoint(self, execution: str) -> dict[str, Any]:
        with self.connect() as conn:
            checkpoint = conn.execute(
                "SELECT body,hash FROM checkpoints WHERE execution_id=?", (execution,)
            ).fetchone()
            records = conn.execute("SELECT body FROM events ORDER BY n DESC").fetchall()
        if checkpoint is None:
            raise ValueError("Missing durable checkpoint; do not reissue driver")
        expected = next(
            json.loads(r[0])["hash"]
            for r in records
            if json.loads(r[0]).get("kind") == "CHECKPOINT"
            and json.loads(r[0]).get("execution_id") == execution
        )
        if (
            hashlib.sha256(checkpoint[0].encode()).hexdigest() != expected
            or checkpoint[1] != expected
        ):
            raise ValueError("CHECKPOINT_HASH_DRIFT")
        return dict(json.loads(checkpoint[0]))

    def admit(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            active = conn.execute("SELECT * FROM slots WHERE state IN ('RUNNING','CHECKPOINTED')")
            row = active.fetchone()
            if row:
                return dict(row)
            row = conn.execute(
                "SELECT * FROM slots WHERE state='PLANNED' ORDER BY sequence LIMIT 1"
            )
            item = row.fetchone()
            if item is None:
                return None
            if not item["case_id"].startswith(PREFIX):
                raise ValueError("MAIN_CAMPAIGN_GUARD: only setup calibration IDs admitted")
            execution = str(uuid4())
            conn.execute(
                "UPDATE slots SET state='RUNNING',execution_id=? WHERE sequence=?",
                (execution, item["sequence"]),
            )
            return {**dict(item), "state": "RUNNING", "execution_id": execution}

    def update(self, execution: str, **values: Any) -> None:
        allowed = {"state", "deadline", "export_hash", "error"}
        if not values or not set(values) <= allowed:
            raise ValueError("Invalid ledger transition")
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM slots WHERE execution_id=?", (execution,)
            ).fetchone()
            if existing is None or existing["state"] == "EXPORTED":
                raise ValueError("Finalized original attempt cannot be replaced")
            if (
                existing["deadline"]
                and values.get("deadline", existing["deadline"]) != existing["deadline"]
            ):
                raise ValueError("Original deadline cannot be reset")
            assignments = ",".join(f"{name}=?" for name in values)
            conn.execute(
                f"UPDATE slots SET {assignments} WHERE execution_id=?",
                (*values.values(), execution),
            )

    def seal(self, path: Path) -> str:
        relative, hashed = path.relative_to(self.root).as_posix(), digest(path)
        with self.connect() as conn:
            conn.execute("INSERT INTO files VALUES (?,?)", (relative, hashed))
        return hashed

    def verify(self) -> None:
        with self.connect() as conn:
            check_inventory({r[0]: r[1] for r in conn.execute("SELECT * FROM files")}, self.root)
            previous = "GENESIS"
            for r in conn.execute("SELECT * FROM events ORDER BY n"):
                hashed = hashlib.sha256((r["at"] + r["body"] + previous).encode()).hexdigest()
                if r["previous"] != previous or r["hash"] != hashed:
                    raise ValueError("LEDGER_HASH_DRIFT")
                previous = hashed
            executions = [r[0] for r in conn.execute("SELECT execution_id FROM checkpoints")]
        for execution in executions:
            self.recover_checkpoint(execution)

    def backup(self, destination: Path) -> Path:
        self.verify()
        folder = destination / f"backup-{uuid4()}"
        folder.mkdir(parents=True, exist_ok=False)
        with self.connect() as source, sqlite3.connect(folder / "ledger.sqlite3") as target:
            source.backup(target)
        with self.connect() as conn:
            paths = [r[0] for r in conn.execute("SELECT path FROM files")]
        # Checkpoints and logs are copied as crash-recovery material, not immutable final outcomes.
        for p in self.root.rglob("*"):
            if p.is_file() and p.name not in {"ledger.sqlite3", "runner.lock"}:
                target_path = folder / p.relative_to(self.root)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target_path)
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
                        folder / f"{user}-backup-failure.json",
                        {
                            "at": now(),
                            "exit": result.returncode,
                            "stderr": result.stderr.decode(errors="replace"),
                        },
                    )
                    raise RuntimeError(f"Database backup failed: retained in {folder}")
                with gzip.open(folder / f"{user}.sql.gz", "wb") as handle:
                    handle.write(result.stdout)
        manifest = {
            p.relative_to(folder).as_posix(): digest(p) for p in folder.rglob("*") if p.is_file()
        }
        immutable(folder / "backup-manifest.json", {"hashes": manifest, "sealed_paths": paths})
        check_inventory(manifest, folder)
        self.event("BACKUP_VERIFIED", path=str(folder))
        return folder


@contextmanager
def runner_lock(root: Path) -> Iterator[None]:
    """OS-released lock: a stale PID text file cannot block crash recovery."""
    with (root / "runner.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            raise RuntimeError("This runner is qualified for Windows terminals")
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
