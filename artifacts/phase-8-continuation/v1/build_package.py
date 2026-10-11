"""Versioned deployment delta only; original source archive remains immutable."""

from __future__ import annotations

import hashlib
import tarfile

from controls import canonical, hash_file, read, write_new
from handover import HERE, REPO
from verify_package import verify


def build() -> None:
    verify(include_candidate=False)
    parent = REPO / "artifacts/phase-8-review-freeze/v2"
    files = dict(read(parent / "review-inventory.json")["files"])
    excluded = {
        "candidate-inventory.json",
        "bundle-receipt.json",
        "final-verification.json",
        "continuation-delta.tar.gz",
        "verify-final.txt",
    }
    chosen = [
        p
        for p in HERE.rglob("*")
        if p.is_file()
        and p.name not in excluded
        and p.suffix != ".pyc"
        and not set(p.parts).intersection(
            {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        )
    ]
    # Dependency/provenance records referenced by the unchanged-policy check.
    chosen.extend(
        REPO / n
        for n in (
            "artifacts/phase-8-launch/v1/launch-policy.json",
            "artifacts/phase-8-launch/v1/local-postflight.json",
            "artifacts/phase-8-launch/v1/python-download-catalog.json",
            "artifacts/phase-8-launch/v1/python-installer-resolution.json",
            "artifacts/phase-8-runner-amendment/v1/first-original-sidecar.json",
            "artifacts/phase-8-runner-amendment/v1/preexisting-drift.json",
            "artifacts/phase-8-runner-amendment/v1/historical-report-as-found.md",
            "artifacts/phase-8-runner-amendment/v1/historical-report-sealed-recovered.md",
            "artifacts/phase-8-runner-amendment/v1/QUALIFICATION-REPORT.md",
            "artifacts/phase-8-runner-amendment/v1/final-verification.json",
            "artifacts/phase-8-runner-amendment/v1/final-candidate-inventory.json",
        )
    )
    for path in chosen:
        name = path.relative_to(REPO).as_posix()
        digest = hash_file(path)
        if name in files and files[name] != digest:
            raise ValueError("FROZEN_PARENT_OVERWRITE")
        files[name] = digest
    inventory = {
        "version": "phase85-continuation-v1",
        "kind": "CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE",
        "accepted": False,
        "frozen": False,
        "launch_authorized": False,
        "parent_package_hash": read(parent / "review-inventory.json")["package_hash"],
        "parent_archive_sha256": hash_file(parent / "campaign-source.tar.gz"),
        "package_hash": hashlib.sha256(canonical(files)).hexdigest(),
        "files": files,
        "changed_application_files": 0,
        "migrations": 0,
        "new_main_inputs": 0,
        "identity_policy": "Import existing 1500 identities; retain first; no UUID allocation",
    }
    write_new(HERE / "candidate-inventory.json", inventory)
    members = sorted({p.relative_to(REPO).as_posix() for p in chosen})
    members.append((HERE / "candidate-inventory.json").relative_to(REPO).as_posix())
    archive = HERE / "continuation-delta.tar.gz"
    with tarfile.open(archive, "x:gz") as outgoing:
        for name in members:
            outgoing.add(REPO / name, arcname=name, recursive=False)
    write_new(
        HERE / "bundle-receipt.json",
        {
            "kind": "REVIEW_DELTA_CHECKSUMS_NOT_FREEZE",
            "accepted": False,
            "frozen": False,
            "launch_authorized": False,
            "parent_archive_sha256": inventory["parent_archive_sha256"],
            "archive_sha256": hash_file(archive),
            "archive_bytes": archive.stat().st_size,
            "inventory_sha256": hash_file(HERE / "candidate-inventory.json"),
            "package_hash": inventory["package_hash"],
            "archive_members": members,
        },
    )
    print("PASS: review-only deployment delta; original archive unchanged")


if __name__ == "__main__":
    build()
