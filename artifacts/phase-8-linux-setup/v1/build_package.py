"""Deterministic source capsule; no credentials, environment, models or main executions."""

import gzip
import hashlib
import json
import sys
import tarfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.execution_setup.core import (  # noqa: E402
    ROOT,
    check_inventory,
    digest,
    load,
    source_inventory,
)

PACKAGE = ROOT / "artifacts/phase-8-linux-setup/v1"


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


def build() -> None:
    before = load(PACKAGE / "preserved-before.json")
    check_inventory(before)
    paths = set(before) | set(source_inventory())
    paths.update(("alembic.ini", "Dockerfile.python", ".dockerignore"))
    paths.update(
        p.relative_to(ROOT).as_posix()
        for p in PACKAGE.iterdir()
        if p.suffix in (".py", ".md", ".service", ".sh") or p.name == "Dockerfile"
    )
    # Only the baseline map, not evolving logs/reports, belongs to the executable capsule.
    paths.add("artifacts/phase-8-linux-setup/v1/preserved-before.json")
    hashes = {p: digest(ROOT / p) for p in sorted(paths)}
    aliases = {}
    for name in paths:
        if name.endswith(".json"):
            for value in strings(load(ROOT / name)):
                canonical = value.replace("\\", "/")
                if "\\" in value and "/" not in value and canonical in hashes:
                    aliases[value] = canonical
    manifest = (
        json.dumps(
            {
                "version": "phase8-linux-setup-v1",
                "main_started": False,
                "scope": "CALIBRATION_ONLY_NOT_FROZEN",
                "hashes": hashes,
                "reference_aliases": dict(sorted(aliases.items())),
            },
            indent=2,
        ).encode()
        + b"\n"
    )
    target = PACKAGE / "linux-source.tar.gz"
    with target.open("wb") as output, gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name in sorted(paths):
                data = (ROOT / name).read_bytes()
                entry = tarfile.TarInfo(name)
                entry.size, entry.mtime, entry.mode = len(data), 0, 0o644
                archive.addfile(entry, BytesIO(data))
            entry = tarfile.TarInfo("linux-package-seal.json")
            entry.size, entry.mtime, entry.mode = len(manifest), 0, 0o644
            archive.addfile(entry, BytesIO(manifest))
    (PACKAGE / "package-manifest.json").write_bytes(manifest)
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    (PACKAGE / "linux-source.tar.gz.sha256").write_text(
        f"{checksum}  linux-source.tar.gz\n", encoding="utf-8"
    )
    print(json.dumps({"files": len(hashes), "bytes": target.stat().st_size, "sha256": checksum}))


if __name__ == "__main__":
    build()
