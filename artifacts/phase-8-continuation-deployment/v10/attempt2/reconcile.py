"""One finite, read-only deployment reconciliation; no host actions."""
from __future__ import annotations
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "i-057344e5372faf62f"

def save(name: str, value: object) -> None:
    with (HERE / name).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2)

def main() -> None:
    started = time.monotonic()
    save("read-only-plan.json", {
        "at": datetime.now(UTC).isoformat(), "overall_seconds": 600,
        "requests_max": 4, "automatic_retries": 0,
        "connect_seconds": 5, "read_seconds": 25, "process_seconds": 45,
        "purpose": "Reconcile ambiguous quiescence, broad history plus CloudTrail; no resend/boot",
        "host": HOST,
    })
    calls = [
        ("host", ["ec2", "describe-instances", "--instance-ids", HOST]),
        ("commands", ["ssm", "list-commands", "--instance-id", HOST,
            "--filters", "key=InvokedAfter,value=2026-10-12T16:20:00Z",
            "key=InvokedBefore,value=2026-10-12T16:45:00Z",
            "--max-results", "50", "--no-paginate"]),
        ("invocations", ["ssm", "list-command-invocations", "--instance-id", HOST,
            "--filters", "key=InvokedAfter,value=2026-10-12T16:20:00Z",
            "key=InvokedBefore,value=2026-10-12T16:45:00Z", "--details",
            "--max-results", "50", "--no-paginate"]),
        ("cloudtrail", ["cloudtrail", "lookup-events", "--lookup-attributes",
            "AttributeKey=EventName,AttributeValue=SendCommand", "--start-time",
            "2026-10-12T16:20:00Z", "--end-time", "2026-10-12T16:45:00Z",
            "--max-results", "50", "--no-paginate"]),
    ]
    env = {**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_RETRY_MODE": "standard", "AWS_PAGER": ""}
    for name, args in calls:
        if time.monotonic() - started > 550:
            raise RuntimeError("OVERALL_DEADLINE_NO_MORE_REQUESTS")
        command = ["aws", *args, "--profile", "fyp-research", "--region", "ap-southeast-2",
                   "--cli-connect-timeout", "5", "--cli-read-timeout", "25", "--output", "json", "--no-cli-pager"]
        save(name + "-request.json", {"at": datetime.now(UTC).isoformat(), "command": command})
        tick = time.monotonic()
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=45, env=env)
            record = {"exit": result.returncode, "stderr": result.stderr,
                      "result": json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else result.stdout}
        except subprocess.TimeoutExpired:
            record = {"exit": "PROCESS_TIMEOUT", "deadline_seconds": 45}
        record.update(seconds=time.monotonic() - tick, at=datetime.now(UTC).isoformat())
        save(name + "-result.json", record)
        print(json.dumps({"call": name, "exit": record["exit"], "seconds": record["seconds"]}), flush=True)

if __name__ == "__main__":
    main()
