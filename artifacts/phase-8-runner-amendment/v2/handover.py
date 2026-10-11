"""Closed-slot cold handover. Staging never signs, provisions or admits a slot."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from controls import Authority, Journal, Policy, Strict, canonical, hash_file, read, utc, write_new
from pydantic import Field

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
FIRST = "01a11705-11f0-79f1-9293-78f7f8207f70"
START = "2026-10-07T15:24:23.810674Z"
FIRST_HASH = "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"
PARENT_FREEZE = "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"
CHECKS = (
    "original_host_stopped",
    "original_backups_pinned_verified",
    "imported_closed_boundary",
    "source_and_dependency_hashes",
    "no_original_replay",
    "exact_original_policy",
    "deadline_and_budget_fit",
    "disk_ram_capacity",
    "s3_versioning_and_permissions",
    "cloud_cap_inventory",
    "prelaunch_master_backup_verified",
    "independent_absolute_stop",
    "independent_bootstrap_stop",
    "no_inbound_access",
    "owner_key_permissions",
    "retained_disk_disposition_within_original_limit",
)


class ContinuationPolicy(Policy):
    def committed_cost(self, at: datetime) -> float:
        # Conservative cold-handover reserve, within the unchanged $55/$65 limits.
        # Original elapsed-clock accounting is retained, including all paused time.
        return super().committed_cost(at) + 1.25


def ro_rows(master: Path) -> list[dict[str, Any]]:
    uri = master.joinpath("campaign.sqlite3").resolve().as_uri() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("IMPORTED_LEDGER_CORRUPTION")
        previous = "GENESIS"
        for row in db.execute("SELECT * FROM notices ORDER BY n"):
            if (
                row["previous"] != previous
                or hashlib.sha256((row["body"] + previous).encode()).hexdigest() != row["hash"]
            ):
                raise ValueError("IMPORTED_LEDGER_CHAIN_DRIFT")
            previous = row["hash"]
        return [dict(row) for row in db.execute("SELECT * FROM slots ORDER BY sequence")]


def verify_members(folder: Path) -> None:
    for name, digest in read(folder / "manifest.json")["files"].items():
        target = (folder / name).resolve()
        if folder.resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("RETAINED_MEMBER_DRIFT: " + name)


def closed_boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    keys = ("sequence", "case_id", "arm", "attempt", "fixture_hash")
    if len(rows) != 1500 or len(saved) != 1500:
        raise ValueError("EXACT_1500_ORIGINALS_REQUIRED")
    if len({row["execution_id"] for row in rows}) != 1500:
        raise ValueError("EXECUTION_IDENTITY_DUPLICATION")
    if any(any(row[k] != plan[k] for k in keys) for row, plan in zip(rows, saved, strict=True)):
        raise ValueError("SAVED_ORDER_OR_BINDING_DRIFT")
    if rows[0]["execution_id"] != FIRST or rows[0]["state"] != "BACKED_UP":
        raise ValueError("FIRST_ORIGINAL_NOT_CLOSED")
    if any(
        row["state"] != "PLANNED" or row["deadline"] or row["backup_hash"] or row["error"]
        for row in rows[1:]
    ):
        raise ValueError("ACTIVE_OR_CHANGED_SLOT_NO_COLD_HANDOVER")


def original_policy(raw: dict[str, Any]) -> Policy:
    expected = read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json")
    policy = Policy.model_validate(raw)
    if (
        policy != Policy.model_validate(expected)
        or policy.run_id != RUN
        or (policy.host_started_at != datetime.fromisoformat(START.replace("Z", "+00:00")))
    ):
        raise ValueError("ORIGINAL_POLICY_OR_CLOCK_RESET")
    return policy


def stage(master: Path, first: Path, destination: Path) -> dict[str, Any]:
    if destination.exists():
        raise ValueError("FRESH_IMPORT_ONLY_RETAIN_ATTEMPTS")
    verify_members(master)
    verify_members(first)
    rows = ro_rows(master)
    saved = read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")["rows"]
    closed_boundary(rows, saved)
    config = read(master / "run.json")
    original_policy(config["policy"])
    bindings = read(master / "bindings.json")
    if [{k: row[k] for k in bindings[0]} for row in rows] != bindings:
        raise ValueError("ORIGINAL_BINDINGS_DRIFT")
    seal = read(master / "binding-seal.json")
    if seal != {
        "run": hash_file(master / "run.json"),
        "bindings": hash_file(master / "bindings.json"),
    }:
        raise ValueError("ORIGINAL_BINDING_SEAL_DRIFT")
    exported = first / "executions" / FIRST / "export.json"
    if hash_file(exported) != FIRST_HASH or read(exported)["status"] != "FAILED":
        raise ValueError("FIRST_FAILED_EXPORT_DRIFT")
    backup = master / "backups" / f"{FIRST}.json"
    if hash_file(backup) != rows[0]["backup_hash"]:
        raise ValueError("FIRST_BACKUP_RECEIPT_DRIFT")
    sidecar = read(REPO / "artifacts/phase-8-runner-amendment/v1/first-original-sidecar.json")
    if sidecar["source_sha256"] != FIRST_HASH or not sidecar["outcome_values_identical"]:
        raise ValueError("FIRST_SIDECAR_DRIFT")
    destination.mkdir(parents=True)
    history = destination / "historical"
    shutil.copytree(master, history / "master")
    shutil.copytree(first, history / "first-slot")
    for name in ("campaign.sqlite3", "bindings.json", "cloud.json"):
        shutil.copyfile(master / name, destination / name)
    shutil.copytree(master / "backups", destination / "backups")
    shutil.copyfile(HERE / "saved-identities.json", destination / "saved-identities.json")
    expected_ids = read(destination / "saved-identities.json")["rows"]
    if rows != expected_ids:
        raise ValueError("REVIEWED_IDENTITY_INVENTORY_DRIFT")
    config.update(
        source="/opt/fyp-phase8-continuation-v1",
        manifest="/opt/fyp-phase8-continuation-v1/artifacts/phase-8-review-freeze/v2/review-inventory.json",
        backup="/var/lib/p8-continuation/backup",
        continuation={
            "manifest": "artifacts/phase-8-continuation/v1/candidate-inventory.json",
            "receipts": "/var/lib/fyp-owner/continuation-receipts",
        },
    )
    write_new(destination / "run.json", config)
    write_new(
        destination / "binding-seal.json",
        {
            "run": hash_file(destination / "run.json"),
            "bindings": hash_file(destination / "bindings.json"),
        },
    )
    history_files = {
        p.relative_to(history).as_posix(): hash_file(p) for p in history.rglob("*") if p.is_file()
    }
    record = {
        "version": "phase85-continuation-v1",
        "kind": "CLOSED_BOUNDARY_IMPORT_NOT_LAUNCH",
        "run_id": RUN,
        "accepted": False,
        "frozen": False,
        "launch_authorized": False,
        "first_execution_id": FIRST,
        "first_raw_status": "FAILED",
        "first_export_sha256": FIRST_HASH,
        "first_backup_receipt_sha256": hash_file(backup),
        "source_ledger_sha256": hash_file(master / "campaign.sqlite3"),
        "saved_identities_sha256": hash_file(destination / "saved-identities.json"),
        "parent_freeze_sha256": PARENT_FREEZE,
        "history_files": history_files,
        "first_old_resources_restored": False,
        "old_resources_deleted": False,
        "operational_clock_reset": False,
        "planned": 1499,
        "driver_calls": 0,
    }
    write_new(destination / "handover.json", record)
    journal = Journal(destination)
    journal.verify()
    journal.event("CLOSED_BOUNDARY_IMPORT", proof=hash_file(destination / "handover.json"))
    journal.event(
        "BINDINGS_SEALED",
        run=hash_file(destination / "run.json"),
        bindings=hash_file(destination / "bindings.json"),
    )
    journal.pause("CONTINUATION_REVIEW_REQUIRED")
    return record


def verify_imported_first(root: Path) -> None:
    record = read(root / "handover.json")
    if record["first_execution_id"] != FIRST or record["first_export_sha256"] != FIRST_HASH:
        raise ValueError("HANDOVER_IDENTITY_DRIFT")
    for name, digest in record["history_files"].items():
        target = (root / "historical" / name).resolve()
        if (root / "historical").resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("HANDOVER_HISTORY_DRIFT")
    rows = ro_rows(root)
    identities = read(root / "saved-identities.json")["rows"]
    if rows[0] != identities[0] or any(
        any(
            a[k] != b[k]
            for k in ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
        )
        for a, b in zip(rows, identities, strict=True)
    ):
        raise ValueError("IMPORTED_IDENTITY_DRIFT")
    if hash_file(root / "backups" / f"{FIRST}.json") != record["first_backup_receipt_sha256"]:
        raise ValueError("IMPORTED_BACKUP_DRIFT")


def record_provenance(root: Path, folder: Path, execution_id: str) -> None:
    from research.execution_setup.core import Ledger

    config = read(root / "run.json")
    inventory = read(Path(config["source"]) / config["continuation"]["manifest"])
    value = {
        "version": "phase85-continuation-v1",
        "execution_id": execution_id,
        "run_id": RUN,
        "parent_freeze_sha256": PARENT_FREEZE,
        "continuation_package_hash": inventory["package_hash"],
        "qualified_refusal_amendment": "phase85-refusal-amendment-v1",
        "collector_sha256": hash_file(HERE / "collector.py"),
        "instrument_sha256": hash_file(HERE / "instrument.py"),
        "refusal_sha256": hash_file(HERE / "refusal.py"),
        "handover_sha256": hash_file(root / "handover.json"),
        "boot_anchor_sha256": hash_file(root / "host-clock.json"),
        "readiness_sha256": hash_file(root / "continuation-readiness.json"),
        "export_sha256": hash_file(folder / "executions" / execution_id / "export.json"),
        "outcomes_rewritten": False,
    }
    path = folder / "executions" / execution_id / "continuation-provenance.json"
    if path.exists():
        if read(path) != value:
            raise ValueError("CONTINUATION_PROVENANCE_DRIFT")
    else:
        write_new(path, value)
        Ledger(folder).seal(path)


class ContinuationReceipt(Strict):
    kind: Literal["CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"]
    package_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    predecessor_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    identities_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parent_freeze_sha256: Literal[
        "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"
    ]
    first_export_sha256: Literal["283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"]
    expires_at: datetime
    signer: str
    readiness_sha256: str | None
    instance_id: str | None
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")


def verify_chain(
    receipts: Path,
    key: bytes,
    package: str,
    policy: Policy,
    identities: str,
    predecessor: str,
    at: datetime,
    *,
    prelaunch: bool = False,
) -> ContinuationReceipt:
    if len(key) < 32:
        raise ValueError("INVALID_CONTINUATION_KEY")
    last: ContinuationReceipt | None = None
    kinds = ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH")
    for kind in kinds[:2] if prelaunch else kinds:
        raw = read(receipts / f"{kind}.json")
        item = ContinuationReceipt.model_validate(raw)
        body = {k: v for k, v in raw.items() if k != "signature"}
        if (
            not hmac.compare_digest(
                hmac.new(key, canonical(body), "sha256").hexdigest(), item.signature
            )
            or item.kind != kind
            or item.package_hash != package
            or (
                item.predecessor_hash != predecessor
                or item.policy_sha256
                != hashlib.sha256(canonical(policy.model_dump(mode="json"))).hexdigest()
                or item.identities_sha256 != identities
            )
            or item.expires_at.tzinfo is None
            or item.expires_at <= at
            or (item.expires_at < policy.stop_at)
        ):
            raise ValueError("INVALID_CONTINUATION_AUTHORIZATION")
        predecessor = hashlib.sha256(canonical(raw)).hexdigest()
        last = item
    assert last is not None
    if not prelaunch and (not last.instance_id or not last.readiness_sha256):
        raise ValueError("CONTINUATION_LAUNCH_HOST_READINESS_REQUIRED")
    return last


class ContinuationAuthority(Authority):
    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        self.root, self.config = root, config
        super().__init__(
            Path(config["source"]),
            Path(config["manifest"]),
            original_policy(config["policy"]),
            config["schedule_hash"],
            Path(config["receipts"]),
            Path(config["key"]),
        )
        self.policy = ContinuationPolicy.model_validate(config["policy"])

    def verify(self, at: datetime | None = None, *, prelaunch: bool = False) -> str:
        at = at or utc()
        inventory = read(self.source / self.config["continuation"]["manifest"])
        files = inventory["files"]
        package = hashlib.sha256(canonical(files)).hexdigest()
        if inventory["kind"] != "CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE" or (
            package != inventory["package_hash"]
        ):
            raise ValueError("CONTINUATION_INVENTORY_DRIFT")
        for name, digest in files.items():
            path = (self.source / name).resolve()
            if self.source.resolve() not in path.parents or hash_file(path) != digest:
                raise ValueError("CONTINUATION_SOURCE_DRIFT: " + name)
        prefix = "artifacts/phase-8-continuation/v1/"
        scripts = {
            p.relative_to(self.source).as_posix() for p in (self.source / prefix).glob("*.py")
        }
        if scripts != {n for n in files if n.startswith(prefix) and n.endswith(".py")}:
            raise ValueError("CONTINUATION_EXECUTABLE_CLOSURE_DRIFT")
        super().verify(at)
        predecessor = hashlib.sha256(canonical(read(self.receipts / "LAUNCH.json"))).hexdigest()
        launch = verify_chain(
            Path(self.config["continuation"]["receipts"]),
            self.key.read_bytes(),
            package,
            self.policy,
            hash_file(self.root / "saved-identities.json"),
            predecessor,
            at,
            prelaunch=prelaunch,
        )
        verify_imported_first(self.root)
        if prelaunch:
            return hashlib.sha256(canonical(launch.model_dump(mode="json"))).hexdigest()
        readiness = self.root / "continuation-readiness.json"
        if hash_file(readiness) != launch.readiness_sha256:
            raise ValueError("CONTINUATION_READINESS_DRIFT")
        ready = read(readiness)
        if (
            ready["instance_id"] != launch.instance_id
            or ready["instance_id"] == ("i-0a6196aff6f8098ac")
            or ready["run_id"] != RUN
            or ready["policy_sha256"] != launch.policy_sha256
            or (ready["handover_sha256"] != hash_file(self.root / "handover.json"))
            or any(ready["checks"].get(k) is not True for k in CHECKS)
        ):
            raise ValueError("COLD_HANDOVER_READINESS_REQUIRED")
        if ready["boot_anchor_sha256"] != hash_file(self.root / "host-clock.json"):
            raise ValueError("CONTINUATION_BOOT_ANCHOR_DRIFT")
        return hashlib.sha256(canonical(launch.model_dump(mode="json"))).hexdigest()


def bind_host_segment(root: Path) -> None:
    """Fresh closed-boundary anchor after review/freeze; no admission or clock reset."""
    from research.execution_linux_v1.platform import boot_id

    if sys.platform != "linux":
        raise ValueError("LINUX_COLD_HANDOVER_ONLY")
    authority = ContinuationAuthority(root, read(root / "run.json"))
    proof = authority.verify(prelaunch=True)
    closed_boundary(
        Journal(root).rows(),
        read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")["rows"],
    )
    at = utc()
    if at < authority.policy.host_started_at or at >= authority.policy.stop_at:
        raise ValueError("ORIGINAL_DEADLINE_EXPIRED_OR_CLOCK_ROLLBACK")
    path = root / "host-clock.json"
    write_new(path, {"boot_id": boot_id(), "monotonic": time.monotonic(), "wall": at.isoformat()})
    journal = Journal(root)
    journal.event("HOST_CLOCK_SEALED", hash=hash_file(path))
    journal.event(
        "NEW_HOST_SEGMENT_CLOSED_BOUNDARY",
        freeze=proof,
        original_start=START,
        original_deadline=authority.policy.stop_at.isoformat(),
        operational_clock_reset=False,
    )


def release_reviewed_boundary(root: Path) -> None:
    """Release only this reviewed boundary; never clear later failure pauses."""
    authority = ContinuationAuthority(root, read(root / "run.json"))
    proof = authority.verify()
    from runner import verify_clock, verify_host_timer

    verify_clock(root, authority.policy, utc())
    verify_host_timer(root)
    journal = Journal(root)
    journal.verify()
    rows = journal.rows()
    saved = read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")["rows"]
    closed_boundary(rows, saved)
    if read(root / "pause.json")["reason"] != "CONTINUATION_REVIEW_REQUIRED":
        raise ValueError("ONLY_REVIEWED_IMPORT_PAUSE_CAN_BE_RELEASED")
    pause = root / "pause.json"
    pause.rename(root / "retained-import-pause.json")
    journal.event(
        "CONTINUATION_REVIEW_RELEASED", proof=proof, first=FIRST, operational_clock_reset=False
    )
    journal.event("RESUME_SAVED_ORDER", continuation_launch=proof)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("stage", "verify-import", "bind-host", "release-reviewed-boundary")
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--first", type=Path)
    args = parser.parse_args()
    if args.action == "stage":
        if args.master is None or args.first is None:
            parser.error("stage requires retained master and first-slot directories")
        stage(args.master.resolve(), args.first.resolve(), args.root.resolve())
    elif args.action == "verify-import":
        verify_imported_first(args.root.resolve())
    elif args.action == "bind-host":
        bind_host_segment(args.root.resolve())
    else:
        release_reviewed_boundary(args.root.resolve())
    print("PASS: no driver execution, AWS provisioning or signing performed")


if __name__ == "__main__":
    main()
