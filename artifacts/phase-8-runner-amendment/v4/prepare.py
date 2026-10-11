"""Assemble the minimal local-only candidate; never mutate frozen v3."""

from __future__ import annotations

import difflib
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "v3"


def main() -> None:
    original = (BASE / "controls.py").read_bytes()
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    before = newline.join(
        [b"    def verify(self) -> None:", b"        with self.connect() as db:", b""]
    )
    after = before + b'            db.execute("BEGIN")' + newline
    assert original.count(before) == 1
    revised = original.replace(before, after, 1)
    with (HERE / "controls.py").open("xb") as file:
        file.write(revised)
    diff = "".join(
        difflib.unified_diff(
            original.decode().splitlines(keepends=True),
            revised.decode().splitlines(keepends=True),
            fromfile="v3/controls.py",
            tofile="v4/controls.py",
        )
    )
    with (HERE / "controls.diff").open("x", encoding="utf-8", newline="\n") as file:
        file.write(diff)
    value = {
        "recorded_before_checks_utc": datetime.now(UTC).isoformat(),
        "version": "phase85-ledger-snapshot-amendment-v4-local-candidate",
        "tests": 15,
        "maximum_wall_seconds": 300,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "candidate_sha256": hashlib.sha256(revised).hexdigest(),
        "scope": "TEMPORARY_SQLITE_CONTROLS_AND_RETAINED_READ_ONLY_EVIDENCE",
        "research_executions": 0,
        "aws_actions": 0,
        "application_stacks": 0,
        "frozen": False,
        "launch_authorized": False,
    }
    with (HERE / "qualification-plan.json").open("x") as file:
        json.dump(value, file, indent=2)


if __name__ == "__main__":
    main()
