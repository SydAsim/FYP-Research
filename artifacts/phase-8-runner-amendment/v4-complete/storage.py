"""Per-slot backups and conservative versioned-object capacity reservations."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import shutil
import sqlite3
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any, Protocol

from controls import Journal, Policy, Strict, hash_file, read, write_new
from pydantic import BaseModel, ConfigDict, Field


class ObjectProof(Strict):
    bucket: str
    key: str
    version_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0)


class VersionRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    Key: str
    VersionId: str = Field(min_length=1)
    Size: int = Field(ge=0, strict=True)


class VersionPage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    Versions: list[VersionRecord] = []


class HeadRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    VersionId: str
    ContentLength: int = Field(ge=0, strict=True)
    Metadata: dict[str, str]
    ChecksumSHA256: str


class Cloud(Protocol):
    bucket: str
    prefix: str

    def inventory(self) -> int: ...
    def put(self, path: Path, key: str) -> ObjectProof: ...
    def verify(self, proof: ObjectProof) -> None: ...
    def find(self, key: str, digest: str, size: int) -> ObjectProof: ...


class S3Cloud:
    def __init__(self, bucket: str, prefix: str) -> None:
        import boto3
        from botocore.config import Config

        self.bucket, self.prefix = bucket, prefix
        # One client; role credentials on the eventual host. No credentials in source.
        self.client: Any = boto3.Session(region_name="ap-southeast-2").client(
            "s3",
            config=Config(
                connect_timeout=10,
                read_timeout=30,
                retries={"total_max_attempts": 1, "mode": "standard"},
            ),
        )
        if (
            self.client.get_bucket_location(Bucket=bucket).get("LocationConstraint")
            != "ap-southeast-2"
        ):
            raise ValueError("SYDNEY_EVIDENCE_BUCKET_REQUIRED")
        if self.client.get_bucket_versioning(Bucket=bucket).get("Status") != "Enabled":
            raise ValueError("VERSIONED_CLOUD_REQUIRED")

    def inventory(self) -> int:
        from inventory_read import bounded_inventory

        return bounded_inventory(self.bucket, self.prefix)

    def put(self, path: Path, key: str) -> ObjectProof:
        if not key.startswith(self.prefix) or path.stat().st_size >= 5 * 1024**3:
            raise ValueError("DEDICATED_SINGLE_PUT_SCOPE_LIMIT")
        digest = hash_file(path)
        with path.open("rb") as body:
            value = self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentLength=path.stat().st_size,
                ServerSideEncryption="AES256",
                Metadata={"sha256": digest},
                ChecksumSHA256=base64.b64encode(bytes.fromhex(digest)).decode(),
                IfNoneMatch="*",
            )
        proof = ObjectProof(
            bucket=self.bucket,
            key=key,
            version_id=value["VersionId"],
            sha256=digest,
            bytes=path.stat().st_size,
        )
        self.verify(proof)
        return proof

    def verify(self, proof: ObjectProof) -> None:
        if proof.bucket != self.bucket or not proof.key.startswith(self.prefix):
            raise ValueError("CLOUD_PROOF_SCOPE_DRIFT")
        head = self.client.head_object(
            Bucket=self.bucket, Key=proof.key, VersionId=proof.version_id, ChecksumMode="ENABLED"
        )
        head = HeadRecord.model_validate(head).model_dump()
        if (
            head.get("VersionId") != proof.version_id
            or head["ContentLength"] != proof.bytes
            or head.get("Metadata", {}).get("sha256") != proof.sha256
            or base64.b64decode(head.get("ChecksumSHA256", "")).hex() != proof.sha256
        ):
            raise ValueError("CLOUD_VERSION_HASH_DRIFT")

    def find(self, key: str, digest: str, size: int) -> ObjectProof:
        matches = []
        for page in self.client.get_paginator("list_object_versions").paginate(
            Bucket=self.bucket, Prefix=key
        ):
            for value in VersionPage.model_validate(page).Versions:
                if value.Key == key:
                    proof = ObjectProof(
                        bucket=self.bucket,
                        key=key,
                        version_id=value.VersionId,
                        sha256=digest,
                        bytes=size,
                    )
                    self.verify(proof)
                    matches.append(proof)
        if len(matches) != 1:
            raise ValueError("AMBIGUOUS_UPLOAD_NOT_UNIQUELY_RECONCILED")
        return matches[0]


class OfflineCloud:
    """Explicit filesystem surrogate, used only for separate local calibration."""

    bucket = "offline-calibration"

    def __init__(self, root: Path, prefix: str = "calibration/") -> None:
        self.root, self.prefix = root, prefix
        root.mkdir(parents=True, exist_ok=True)

    def inventory(self) -> int:
        return sum(p.stat().st_size for p in self.root.rglob("*.object"))

    def put(self, path: Path, key: str) -> ObjectProof:
        if not key.startswith(self.prefix):
            raise ValueError("OFFLINE_SCOPE")
        digest = hash_file(path)
        destination = self.root / f"{digest}.object"
        with path.open("rb") as incoming, destination.open("xb") as output:
            shutil.copyfileobj(incoming, output)
        return ObjectProof(
            bucket=self.bucket,
            key=key,
            version_id=destination.name,
            sha256=digest,
            bytes=destination.stat().st_size,
        )

    def verify(self, proof: ObjectProof) -> None:
        path = self.root / proof.version_id
        if hash_file(path) != proof.sha256 or path.stat().st_size != proof.bytes:
            raise ValueError("OFFLINE_CLOUD_DRIFT")

    def find(self, key: str, digest: str, size: int) -> ObjectProof:
        proof = ObjectProof(
            bucket=self.bucket, key=key, version_id=digest + ".object", sha256=digest, bytes=size
        )
        self.verify(proof)
        return proof


def reconcile_upload(journal: Journal, cloud: Cloud, archive: Path) -> ObjectProof:
    """Read-only object reconciliation. Never repeats a PUT or clears a failure pause."""
    digest = hash_file(archive)
    key = cloud.prefix + digest + ".tar.gz"
    with journal.connect() as db:
        reservation = db.execute("SELECT * FROM reservations WHERE key=?", (key,)).fetchone()
    if reservation is None or reservation["bytes"] != archive.stat().st_size:
        raise ValueError("ORIGINAL_RESERVATION_REQUIRED")
    proof = cloud.find(key, digest, reservation["bytes"])
    cloud.verify(proof)
    with journal.connect() as db:
        db.execute(
            "UPDATE reservations SET state='VERIFIED',version=? WHERE key=?",
            (proof.version_id, key),
        )
    journal.event("READ_ONLY_UPLOAD_RECONCILED", proof=proof.model_dump())
    return proof


def upload(journal: Journal, cloud: Cloud, policy: Policy, archive: Path) -> ObjectProof:
    digest = hash_file(archive)
    key = cloud.prefix + digest + ".tar.gz"
    size = archive.stat().st_size
    with journal.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        prior = db.execute("SELECT * FROM reservations WHERE key=?", (key,)).fetchone()
        outstanding = db.execute(
            "SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'"
        ).fetchone()[0]
        if prior:
            if prior["state"] != "VERIFIED":
                raise ValueError("AMBIGUOUS_UPLOAD_RECONCILE_NO_RESEND")
            proof = ObjectProof(
                bucket=cloud.bucket, key=key, version_id=prior["version"], sha256=digest, bytes=size
            )
            cloud.verify(proof)
            return proof
        if outstanding:
            raise ValueError("AMBIGUOUS_UPLOAD_RECONCILE_NO_NEW_PUT")
        if cloud.inventory() + outstanding + size >= policy.cloud_limit_bytes:
            raise ValueError("CLOUD_30GIB_RESERVATION_STOP")
        db.execute("INSERT INTO reservations VALUES(?,?,'RESERVED',NULL)", (key, size))
    journal.event("CLOUD_PUT_RESERVED", key=key, bytes=size)
    try:
        proof = cloud.put(archive, key)
        cloud.verify(proof)
    except Exception as error:
        journal.event("UPLOAD_UNKNOWN_NO_RETRY", key=key, type=type(error).__name__)
        journal.pause("BACKUP_FAILURE")
        raise
    with journal.connect() as db:
        db.execute(
            "UPDATE reservations SET state='VERIFIED',version=? WHERE key=?",
            (proof.version_id, key),
        )
    journal.event("CLOUD_VERSION_VERIFIED", proof=proof.model_dump())
    return proof


def make_backup(slot_root: Path, destination: Path, *, dumps: bool = True) -> Path:
    """Snapshot only this slot, including its full ledger and both truth/app dumps."""
    from research.execution_setup.core import Ledger

    folder = destination / f"attempt-{time.time_ns()}"
    folder.mkdir(parents=True, exist_ok=False)
    ledger = Ledger(slot_root)
    ledger.verify()
    with ledger.connect() as source_db, sqlite3.connect(folder / "ledger.sqlite3") as target_db:
        source_db.backup(target_db)
        if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("BACKUP_SQLITE_INTEGRITY")
    for name in ("qualification-plan.json", "resources.json", "source-seal.json", "config.json"):
        shutil.copyfile(slot_root / name, folder / name)
    master_root = slot_root.parent.parent
    if (master_root / "campaign.sqlite3").is_file():
        master = folder / "master"
        master.mkdir()
        with (
            Journal(master_root).connect() as source_db,
            sqlite3.connect(master / "campaign.sqlite3") as target_db,
        ):
            source_db.backup(target_db)
        for name in ("run.json", "bindings.json", "binding-seal.json"):
            shutil.copyfile(master_root / name, master / name)
        copy_continuation_metadata(master_root, master)
    for source in (slot_root / "executions").rglob("*"):
        if source.is_file() and source.name != "runner.lock" and source.suffix != ".tmp":
            target_path = folder / source.relative_to(slot_root)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as incoming, target_path.open("xb") as output:
                shutil.copyfileobj(incoming, output)
    if dumps:
        config = read(slot_root / "resources.json")
        for container, user in zip(
            config["containers"][:2], ("setup_app", "setup_truth"), strict=True
        ):
            result = subprocess.run(
                ["docker", "exec", container, "pg_dump", "-U", user, user],
                capture_output=True,
                timeout=60,
            )
            if result.returncode:
                write_new(
                    folder / f"{user}-FAILURE.json",
                    {"exit": result.returncode, "stderr": result.stderr.decode(errors="replace")},
                )
                raise ValueError("POSTGRES_DUMP_FAILED_RETAIN_ATTEMPT")
            with gzip.open(folder / f"{user}.sql.gz", "wb") as outgoing:
                outgoing.write(result.stdout)
    files = {
        p.relative_to(folder).as_posix(): hash_file(p) for p in folder.rglob("*") if p.is_file()
    }
    write_new(folder / "manifest.json", {"files": files, "postgres_dumps": dumps})
    for name, digest in files.items():
        if hash_file(folder / name) != digest:
            raise ValueError("LOCAL_BACKUP_HASH_DRIFT")
    archive = folder.parent / (folder.name + ".tar.gz")
    with tarfile.open(archive, "x:gz") as outgoing:
        outgoing.add(folder, arcname="slot")
    write_new(
        archive.with_suffix(".receipt.json"),
        {"sha256": hash_file(archive), "bytes": archive.stat().st_size},
    )
    return archive


def verify_local(archive: Path, expected: str) -> None:
    if hash_file(archive) != expected:
        raise ValueError("LOCAL_ARCHIVE_DRIFT")
    # Read through the gzip trailer: tar readers may accept a missing trailer.
    with gzip.open(archive, "rb") as compressed:
        for _ in iter(lambda: compressed.read(1024**2), b""):
            pass
    with tarfile.open(archive, "r:gz") as incoming:
        handle = incoming.extractfile("slot/manifest.json")
        if handle is None:
            raise ValueError("MISSING_BACKUP_MANIFEST")
        manifest = json.load(handle)
    # Expanded restart closure must be read once in archive order. Random gzip
    # seeks per member made the bounded metadata-only roundtrip take minutes.
    expected_members = {"slot/" + name: digest for name, digest in manifest["files"].items()}
    seen: set[str] = set()
    with tarfile.open(archive, "r|gz") as incoming:
        for member in incoming:
            if member.name not in expected_members:
                continue
            if member.name in seen or not member.isfile():
                raise ValueError("BACKUP_MEMBER_MISSING_OR_DUPLICATE")
            handle = incoming.extractfile(member)
            calculated = hashlib.sha256()
            if handle is None:
                raise ValueError("BACKUP_MEMBER_MISSING")
            while block := handle.read(1024**2):
                calculated.update(block)
            if calculated.hexdigest() != expected_members[member.name]:
                raise ValueError("BACKUP_MEMBER_DRIFT")
            seen.add(member.name)
    if seen != expected_members.keys():
        raise ValueError("BACKUP_MEMBER_MISSING")


def complete_backup(
    journal: Journal, cloud: Cloud, policy: Policy, slot: dict[str, Any], archive: Path
) -> ObjectProof:
    try:
        digest = hash_file(archive)
        receipt = read(archive.with_suffix(".receipt.json"))
        if digest != receipt["sha256"] or archive.stat().st_size != receipt["bytes"]:
            raise ValueError("ORIGINAL_BACKUP_ARCHIVE_DRIFT")
        verify_local(archive, digest)
        proof = upload(journal, cloud, policy, archive)
        proof_path = journal.root / "backups" / f"{slot['execution_id']}.json"
        if not proof_path.exists():
            write_new(
                proof_path,
                {
                    "local": str(archive),
                    "sha256": digest,
                    "cloud": proof.model_dump(),
                    "execution_id": slot["execution_id"],
                },
            )
        elif read(proof_path)["sha256"] != digest:
            raise ValueError("ORIGINAL_BACKUP_PROOF_DRIFT")
        journal.update(slot["execution_id"], state="BACKED_UP", backup_hash=hash_file(proof_path))
        return proof
    except Exception as error:
        journal.event(
            "BACKUP_FAILURE", execution_id=slot["execution_id"], type=type(error).__name__
        )
        journal.pause("BACKUP_FAILURE")
        raise


def verify_continuation_metadata(root: Path) -> None:
    """Readback closure only. This never issues or substitutes launch authority."""
    if not (root / "handover.json").exists():
        if (root / "continuation-backup.json").exists() or (
            (root / "run.json").exists() and "continuation" in read(root / "run.json")
        ):
            raise ValueError("CONTINUATION_BACKUP_REQUIRED_METADATA_MISSING")
        return
    from handover import verify_imported_first

    record = read(root / "continuation-backup.json")
    mode = record["phase"]
    if mode not in ("PRELAUNCH", "COMPLETE") or record["admission_authority"] is not False:
        raise ValueError("CONTINUATION_BACKUP_PHASE_DRIFT")
    required = {
        "handover.json",
        "saved-identities.json",
        "host-clock.json",
        "restart-boundary.json",
        "historical-evidence.tar.gz",
        "cloud.json",
        "public-authority/original/REVIEW_ACCEPTED.json",
        "public-authority/original/FREEZE.json",
        "public-authority/original/LAUNCH.json",
        "public-authority/continuation/CONTINUATION_ACCEPTED.json",
        "public-authority/continuation/CONTINUATION_FREEZE.json",
    }
    late = {"continuation-readiness.json", "public-authority/continuation/CONTINUATION_LAUNCH.json"}
    if mode == "COMPLETE":
        required |= late
    elif any((root / name).exists() for name in late):
        raise ValueError("PRELAUNCH_MUST_PRECEDE_READINESS_AND_LAUNCH")
    if not required <= record["files"].keys():
        raise ValueError("CONTINUATION_BACKUP_REQUIRED_METADATA_MISSING")
    for name, digest in record["files"].items():
        target = (root / name).resolve()
        if root.resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("CONTINUATION_BACKUP_METADATA_DRIFT: " + name)
    if (
        hash_file(root / "historical-evidence.tar.gz")
        != read(root / "handover.json")["historical_bundle_sha256"]
    ):
        raise ValueError("HISTORICAL_BUNDLE_DRIFT")
    Journal(root).verify()
    verify_imported_first(root)  # all 82 receipts, identities, notices and both sidecars


def copy_continuation_metadata(source: Path, destination: Path, *, prelaunch: bool = False) -> None:
    """Preserve public cold-handover controls; never copy the private signing key."""
    if not (source / "handover.json").exists():
        if prelaunch or (
            (source / "run.json").exists() and "continuation" in read(source / "run.json")
        ):
            raise ValueError("PRELAUNCH_CONTINUATION_REQUIRED")
        return
    from handover import verify_imported_first

    verify_imported_first(source)
    config = read(source / "run.json")
    continuation_receipts = Path(config["continuation"]["receipts"])
    if prelaunch and (
        (source / "continuation-readiness.json").exists()
        or (continuation_receipts / "CONTINUATION_LAUNCH.json").exists()
    ):
        raise ValueError("PRELAUNCH_MUST_PRECEDE_READINESS_AND_LAUNCH")
    for name in (
        "handover.json",
        "saved-identities.json",
        "host-clock.json",
        "restart-boundary.json",
        "cloud.json",
    ):
        shutil.copyfile(source / name, destination / name)
    if not prelaunch:
        shutil.copyfile(
            source / "continuation-readiness.json", destination / "continuation-readiness.json"
        )
    shutil.copytree(source / "restart-history", destination / "restart-history")
    shutil.copytree(source / "backups", destination / "backups", dirs_exist_ok=True)
    # Preserve real preparation evidence and pauses; no synthesized readiness.
    for name in (
        "pause.json",
        "retained-import-pause.json",
        "reuse-preparation.json",
        "prelaunch-backup-proof.json",
    ):
        if (source / name).exists():
            shutil.copyfile(source / name, destination / name)
    if (source / "postboot-old-operational-evidence").exists():
        shutil.copytree(
            source / "postboot-old-operational-evidence",
            destination / "postboot-old-operational-evidence",
        )
    if (source / "historical-evidence.tar.gz").exists():
        # Carry the complete original evidence once in compressed form, not raw
        # copies of every old poll in every slot/backup staging directory.
        expected = read(source / "handover.json")["historical_bundle_sha256"]
        if hash_file(source / "historical-evidence.tar.gz") != expected:
            raise ValueError("HISTORICAL_BUNDLE_DRIFT")
        shutil.copyfile(
            source / "historical-evidence.tar.gz", destination / "historical-evidence.tar.gz"
        )
    for label, directory, names in (
        ("original", Path(config["receipts"]), ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH")),
        (
            "continuation",
            Path(config["continuation"]["receipts"]),
            ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE")
            if prelaunch
            else ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"),
        ),
    ):
        target = destination / "public-authority" / label
        target.mkdir(parents=True)
        for name in names:
            shutil.copyfile(directory / f"{name}.json", target / f"{name}.json")
    write_new(
        destination / "continuation-backup.json",
        {
            "version": "phase85-continuation-v6",
            "phase": "PRELAUNCH" if prelaunch else "COMPLETE",
            "admission_authority": False,
            "files": {
                p.relative_to(destination).as_posix(): hash_file(p)
                for p in destination.rglob("*")
                if p.is_file()
            },
        },
    )
    verify_continuation_metadata(destination)


def final_backup(journal: Journal, destination: Path, *, prelaunch: bool = False) -> Path:
    """Final master metadata plus all per-slot version receipts, without deleting raw evidence."""
    folder = destination / f"final-{time.time_ns()}"
    folder.mkdir(parents=True, exist_ok=False)
    journal.verify()
    with journal.connect() as source, sqlite3.connect(folder / "campaign.sqlite3") as target:
        source.backup(target)
    for name in ("run.json", "bindings.json", "binding-seal.json", "cloud.json"):
        shutil.copyfile(journal.root / name, folder / name)
    copy_continuation_metadata(journal.root, folder, prelaunch=prelaunch)
    for receipt_file in (journal.root / "backups").glob("*.json"):
        target_path = folder / "backups" / receipt_file.name
        target_path.parent.mkdir(exist_ok=True)
        shutil.copyfile(receipt_file, target_path)
    files = {
        p.relative_to(folder).as_posix(): hash_file(p) for p in folder.rglob("*") if p.is_file()
    }
    write_new(
        folder / "manifest.json",
        {
            "files": files,
            "postgres_dumps": False,
            "kind": "PRELAUNCH_MASTER_METADATA" if prelaunch else "FINAL_MASTER_METADATA",
        },
    )
    archive = folder.with_suffix(".tar.gz")
    with tarfile.open(archive, "x:gz") as outgoing:
        outgoing.add(folder, arcname="slot")
    write_new(
        archive.with_suffix(".receipt.json"),
        {"sha256": hash_file(archive), "bytes": archive.stat().st_size},
    )
    verify_local(archive, hash_file(archive))
    return archive
