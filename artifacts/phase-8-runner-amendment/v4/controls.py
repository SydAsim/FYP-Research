"""Typed proposal controls and owner-signed, chained execution capabilities."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def utc() -> datetime:
    return datetime.now(UTC)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def hash_file(path: Path) -> str:
    with path.open("rb") as incoming:
        return hashlib.file_digest(incoming, "sha256").hexdigest()


def write_new(path: Path, value: object) -> None:
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def uuid7() -> str:
    millis = int(time.time() * 1000)
    return str(
        UUID(
            int=(millis << 80)
            | (7 << 76)
            | (secrets.randbits(12) << 64)
            | (2 << 62)
            | secrets.randbits(62)
        )
    )


class Policy(Strict):
    version: Literal["phase84-final-v2"] = "phase84-final-v2"
    region: Literal["ap-southeast-2"] = "ap-southeast-2"
    scope: Literal["CAMPAIGN", "CALIBRATION"]
    run_id: str = Field(pattern=r"^[a-z0-9-]{8,64}$")
    host_started_at: datetime
    host_hours: Literal[360] = 360
    admission_cutoff_seconds: Literal[1800] = 1800
    observation_seconds: Literal[600] = 600
    budget_usd: Literal[65] = 65
    admission_committed_usd: Literal[55] = 55
    volume_gib: Literal[160] = 160
    stopped_retention_hours: Literal[48] = 48
    admission_ram_bytes: int = Field(default=2 * 1024**3, ge=2 * 1024**3)
    active_ram_bytes: int = Field(default=1024**3, ge=1024**3)
    admission_disk_bytes: int = Field(default=20 * 1024**3, ge=20 * 1024**3)
    active_disk_bytes: int = Field(default=10 * 1024**3, ge=10 * 1024**3)
    cloud_limit_bytes: Literal[32212254720] = 32212254720
    slot_capacity_reserve_bytes: Literal[1073741824] = 1073741824
    cloud_bucket: str = Field(
        default="fyp-p82-20261005-018da1d6-803656589923",
        pattern=r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$",
    )
    compute_usd_hour: float = Field(default=0.1197, ge=0, allow_inf_nan=False)
    ipv4_usd_hour: float = Field(default=0.005, ge=0, allow_inf_nan=False)
    disk_usd_gib_month: float = Field(default=0.096, ge=0, allow_inf_nan=False)
    s3_usd_gib_month: float = Field(default=0.025, ge=0, allow_inf_nan=False)
    request_transfer_reserve_usd: float = Field(default=5, ge=5, allow_inf_nan=False)
    poll_seconds: Literal[5] = 5

    @field_validator("host_started_at")
    @classmethod
    def offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("UTC offset required")
        return value.astimezone(UTC)

    @property
    def stop_at(self) -> datetime:
        return self.host_started_at + timedelta(hours=self.host_hours)

    def committed_cost(self, at: datetime) -> float:
        hours = max(0.0, (at - self.host_started_at).total_seconds() / 3600)
        return (
            hours * (self.compute_usd_hour + self.ipv4_usd_hour)
            + (hours + self.stopped_retention_hours)
            / 730
            * self.volume_gib
            * self.disk_usd_gib_month
            + 30 * self.s3_usd_gib_month
            + self.request_transfer_reserve_usd
        )


class Receipt(Strict):
    kind: Literal["REVIEW_ACCEPTED", "FREEZE", "LAUNCH"]
    scope: Literal["CAMPAIGN", "CALIBRATION"]
    package_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    schedule_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    predecessor_hash: str | None
    expires_at: datetime
    signer: str = Field(min_length=1)
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("expires_at")
    @classmethod
    def offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("UTC offset required")
        return value.astimezone(UTC)


class Authority:
    def __init__(
        self,
        source: Path,
        manifest: Path,
        policy: Policy,
        schedule_hash: str,
        receipts: Path,
        key: Path,
    ) -> None:
        self.source, self.manifest, self.policy = source, manifest, policy
        self.schedule_hash, self.receipts, self.key = schedule_hash, receipts, key

    def verify(self, at: datetime | None = None) -> str:
        at = at or utc()
        inventory = read(self.manifest)
        if inventory["kind"] != "REVIEW_INVENTORY" or inventory["scope"] != self.policy.scope:
            raise ValueError("PACKAGE_SCOPE_DRIFT")
        files = inventory["files"]
        if hashlib.sha256(canonical(files)).hexdigest() != inventory["package_hash"]:
            raise ValueError("MANIFEST_HASH_DRIFT")
        for name, expected in files.items():
            path = (self.source / name).resolve()
            if self.source.resolve() not in path.parents or hash_file(path) != expected:
                raise ValueError(f"SOURCE_DRIFT: {name}")
        roots = (
            ("apps", "packages", "research", "tests", "database", "contracts", "docs")
            if self.policy.scope == "CAMPAIGN"
            else inventory.get("closed_source_roots", [])
        )
        for relative in roots:
            base = (self.source / relative).resolve()
            if self.source.resolve() not in base.parents:
                raise ValueError("UNSAFE_SOURCE_ROOT")
            excluded = {
                "__pycache__",
                "node_modules",
                ".next",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "test-results",
                "playwright-report",
                "coverage",
            }
            actual = {
                p.relative_to(self.source).as_posix()
                for p in base.rglob("*")
                if p.is_file() and not excluded.intersection(p.parts) and p.suffix != ".pyc"
            }
            expected_names = {name for name in files if name.startswith(relative + "/")}
            if actual != expected_names:
                raise ValueError("ADDED_OR_REMOVED_SOURCE_DRIFT")
        if self.policy.scope == "CAMPAIGN":
            prefix = "artifacts/phase-8-review-freeze/v2/"
            proposal = read(self.source / prefix / "policy-proposal.json")["static_policy"]
            if (
                self.policy.model_dump(mode="json", exclude={"host_started_at", "run_id"})
                != proposal
            ):
                raise ValueError("REVIEWED_STATIC_POLICY_DRIFT")
            if hash_file(self.source / prefix / "schedule.json") != self.schedule_hash:
                raise ValueError("REVIEWED_SCHEDULE_DRIFT")
            actual_scripts = {
                p.relative_to(self.source).as_posix() for p in (self.source / prefix).glob("*.py")
            }
            if actual_scripts != {
                name for name in files if name.startswith(prefix) and name.endswith(".py")
            }:
                raise ValueError("RUNNER_EXECUTABLE_CLOSURE_DRIFT")
        if self.source.resolve() in self.key.resolve().parents:
            raise ValueError("SIGNING_KEY_MUST_BE_OUTSIDE_SOURCE")
        secret = self.key.read_bytes()
        if len(secret) < 32:
            raise ValueError("INVALID_OWNER_KEY")
        previous: str | None = None
        for kind in ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH"):
            raw = read(self.receipts / f"{kind}.json")
            receipt = Receipt.model_validate(raw)
            body = {k: v for k, v in raw.items() if k != "signature"}
            expected = hmac.new(secret, canonical(body), "sha256").hexdigest()
            if (
                not hmac.compare_digest(expected, receipt.signature)
                or receipt.kind != kind
                or receipt.scope != self.policy.scope
                or receipt.package_hash != inventory["package_hash"]
                or receipt.policy_hash != policy_commitment(self.policy, kind)
                or receipt.schedule_hash != self.schedule_hash
                or receipt.predecessor_hash != previous
                or receipt.expires_at <= at
                or receipt.expires_at < self.policy.stop_at
            ):
                raise ValueError("INVALID_OR_EXPIRED_AUTHORIZATION_CHAIN")
            previous = hashlib.sha256(canonical(raw)).hexdigest()
        assert previous is not None
        return previous


def policy_commitment(policy: Policy, kind: str) -> str:
    # Review/freeze bind static proposals. Only the separately signed launch binds
    # its fresh run identity and conservative host-clock start.
    excluded = {"host_started_at", "run_id"} if kind != "LAUNCH" else set()
    return hashlib.sha256(canonical(policy.model_dump(mode="json", exclude=excluded))).hexdigest()


def guard(
    policy: Policy,
    sample: dict[str, Any],
    at: datetime,
    cloud_bytes: int,
    *,
    active: bool = False,
    extra_bytes: int = 0,
) -> None:
    if at < policy.host_started_at:
        raise ValueError("BEFORE_AUTHORIZED_START")
    if at >= policy.stop_at:
        raise ValueError("HOST_360H_LIMIT")
    if not active and at >= policy.stop_at - timedelta(seconds=policy.admission_cutoff_seconds):
        raise ValueError("ADMISSION_CUTOFF")
    if not active and policy.committed_cost(at + timedelta(minutes=30)) >= 55:
        raise ValueError("ESTIMATED_COMMITTED_COST_STOP")
    if cloud_bytes + extra_bytes >= policy.cloud_limit_bytes:
        raise ValueError("CLOUD_30GIB_LIMIT")
    ram = policy.active_ram_bytes if active else policy.admission_ram_bytes
    disk = policy.active_disk_bytes if active else policy.admission_disk_bytes
    if sample["available_memory_bytes"] < ram:
        raise ValueError("RAM_STOP")
    if (
        min(sample[k] for k in ("system_free_bytes", "output_free_bytes", "backup_free_bytes"))
        < disk + extra_bytes
    ):
        raise ValueError("DISK_STOP")
    if (
        not active
        and sample.get("working_bytes", 0) + policy.slot_capacity_reserve_bytes > 50 * 1024**3
    ):
        raise ValueError("WORKING_RESERVATION_STOP")
    if (
        not active
        and sample.get("backup_bytes", 0) + policy.slot_capacity_reserve_bytes > 50 * 1024**3
    ):
        raise ValueError("BACKUP_RESERVATION_STOP")


def clock_check(
    policy: Policy, anchor: dict[str, Any], at: datetime, monotonic: float, boot: str
) -> None:
    if boot != anchor["boot_id"]:
        raise ValueError("HOST_REBOOT_UNQUALIFIED")
    elapsed = monotonic - anchor["monotonic"]
    if elapsed < 0:
        raise ValueError("MONOTONIC_CLOCK_DRIFT")
    if elapsed >= 360 * 3600 or at >= policy.stop_at:
        raise ValueError("HOST_360H_LIMIT")
    wall = (at - datetime.fromisoformat(anchor["wall"])).total_seconds()
    if wall < elapsed - 5:
        raise ValueError("WALL_CLOCK_BACKWARD_STOP_ADMISSIONS")


class Journal:
    """Serial master ledger; research metadata only, never application correctness."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "campaign.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS slots(
                  sequence INTEGER PRIMARY KEY,case_id TEXT,arm TEXT,attempt INTEGER,
                  execution_id TEXT UNIQUE,fixture_hash TEXT,state TEXT,deadline TEXT,
                  backup_hash TEXT,error TEXT);
                CREATE TABLE IF NOT EXISTS notices(
                  n INTEGER PRIMARY KEY,body TEXT,previous TEXT,hash TEXT);
                CREATE TABLE IF NOT EXISTS reservations(
                  key TEXT PRIMARY KEY,bytes INTEGER,state TEXT,version TEXT);
            """)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    def event(self, kind: str, **facts: Any) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self.event_in(db, kind, **facts)

    def event_in(self, db: sqlite3.Connection, kind: str, **facts: Any) -> None:
        last = db.execute("SELECT hash FROM notices ORDER BY n DESC LIMIT 1").fetchone()
        previous = last[0] if last else "GENESIS"
        body = canonical({"at": utc().isoformat(), "kind": kind, **facts}).decode()
        digest = hashlib.sha256((body + previous).encode()).hexdigest()
        db.execute(
            "INSERT INTO notices(body,previous,hash) VALUES(?,?,?)", (body, previous, digest)
        )

    def rows(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM slots ORDER BY sequence")]

    def initialize(self, rows: list[dict[str, Any]], scope: str) -> None:
        if self.rows():
            raise ValueError("EXISTING_LEDGER_RETAIN_ORIGINALS")
        if scope == "CAMPAIGN" and (
            len(rows) != 1500 or any(not r["case_id"].startswith("p8v4-") for r in rows)
        ):
            raise ValueError("EXACT_CAMPAIGN_SCOPE_REQUIRED")
        if scope == "CALIBRATION" and any(not r["case_id"].startswith("cal-v4-") for r in rows):
            raise ValueError("CALIBRATION_MAIN_SEPARATION")
        with self.connect() as db:
            db.executemany(
                "INSERT INTO slots VALUES(?,?,?,?,?,?,'PLANNED',NULL,NULL,NULL)",
                [
                    (r["sequence"], r["case_id"], r["arm"], 1, uuid7(), r["fixture_hash"])
                    for r in rows
                ],
            )
        self.event("INITIALIZED", scope=scope, originals=len(rows))

    def admit(
        self, authority: Authority, sample: dict[str, Any], at: datetime, cloud_bytes: int
    ) -> dict[str, Any] | None:
        authority.verify(at)
        self.verify()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute(
                "SELECT * FROM slots WHERE state IN('RUNNING','EXPORTED')"
            ).fetchone()
            if active:
                if at >= authority.policy.stop_at or at < authority.policy.host_started_at:
                    raise ValueError("HOST_360H_LIMIT")
                return dict(active)  # recovery/backup only, not a new attempt
            if (self.root / "pause.json").exists():
                raise ValueError("PAUSED_ADMISSIONS")
            decisions = [
                json.loads(r[0])["kind"]
                for r in db.execute("SELECT body FROM notices ORDER BY n")
                if json.loads(r[0])["kind"] in ("STOP_NEW_ADMISSIONS", "RESUME_SAVED_ORDER")
            ]
            if decisions and decisions[-1] == "STOP_NEW_ADMISSIONS":
                raise ValueError("DURABLE_PAUSE_REQUIRES_REVIEW")
            guard(authority.policy, sample, at, cloud_bytes)
            row = db.execute(
                "SELECT * FROM slots WHERE state='PLANNED' ORDER BY sequence"
            ).fetchone()
            if row is None:
                return None
            if (
                row["sequence"] > 1
                and db.execute(
                    "SELECT state FROM slots WHERE sequence=?", (row["sequence"] - 1,)
                ).fetchone()[0]
                != "BACKED_UP"
            ):
                raise ValueError("PREVIOUS_BACKUP_REQUIRED")
            db.execute("UPDATE slots SET state='RUNNING' WHERE sequence=?", (row["sequence"],))
            self.event_in(
                db,
                "ADMITTED",
                execution_id=row["execution_id"],
                state="RUNNING",
                deadline=None,
                backup_hash=None,
            )
            return {**dict(row), "state": "RUNNING"}

    def update(
        self,
        execution: str,
        *,
        state: str | None = None,
        deadline: str | None = None,
        backup_hash: str | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM slots WHERE execution_id=?", (execution,)).fetchone()
            if row is None or row["state"] == "BACKED_UP":
                raise ValueError("ORIGINAL_IMMUTABLE")
            if row["deadline"] and deadline and row["deadline"] != deadline:
                raise ValueError("ORIGINAL_DEADLINE_IMMUTABLE")
            legal = {"RUNNING": {"RUNNING", "EXPORTED"}, "EXPORTED": {"BACKED_UP"}}
            if state and state not in legal.get(row["state"], set()):
                raise ValueError("ILLEGAL_TRANSITION")
            if state == "BACKED_UP" and not backup_hash:
                raise ValueError("BACKUP_PROOF_REQUIRED")
            db.execute(
                "UPDATE slots SET state=?,deadline=?,backup_hash=? WHERE execution_id=?",
                (
                    state or row["state"],
                    deadline or row["deadline"],
                    backup_hash or row["backup_hash"],
                    execution,
                ),
            )
            self.event_in(
                db,
                "TRANSITION",
                execution_id=execution,
                state=state or row["state"],
                deadline=deadline or row["deadline"],
                backup_hash=backup_hash or row["backup_hash"],
            )

    def pause(self, reason: str) -> None:
        self.event("STOP_NEW_ADMISSIONS", reason=reason)
        path = self.root / "pause.json"
        if path.exists() and read(path)["reason"] == "BETWEEN_SLOTS" and reason != "BETWEEN_SLOTS":
            path.rename(self.root / f"retained-pause-{time.time_ns()}.json")
        if not path.exists():
            write_new(path, {"reason": reason, "at": utc().isoformat()})

    def resume(self) -> None:
        path = self.root / "pause.json"
        if read(path)["reason"] != "BETWEEN_SLOTS":
            raise ValueError("FAILURE_REQUIRES_REVIEW_NO_AUTO_UNPAUSE")
        path.rename(self.root / f"retained-pause-{time.time_ns()}.json")
        self.event("RESUME_SAVED_ORDER")

    def verify(self) -> None:
        with self.connect() as db:
            db.execute("BEGIN")
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("LEDGER_CORRUPTION")
            previous = "GENESIS"
            transitions = {}
            for row in db.execute("SELECT * FROM notices ORDER BY n"):
                if (
                    row["previous"] != previous
                    or hashlib.sha256((row["body"] + previous).encode()).hexdigest() != row["hash"]
                ):
                    raise ValueError("LEDGER_HASH_DRIFT")
                previous = row["hash"]
                event = json.loads(row["body"])
                if event["kind"] in ("ADMITTED", "TRANSITION"):
                    transitions[event["execution_id"]] = event
            for slot in db.execute("SELECT * FROM slots WHERE state!='PLANNED'"):
                recorded = transitions.get(slot["execution_id"])
                if recorded is None or any(
                    recorded.get(key) != slot[key] for key in ("state", "deadline", "backup_hash")
                ):
                    raise ValueError("LEDGER_TRANSITION_DRIFT")
