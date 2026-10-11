"""One isolated calibration ledger, using preserved Linux collector code."""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
from research.execution_linux_v1 import platform, runner, runtime  # noqa: E402
from research.execution_setup import core  # noqa: E402
from research.execution_setup.core import immutable, load, now  # noqa: E402
from research.study.models import StudyCase  # noqa: E402


def initialize(root: Path, backup: Path, lane: str) -> None:
    if lane not in ("A", "B") or root.exists() and any(root.iterdir()):
        raise ValueError("NEW_CALIBRATION_DIRECTORY_REQUIRED")
    runner.install()
    runner.verify_package()
    root.mkdir(parents=True)
    backup.mkdir(parents=True, exist_ok=True)
    bank = load(SOURCE / "research/fixtures/phase8_design_v4/inputs.json")
    family = "restart-before-repair" if lane == "A" else "redis-loss"
    original = next(c for c in bank["calibration_inputs"] if c["generator_family"] == family)
    case = StudyCase.model_validate(
        {**original, "case_id": f"{runner.PREFIX}aws-parallel-{lane}"}
    ).model_dump(mode="json")
    identity = uuid4().hex[:10]
    names = [f"p8-aws-par-{identity}-{kind}" for kind in ("app", "truth", "cache")]
    resources = {
        "resource_id": identity,
        "containers": names,
        "database": f"postgresql://setup_app:setup_local_only@{names[0]}/setup_app",
        "sim_database": f"postgresql://setup_truth:setup_local_only@{names[1]}/setup_truth",
        "services": [19100, 19101, 19102, 19110],
        "concurrency": 1,
        "validation_network": os.environ["P8_VALIDATION_NETWORK"],
        "image_digests": runner.IMAGE_DIGESTS,
    }
    historical = load(runner.PACKAGE / "preserved-before.json")
    core.check_inventory(historical)
    ledger: Any = runner.ledger_for(root)
    objects = {
        "qualification-plan.json": {
            "version": runner.VERSION,
            "classification": "CALIBRATION_ONLY_NOT_MAIN",
            "created_at": now(),
            "cases": {case["case_id"]: case},
            "order": [[case["case_id"], "P2"]],
            "window_seconds": 600,
            "poll_seconds": 5,
            "concurrency": 1,
            "main_started": False,
            "review_receipt": None,
            "freeze_hash": None,
        },
        "config.json": {"version": runner.VERSION, "backup": str(backup), "main_started": False},
        "resources.json": resources,
        "source-seal.json": core.source_inventory(),
        "linux-package-seal.json": load(SOURCE / "linux-package-seal.json"),
        "historical-hashes-before.json": historical,
        "addon-seal.json": load(Path(__file__).parent / "seal.json"),
    }
    for name, value in objects.items():
        immutable(root / name, value)
        ledger.seal(root / name)
    for name, expected in objects["addon-seal.json"]["files"].items():
        path = Path(__file__).parent / name
        if core.digest(path) != expected:
            raise ValueError("ADDON_HASH_DRIFT")
        # Copy the immutable orchestrator into each evidence tree for drift checks.
        target = root / "orchestrator" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(path.read_bytes())
        ledger.seal(target)
    with ledger.connect() as conn:
        conn.execute(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) VALUES (?,?,?,?,?,?)",
            (1, case["case_id"], "P2", "PLANNED", 1, "ORIGINAL_PLANNED"),
        )
    immutable(root / "initial-resources.json", platform.host(root, backup))
    ledger.seal(root / "initial-resources.json")
    runtime.provision(root)
    immutable(root.parent / "ready.json", {"at": now(), "lane": lane, "resources": resources})


def main() -> None:
    root, backup, lane = Path("/work/run"), Path("/backup/run"), sys.argv[1]
    initialize(root, backup, lane)
    until = time.monotonic() + 120
    while not Path("/barriers/release.json").exists():
        if time.monotonic() > until:
            raise TimeoutError("BOTH_RESOURCES_READY_RELEASE_MISSING")
        time.sleep(0.2)
    command = [
        sys.executable,
        str(SOURCE / "artifacts/phase-8-linux-setup/v1/runner.py"),
        "run",
        "--root",
        str(root),
    ]
    result = subprocess.run(command, cwd=SOURCE, timeout=800)
    immutable(root.parent / "lane-exit.json", {"at": now(), "exit": result.returncode})
    result.check_returncode()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        immutable(Path("/work/lane-failure.json"), {"at": now(), "detail": str(error)})
        raise
