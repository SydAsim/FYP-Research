"""Recognize only the evidenced, non-retryable B3 operation-history refusal."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError

from packages.domain.phase3_verification import Result, evaluate_appointment
from research.scenario_dsl.models import stable_hash

VERSION = "phase85-refusal-amendment-v1"
EXPECTED = "EXPECTED_EVIDENCE_REFUSAL"


class BackendProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: Literal["https://example.invalid/problems/b3-evidence"]
    title: Literal["B3 evidence unavailable"]
    status: Literal[409]
    detail: Literal["Current provider facts do not support speech"]
    instance: str
    trace_id: str
    retryable: Literal[False]


class VoiceProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: Literal["https://example.invalid/problems/voice-command-rejected"]
    title: Literal["Voice Command Rejected"]
    status: Literal[409]
    detail: str
    instance: Literal["/internal/phase6/b3/schedule"]
    trace_id: str


def recognize(row: dict[str, Any], error_detail: str | None = None) -> dict[str, Any] | None:
    """Missing or contradictory evidence defaults to a technical failure.

    Arm is checked because this endpoint belongs to B3, not to grant better grades.
    Business and speech outcomes are subsequently graded by the independent oracle.
    No refusal retry, write request, or backend evidence relaxation occurs here.
    """
    try:
        if row["arm"] != "B3" or row["status"] != "FAILED":
            return None
        failure = row["failure"]
        if failure["type"] != "RuntimeError":
            return None
        errors = [r for r in row["http"] if isinstance(r.get("status"), int) and r["status"] >= 400]
        call = errors[-1]
        request = call["request"]
        workflow = row["workflow_id"]
        if (
            call["method"] != "POST"
            or call["path"] != "/internal/phase6/b3/schedule"
            or call["status"] != 409
            or request != {"workflow_id": workflow, "expected_intent_revision": 2}
            or len(row["input"]["intents"]) != 2
            or row["input"]["provider"]["status_lookup"] is not False
            or row["input"]["provider"]["resource_lookup"] is not True
            or row["input"]["provider"]["supports_reschedule"] is not True
        ):
            return None
        detail = f"HTTP 409: {call['path']}: {call['response']}"
        if failure["detail"] != detail or (error_detail is not None and error_detail != detail):
            return None
        wrapper = VoiceProblem.model_validate(call["response"])
        UUID(wrapper.trace_id)
        synthesis_path = f"/internal/phase6/b3/workflows/{workflow}/synthesis-input"
        prefix = f"Controller rejected GET {synthesis_path}?revision=2: 409 "
        if not wrapper.detail.startswith(prefix):
            return None
        problem = BackendProblem.model_validate(json.loads(wrapper.detail[len(prefix) :]))
        UUID(problem.trace_id)
        if problem.instance != synthesis_path:
            return None
        snapshot = row["snapshot"]
        history = snapshot["history"]
        revisions = {r["revision"]: r for r in history["revisions"]}
        if history["workflow_id"] != workflow or 2 not in revisions:
            return None
        operations = {o["intent_revision"]: o for o in history["operations"]}
        old, current = operations[1], operations[2]
        if current["effect_knowledge"] != "PRESENT":
            return None
        sent, received = (
            datetime.fromisoformat(call["sent_at"]),
            datetime.fromisoformat(call["received_at"]),
        )
        fresh = [
            o
            for o in snapshot["observations"]
            if sent <= datetime.fromisoformat(o["available_at"]) <= received
        ]
        if len(fresh) != 3:
            return None
        if any(stable_hash(o["raw"]) != o["raw_hash"] for o in fresh):
            return None
        resource = next(o for o in fresh if o["source_type"] == "SIMULATOR_RESOURCE")
        key = row["targets"][-1]["resource_key"]
        if (
            resource["raw"]["status"] != 200
            or resource["source_identifier"] != key
            or resource["query"]
            != {
                "scenario_id": row["scenario_id"],
                "operation_id": current["id"],
                "resource_key": key,
            }
            or evaluate_appointment(
                revisions[2]["desired_state_json"], key, resource["raw"]["body"]
            ).result
            is not Result.SATISFIED
        ):
            return None
        statuses = [o for o in fresh if o["source_type"] == "SIMULATOR_OPERATION"]
        if len(statuses) != 2:
            return None
        expected = {current["id"]: "RESCHEDULE", old["id"]: "CREATE"}
        if {o["source_identifier"] for o in statuses} != set(expected):
            return None
        for observation in statuses:
            operation = observation["source_identifier"]
            if observation["raw"] != {
                "body": {"detail": "Operation status lookup is absent"},
                "status": 501,
            } or observation["query"] != {
                "scenario_id": row["scenario_id"],
                "operation_id": operation,
                "action": expected[operation],
            }:
                return None
        proof = {
            "version": VERSION,
            "classification": EXPECTED,
            "raw_driver_status": "FAILED",
            "original_instrument_status": "INFRASTRUCTURE_FAILURE",
            "revised_instrument_status": "COMPLETED",
            "reason": (
                "Current resource matches; both linked operation-status reads are unavailable"
            ),
            "call_hash": stable_hash(call),
            "observation_hashes": [stable_hash(o) for o in fresh],
            "trace_id": wrapper.trace_id,
            "backend_trace_id": problem.trace_id,
            "workflow_id": workflow,
            "intent_revision": 2,
            "operation_id": current["id"],
            "retryable": False,
            "retry_performed": False,
            "business_success_inferred_from_refusal": False,
        }
        return {**proof, "hash": stable_hash(proof)}
    except (KeyError, IndexError, TypeError, ValueError, StopIteration, ValidationError):
        return None


def validate_classification(row: dict[str, Any]) -> bool:
    stored = row.get("driver_classification")
    if stored is None:
        return False
    actual = recognize(row)
    if actual is None or stored != actual:
        raise ValueError("REFUSAL_CLASSIFICATION_EVIDENCE_DRIFT")
    return True


def timing_eligible(row: dict[str, Any]) -> bool:
    if not validate_classification(row):
        return False
    if row.get("missing_final_anchor") or row.get("collection_errors") or row.get("source_drift"):
        return False
    anchor = row["external_requests"][-1]
    if anchor["revision"] != 2:
        return False
    cutoff = datetime.fromisoformat(row["original_deadline"])
    if (cutoff - datetime.fromisoformat(anchor["issued_at"])).total_seconds() != 600:
        return False
    return bool(row.get("polls")) and datetime.fromisoformat(row["polls"][-1]["at"]) >= cutoff
