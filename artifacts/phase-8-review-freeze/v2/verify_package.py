"""Verify exact candidate bytes and historical hashes; never sign/freeze/launch."""

from __future__ import annotations

import hashlib
import json
import tarfile

from controls import canonical, hash_file, read, write_new
from runner import HERE, REPO


def verify() -> None:
    receipt = read(HERE / "bundle-receipt.json")
    inventory = read(HERE / "review-inventory.json")
    archive = HERE / receipt["archive"]
    if (
        hash_file(archive) != receipt["sha256"]
        or hash_file(HERE / "review-inventory.json") != receipt["inventory_sha256"]
    ):
        raise ValueError("CANDIDATE_DRIFT")
    if hashlib.sha256(canonical(inventory["files"])).hexdigest() != inventory["package_hash"]:
        raise ValueError("INVENTORY_DRIFT")
    for name, digest in inventory["files"].items():
        if hash_file(REPO / name) != digest:
            raise ValueError(f"CANDIDATE_SOURCE_DRIFT: {name}")
    with tarfile.open(archive, "r:gz") as incoming:
        names = incoming.getnames()
        if len(names) != len(set(names)):
            raise ValueError("CAPSULE_DUPLICATE")
        for name, digest in inventory["files"].items():
            handle = incoming.extractfile(name)
            assert handle is not None
            if hashlib.sha256(handle.read()).hexdigest() != digest:
                raise ValueError(f"CAPSULE_SOURCE_DRIFT: {name}")
    preservation = read(HERE / "preserved-before.json")
    for name, digest in preservation.items():
        if hash_file(REPO / name) != digest:
            raise ValueError(f"HISTORICAL_EVIDENCE_DRIFT: {name}")
    slots = read(REPO / "artifacts/phase-8-study-design/v4/main-slots.json")
    assert len(slots) == 1500 and all(
        s["execution_id"] is None and s["status"] == "NOT_STARTED" for s in slots
    )
    assert hash_file(HERE / "schedule.json") == hash_file(
        REPO / "artifacts/phase-8-review-freeze/v1/schedule.json"
    )
    assert not any(
        inventory[k] for k in ("accepted", "frozen", "launch_authorized", "main_started")
    )
    write_new(
        HERE / "preservation-after.json",
        {
            "status": "UNCHANGED",
            "files": len(preservation),
            "before_manifest_sha256": hash_file(HERE / "preserved-before.json"),
        },
    )
    verification_files = {
        p.relative_to(HERE).as_posix(): hash_file(p)
        for p in HERE.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.name not in ("final-verification.json", "campaign-source.tar.gz")
    }
    write_new(
        HERE / "final-verification.json",
        {
            "status": "PASS",
            "review_candidate": receipt,
            "source_files_verified": len(inventory["files"]),
            "historical_files_unchanged": len(preservation),
            "exact_original_slots_unstarted": 1500,
            "main_inputs": 500,
            "scope": "B3/P1/P2_SERIAL",
            "new_cloud_calls": 0,
            "new_cloud_spending_usd": 0,
            "accepted": False,
            "frozen": False,
            "launch_authorized": False,
            "verification_artifact_hashes": verification_files,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "source_files": len(inventory["files"]),
                "historical_files": len(preservation),
                "package_hash": inventory["package_hash"],
            }
        )
    )


if __name__ == "__main__":
    verify()
