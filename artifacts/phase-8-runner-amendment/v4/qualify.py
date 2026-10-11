"""Bounded local checks only; no cloud, application or research-execution entrypoint."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = HERE.parent / "v3"


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as file:
        json.dump(value, file, indent=2)


def main() -> None:
    began = time.monotonic()
    deadline = began + 300
    attempt = HERE / f"qualification-{time.time_ns()}"
    attempt.mkdir()
    plan = read(HERE / "qualification-plan.json")
    assert plan["tests"] == 15 and plan["maximum_wall_seconds"] == 300
    protected = read(BASE / "preservation-before.json")
    inventory = read(BASE / "candidate-inventory.json")
    frozen = REPO / "artifacts/phase-8-continuation-freeze/v3"
    if sys.platform == "win32":
        frozen = Path("\\\\?\\" + str(frozen.resolve()))
    frozen_manifest = read(frozen / "freeze-manifest.json")
    evidence = Path("E:/FYP Project/p8-observation-20261008-1")
    evidence_manifest = read(evidence / "x/inspection/manifest.json")

    def preservation() -> dict[str, int]:
        groups = {
            "historical": [(Path(n), h) for n, h in protected.items()],
            "accepted_v3_source": [(REPO / n, h) for n, h in inventory["files"].items()],
            "frozen_v3_members": [(frozen / n, h) for n, h in frozen_manifest["files"].items()],
            "retained_stop_snapshot": [
                (evidence / "x/inspection" / n, h) for n, h in evidence_manifest["files"].items()
            ],
        }
        for files in groups.values():
            for path, expected in files:
                if time.monotonic() > deadline:
                    raise TimeoutError("FIXED_LOCAL_QUALIFICATION_BUDGET")
                if digest(path) != expected:
                    raise ValueError("PRESERVATION_DRIFT: " + str(path))
        assert digest(frozen / "freeze-manifest.json") == (
            "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86"
        )
        assert digest(evidence / "evidence.tar.gz") == (
            "257cdc762459f07c67f132ed0141021dd38430a9f5cb2040cd3479e3e7d37905"
        )
        assert digest(BASE.parent / "v3-combined-review-candidate.tar.gz") == (
            "0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf"
        )
        assert digest(BASE / "controls.py") == plan["source_sha256"]
        original = (BASE / "controls.py").read_bytes()
        newline = b"\r\n" if b"\r\n" in original else b"\n"
        assert (HERE / "controls.py").read_bytes().replace(
            b'            db.execute("BEGIN")' + newline, b"", 1
        ) == original
        return {name: len(files) for name, files in groups.items()}

    result: dict[str, object] = {"scope": plan["scope"], "planned_tests": 15}
    try:
        result["before_preservation"] = preservation()
        commands = [
            ("pytest", ["-m", "pytest", "-q", str(HERE / "test_ledger_snapshot.py")]),
            ("ruff", ["-m", "ruff", "check", str(HERE)]),
            ("format", ["-m", "ruff", "format", "--check", str(HERE)]),
            (
                "types",
                [
                    "-m",
                    "mypy",
                    "--strict",
                    str(HERE / "controls.py"),
                    str(HERE / "test_ledger_snapshot.py"),
                ],
            ),
        ]
        environment = {**os.environ, "PYTHONUTF8": "1", "MYPYPATH": str(HERE)}
        for name, args in commands:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("FIXED_LOCAL_QUALIFICATION_BUDGET")
            start = time.monotonic()
            p = subprocess.run(
                [sys.executable, *args],
                cwd=REPO,
                env=environment,
                capture_output=True,
                timeout=min(120, remaining),
            )
            (attempt / (name + ".stdout.txt")).write_bytes(p.stdout)
            (attempt / (name + ".stderr.txt")).write_bytes(p.stderr)
            write(
                attempt / (name + ".json"),
                {"args": args, "exit": p.returncode, "elapsed_seconds": time.monotonic() - start},
            )
            if p.returncode:
                raise ValueError("FOCUSED_CHECK_FAILED: " + name)
        result["after_preservation"] = preservation()
        result["status"] = "PASS"
    except Exception as error:
        result.update(status="FAIL", error_type=type(error).__name__, detail=str(error))
    result.update(
        ended_at_utc=datetime.now(UTC).isoformat(),
        elapsed_seconds=time.monotonic() - began,
        frozen=False,
        main_launched=False,
        aws_actions=0,
        research_executions=0,
    )
    write(attempt / "result.json", result)
    print(json.dumps({"attempt": attempt.name, **result}))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
