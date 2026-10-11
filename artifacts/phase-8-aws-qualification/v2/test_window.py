"""Deterministic cutoff straddle reproduction: post-cutoff read must still occur."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from research.execution_setup import worker as original
from research.execution_setup.core import digest


def revised() -> Any:
    path = Path(__file__).with_name("worker_v2.py")
    spec = importlib.util.spec_from_file_location("aws_worker_cutoff_v2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("version", "expected_reads"), [("v1", 1), ("v2", 2)])
def test_query_straddling_cutoff_does_not_substitute_for_post_cutoff_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, version: str, expected_reads: int
) -> None:
    module = original if version == "v1" else revised()
    snapshots: list[int] = []
    times = iter(
        [
            "2020-01-01T00:09:59.900000+00:00",
            "2020-01-01T00:10:00.040000+00:00",
            "2020-01-01T00:10:00.100000+00:00",
            "2020-01-01T00:10:00.240000+00:00",
            "2020-01-01T00:10:00.300000+00:00",
        ]
    )
    monkeypatch.setattr(module, "now", lambda: next(times))
    monkeypatch.setattr(
        module,
        "host",
        lambda *args: {
            "available_memory_bytes": 8 * 1024**3,
            "system_free_bytes": 30 * 1024**3,
        },
    )
    monkeypatch.setattr(module, "check_source", lambda *args: None)
    monkeypatch.setattr(module, "cpu_fraction", lambda *args: 0.0)
    monkeypatch.setattr(module, "database", lambda *args: {})
    monkeypatch.setattr(module, "docker_stats", lambda *args: [])
    monkeypatch.setattr(
        module,
        "evidence_for",
        lambda *args: (
            None,
            SimpleNamespace(acceptances=[]),
        ),
    )
    monkeypatch.setattr(
        module,
        "revised_evaluate",
        lambda *args, **kw: (
            {},
            SimpleNamespace(model_dump=lambda **kw: {}),
        ),
    )
    ledger = SimpleNamespace(
        root=tmp_path,
        update=lambda *args, **kw: None,
        event=lambda *args, **kw: None,
        seal=digest,
        verify=lambda: None,
    )
    module.immutable(tmp_path / "config.json", {"backup": str(tmp_path)})
    stopped: list[bool] = []
    runtime = SimpleNamespace(
        database="unused",
        sim_database="unused",
        config={"containers": []},
        events=[],
        stop_all=lambda: stopped.append(True),
    )

    def snapshot() -> dict[str, Any]:
        snapshots.append(len(snapshots) + 1)
        return {"read": snapshots[-1]}

    trial = SimpleNamespace(
        id="unit-cutoff",
        arm="B3",
        ledger=ledger,
        runtime=runtime,
        execution_directory=tmp_path / "execution",
        save=lambda: None,
        snapshot=snapshot,
        row={"original_deadline": "2020-01-01T00:10:00+00:00", "polls": []},
    )
    assert module.collect(trial)
    assert len(snapshots) == expected_reads and stopped == [True]
    if version == "v2":
        assert trial.row["snapshot"]["read"] == 2
        assert trial.row["polls"][-1]["at"] >= trial.row["original_deadline"]
