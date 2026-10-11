"""Research collector v2 boundary. Sealed application and Linux capsule unchanged."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(Path(__file__).parent))
import worker_v2  # noqa: E402

from research.execution_linux_v1 import runner  # noqa: E402
from research.execution_setup.core import digest, immutable, load, now  # noqa: E402

initialize_v1 = runner.initialize


def initialize(root: Path, backup: Path) -> None:
    initialize_v1(root, backup)
    ledger = runner.ledger_for(root)
    addon = Path(__file__).parent
    seal = load(addon / "seal.json")
    for name, expected in seal["files"].items():
        source = addon / name
        if digest(source) != expected:
            raise ValueError("RESEARCH_COLLECTOR_V2_DRIFT")
        target = root / "collector-v2" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(source.read_bytes())
        ledger.seal(target)
    immutable(
        root / "collector-version.json",
        {
            "at": now(),
            "version": "aws-collector-v2",
            "main_started": False,
            "original_failure_retained": "8e07da51-1185-413c-aac3-80640caada4c",
            "change": "Final snapshot must start at or after original deadline",
        },
    )
    ledger.seal(root / "collector-version.json")
    with ledger.connect() as conn:
        conn.execute(
            "UPDATE slots SET label='DIAGNOSTIC_RERUN', original_id=? WHERE sequence=1",
            ("8e07da51-1185-413c-aac3-80640caada4c",),
        )


vars(runner)["worker"] = worker_v2
runner.initialize = initialize


def collector_process(command: list[str], **options: Any) -> subprocess.Popen[bytes]:
    # The preserved parent normally launches its historical module. Carry the
    # version into the separately spawned collector too, without changing any
    # application service launch or global subprocess module.
    prefix = [sys.executable, "-m", "research.execution_linux_v1.runner", "worker"]
    if command[:4] != prefix:
        raise ValueError("UNEXPECTED_RESEARCH_COLLECTOR_COMMAND")
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "worker", *command[4:]], **options
    )


vars(runner)["subprocess"] = SimpleNamespace(
    Popen=collector_process, TimeoutExpired=subprocess.TimeoutExpired
)

if __name__ == "__main__":
    runner.entrypoint()
