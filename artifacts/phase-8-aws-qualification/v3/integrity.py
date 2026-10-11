"""Seal and check executing research adapters, including code outside the capsule."""

from pathlib import Path
from typing import Any

from research.execution_setup.core import Ledger, atomic, check_inventory, immutable, load, now


def register(root: Path, inventory: dict[str, str], ledger: Any) -> None:
    # Absolute paths intentionally bind the exact executing adapter locations.
    check_inventory(inventory)
    path = root / "executing-adapters-seal.json"
    immutable(path, {"version": "aws-integrity-v3", "files": inventory, "main_started": False})
    ledger.seal(path)


def verify(root: Path) -> None:
    ledger = Ledger(root)
    path = root / "executing-adapters-seal.json"
    try:
        with ledger.connect() as conn:
            row = conn.execute(
                "SELECT hash FROM files WHERE path=?", (path.relative_to(root).as_posix(),)
            ).fetchone()
        if row is None:
            raise ValueError("UNREGISTERED_EXECUTING_ADAPTER_MANIFEST")
        check_inventory({path.name: row[0]}, root)
        check_inventory(load(path)["files"])
    except ValueError as error:
        ledger.event("EXECUTING_ADAPTER_SOURCE_DRIFT", detail=str(error), main_started=False)
        atomic(root / "pause.json", {"reason": "EXECUTING_ADAPTER_SOURCE_DRIFT", "at": now()})
        raise
