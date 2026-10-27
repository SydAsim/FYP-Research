"""Post-authorization, closed-boundary preparation. Never launches a driver."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import socket
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from closed_restart import NEXT, boundary, stage
from controls import Journal, canonical, hash_file, read, utc, write_new
from handover import ContinuationAuthority, bind_host_segment, ro_rows, verify_imported_first

OLD = Path("/var/lib/p8-continuation-v7/run")
INSTANCE = "i-057344e5372faf62f"


def prepare(root: Path, external: Path) -> None:
    """Called only after exact freeze and deployment authorization are verified."""
    if root.exists() or os.name != "posix":
        raise ValueError("FRESH_LINUX_METADATA_ROOT_REQUIRED")
    proof = read(external)
    key = Path("/var/lib/fyp-owner/owner.key").read_bytes()
    body = {k: v for k, v in proof.items() if k != "signature"}
    if not hmac.compare_digest(
        hmac.new(key, canonical(body), "sha256").hexdigest(), proof["signature"]
    ):
        raise ValueError("UNSIGNED_EXTERNAL_REUSE_GATES")
    required = (
        "freeze_verified",
        "explicit_deployment_authorization",
        "host_ownership",
        "prestart_independent_preparation_stop",
        "source_archive_and_members",
        "dependency_records_and_versions",
        "same_instance_and_root",
        "no_inbound_access",
        "original_deadline_and_budget_fit",
    )
    if proof["instance_id"] != INSTANCE or any(
        proof["checks"].get(k) is not True for k in required
    ):
        raise ValueError("REUSE_EXTERNAL_GATES_NOT_VERIFIED")
    expiration = datetime.fromisoformat(proof["expires_at"].replace("Z", "+00:00"))
    if expiration.tzinfo is None or expiration <= utc():
        raise ValueError("STALE_REUSE_EXTERNAL_GATES")
    # Quiesce operational units only. The old durable pause and entire old root remain.
    subprocess.run(
        ["systemctl", "stop", "fyp-phase8-campaign.service", "fyp-phase8-watchdog.service"],
        check=True,
        timeout=40,
    )
    for unit in ("fyp-phase8-campaign.service", "fyp-phase8-watchdog.service"):
        result = subprocess.run(
            ["systemctl", "show", unit, "--property=MainPID", "--value"],
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        )
        if result.stdout.strip() != "0":
            raise ValueError("OLD_OPERATIONAL_PROCESS_NOT_QUIESCED")
    pinned = read(Path(__file__).parent / "closed-120/ledger-read-only.json")["rows"]
    boundary(ro_rows(OLD), pinned)
    if read(OLD / "pause.json")["reason"] != "WALL_CLOCK_BACKWARD_STOP_ADMISSIONS":
        raise ValueError("OLD_PAUSE_DRIFT")
    for port in (16432, 16433, 19100, 19101, 19102, 19110):
        with socket.socket() as handle:
            handle.bind(("127.0.0.1", port))
    stage(Path(__file__).parent / "closed-120", root)
    # Retain additional old operational notices emitted during boot, separately
    # from the accepted snapshot; neither historical source is overwritten.
    folder = root / "postboot-old-operational-evidence"
    folder.mkdir()
    uri = (OLD / "campaign.sqlite3").resolve().as_uri() + "?mode=ro"
    with (
        sqlite3.connect(uri, uri=True) as original,
        sqlite3.connect(folder / "campaign.sqlite3") as saved,
    ):
        original.execute("BEGIN")
        original.backup(saved)
    (folder / "pause.json").write_bytes((OLD / "pause.json").read_bytes())
    journal = subprocess.run(
        [
            "journalctl",
            "-u",
            "fyp-phase8-campaign.service",
            "-u",
            "fyp-phase8-watchdog.service",
            "--no-pager",
            "-o",
            "short-iso-precise",
        ],
        check=True,
        text=True,
        capture_output=True,
        timeout=30,
    )
    (folder / "journal.log").write_text(journal.stdout)
    write_new(folder / "external-readiness.json", proof)
    authority = ContinuationAuthority(root, read(root / "run.json"))
    if (
        read(
            Path(read(root / "run.json")["source"])
            / read(root / "run.json")["continuation"]["manifest"]
        )["package_hash"]
        != proof["package_hash"]
    ):
        raise ValueError("REUSE_EXTERNAL_PACKAGE_BINDING_DRIFT")
    authority.verify(prelaunch=True)  # no launch receipt means no main admission
    verify_imported_first(root)
    bind_host_segment(root)  # fresh monotonic boot anchor; original start/deadline unchanged
    write_new(
        root / "reuse-preparation.json",
        {
            "status": "PASS_PREPARATION_NOT_LAUNCH",
            "instance_id": INSTANCE,
            "next_execution_id": NEXT,
            "backed_up": 120,
            "planned": 1380,
            "external_sha256": hash_file(external),
            "original_deadline": authority.policy.stop_at.isoformat(),
            "original_policy_unchanged": True,
            "old_root_untouched": True,
            "driver_calls": 0,
        },
    )
    Journal(root).event(
        "REUSED_HOST_CLOSED120_PREPARED", hash=hash_file(root / "reuse-preparation.json")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--external-gates", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.root.resolve(), args.external_gates.resolve())
    print(json.dumps(read(args.root / "reuse-preparation.json")))


if __name__ == "__main__":
    main()
