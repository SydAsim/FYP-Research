"""Fresh single-slot initialization over the preserved v3.1 combined collector.

Changes only research initialization. Child collection is the exact v3.1 entrypoint
using v2 cutoff semantics. No service/domain module is patched by this adapter.
"""

import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

SOURCE = Path("/opt/fyp-phase8-linux-v1")
ADDON = Path(__file__).parent
V2 = Path("/opt/fyp-phase82-qualification-v2")
V31 = Path("/opt/fyp-phase82-qualification-v3.1")
sys.path[:0] = [str(SOURCE), str(V31), str(V2), str(ADDON)]
import integrity  # noqa: E402
import runner_v3  # noqa: E402,F401 -- installs the preserved combined process boundary
from plan import validate_plan  # noqa: E402

from research.execution_linux_v1 import platform, runner  # noqa: E402
from research.execution_setup.core import (  # noqa: E402
    check_inventory,
    digest,
    immutable,
    load,
    now,
    source_inventory,
)


def initialize(root: Path, backup: Path) -> None:
    root, backup = root.resolve(), backup.resolve()
    if root == backup or root in backup.parents or backup in root.parents:
        raise ValueError("SEPARATE_BACKUP_REQUIRED")
    if SOURCE == root or SOURCE in root.parents or SOURCE == backup or SOURCE in backup.parents:
        raise ValueError("EVIDENCE_MUST_BE_OUTSIDE_SOURCE")
    if root.exists() and any(root.iterdir()):
        raise ValueError("NEW_DIRECTORY_REQUIRED_RETAIN_ORIGINALS")
    runner.verify_package()
    check_inventory(load(ADDON / "seal.json")["files"], ADDON)
    slot_id = os.environ["P83_SLOT_ID"]
    selected = [s for s in validate_plan(ADDON / "slots.json") if s.slot_id == slot_id]
    if len(selected) != 1:
        raise ValueError("DECLARED_CALIBRATION_SLOT_REQUIRED")
    slot = selected[0]
    reference = os.environ.get("P83_REFERENCE_EXECUTION")
    if (slot.reference_slot is not None) != bool(reference):
        raise ValueError("SCHEDULE_REPEAT_LINK_REQUIRED")
    root.mkdir(parents=True)
    backup.mkdir(parents=True, exist_ok=True)
    ledger: Any = runner.ledger_for(root)
    network = os.environ["P8_VALIDATION_NETWORK"]
    identity = uuid4().hex[:10]
    names = [f"p83-{identity}-{kind}" for kind in ("app", "truth", "cache")]
    resources = {
        "resource_id": identity,
        "containers": names,
        "database": f"postgresql://setup_app:setup_local_only@{names[0]}/setup_app",
        "sim_database": f"postgresql://setup_truth:setup_local_only@{names[1]}/setup_truth",
        "services": [19100, 19101, 19102, 19110],
        "concurrency": 1,
        "validation_network": network,
        "image_digests": runner.IMAGE_DIGESTS,
    }
    historical = load(runner.PACKAGE / "preserved-before.json")
    check_inventory(historical)
    case = slot.case.model_dump(mode="json")
    objects = {
        "qualification-plan.json": {
            "version": runner.VERSION,
            "classification": "CALIBRATION_ONLY_NOT_MAIN",
            "created_at": now(),
            "cases": {case["case_id"]: case},
            "order": [[case["case_id"], slot.arm]],
            "window_seconds": 600,
            "poll_seconds": 5,
            "concurrency": 1,
            "main_started": False,
            "review_receipt": None,
            "freeze_hash": None,
        },
        "config.json": {"version": runner.VERSION, "backup": str(backup), "main_started": False},
        "resources.json": resources,
        "source-seal.json": source_inventory(),
        "linux-package-seal.json": load(SOURCE / "linux-package-seal.json"),
        "historical-hashes-before.json": historical,
        "p83-slot.json": {**slot.model_dump(mode="json"), "reference_execution": reference},
    }
    for name, value in objects.items():
        immutable(root / name, value)
        ledger.seal(root / name)
    inventory = {}
    for folder in (V2, V31, ADDON):
        expected = load(folder / "seal.json")["files"]
        check_inventory(expected, folder)
        inventory.update({str(folder / name): value for name, value in expected.items()})
        inventory[str(folder / "seal.json")] = digest(folder / "seal.json")
    integrity.register(root, inventory, ledger)
    with ledger.connect() as conn:
        conn.execute(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label,original_id) "
            "VALUES (?,?,?,?,?,?,?)",
            (1, case["case_id"], slot.arm, "PLANNED", 1, slot.label, reference),
        )
    immutable(root / "initial-resources.json", platform.host(root, backup))
    ledger.seal(root / "initial-resources.json")
    ledger.event("P83_CALIBRATION_INITIALIZED", slot_id=slot_id, main_started=False)


runner.initialize = initialize

if __name__ == "__main__":
    runner.entrypoint()
