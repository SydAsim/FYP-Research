"""Read only the owned worker identity in a lane, without printing service tokens."""

import sys
from pathlib import Path

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
from research.execution_linux_v1.platform import process_identity  # noqa: E402
from research.execution_setup.core import Ledger, load, now  # noqa: E402


def sample() -> dict[str, object]:
    root = Path("/work/run")
    row = Ledger(root).rows()[0]
    execution = row["execution_id"]
    if execution is None:
        return {"at": now(), "required": False, "phase": "NOT_ADMITTED"}
    directory = root / "executions" / execution
    checkpoint = directory / "checkpoint.json"
    phase = load(checkpoint) if checkpoint.exists() else {}
    services = directory / "services.json"
    worker = load(services)["records"].get("worker") if services.exists() else None
    required = bool(phase.get("driver_finished_at")) and row["state"] != "EXPORTED"
    alive = bool(worker and process_identity(worker["pid"]) == worker["identity"])
    return {
        "at": now(),
        "execution_id": execution,
        "state": row["state"],
        "required": required,
        "worker_alive": alive,
        "worker_pid": worker["pid"] if worker else None,
        "worker_identity": worker["identity"] if worker else None,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(sample()))
