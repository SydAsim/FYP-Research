"""Finite native Linux collector qualification; runs without any Codex API."""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
from research.execution_linux_v1 import platform  # noqa: E402
from research.execution_setup.core import Ledger, digest, immutable, load, now  # noqa: E402
from research.execution_setup.resources import admission  # noqa: E402

ENTRY = Path(__file__).with_name("runner_v2.py")


def invoke(root: Path, stage: str, arguments: list[str], timeout: int = 800) -> None:
    log = root.parent / f"{root.name}-{stage}.log"
    with log.open("xb") as output:
        result = subprocess.run(
            [sys.executable, str(ENTRY), *arguments, "--root", str(root)],
            cwd=SOURCE,
            stdout=output,
            stderr=output,
            timeout=timeout,
        )
    immutable(
        root.parent / f"{root.name}-{stage}-exit.json",
        {
            "at": now(),
            "exit": result.returncode,
            "log": str(log),
            "main_started": False,
        },
    )
    result.check_returncode()


def first(root: Path) -> dict[str, Any]:
    return Ledger(root).rows()[0]


def verify_export(root: Path, slot: dict[str, Any]) -> dict[str, Any]:
    if slot["state"] != "EXPORTED":
        raise ValueError("ORIGINAL_NOT_EXPORTED")
    path = root / "executions" / slot["execution_id"] / "export.json"
    trace = load(path)
    if trace["status"] != "COMPLETED":
        raise ValueError("DRIVER_NOT_COMPLETED: retain failure, no diagnostic replacement")
    if trace.get("oracle_failure") or trace.get("collection_errors") or trace.get("source_drift"):
        raise ValueError("QUALIFICATION_PROTOCOL_FAILURE: retain original and stop")
    deadline = datetime.fromisoformat(slot["deadline"])
    polls = trace["polls"]
    latest = datetime.fromisoformat(polls[-1]["at"])
    if latest < deadline or trace["missing_final_anchor"]:
        raise ValueError("FULL_FINAL_REQUEST_WINDOW_NOT_ESTABLISHED")
    gaps = [
        (datetime.fromisoformat(b["at"]) - datetime.fromisoformat(a["at"])).total_seconds()
        for a, b in zip(polls, polls[1:], strict=False)
    ]
    return {
        "execution_id": slot["execution_id"],
        "case_id": slot["case_id"],
        "arm": slot["arm"],
        "deadline": slot["deadline"],
        "driver_status": trace["status"],
        "polls": len(polls),
        "maximum_poll_gap_seconds": max(gaps, default=0),
        "deadline_overshoot_seconds": (latest - deadline).total_seconds(),
        "export": str(path),
        "export_hash": digest(path),
        "grade": trace["revised_grade"],
        "resource_start": trace["resource_start"],
        "resource_end": trace["resource_end"],
    }


def qualify(root: Path, backup: Path) -> None:
    host_stop = datetime.fromisoformat(os.environ["P82_HOST_STOP_AT"])
    if (host_stop - datetime.fromisoformat(now())).total_seconds() < 1800:
        raise ValueError("ABSOLUTE_HOST_DEADLINE_ADMISSION_STOP")
    if float(Path("/proc/uptime").read_text().split()[0]) > 12600:
        raise ValueError("HOST_DEADLINE_ADMISSION_STOP: insufficient complete-window reserve")
    immutable(
        root.parent / "qualification-start.json",
        {
            "at": now(),
            "main_started": False,
            "plan": "AWS_8_2_NATIVE_TWO_SLOTS_DIAGNOSTIC_V2",
            "source_capsule_sha256": (
                "2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5"
            ),
        },
    )
    root.parent.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)
    admission(platform.host(root.parent, backup))
    invoke(root, "initialize", ["init", "--backup", str(backup)], 60)
    invoke(root, "checkpoint", ["run", "--checkpoint-once"], 180)
    original = first(root)
    if original["state"] != "CHECKPOINTED":
        raise ValueError("REAL_CHECKPOINT_NOT_OBSERVED")
    immutable(root.parent / "original-checkpoint.json", original)
    resumed_log = root.parent / "parent-stop.log"
    with resumed_log.open("xb") as output:
        parent = subprocess.Popen(
            [sys.executable, str(ENTRY), "run", "--pause-after", "1", "--root", str(root)],
            cwd=SOURCE,
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
    owner_path = root / "executions" / original["execution_id"] / "linux-collector-owner.json"
    until = time.monotonic() + 90
    while time.monotonic() < until:
        current = first(root)
        owner = load(owner_path)
        if (
            current["state"] == "RUNNING"
            and platform.process_identity(owner["pid"]) == owner["identity"]
        ):
            break
        if parent.poll() is not None:
            raise ValueError("PARENT_EXITED_BEFORE_SAFE_STOP")
        time.sleep(0.1)  # observe persisted collector state; no race fault placement
    else:
        raise TimeoutError("SAME_EXECUTION_RESUME_NOT_OBSERVED")
    os.kill(parent.pid, signal.SIGTERM)
    parent.wait(timeout=40)
    if parent.returncode or platform.process_identity(owner["pid"]) != owner["identity"]:
        raise ValueError("DETACHED_COLLECTOR_DID_NOT_SURVIVE")
    immutable(
        root.parent / "safe-parent-stop.json",
        {
            "at": now(),
            "collector": owner,
            "execution_id": current["execution_id"],
            "deadline": current["deadline"],
            "same_as_original": current["deadline"] == original["deadline"],
            "collector_alive_after_parent_exit": True,
            "main_started": False,
        },
    )
    invoke(root, "reattach-first-window", ["resume", "--pause-after", "1"])
    exported = first(root)
    if (
        exported["deadline"] != original["deadline"]
        or exported["execution_id"] != original["execution_id"]
    ):
        raise ValueError("EXECUTION_OR_DEADLINE_REPLACED")
    first_evidence = verify_export(root, exported)
    if Ledger(root).rows()[1]["state"] != "PLANNED":
        raise ValueError("BETWEEN_SLOT_PAUSE_FAILED")
    invoke(root, "saved-order-second-window", ["resume", "--pause-after", "1"])
    rows = Ledger(root).rows()
    second_trace = load(root / "executions" / rows[1]["execution_id"] / "export.json")
    if second_trace["unsafe_attempt"]["status"] != 409:
        raise ValueError("EXPECTED_STALE_START_REFUSAL_NOT_OBSERVED")
    evidence = [first_evidence, verify_export(root, rows[1])]
    if digest(Path(first_evidence["export"])) != first_evidence["export_hash"]:
        raise ValueError("ORIGINAL_OUTCOME_REPLACED")
    invoke(root, "verify", ["verify"], 60)
    admission_end = platform.host(root, backup)
    immutable(
        root.parent / "qualification-success.json",
        {
            "at": now(),
            "status": "PASS_NATIVE_COLLECTOR_V2",
            "executions": evidence,
            "same_id_deadline_resume": True,
            "parent_stop_reattach": True,
            "saved_order_pause": True,
            "main_started": False,
            "main_slots_not_started": 1500,
            "end_resources": admission_end,
        },
    )
    print(json.dumps({"status": "PASS_NATIVE_COLLECTOR_V2", "main_started": False}), flush=True)


if __name__ == "__main__":
    root, backup = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        qualify(root, backup)
    except Exception as error:
        immutable(
            root.parent / "qualification-failure.json",
            {
                "at": now(),
                "type": type(error).__name__,
                "detail": str(error),
                "new_admissions_stopped": True,
                "main_started": False,
            },
        )
        raise
