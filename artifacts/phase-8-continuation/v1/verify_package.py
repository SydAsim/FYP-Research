"""Read-only review verification. No AWS, services, acceptance or driver commands."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path
from typing import IO, Any

from controls import canonical, hash_file, read
from handover import FIRST, FIRST_HASH, HERE, REPO, closed_boundary, ro_rows, verify_imported_first


def member_hash(member: IO[bytes]) -> str:
    digest = hashlib.sha256()
    while block := member.read(1024**2):
        digest.update(block)
    return digest.hexdigest()


def verify_original_archives() -> int:
    local = read(REPO / "artifacts/phase-8-launch/v1/local-postflight.json")
    count = 0
    for obj in local["objects"]:
        archive = Path(obj["extracted"]).parent / "t/e.tar.gz"
        if hash_file(archive) != obj["proof"]["sha256"]:
            raise ValueError("ORIGINAL_ARCHIVE_DRIFT")
        with tarfile.open(archive, "r:gz") as incoming:
            handle = incoming.extractfile("slot/manifest.json")
            assert handle is not None
            manifest = json.load(handle)
            if obj["label"] == "slot1" and (
                not manifest["postgres_dumps"]
                or not {"setup_app.sql.gz", "setup_truth.sql.gz"}.issubset(manifest["files"])
            ):
                raise ValueError("ORIGINAL_DATABASE_DUMPS_MISSING")
            for name, expected in manifest["files"].items():
                member = incoming.extractfile("slot/" + name)
                assert member is not None
                if member_hash(member) != expected:
                    raise ValueError("ORIGINAL_ARCHIVE_MEMBER_DRIFT")
                count += 1
    return count


def verify(*, include_candidate: bool = True) -> dict[str, Any]:
    baseline = read(HERE / "preserved-before.json")
    for name, expected in baseline.items():
        if hash_file(Path(name)) != expected:
            raise ValueError("HISTORICAL_OR_AMENDMENT_DRIFT: " + name)
    root = HERE / "import-preview"
    verify_imported_first(root)
    rows = ro_rows(root)
    closed_boundary(rows, read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")["rows"])
    exported = root / "historical/first-slot/executions" / FIRST / "export.json"
    if hash_file(exported) != FIRST_HASH or read(exported)["status"] != "FAILED":
        raise ValueError("FIRST_ORIGINAL_CHANGED")
    if read(root / "pause.json")["reason"] != "CONTINUATION_REVIEW_REQUIRED" or (
        (root / "slots").exists() or (root / "host-clock.json").exists()
    ):
        raise ValueError("REVIEW_PREVIEW_MUST_REMAIN_UNADMITTED")
    members = verify_original_archives()
    if include_candidate:
        inventory = read(HERE / "candidate-inventory.json")
        if hashlib.sha256(canonical(inventory["files"])).hexdigest() != inventory["package_hash"]:
            raise ValueError("CANDIDATE_MANIFEST_DRIFT")
        for name, expected in inventory["files"].items():
            if hash_file(REPO / name) != expected:
                raise ValueError("CANDIDATE_SOURCE_DRIFT: " + name)
        receipt = read(HERE / "bundle-receipt.json")
        if hash_file(HERE / "continuation-delta.tar.gz") != receipt["archive_sha256"]:
            raise ValueError("CONTINUATION_ARCHIVE_DRIFT")
        if hash_file(HERE / "candidate-inventory.json") != receipt["inventory_sha256"]:
            raise ValueError("CONTINUATION_INVENTORY_RECEIPT_DRIFT")
        with tarfile.open(HERE / "continuation-delta.tar.gz", "r:gz") as incoming:
            for name in receipt["archive_members"]:
                member = incoming.extractfile(name)
                assert member is not None
                if member_hash(member) != hash_file(REPO / name):
                    raise ValueError("CONTINUATION_DELTA_MEMBER_DRIFT")
    return {
        "status": "PASS",
        "scope": "OFFLINE_REVIEW_NOT_HOST_READINESS",
        "protected_paths": len(baseline),
        "original_archives": 3,
        "original_archive_members": members,
        "originals": 1500,
        "original_BACKED_UP": 1,
        "remaining_PLANNED": 1499,
        "first_raw_status": "FAILED",
        "first_export_sha256": FIRST_HASH,
        "main_driver_calls": 0,
        "new_acceptance": False,
        "new_freeze": False,
        "continuation_launch": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
