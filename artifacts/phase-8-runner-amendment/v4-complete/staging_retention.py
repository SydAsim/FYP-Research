"""Remove only redundant future backup staging after two verified evidence copies."""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

from controls import Journal, hash_file, read, write_new
from storage import Cloud, ObjectProof, verify_local


def remove_redundant_staging(archive: Path, digest: str, backup_root: Path, sequence: int) -> bool:
    """Caller must first verify BACKED_UP, local proof and pinned cloud version."""
    if sequence <= 82:
        raise ValueError("HISTORICAL_STAGING_PROTECTED")
    base = backup_root.resolve()
    if archive.is_symlink() or archive.parent.is_symlink() or backup_root.is_symlink():
        raise ValueError("STAGING_SYMLINK_REJECTED")
    if archive.resolve().parent != base / f"{sequence:04d}":
        raise ValueError("STAGING_OUTSIDE_OWNED_SEQUENCE")
    if not archive.name.startswith("attempt-") or not archive.name.endswith(".tar.gz"):
        raise ValueError("STAGING_ARCHIVE_NAME_REJECTED")
    verify_local(archive, digest)
    staging = archive.parent / archive.name.removesuffix(".tar.gz")
    if not staging.exists():
        return False  # Recovery after removal; verified archive remains.
    if (
        staging.is_symlink()
        or not staging.is_dir()
        or staging.resolve().parent != archive.resolve().parent
    ):
        raise ValueError("STAGING_PATH_REJECTED")
    with tarfile.open(archive, "r:gz") as incoming:
        stream = incoming.extractfile("slot/manifest.json")
        if stream is None:
            raise ValueError("STAGING_MANIFEST_MISSING")
        archived_manifest = stream.read()
    manifest = json.loads(archived_manifest)
    expected = dict(manifest["files"])
    expected["manifest.json"] = hashlib.sha256(archived_manifest).hexdigest()
    observed: dict[str, str] = {}
    for path in staging.rglob("*"):
        if path.is_symlink():
            raise ValueError("STAGING_SYMLINK_REJECTED")
        if path.is_file():
            observed[path.relative_to(staging).as_posix()] = hash_file(path)
    if observed != expected:
        raise ValueError("STAGING_CONTENT_NOT_REDUNDANT")
    # Both the resolved target and its parent have been checked above. Only the
    # redundant folder is removed; archive, receipt and original slot stay.
    shutil.rmtree(staging)
    return True


def retain_archives_only(journal: Journal, cloud: Cloud, slot: dict[str, Any]) -> None:
    config = read(journal.root / "run.json")
    if "operational_limits_sha256" not in config:
        return  # Historical/calibration policy is unchanged.
    from operational_limits import LIMITS_SHA256, verified_limits

    if config["operational_limits_sha256"] != LIMITS_SHA256:
        raise ValueError("STAGING_POLICY_AUTHORITY_DRIFT")
    verified_limits()
    rows = [row for row in journal.rows() if row["execution_id"] == slot["execution_id"]]
    if len(rows) != 1 or rows[0]["state"] != "BACKED_UP" or rows[0]["sequence"] <= 82:
        raise ValueError("STAGING_CLOSED_FUTURE_SLOT_REQUIRED")
    row = rows[0]
    proof_path = journal.root / "backups" / f"{row['execution_id']}.json"
    if hash_file(proof_path) != row["backup_hash"]:
        raise ValueError("STAGING_BACKUP_PROOF_DRIFT")
    proof = read(proof_path)
    if proof["execution_id"] != row["execution_id"]:
        raise ValueError("STAGING_BACKUP_IDENTITY_DRIFT")
    archive = Path(proof["local"])
    cloud_proof = ObjectProof.model_validate(proof["cloud"])
    if cloud_proof.sha256 != proof["sha256"] or cloud_proof.bytes != archive.stat().st_size:
        raise ValueError("STAGING_COPY_PROOF_DRIFT")
    cloud.verify(cloud_proof)  # Pinned version and full SHA checksum; unavailable => stop.
    marker = journal.root / "slots" / f"{row['sequence']:04d}" / "staging-retained.json"
    record = {
        "execution_id": row["execution_id"],
        "archive": str(archive),
        "sha256": proof["sha256"],
        "cloud": cloud_proof.model_dump(),
        "operational_limits_sha256": LIMITS_SHA256,
    }
    if marker.exists():
        if read(marker) != record:
            raise ValueError("STAGING_RETENTION_RECORD_DRIFT")
        return
    journal.event("VERIFIED_REDUNDANT_STAGING_REMOVAL_INTENT", **record)
    removed = remove_redundant_staging(
        archive, proof["sha256"], Path(config["backup"]), row["sequence"]
    )
    write_new(marker, record)
    journal.event(
        "VERIFIED_ARCHIVE_RETENTION_COMPLETE",
        execution_id=row["execution_id"],
        redundant_staging_removed=removed,
        archive=str(archive),
    )
