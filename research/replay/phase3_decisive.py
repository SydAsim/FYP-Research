"""Replay hidden commit, revision-2 evidence, and one authorized 4 PM text release."""

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from research.replay.phase2_decisive import API, call
from research.replay.phase2_decisive import run as run_phase2


def run() -> dict[str, Any]:
    phase2 = run_phase2()
    workflow_id = phase2["workflow_id"]
    operations = phase2["final_resolution"]
    current = next(item for item in operations if item["intent_revision"] == 2)
    verify = call(
        API,
        "POST",
        "/internal/phase3/verifications",
        {
            "command_id": str(uuid4()),
            "operation_id": current["id"],
            "expected_intent_revision": 2,
            "claim_type": "RESCHEDULED_APPOINTMENT",
        },
    )
    assert verify["result"] == "SATISFIED", verify
    receipt = call(API, "GET", f"/v1/receipts/{verify['receipt_id']}")
    permit = call(
        API,
        "POST",
        "/internal/phase3/claims",
        {
            "command_id": str(uuid4()),
            "receipt_id": verify["receipt_id"],
            "expected_intent_revision": 2,
        },
    )
    queued = call(
        API,
        "POST",
        f"/internal/phase3/permits/{permit['permit_id']}/queue",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": 2,
        },
    )
    published = call(
        API,
        "POST",
        f"/internal/phase3/permits/{permit['permit_id']}/publish",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": 2,
        },
    )
    assert queued["state"] == "QUEUED"
    assert published["state"] == "PUBLISHED"
    assert "4:00 PM" in published["text"]
    assert "3:00 PM" not in published["text"]
    after = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
    assert not any(
        event["event_name"] == "ClaimPublished" and event["intent_revision"] == 1
        for event in after["events"]
    )
    result = {
        "workflow_id": workflow_id,
        "phase2_timeline": phase2["normalized_timeline"],
        "simulator_truth_log": phase2["simulator_truth_log"],
        "receipt": receipt,
        "permit": permit,
        "queued": queued,
        "publication": published,
        "normalized_timeline": after["events"],
    }
    output = os.environ.get("PHASE3_REPLAY_OUTPUT")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
