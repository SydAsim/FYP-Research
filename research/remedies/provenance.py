"""Content-address the revised instrument without modifying historical freezes."""

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from typing import Any

from research.pilot.freeze import source_inventory
from research.remedies.preserve import OUTPUT, ROOT
from research.scenario_dsl.models import stable_hash


def inventory() -> dict[str, str]:
    files = source_inventory()
    for area in ("tests", "docs"):
        for path in (ROOT / area).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".md", ".json"):
                files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    for name in ("AGENTS.md", "README.md"):
        files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return dict(sorted(files.items()))


def freeze_source() -> dict[str, Any]:
    target = OUTPUT / "source-freeze.json"
    files = inventory()
    if target.exists():
        saved: dict[str, Any] = json.loads(target.read_text(encoding="utf-8"))
        if files != saved["files"]:
            raise ValueError("Revised source drift; create another version")
        verify_source(saved)
        return saved
    archive = OUTPUT / "source-v2.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in files:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, (ROOT / name).read_bytes())
    saved = {
        "version": "readiness-source-v2",
        "created_at": datetime.now(UTC).isoformat(),
        "files": files,
        "source_hash": stable_hash(files),
        "archive": str(archive),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    }
    target.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    return saved


def verify_source(saved: dict[str, Any]) -> None:
    archive = OUTPUT / "source-v2.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != saved["archive_sha256"]:
        raise ValueError("Revised archive changed")
    if stable_hash(saved["files"]) != saved["source_hash"]:
        raise ValueError("Revised source inventory changed")
    with zipfile.ZipFile(archive) as bundle:
        actual = {n: hashlib.sha256(bundle.read(n)).hexdigest() for n in bundle.namelist()}
    if actual != saved["files"]:
        raise ValueError("Revised archive inventory mismatch")
