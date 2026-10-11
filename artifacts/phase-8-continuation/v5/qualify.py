"""Fixed offline Linux checks; numbered attempts and failures remain retained."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path("E:/p8v5/source")
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
IMAGE = "sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8"

def main() -> None:
    attempt = sys.argv[1]
    if attempt not in ("attempt1", "attempt2", "attempt3"):
        raise ValueError("FIXED_THREE_ATTEMPT_LIMIT")
    output = HERE / attempt
    output.mkdir(exist_ok=False)
    command = (
        "set -eu; mkdir /tmp/candidate; tar -xzf /tmp/source.tar.gz -C /tmp/candidate; cd /tmp/candidate; "
        "export PYTHONDONTWRITEBYTECODE=1 AWS_EC2_METADATA_DISABLED=true "
        "PYTHONPATH=/tmp/candidate:/tmp/candidate/" + PREFIX + ":"
        "/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:"
        "/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages; "
        "python -m research.execution_linux_v1.portable; "
        "python -c 'import sys,sqlite3,botocore; assert sys.version_info[:3]==(3,12,13); "
        "assert botocore.__version__==\"1.43.108\"; print(sys.version,sqlite3.sqlite_version,botocore.__version__)'; "
        "timeout --signal=TERM --kill-after=5s 180s python -m pytest -x -q -o addopts='' "
        + PREFIX + "/test_inventory_read.py " + PREFIX + "/test_closed_restart.py "
        "--basetemp=/tmp/cal-v5 --junitxml=/out/results.xml"
    )
    archive = output / "source.tar.gz"
    with tarfile.open(archive, "x:gz") as target:
        for path in sorted(SOURCE.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                target.add(path, arcname=path.relative_to(SOURCE).as_posix(), recursive=False)
    args = ["docker", "create", "--pull=never", "--name", "p85-v5-stubs-" + attempt,
            "--network", "none", "--memory", "2g", "--cpus", "1",
            "-v", str(output.resolve()) + ":/out",
            IMAGE, "sh", "-c", command]
    (output / "command.json").write_text(json.dumps(args, indent=2))
    started = time.monotonic()
    try:
        setup = subprocess.run(args, capture_output=True, encoding="utf-8", timeout=30)
        (output / "create.json").write_text(json.dumps({"exit":setup.returncode,"stdout":setup.stdout,"stderr":setup.stderr}))
        setup.check_returncode()
        transfer = subprocess.run(["docker", "cp", str(archive.resolve()), "p85-v5-stubs-" + attempt + ":/tmp/source.tar.gz"], capture_output=True, encoding="utf-8", timeout=60)
        (output / "transfer.json").write_text(json.dumps({"exit":transfer.returncode,"stdout":transfer.stdout,"stderr":transfer.stderr}))
        transfer.check_returncode()
        args = ["docker", "start", "-a", "p85-v5-stubs-" + attempt]
        result = subprocess.run(args, capture_output=True, encoding="utf-8", timeout=240,
                                env={**os.environ, "PYTHONUTF8": "1"})
        (output / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (output / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        record = {"status": "PASS" if result.returncode == 0 else "FAIL",
                  "exit": result.returncode, "wall_seconds": time.monotonic() - started,
                  "image": IMAGE, "research_executions": 0, "AWS_changes": 0}
    except subprocess.TimeoutExpired as error:
        (output / "timeout.txt").write_text(str(error))
        subprocess.run(["docker", "stop", "-t", "5", "p85-v5-stubs-" + attempt], timeout=15)
        record = {"status": "FAIL_TIMEOUT_RETAINED", "wall_seconds": time.monotonic() - started}
    (output / "qualification.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record))
    if record["status"] != "PASS":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
