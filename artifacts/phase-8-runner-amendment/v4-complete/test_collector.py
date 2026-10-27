"""Control-only virtual clock; real SQLite checkpoints; no simulated oracle success."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import collector
import pytest
from controls import Journal, read, utc
from runner import prepare_slot
from test_controls import calibration, sample

from research.execution_setup.core import Ledger


@pytest.mark.parametrize("refused", [False, True, "permissive"])
def test_actual_collector_resume_keeps_driver_once_and_600_second_cutoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refused: bool | str
) -> None:
    root, authority = calibration(tmp_path)
    slot = Journal(root).admit(authority, sample(), utc(), 0)
    assert slot
    folder = prepare_slot(root, slot)
    ledger = Ledger(folder)
    clock = {"seconds": 0, "drivers": 0, "stops": 0}
    start = datetime.now(UTC)

    class Clock(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> "Clock":
            return cls.fromtimestamp((start + timedelta(seconds=clock["seconds"])).timestamp(), UTC)

    class Wait:
        def wait(self, duration: float) -> None:
            clock["seconds"] += 5

    def runtime(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(
            database="control-only",
            sim_database="control-only",
            config={"containers": []},
            events=[],
            start_all=lambda: None,
            stop_all=lambda: clock.update(stops=clock["stops"] + 1),
        )

    def driver(trial: Any) -> None:
        clock["drivers"] += 1
        deadline = (start + timedelta(seconds=600)).isoformat()
        trial.row["original_deadline"] = deadline
        trial.row["external_requests"] = [
            {"revision": trial.case.intents[-1].revision, "issued_at": start.isoformat()}
        ]
        trial.save()
        if refused == "permissive":
            from response_guard import retain

            retain(
                trial,
                {
                    "classification": "UNEXPECTED_RESPONSE",
                    "trace_id": "cal-control-trace",
                    "response": {"unexpected": True},
                },
            )
        elif refused:
            raise ValueError("CONTROL_ONLY_REFUSAL")

    monkeypatch.setattr(collector, "datetime", Clock)
    monkeypatch.setattr(collector, "now", lambda: Clock.now().isoformat())
    monkeypatch.setattr(collector, "Event", Wait)
    monkeypatch.setattr(collector, "Runtime", runtime)
    from contextlib import nullcontext

    monkeypatch.setattr(collector, "runner_lock", lambda *a: nullcontext())
    monkeypatch.setattr(collector, "bind", lambda *a: None)
    monkeypatch.setattr(collector, "host", lambda *a: sample())
    monkeypatch.setattr(collector, "cpu_fraction", lambda *a: 0.0)
    monkeypatch.setattr(collector, "database", lambda *a: {})
    monkeypatch.setattr(collector, "docker_stats", lambda *a: [])
    monkeypatch.setattr(collector.Trial, "run", driver)
    # No business-state oracle is mocked: control-only snapshots deliberately
    # produce a retained oracle failure, never a purported research success.
    monkeypatch.setattr(collector.Trial, "snapshot", lambda *a: {"CONTROL_ONLY": True})
    monkeypatch.setattr(
        "research.execution_linux_v1.runtime.install_process_boundary", lambda: None
    )
    assert not collector.execute(folder, ledger.rows()[0], checkpoint_once=True)
    first = ledger.rows()[0]
    assert first["state"] == "CHECKPOINTED" and clock["drivers"] == 1
    assert not (folder / "executions" / slot["execution_id"] / "export.json").exists()
    # Delayed restart, with the same source/ledger and original cutoff.
    clock["seconds"] = 20
    assert collector.execute(folder, ledger.rows()[0])
    final = ledger.rows()[0]
    trace = read(folder / "executions" / slot["execution_id"] / "export.json")
    assert final["execution_id"] == first["execution_id"]
    assert final["deadline"] == first["deadline"]
    assert clock["drivers"] == clock["stops"] == 1
    assert clock["seconds"] == 600 and len(trace["collector_resumes"]) == 1
    assert trace["polls"][-1]["at"] == first["deadline"]
    assert "oracle_failure" in trace
    assert trace["status"] == ("FAILED" if refused else "COMPLETED")
    ledger.verify()


def test_missing_final_request_is_not_invented_and_fallback_never_resets() -> None:
    row: dict[str, Any] = {
        "started_at": "2026-10-07T00:00:00+00:00",
        "external_requests": [{"issued_at": "2026-10-07T00:00:10+00:00"}],
    }
    deadline, missing = collector.fixed_deadline(row)
    assert deadline == "2026-10-07T00:10:10+00:00" and missing
    row.update(original_deadline=deadline, missing_final_anchor=True)
    row["external_requests"].append({"issued_at": "2026-10-07T00:15:00+00:00"})
    assert collector.fixed_deadline(row) == (deadline, True)
