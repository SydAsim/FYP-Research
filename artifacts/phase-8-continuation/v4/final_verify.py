"""Read-only integrated source/authority/preservation checks; no new authorization."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("E:/p8v4/source")
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
RUNTIME = SOURCE / PREFIX
sys.path.insert(0, str(RUNTIME))
from controls import canonical, hash_file, read, write_new  # noqa: E402
from handover import ContinuationAuthority, ContinuationPolicy  # noqa: E402


def main() -> None:
    package = read(HERE / "candidate-package.json")
    inventory = read(HERE / "candidate-inventory.json")
    assert hashlib.sha256(canonical(inventory["files"])).hexdigest() == package["package_hash"]
    assert hash_file(HERE / "v4-complete-continuation-review-candidate.tar.gz") == package["archive_sha256"]
    assert hash_file(RUNTIME / "candidate-inventory.json") == package["inventory_sha256"]
    qualification = sorted(HERE.glob("linux-control-attempt-*/qualification.json"))[-1]
    assert read(qualification)["status"] == "PASS"
    qarchive = qualification.parent / "qualification-source.tar.gz"
    critical = ("controls.py", "closed_prefix.py", "handover.py", "runner.py", "analyze.py", "imported_analysis.py", "test_closed_prefix.py", "test_ledger_snapshot.py")
    with tarfile.open(qarchive) as raw:
        for name in critical:
            stream = raw.extractfile(PREFIX + "/" + name)
            assert stream is not None
            assert hashlib.sha256(stream.read()).hexdigest() == inventory["files"][PREFIX + "/" + name], name
    sys.path.insert(0, str(HERE))
    from qualify import verify_preserved

    preserved = verify_preserved()
    config = read(Path("E:/p8v4/qualified-import/run.json"))
    config.update(source=str(SOURCE), manifest=str(SOURCE / "artifacts/phase-8-review-freeze/v2/review-inventory.json"),
                  key="C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2/owner.key",
                  receipts="C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2/receipts")
    missing = Path("C:/Users/syeda/.fyp-research/phase8-owner/phase85-complete-v4/receipts")
    assert not missing.exists()
    config["continuation"]["receipts"] = str(missing)
    try:
        ContinuationAuthority(Path("E:/p8v4/qualified-import"), config).verify()
    except FileNotFoundError as error:
        assert error.filename == str(missing / "CONTINUATION_ACCEPTED.json")
        guard = "MISSING_NEW_V4_ACCEPTANCE_FREEZE_LAUNCH_REJECTED_AFTER_SOURCE_AND_PARENT_AUTHORITY_CHECKS"
    else:
        raise AssertionError("UNAUTHORIZED_CANDIDATE_NOT_REJECTED")
    proposal = read(HERE / "deployment-config.json")
    policy = ContinuationPolicy.model_validate(read(RUNTIME / "original-launch-policy.json"))
    now = datetime.now(UTC)
    previous = read(HERE / "feasibility.json")
    finish = now + timedelta(hours=previous["reviewed_allowance_remaining_hours"])
    estimated = policy.committed_cost(finish + timedelta(minutes=30))
    assert estimated < 55 and finish < policy.stop_at - timedelta(minutes=30)
    projected_storage = read(HERE / "storage-projection.json")["projected_before_final_archive_bytes"] + package["archive_bytes"]
    assert projected_storage < policy.cloud_limit_bytes
    proof = read(RUNTIME / "stopped-boundary-reference.json")
    assert inventory["files"][PREFIX + "/boundary/authoritative-snapshot.tar.gz"] == proof["sha256"]
    cli = subprocess.run(["aws", "ec2", "describe-instances", "--instance-ids", "i-002b63326e1566005", "--profile", "fyp-research", "--region", "ap-southeast-2", "--no-cli-pager", "--output", "json"], capture_output=True, encoding="utf-8", timeout=90, env={**os.environ,"PYTHONUTF8":"1"})
    write_new(HERE / "final-host-state-read.json", {"at_utc":now.isoformat(),"exit":cli.returncode,"stdout":cli.stdout,"stderr":cli.stderr})
    assert cli.returncode == 0
    state = json.loads(cli.stdout)["Reservations"][0]["Instances"][0]["State"]["Name"]
    assert state == "stopped"
    assert proposal["accepted"] is False and proposal["frozen"] is False and proposal["launch_authorized"] is False
    final: dict[str, Any] = {
        "status":"PASS","scope":"READY_FOR_REVIEW_NOT_HOST_READINESS","at_utc":datetime.now(UTC).isoformat(),
        "package_hash":package["package_hash"],"archive_sha256":package["archive_sha256"],"inventory_sha256":package["inventory_sha256"],
        "archive_members_verified":read(HERE / "archive-closure-verification.json")["verified_members"],
        "critical_qualified_code_identical_to_final_archive":list(critical),
        "parent_chain":"PASS","preservation":preserved,"Linux_controls_passed":29,
        "successful_Linux_seconds":read(qualification)["elapsed_seconds"],"qualification_file":str(qualification),
        "admission_authority_rejection":guard,"source_and_parent_authority_checks":"PASS",
        "metadata_boundary":{"BACKED_UP":38,"PLANNED":1462,"original_identities":1500,"next_sequence":39,"next_arm":"B3","next_execution_id":"01a11705-11f0-73c0-af15-dd9f1d590b08"},
        "feasibility_refresh":{"at_utc":now.isoformat(),"allowance_finish_utc":finish.isoformat(),"conservative_cost_usd":estimated,"rates_and_cloud_inventory_from":previous["at_utc"],"projected_cloud_bytes_including_candidate":projected_storage},
        "AWS_compute_state":state,"new_AWS_compute_provisioned":False,"new_AWS_compute_started":False,
        "main_driver_calls":0,"replaced_outcomes":0,"database_restores":0,
        "accepted":False,"frozen":False,"deployment_authorized":False,"main_launched":False,
        "original_deadline":"2026-10-22T15:24:23.810674Z","guard_usd":55,"total_usd":65,
        "remaining_requirements":["Review exact candidate","Accept then verify immutable v4 freeze against parent","Separate fresh-host deployment/launch authorization","Actual-host source/runtime/permission/backup/timer/headroom gates and refreshed feasibility","Stopped root retention decision by 2026-10-10T17:14:53.076527Z"],
        "limitations":["Cached pinned Linux image has deployment Python/dependency versions but a different Python binary build from the pinned host standalone distribution","Local Docker incidentally restored old app containers; they were stopped, and no scientific driver/calibration was run","Passing focused tests does not guarantee an error-free campaign","Billing lag and evidence-retention costs remain; no runtime/shutdown policy expansion"]}
    write_new(HERE / "final-verification.json", final)
    print(json.dumps(final,indent=2))


if __name__ == "__main__":
    main()
