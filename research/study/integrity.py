"""Read-only checks of history and a separate, explicitly unapproved source candidate."""

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from research.scenario_dsl.models import stable_hash
from research.study.package import ROOT, write_json


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_history() -> dict[str, Any]:
    before = json.loads((ROOT / "historical-hashes-before.json").read_text(encoding="utf-8"))
    after = {path: sha256(Path(path)) for path in before}
    changed = [path for path in before if before[path] != after[path]]
    write_json(ROOT / "historical-hashes-after.json", after)
    summary = {
        "files": len(before),
        "changed": changed,
        "before_inventory_hash": stable_hash(before),
        "after_inventory_hash": stable_hash(after),
    }
    write_json(ROOT / "historical-integrity.json", summary)
    if changed:
        raise ValueError("Historical evidence modified: " + ", ".join(changed))
    return summary


def source_candidate() -> dict[str, Any]:
    roots = (
        "apps",
        "packages",
        "research",
        "tests",
        "docs",
        "database",
        "contracts",
        "deployment",
        "acceptance",
    )
    suffixes = {
        ".py",
        ".json",
        ".ts",
        ".tsx",
        ".css",
        ".md",
        ".sql",
        ".yaml",
        ".yml",
        ".toml",
        ".txt",
        ".mjs",
        ".js",
        ".html",
    }
    paths = [
        p
        for root in roots
        for p in Path(root).rglob("*")
        if p.is_file()
        and p.suffix in suffixes
        and not set(p.parts).intersection(
            {
                "__pycache__",
                "node_modules",
                ".next",
                "test-results",
                "playwright-report",
            }
        )
    ]
    paths.extend(
        Path(p)
        for p in (
            "AGENTS.md",
            "README.md",
            "pyproject.toml",
            "uv.lock",
            "compose.yaml",
            "Dockerfile.python",
            "alembic.ini",
            "package.json",
            "pnpm-lock.yaml",
            "pnpm-workspace.yaml",
            ".env.example",
            ".gitignore",
            ".dockerignore",
        )
    )
    inventory = {p.as_posix(): sha256(p) for p in sorted(set(paths))}
    digest = stable_hash(inventory)
    archive = ROOT / "source-candidate.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in inventory:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(info, Path(name).read_bytes())
    write_json(
        ROOT / "source-candidate-inventory.json",
        {
            "status": "UNAPPROVED_DRAFT_SOURCE_CANDIDATE",
            "source_hash": digest,
            "files": inventory,
            "archive_sha256": sha256(archive),
            "secret_env_excluded": True,
            "freeze_created": False,
        },
    )
    return {"files": len(inventory), "source_hash": digest, "archive_sha256": sha256(archive)}


if __name__ == "__main__":
    print(json.dumps({"history": verify_history(), "candidate": source_candidate()}, indent=2))
