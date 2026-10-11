"""Account for every fixed slot; regrade exports without replacing observations."""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from backups_p82 import verify
from measure_p82 import execution
from plan import validate_plan

from research.execution_setup.core import immutable, load
from research.execution_setup.resources import tree_bytes


def summarize(root: Path, backup: Path) -> dict[str, Any]:
    slots = validate_plan(Path(__file__).parent / "slots.json")
    observed: dict[str, Path] = {}
    for meta in root.glob("blocks/*/*/run/p83-slot.json"):
        identity = load(meta)["slot_id"]
        if identity in observed:
            raise ValueError("DUPLICATE_PLANNED_SLOT_RETAIN_ORIGINALS")
        observed[identity] = meta.parent
    rows: list[dict[str, Any]] = []
    for slot in slots:
        row: dict[str, Any] = {
            "slot_id": slot.slot_id, "arm": slot.arm,
            "recipe": slot.case.generator_family, "label": slot.label,
            "reference_slot": slot.reference_slot, "state": "NOT_ADMITTED",
        }
        if slot.slot_id in observed:
            lane = observed[slot.slot_id]
            uri = f"file:{(lane / 'ledger.sqlite3').as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                recorded = [dict(r) for r in conn.execute("SELECT * FROM slots ORDER BY sequence")]
            if len(recorded) != 1:
                raise ValueError("ONE_SLOT_PER_PRIVATE_LANE_REQUIRED")
            entry = recorded[0]
            row.update({"state": entry["state"], "execution_id": entry["execution_id"],
                        "deadline": entry["deadline"], "ledger": str(lane / "ledger.sqlite3")})
            path = lane / "executions" / str(entry["execution_id"]) / "export.json"
            if path.is_file():
                try:
                    row["measurement"] = execution(path)
                except Exception as error:
                    # Preserve the unchanged original export and expose an analysis defect.
                    row["analysis_failure"] = {"type": type(error).__name__, "detail": str(error)}
            elif entry["execution_id"]:
                row["measurement"] = "INCOMPLETE_NO_EXPORT_UNKNOWN_OUTCOMES"
        rows.append(row)
    try:
        backups: dict[str, Any] = {"checks": verify(backup), "restoration_tested": False}
    except Exception as error:
        backups = {"failure": {"type": type(error).__name__, "detail": str(error)}}
    blocks = []
    for path in sorted(root.glob("blocks/*/result.json")):
        block = load(path)
        start = load(path.parent / "barriers/release.json")["at"]
        block["released_wall_seconds"] = (
            datetime.fromisoformat(block["at"]) - datetime.fromisoformat(start)
        ).total_seconds()
        blocks.append(block)
    serial = [b["released_wall_seconds"] for b in blocks if len(b["slots"]) == 1]
    pairs = [b["released_wall_seconds"] for b in blocks if len(b["slots"]) == 2]
    return {
        "classification": "CALIBRATION_ONLY", "main_started": False,
        "planned_executions": 24, "main_inferential_inputs": 0,
        "slots": rows, "blocks": blocks, "backups": backups,
        "raw_directory_bytes": tree_bytes(root), "backup_directory_bytes": tree_bytes(backup),
        "serial_block_median_seconds": median(serial) if serial else None,
        "paired_block_median_seconds": median(pairs) if pairs else None,
        "serial_1500_reference_hours": median(serial) * 1500 / 3600 if serial else None,
        "scope": "No whole-bank parallel speedup or superiority inference. Tone/ACK only.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("backup", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    immutable(args.output, summarize(args.root, args.backup))
