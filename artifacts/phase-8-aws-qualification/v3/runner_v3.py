"""V2 collection semantics with executing-adapter integrity at every boundary."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

SOURCE = Path("/opt/fyp-phase8-linux-v1")
V2 = Path("/opt/fyp-phase82-qualification-v2")
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(V2))
import integrity  # noqa: E402
import runner_v2 as delegate  # noqa: E402
import worker_v2  # noqa: E402

from research.execution_linux_v1 import runner  # noqa: E402
from research.execution_setup.core import check_source, digest, load  # noqa: E402

initialize_v2, verify_v2 = delegate.initialize, runner.verify


def initialize(root: Path, backup: Path) -> None:
    initialize_v2(root, backup)
    expected = load(V2 / "seal.json")["files"]
    inventory = {str(V2 / name): value for name, value in expected.items()}
    inventory[str(V2 / "seal.json")] = digest(V2 / "seal.json")
    addon = Path(__file__).parent
    expected_v3 = load(addon / "seal.json")["files"]
    inventory.update({str(addon / name): value for name, value in expected_v3.items()})
    inventory[str(addon / "seal.json")] = digest(addon / "seal.json")
    integrity.register(root, inventory, runner.ledger_for(root))


def verify(root: Path) -> None:
    integrity.verify(root)
    verify_v2(root)


def check_all(root: Path) -> None:
    integrity.verify(root)
    check_source(root)


def collector_process(command: list[str], **options: Any) -> subprocess.Popen[bytes]:
    prefix = [sys.executable, "-m", "research.execution_linux_v1.runner", "worker"]
    if command[:4] != prefix:
        raise ValueError("UNEXPECTED_RESEARCH_COLLECTOR_COMMAND")
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "worker", *command[4:]], **options
    )


runner.initialize, runner.verify = initialize, verify
vars(worker_v2)["check_source"] = check_all
vars(runner)["subprocess"] = SimpleNamespace(
    Popen=collector_process, TimeoutExpired=subprocess.TimeoutExpired
)

if __name__ == "__main__":
    if "--root" in sys.argv and len(sys.argv) > 1 and sys.argv[1] != "init":
        integrity.verify(Path(sys.argv[sys.argv.index("--root") + 1]))
    runner.entrypoint()
