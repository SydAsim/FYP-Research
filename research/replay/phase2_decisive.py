"""Replay the hidden 3 PM commit and 4 PM correction against running services."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

API = os.environ.get("PHASE2_API_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER = os.environ.get("PHASE2_WORKER_URL", "http://127.0.0.1:8002").rstrip("/")
SIMULATOR = os.environ.get("PHASE2_SIMULATOR_URL", "http://127.0.0.1:8010").rstrip("/")


def call(
    base: str, method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urlopen(request, timeout=40) as response:
        value: dict[str, Any] = json.load(response)
        return value


def _revision(fixture: dict[str, Any], number: int, hour: int) -> dict[str, Any]:
    return {
        "command_id": str(uuid4()),
        "expected_revision": number - 1,
        "change_class": "INITIAL" if number == 1 else "PARAMETER_CORRECTION",
        "desired_state": {
            "ticket_id": fixture["ticket_id"],
            "requested_start": f"2026-10-01T{hour:02d}:00:00+05:00",
            "requested_end": f"2026-10-01T{hour + 1:02d}:00:00+05:00",
            "timezone": "Asia/Karachi",
        },
        "candidate_source": {
            "utterance_id": fixture["utterance_ids"][number - 1],
            "model": "phase2-deterministic-fixture",
            "prompt_hash": f"phase2-fixture-revision-{number}",
            "transcript_version": 1,
        },
    }


def run() -> dict[str, Any]:
    scenario = call(
        SIMULATOR,
        "POST",
        "/internal/scenarios",
        {
            "idempotency": True,
            "status_lookup": True,
            "resource_lookup": True,
            "visibility": "IMMEDIATE",
            "supports_reschedule": True,
            "held_barriers": ["AFTER_COMMIT_BEFORE_RESPONSE:1"],
            "faults": [
                {
                    "request_index": 1,
                    "stage": "AFTER_COMMIT_BEFORE_RESPONSE",
                    "kind": "DROP_RESPONSE",
                }
            ],
        },
    )
    scenario_id = scenario["scenario_id"]
    fixture = call(API, "POST", "/internal/phase1/fixtures", {"command_id": str(uuid4())})
    workflow_id = fixture["workflow_id"]
    call(API, "POST", f"/v1/workflows/{workflow_id}/revisions", _revision(fixture, 1, 15))
    prepared = call(
        API,
        "POST",
        "/internal/phase2/operations",
        {
            "command_id": str(uuid4()),
            "workflow_id": workflow_id,
            "scenario_id": scenario_id,
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase2:{uuid4()}",
        },
    )
    first_operation_id = prepared["operation_id"]
    with ThreadPoolExecutor(max_workers=1) as pool:
        dispatch = pool.submit(call, WORKER, "POST", "/internal/phase2/step", {})
        barrier = "AFTER_COMMIT_BEFORE_RESPONSE:1"
        reached = call(
            SIMULATOR,
            "GET",
            f"/internal/scenarios/{scenario_id}/barriers/{quote(barrier)}?wait=true",
        )
        assert reached["reached_at"] is not None, reached
        call(API, "POST", f"/v1/workflows/{workflow_id}/revisions", _revision(fixture, 2, 16))
        call(
            SIMULATOR,
            "POST",
            f"/internal/scenarios/{scenario_id}/barriers/{quote(barrier)}/release",
            {},
        )
        dispatch.result(timeout=40)
    steps: list[dict[str, Any]] = []
    for _ in range(12):
        result = call(WORKER, "POST", "/internal/phase2/step", {})
        steps.append(result)
        if result["action"] == "idle":
            break
    history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
    truth = call(SIMULATOR, "GET", f"/internal/scenarios/{scenario_id}/truth")
    operation = call(API, "GET", f"/v1/operations/{first_operation_id}")
    commits = truth["commits"]
    assert len(commits) == 2, commits
    assert [commit["action"] for commit in commits] == ["CREATE", "RESCHEDULE"], commits
    assert commits[-1]["after_facts"]["starts_at"] == "2026-10-01T11:00:00+00:00", commits
    assert history["current_revision"] == 2, history
    assert all(
        item["effect_knowledge"] != "ABSENT"
        for item in history["operations"]
        if item["id"] == first_operation_id
    ), history
    result = {
        "scenario_id": scenario_id,
        "workflow_id": workflow_id,
        "normalized_timeline": history["events"],
        "worker_steps": steps,
        "first_operation": operation,
        "simulator_truth_log": commits,
        "final_resolution": history["operations"],
    }
    output = os.environ.get("PHASE2_REPLAY_OUTPUT")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
