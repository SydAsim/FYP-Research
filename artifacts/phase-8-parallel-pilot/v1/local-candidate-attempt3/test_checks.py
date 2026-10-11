"""Reject realistic peer leaks and record both lanes; no domain outcome is mocked."""

from copy import deepcopy
from typing import Any

import pytest
from checks import validate_isolation


def evidence() -> dict[str, dict[str, Any]]:
    start = {"event": "PROCESS_STARTED", "name": "worker"}
    return {
        "A": {
            "fixture_identity": {"workflow_id": "workflow-a"},
            "processes": [{**start, "pid": 1}, {**start, "pid": 3}],
            "snapshot": {"own": "workflow-a"},
        },
        "B": {
            "fixture_identity": {"workflow_id": "workflow-b"},
            "processes": [{**start, "pid": 2}],
            "snapshot": {"own": "workflow-b"},
            "redis_fault": [{"args": ["FLUSHDB", "SYNC"]}],
        },
    }


def test_recorded_owned_pair_passes() -> None:
    validate_isolation(
        evidence(), {"A": "restart-before-repair", "B": "redis-loss"}, {"A": "A", "B": ""}
    )


@pytest.mark.parametrize("fault", ["cache-peer", "restart-peer", "query-peer", "missing-fault"])
def test_shared_faults_cannot_be_qualified(fault: str) -> None:
    traces = deepcopy(evidence())
    caches = {"A": "A", "B": ""}
    if fault == "cache-peer":
        caches["A"] = ""
    elif fault == "restart-peer":
        traces["B"]["processes"].append({"event": "PROCESS_STARTED", "name": "worker", "pid": 4})
    elif fault == "query-peer":
        traces["A"]["snapshot"]["foreign"] = "workflow-b"
    else:
        traces["B"].pop("redis_fault")
    with pytest.raises(ValueError):
        validate_isolation(traces, {"A": "restart-before-repair", "B": "redis-loss"}, caches)
