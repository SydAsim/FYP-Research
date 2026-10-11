"""Assemble a review candidate only. No signing, freeze, launch or cloud operations."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from typing import Any

from controls import canonical, hash_file, write_new
from runner import HERE, REPO


def build() -> None:
    from research.execution_setup.core import source_inventory

    original = REPO / "artifacts/phase-8-linux-setup/v1/linux-source.tar.gz"
    expected = (original.parent / "linux-source.tar.gz.sha256").read_text().split()[0]
    if hash_file(original) != expected:
        raise ValueError("HISTORICAL_CAPSULE_DRIFT")
    with tarfile.open(original, "r:gz") as incoming:
        handle = incoming.extractfile("linux-package-seal.json")
        assert handle is not None
        legacy_seal: bytes = handle.read()
        previous = json.loads(legacy_seal)
    files: dict[str, str] = previous["hashes"]
    for name, digest in files.items():
        if hash_file(REPO / name) != digest:
            raise ValueError(f"HISTORICAL_SOURCE_DRIFT: {name}")
    files.update(source_inventory())
    for name in ("schedule.json", "measurements.json", "budget.json"):
        path = REPO / "artifacts/phase-8-review-freeze/v1" / name
        files[path.relative_to(REPO).as_posix()] = hash_file(path)
    chosen = [p for p in HERE.glob("*.py")]
    chosen.extend(
        HERE / name
        for name in (
            "requirements.txt",
            "Dockerfile",
            "schedule.json",
            "schedule.csv",
            "policy-proposal.json",
            "REVIEW.md",
            "OPERATING.md",
            "qualification-plan.json",
            "validation.json",
            "checklist.json",
            "measurements.json",
            "budget.json",
        )
    )
    files.update({p.relative_to(REPO).as_posix(): hash_file(p) for p in chosen})
    prefix = HERE.relative_to(REPO).as_posix() + "/"
    categories = {
        "application_and_contracts": {
            n: d
            for n, d in files.items()
            if n.startswith(("apps/", "packages/", "database/", "contracts/"))
        },
        "executables": {
            n: d for n, d in files.items() if n.startswith(prefix) and n.endswith(".py")
        },
        "configuration": {
            n: d
            for n, d in files.items()
            if n.endswith(("uv.lock", "pyproject.toml", "requirements.txt"))
            or n.startswith(prefix)
            and n.endswith(("policy-proposal.json", "schedule.json", "schedule.csv", "Dockerfile"))
        },
        "fixtures": {n: d for n, d in files.items() if n.startswith("research/fixtures/")},
        "oracle": {
            n: d
            for n, d in files.items()
            if n.startswith(
                ("research/oracle/", "research/study/oracle.py", "research/study_v4/oracle.py")
            )
            or n == prefix + "instrument.py"
        },
        "analysis": {
            n: d
            for n, d in files.items()
            if n.startswith(
                (
                    "research/analysis/",
                    "research/study/analysis.py",
                    "research/study/statistical_models.py",
                    "research/study_v4/analysis.py",
                    "research/execution_setup/timing.py",
                )
            )
            or n == prefix + "analyze.py"
        },
    }
    sorted_files = dict(sorted(files.items()))
    inventory: dict[str, Any] = {
        "kind": "REVIEW_INVENTORY",
        "scope": "CAMPAIGN",
        "version": "phase84-final-v2",
        "accepted": False,
        "frozen": False,
        "launch_authorized": False,
        "main_started": False,
        "package_hash": hashlib.sha256(canonical(sorted_files)).hexdigest(),
        "files": sorted_files,
        "categories": categories,
        "historical_linux_archive": {"sha256": expected, "bytes": original.stat().st_size},
    }
    target = HERE / "campaign-source.tar.gz"
    write_new(HERE / "review-inventory.json", inventory)
    extra = {
        "linux-package-seal.json": legacy_seal,
        prefix + "review-inventory.json": (HERE / "review-inventory.json").read_bytes(),
    }
    with (
        target.open("xb") as output,
        gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed,
    ):
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name in sorted(set(files) | set(extra)):
                data = extra[name] if name in extra else (REPO / name).read_bytes()
                entry = tarfile.TarInfo(name)
                entry.size, entry.mtime, entry.mode = len(data), 0, 0o644
                archive.addfile(entry, io.BytesIO(data))
    write_new(
        HERE / "bundle-receipt.json",
        {
            "classification": "REVIEW_CANDIDATE_NOT_FREEZE",
            "package_hash": inventory["package_hash"],
            "archive": target.name,
            "sha256": hash_file(target),
            "bytes": target.stat().st_size,
            "inventory_sha256": hash_file(HERE / "review-inventory.json"),
            "source_files": len(files),
            "accepted": False,
            "frozen": False,
            "launch_authorized": False,
        },
    )


if __name__ == "__main__":
    build()
