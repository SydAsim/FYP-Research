"""Recorded pair isolation gates; protocol evidence, not a treatment-effect grader."""

import json
from typing import Any


def validate_isolation(
    traces: dict[str, dict[str, Any]],
    families: dict[str, str],
    caches: dict[str, str],
) -> None:
    workflows = {lane: trace["fixture_identity"]["workflow_id"] for lane, trace in traces.items()}
    if len(set(workflows.values())) != len(workflows):
        raise ValueError("WORKFLOW_COLLISION")
    for lane, trace in traces.items():
        workers = [
            e
            for e in trace["processes"]
            if e["event"] == "PROCESS_STARTED" and e["name"] == "worker"
        ]
        count = 2 if families[lane] == "restart-before-repair" else 1
        if len(workers) != count:
            raise ValueError("RESTART_LIFECYCLE_INTERFERENCE")
        expected = "" if families[lane] == "redis-loss" else lane
        if caches[lane] != expected:
            raise ValueError("CACHE_FAULT_CROSSED_OR_NOT_APPLIED")
        if families[lane] == "redis-loss" and not trace.get("redis_fault"):
            raise ValueError("DECLARED_CACHE_FAULT_MISSING")
        if any(w in json.dumps(trace["snapshot"]) for peer, w in workflows.items() if peer != lane):
            raise ValueError("CROSS_EXECUTION_QUERY_CONTAMINATION")
