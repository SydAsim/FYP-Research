"""Recorded administrative deadlines for separate calibration observations."""

import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from threading import Event
from typing import Any

from research.remedies.runner import Trial, now
from research.scenario_dsl.models import stable_hash


def observe(
    trial: Trial,
    seconds: int,
    name: str,
    predicate: Callable[[dict[str, Any], datetime], bool] | None = None,
) -> dict[str, Any]:
    if not trial.row["input"]["case_id"].startswith("cal-v4-"):
        raise ValueError("Main campaign observation is not enabled")
    start = time.monotonic()
    until = datetime.now(UTC) + timedelta(seconds=seconds)
    record: dict[str, Any] = {
        "name": name,
        "started_at": now(),
        "deadline": until.isoformat(),
        "budget_seconds": seconds,
        "polls": [],
        "main_started": False,
    }
    trial.row.setdefault("observation_windows", []).append(record)
    trial.save()
    while True:
        snapshot = trial.snapshot()
        record["polls"].append(
            {
                "at": now(),
                "journal_hash": stable_hash(snapshot),
                "obligations": snapshot["obligations"],
                "playback_rows": snapshot["playback_rows"],
            }
        )
        met = predicate(snapshot, until) if predicate else False
        remaining = seconds - (time.monotonic() - start)
        trial.save()
        if met or remaining <= 0:
            record.update(
                ended_at=now(),
                elapsed_seconds=time.monotonic() - start,
                outcome="CONDITION_OBSERVED" if met else "ADMINISTRATIVE_TIMEOUT",
                snapshot=snapshot,
            )
            trial.save()
            return record
        Event().wait(min(remaining, 5))  # journal polling, never fault placement
