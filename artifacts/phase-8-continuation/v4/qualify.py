"""One fixed, network-free pinned Linux control qualification with retained logs."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("E:/p8v4/source")
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
IMAGE = "sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def long(path: Path) -> Path:
    return Path("\\\\?\\" + str(path.resolve()))


def verify_preserved() -> dict[str, int]:
    parent = REPO / "artifacts/phase-8-runner-amendment/v3"
    historical = json.loads((parent / "preservation-before.json").read_text())
    for name, digest in historical.items():
        path = Path(name)
        if not path.is_absolute():
            path = REPO / path
        assert sha(long(path)) == digest, name
    inventory = json.loads((parent / "candidate-inventory.json").read_text())
    for name, digest in inventory["files"].items():
        assert sha(long(REPO / name)) == digest, name
        assert sha(long(SOURCE / name)) == digest, name
    freeze = REPO / "artifacts/phase-8-continuation-freeze/v3"
    assert sha(freeze / "freeze-manifest.json") == "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86"
    frozen = json.loads((freeze / "freeze-manifest.json").read_text())["files"]
    for name, digest in frozen.items():
        assert sha(long(freeze / name)) == digest, name
    patch = REPO / "artifacts/phase-8-runner-amendment/v4"
    previous = json.loads((patch / "candidate-inventory.json").read_text())
    for name, digest in previous["files"].items():
        path = Path(name)
        if not path.is_absolute():
            path = patch / path
        assert sha(long(path)) == digest, name
    return {"historical": len(historical), "parent_members": len(inventory["files"]), "frozen_members": len(frozen), "previous_local_patch_members": len(previous["files"])}


def main() -> None:
    output = HERE / ("linux-control-attempt-" + str(time.time_ns()))
    output.mkdir()
    before = verify_preserved()
    (output / "preservation-before.json").write_text(json.dumps(before, indent=2))
    archive = output / "qualification-source.tar.gz"
    with tarfile.open(archive, "x:gz") as target:
        for path in sorted(long(SOURCE).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                target.add(path, arcname=path.relative_to(long(SOURCE)).as_posix(), recursive=False)
    calls: list[dict[str, Any]] = []
    name = "p85-v4-controls-" + str(time.time_ns())

    def run(args: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(["docker", *args], capture_output=True, encoding="utf-8", timeout=timeout, env={**os.environ, "PYTHONUTF8": "1"})
        calls.append({"args": args, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        (output / "commands.json").write_text(json.dumps(calls, indent=2))
        if result.returncode:
            raise RuntimeError("QUALIFICATION_COMMAND_FAILED")
        return result

    started = time.monotonic()
    run(["create", "--name", name, "--pull=never", "--network", "none", "--memory", "2g", "--cpus", "1", "-v", str(output.resolve()) + ":/out", IMAGE, "sh", "-c", "mkdir /tmp/v4source; tar -xzf /tmp/source.tar.gz -C /tmp/v4source; cd /tmp/v4source; export PYTHONPATH=/tmp/v4source:/tmp/v4source/" + PREFIX + ":/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages; python -m research.execution_linux_v1.portable; python -c 'import sys,sqlite3,pytest,pydantic; assert sys.version_info[:3]==(3,12,13); print(sys.version); print(sqlite3.sqlite_version); print(pytest.__version__,pydantic.__version__)'; python -m pytest -q -o addopts='' " + PREFIX + "/test_ledger_snapshot.py " + PREFIX + "/test_closed_prefix.py --basetemp=/tmp/cal-v4-controls --junitxml=/out/results.xml >/out/tests.txt 2>&1; code=$?; cat /out/tests.txt; exit $code"])
    run(["cp", str(archive.resolve()), name + ":/tmp/source.tar.gz"])
    result: subprocess.CompletedProcess[str] | None = None
    failure: str | None = None
    try:
        result = run(["start", "-a", name], timeout=600)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        failure = type(error).__name__
        if isinstance(error, subprocess.TimeoutExpired):
            run(["stop", "-t", "5", name])
    run(["inspect", name])
    elapsed = time.monotonic() - started
    after = verify_preserved()
    (output / "qualification.json").write_text(json.dumps({"status": "PASS" if failure is None else "FAIL", "elapsed_seconds": elapsed, "wall_cap_seconds": 600, "failure": failure, "image": IMAGE, "source_archive_sha256": sha(archive), "before": before, "after": after, "container": name, "research_executions": 0, "AWS_changes": 0, "database_restores": 0}, indent=2))
    print(str(output))
    if failure:
        raise RuntimeError("BOUNDED_QUALIFICATION_FAILED_RETAINED")
    assert result is not None
    print(result.stdout)


if __name__ == "__main__":
    main()
