"""A namespaced slot: initialize, announce readiness, await named release, collect."""

import os
import subprocess
import sys
import time
from pathlib import Path

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
from research.execution_setup.core import immutable, load, now  # noqa: E402


def run() -> None:
    addon = Path(__file__).parent
    root, backup = Path("/work/run"), Path("/backup/run")
    entry = addon / "combined.py"
    subprocess.run(
        [sys.executable, str(entry), "init", "--root", str(root), "--backup", str(backup)],
        cwd=SOURCE,
        check=True,
        timeout=120,
    )
    # Provisioning is owned by the original runtime; no controller decision moves here.
    from research.execution_linux_v1.runtime import provision

    provision(root)
    immutable(
        root.parent / "ready.json",
        {
            "at": now(),
            "slot_id": os.environ["P83_SLOT_ID"],
            "resources": load(root / "resources.json"),
        },
    )
    deadline = time.monotonic() + 120
    while not Path("/barriers/release.json").is_file():
        if time.monotonic() > deadline:
            raise TimeoutError("BOTH_RESOURCES_READY_RELEASE_MISSING")
        time.sleep(0.2)  # readiness observation; not fault placement
    subprocess.run(
        [sys.executable, str(entry), "run", "--root", str(root)],
        cwd=SOURCE,
        check=True,
        timeout=850,
    )
    immutable(root.parent / "lane-exit.json", {"at": now(), "exit": 0})


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        immutable(Path("/work/lane-failure.json"), {"at": now(), "detail": str(error)})
        raise
