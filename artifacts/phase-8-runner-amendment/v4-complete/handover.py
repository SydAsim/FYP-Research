"""Closed-slot cold handover. Staging never signs, provisions or admits a slot."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from clock_sampling import anchor_record, sample
from controls import Authority, Journal, Policy, Strict, canonical, hash_file, read, utc, write_new
from operational_limits import LIMITS_SHA256, effective_policy, verified_limits
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
    uri = master.joinpath("campaign.sqlite3").resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("BEGIN")
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
    from closed1297 import REL, check_rows

    if any(
        any(a[k] != b[k] for k in ("sequence", "case_id", "arm", "attempt", "fixture_hash"))
        for a, b in zip(rows, saved, strict=True)
    ):
        raise ValueError("SAVED_ORDER_OR_BINDING_DRIFT")
    check_rows(rows, read(Path("/var/lib/p8-continuation-v9/run") / REL)["rows"])


def original_policy(raw: dict[str, Any]) -> Policy:
    expected = read(HERE / "original-launch-policy.json")
    policy = Policy.model_validate(raw)
    if (
        policy != Policy.model_validate(expected)
        or policy.run_id != RUN
        or (policy.host_started_at != datetime.fromisoformat(START.replace("Z", "+00:00")))
    ):
        raise ValueError("ORIGINAL_POLICY_OR_CLOCK_RESET")
    return policy


def stage(master: Path, destination: Path) -> dict[str, Any]:
    from closed_restart import stage as import_closed

    return import_closed(master, destination)


def verify_imported_first(root: Path) -> None:
    """Compatibility entry point verifies all 120 retained originals."""
    from closed_prefix import verify

    verify(root)
    from closed616 import verify as verify616

    verify616(root)
    from closed1297 import verify as verify1297
    verify1297(root)
    from closed_restart import verify as verify_closed82

    verify_closed82(root)
    from closed145 import verify_history

    verify_history(root)


def record_provenance(root: Path, folder: Path, execution_id: str) -> None:
    from research.execution_setup.core import Ledger

    config = read(root / "run.json")
    inventory = read(Path(config["source"]) / config["continuation"]["manifest"])
    value = {
        "version": "phase85-continuation-v12",
        "execution_id": execution_id,
        "run_id": RUN,
        "parent_freeze_sha256": PARENT_FREEZE,
        "continuation_package_hash": inventory["package_hash"],
        "qualified_refusal_amendment": "phase85-preflight-amendment-v2",
        "collector_sha256": hash_file(HERE / "collector.py"),
        "instrument_sha256": hash_file(HERE / "instrument.py"),
        "refusal_sha256": hash_file(HERE / "refusal.py"),
        "response_guard_sha256": hash_file(HERE / "response_guard.py"),
        "two_originals_sha256": hash_file(HERE / "two_originals.py"),
        "closed_prefix_sha256": hash_file(HERE / "closed_prefix.py"),
        "controls_sha256": hash_file(HERE / "controls.py"),
        "clock_sampling_sha256": hash_file(HERE / "clock_sampling.py"),
        "inventory_read_sha256": hash_file(HERE / "inventory_read.py"),
        "storage_sha256": hash_file(HERE / "storage.py"),
        "closed_restart_sha256": hash_file(HERE / "closed_restart.py"),
        "restart_boundary_sha256": hash_file(root / "restart-boundary.json"),
        "handover_sha256": hash_file(root / "handover.json"),
        "boot_anchor_sha256": hash_file(root / "host-clock.json"),
        "readiness_sha256": hash_file(root / "continuation-readiness.json"),
        "operational_limits_sha256": LIMITS_SHA256,
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
    operational_limits_sha256: Literal[
        "68421df365be6cd8696c137e7b5f32c27634b87085315086ee3b1841c2841769"
    ]
    predecessor_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    identities_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parent_freeze_sha256: Literal[
        "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"
    ]
    first_export_sha256: Literal["283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"]
    second_export_sha256: Literal[
        "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42"
    ]
    immediate_parent_freeze_sha256: Literal[
        "1de01eb9ce2a8ebfa9b8a2591bbf84f62abf031d7dadf32bfaffa3254164095a"
    ]
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
        if config.get("operational_limits_sha256") != LIMITS_SHA256:
            raise ValueError("CONTINUATION_LIMIT_BINDING_REQUIRED")
        verified_limits()
        self.policy = effective_policy(config["policy"])

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
        prefix = "artifacts/phase-8-runner-amendment/v4-complete/"
        scripts = {
            p.relative_to(self.source).as_posix() for p in (self.source / prefix).glob("*.py")
        }
        if scripts != {n for n in files if n.startswith(prefix) and n.endswith(".py")}:
            raise ValueError("CONTINUATION_EXECUTABLE_CLOSURE_DRIFT")
        # Authenticate historical receipts against their exact original 55/30
        # policy. Never re-sign or reinterpret their commitments as 60/60.
        Authority(
            self.source,
            self.manifest,
            original_policy(self.config["policy"]),
            self.schedule_hash,
            self.receipts,
            self.key,
        ).verify(datetime.fromisoformat(START.replace("Z", "+00:00")))
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
            or ready["instance_id"]
            in ("i-0a6196aff6f8098ac", "i-034252c3e9b083abf", "i-002b63326e1566005")
            or ready["run_id"] != RUN
            or ready["policy_sha256"] != launch.policy_sha256
            or ready.get("operational_limits_sha256") != LIMITS_SHA256
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
    boot = boot_id()
    reading = sample()
    at = reading.wall
    if at < authority.policy.host_started_at or at >= authority.policy.stop_at:
        raise ValueError("ORIGINAL_DEADLINE_EXPIRED_OR_CLOCK_ROLLBACK")
    path = root / "host-clock.json"
    path.rename(root / "retained-host-clock-before-v12.json")
    write_new(path, anchor_record(reading, boot))
    journal = Journal(root)
    journal.event("HOST_CLOCK_SEALED", hash=hash_file(path), measurement=read(path))
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
    from prelaunch_backup import verify_proof
    from storage import S3Cloud

    cloud_config = read(root / "cloud.json")
    cloud = S3Cloud(cloud_config["bucket"], cloud_config["prefix"])
    verify_proof(root, "prelaunch", cloud)
    verify_proof(root, "complete", cloud)
    from runner import verify_clock, verify_host_timer

    verify_clock(root, authority.policy)
    verify_host_timer(root)
    journal = Journal(root)
    journal.verify()
    rows = journal.rows()
    saved = read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")["rows"]
    closed_boundary(rows, saved)
    if (
        hash_file(root / "pause.json")
        != "7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8"
    ):
        raise ValueError("ONLY_REVIEWED_IMPORT_PAUSE_CAN_BE_RELEASED")
    pause = root / "pause.json"
    pause.rename(root / "retained-protocol1297-pause-v12.json")
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
    parser.add_argument("--second", type=Path)
    parser.add_argument("--first-archive", type=Path)
    parser.add_argument("--second-archive", type=Path)
    args = parser.parse_args()
    if args.action == "stage":
        if args.master is None:
            parser.error("stage requires the authoritative stopped-boundary metadata")
        stage(args.master.resolve(), args.root.resolve())
    elif args.action == "verify-import":
        verify_imported_first(args.root.resolve())
    elif args.action == "bind-host":
        bind_host_segment(args.root.resolve())
    else:
        release_reviewed_boundary(args.root.resolve())
    print("PASS: no driver execution, AWS provisioning or signing performed")


if __name__ == "__main__":
    main()
