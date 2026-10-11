"""Finite terminal postflight: verify saved evidence, back up, then owned cleanup.

No case admission, driver replay, model calls, or dependency on a Codex session.
Cloud execution continues independently if this local postflight is interrupted.
"""

import argparse
import base64
import json
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PILOT = HERE.parent / "v1"
sys.path[:0] = [str(REPO), str(PILOT)]
from backups_p82 import verify as verify_backups  # noqa: E402
from measure_p82 import execution  # noqa: E402

from research.execution_setup.core import (  # noqa: E402
    check_inventory,
    digest,
    immutable,
    load,
    now,
)

CLI = "C:/Program Files/Amazon/AWSCLIV2/aws.exe"
BUCKET = "fyp-p82-20261005-018da1d6-803656589923"


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0, le=4 * 1024**3)
    version_id: str
    upload_exit: int
    main_started: Literal[False]
    action: str

    def validate_key(self) -> None:
        if self.key != f"exports/phase83-evidence-{self.sha256}.tar.gz":
            raise ValueError("UNEXPECTED_EXPORT_KEY")


def aws(arguments: list[str]) -> dict[str, Any]:
    name = str(time.time_ns())
    args = [CLI, *arguments, "--profile", "fyp-research", "--region", "ap-southeast-2",
            "--output", "json"]
    immutable(HERE / "journal" / (name + "-request.json"), {"at": now(), "args": args})
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        immutable(HERE / "journal" / (name + "-response.json"), {
            "at": now(), "status": "UNKNOWN_TIMEOUT", "reconcile_before_retry": True})
        raise
    immutable(HERE / "journal" / (name + "-response.json"), {
        "at": now(), "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    result.check_returncode()
    value: dict[str, Any] = json.loads(result.stdout) if result.stdout.strip() else {}
    return value  # CLI JSON boundary; destructive actions require guards below.


def owned(config: dict[str, Any]) -> dict[str, Any]:
    response = aws(["ec2", "describe-instances", "--instance-ids", config["instance_id"]])
    instances = [i for r in response["Reservations"] for i in r["Instances"]]
    if len(instances) != 1:
        raise ValueError("EXACT_SINGLE_INSTANCE_REQUIRED")
    instance: dict[str, Any] = instances[0]
    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
    if (instance["InstanceId"] != config["instance_id"]
            or tags.get("research.owner") != config["owner"]
            or tags.get("research.stage") != "8.3"):
        raise ValueError("INSTANCE_OWNERSHIP_GUARD")
    return instance


def check_head(receipt: Receipt, head: dict[str, Any]) -> None:
    receipt.validate_key()
    if (head.get("VersionId") != receipt.version_id
            or head["ContentLength"] != receipt.bytes
            or head.get("Metadata", {}).get("sha256") != receipt.sha256
            or base64.b64decode(head["ChecksumSHA256"]).hex() != receipt.sha256):
        raise ValueError("S3_EXPORT_HASH_SIZE_VERSION_DRIFT")


def copy_verified(source: Path, destination: Path, expected: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with source.open("rb") as incoming, destination.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    if digest(destination) != expected:
        raise ValueError("LOCAL_COPY_HASH_DRIFT_RETAIN_ORIGINAL")


def finish(config: dict[str, Any], receipt: Receipt) -> None:
    head = aws(["s3api", "head-object", "--bucket", BUCKET, "--key", receipt.key,
                "--checksum-mode", "ENABLED"])
    check_head(receipt, head)
    primary = Path(config["primary"]) / config["owner"]
    secondary = Path(config["secondary"]) / config["owner"]
    primary.mkdir(parents=True, exist_ok=True)
    secondary.mkdir(parents=True, exist_ok=True)
    for folder in (primary, secondary):
        if shutil.disk_usage(folder).free < receipt.bytes * 3 + 1024**3:
            raise ValueError("BACKUP_DISK_RESERVE_NO_CLEANUP")
    archive = primary / (receipt.sha256 + ".tar.gz")
    if not archive.exists():
        response = aws(["s3api", "get-object", "--bucket", BUCKET, "--key", receipt.key,
                        "--version-id", receipt.version_id, str(archive)])
        if response.get("VersionId") != receipt.version_id:
            raise ValueError("DOWNLOADED_VERSION_DRIFT")
    if archive.stat().st_size != receipt.bytes or digest(archive) != receipt.sha256:
        raise ValueError("DOWNLOADED_ARCHIVE_DRIFT_RETAIN_ORIGINAL")
    other = secondary / archive.name
    copy_verified(archive, other, receipt.sha256)
    extracted = primary / "x"
    if extracted.exists():
        raise ValueError("EXISTING_EXTRACT_NO_OVERWRITE_OR_SILENT_RETRY")
    extracted.mkdir()
    with tarfile.open(archive, "r:gz") as incoming:
        incoming.extractall(extracted, filter="data")
    root, backup = extracted / "fyp-p83-v1", extracted / "fyp-p83-backup-v1"
    # The source package and observed first execution tie this receipt to this host.
    if digest(extracted / "p83.zip") != config["package_sha256"]:
        raise ValueError("ARCHIVE_SOURCE_PACKAGE_MISMATCH")
    identifiers: list[str] = []
    for path in root.glob("blocks/*/*/run/ledger.sqlite3"):
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as connection:
            identifiers.extend(r[0] for r in connection.execute(
                "SELECT execution_id FROM slots WHERE execution_id IS NOT NULL"))
    if config["first_execution_id"] not in identifiers:
        raise ValueError("ARCHIVE_NOT_THE_OBSERVED_PILOT")
    if load(root / "planned-slots.json") != load(PILOT / "slots.json")["slots"]:
        raise ValueError("PLANNED_ORDER_DRIFT")
    if (root / "accounting.json").exists():
        accounting = load(root / "accounting.json")
        if (accounting["planned_executions"] != 24 or accounting["main_started"] is not False
                or len(accounting["slots"]) != 24):
            raise ValueError("PLANNED_OUTCOME_ACCOUNTING_DRIFT")
    # Preserve failures and unresolved grades; a diagnostic regrade never replaces them.
    regrades = []
    for path in sorted(root.rglob("export.json")):
        try:
            regrades.append(execution(path))
        except Exception as error:
            regrades.append({"trace": str(path), "failure": str(error),
                             "type": type(error).__name__, "original_retained": True})
    backups = verify_backups(backup)
    check_inventory(load(PILOT / "preserved-before.json"), REPO)
    proof = {
        "at": now(), "owner": config["owner"], "receipt": receipt.model_dump(),
        "primary": str(archive), "secondary": str(other), "two_copy_sha256": receipt.sha256,
        "local_physical_storage": "BOTH_ON_DISK_0_NOT_INDEPENDENT_HARDWARE",
        "independent_storage": "VERSIONED_S3_OBJECT_CHECKSUM_VERIFIED",
        "backups": backups, "independent_regrades": regrades,
        "main_started": False, "protocol_frozen": False,
    }
    immutable(HERE / "verified-backups.json", proof)
    instance = owned(config)
    if instance["State"]["Name"] == "terminated":
        raise ValueError("ALREADY_TERMINATED_RECONCILE_NOT_NEW_CLEANUP")
    roots = [b["Ebs"] for b in instance["BlockDeviceMappings"]
             if b["DeviceName"] == instance["RootDeviceName"]]
    if len(roots) != 1 or not roots[0]["DeleteOnTermination"]:
        raise ValueError("ROOT_DISK_DELETE_GUARD")
    volume = roots[0]["VolumeId"]
    described = aws(["ec2", "describe-volumes", "--volume-ids", volume])["Volumes"][0]
    tags = {t["Key"]: t["Value"] for t in described.get("Tags", [])}
    if tags.get("research.owner") != config["owner"] or tags.get("research.stage") != "8.3":
        raise ValueError("ROOT_VOLUME_OWNERSHIP_GUARD")
    immutable(HERE / "cleanup-intent.json", {"at": now(), "instance_id": config["instance_id"],
              "volume_id": volume, "backup_proof_sha256": digest(HERE / "verified-backups.json")})
    aws(["ec2", "terminate-instances", "--instance-ids", config["instance_id"]])
    # An ambiguous terminate stops this controller. A later operator reconciles this exact ID.
    for _ in range(20):
        state = owned(config)["State"]["Name"]
        if state == "terminated":
            break
        time.sleep(15)
    else:
        raise TimeoutError("TERMINATION_NOT_CONFIRMED_RETAIN_CLEANUP_INTENT")
    result = subprocess.run([CLI, "ec2", "describe-volumes", "--volume-ids", volume,
                            "--profile", "fyp-research", "--region", "ap-southeast-2"],
                            capture_output=True, text=True, timeout=60)
    immutable(HERE / "root-volume-final-response.json", {"exit": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr, "volume_id": volume})
    if result.returncode == 0 or "InvalidVolume.NotFound" not in result.stderr:
        raise ValueError("ROOT_VOLUME_DELETION_NOT_CONFIRMED")
    immutable(HERE / "complete.json", {"at": now(), "status": "BACKED_UP_AND_CLEANED",
              "instance_id": config["instance_id"], "volume_id": volume,
              "main_started": False, "qualification_report": "verified-backups.json",
              "note": "Completion of cleanup is not a claim that all pilot gates passed"})
    print("Verified evidence copies and S3; exact pilot host/disk removed.", flush=True)


def main() -> None:
    config = load(HERE / "config.json")
    check_inventory(load(HERE / "seal.json")["files"], HERE)
    check_inventory(load(PILOT / "seal.json")["files"], PILOT)
    hard = datetime.fromisoformat(config["deadline"])
    while datetime.now(UTC) < hard + timedelta(hours=1):
        result = aws(["s3api", "list-objects-v2", "--bucket", BUCKET,
                      "--prefix", "exports/phase83-receipt-"])
        for obj in result.get("Contents", []):
            if datetime.fromisoformat(obj["LastModified"]) < hard - timedelta(hours=6):
                continue
            path = HERE / ("receipt-" + str(time.time_ns()) + ".json")
            aws(["s3api", "get-object", "--bucket", BUCKET, "--key", obj["Key"], str(path)])
            receipt = Receipt.model_validate(load(path))
            finish(config, receipt)
            return
        if datetime.now(UTC) >= hard and not (HERE / "cost-stop-intent.json").exists():
            instance = owned(config)
            immutable(HERE / "cost-stop-intent.json", {"at": now(), "state": instance["State"]})
            if instance["State"]["Name"] in ("running", "pending"):
                aws(["ec2", "stop-instances", "--instance-ids", config["instance_id"]])
        time.sleep(60)  # read-only export polling, no scenario fault placement
    raise TimeoutError("NO_VERIFIED_EXPORT_RETAIN_DISK_EVIDENCE_AND_REQUEST_REVIEW")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    try:
        main()
    except Exception as error:
        immutable(HERE / ("failure-" + str(time.time_ns()) + ".json"), {
            "at": now(), "type": type(error).__name__, "detail": str(error),
            "new_admissions": 0, "evidence_retained": True,
            "instruction": "Reconcile saved IDs and deadlines; do not replay or overwrite"})
        raise
