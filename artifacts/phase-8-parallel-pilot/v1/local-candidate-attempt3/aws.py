"""Local AWS CLI journal. No credentials or application state in this module."""

import json
import subprocess
from pathlib import Path
from typing import Any

from research.execution_setup.core import immutable, now

PACKAGE = Path(__file__).resolve().parent
CLI = "C:/Program Files/Amazon/AWSCLIV2/aws.exe"


def call(name: str, arguments: list[str], *, region: str = "ap-southeast-2") -> Any:
    if region != "ap-southeast-2" and not (region == "us-east-1" and arguments[0] == "pricing"):
        raise ValueError("SELECTED_REGION_ONLY")
    argv = [CLI, *arguments, "--profile", "fyp-research", "--region", region, "--output", "json"]
    immutable(PACKAGE / f"aws-request-{name}.json", {"at": now(), "argv": argv})
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        immutable(
            PACKAGE / f"aws-response-{name}.json",
            {
                "at": now(),
                "status": "UNKNOWN_TIMEOUT",
                "new_admissions_stopped": True,
                "instruction": "Read/reconcile the exact named resource before any write retry",
            },
        )
        raise
    immutable(
        PACKAGE / f"aws-response-{name}.json",
        {
            "at": now(),
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    result.check_returncode()
    return json.loads(result.stdout) if result.stdout.strip() else {}
