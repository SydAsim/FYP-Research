"""Fail-closed semantic classification of recorded evidence refusals, never HTTP alone."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError

from apps.api_controller.phase3_verification_service import Observation, _evaluate
from packages.domain.phase3_verification import ClaimType, Result
from research.provider_simulator.models import ScenarioConfig
from research.scenario_dsl.models import stable_hash
from research.study_v4.design import cells

VERSION = "phase85-preflight-amendment-v2"
EXPECTED = "EXPECTED_EVIDENCE_REFUSAL"


class ReceiptProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: Literal["https://example.invalid/problems/receipt-not-applicable"]
    title: Literal["Receipt not applicable"]
    status: Literal[409]
    detail: Literal["A current SATISFIED receipt is required"]
    instance: Literal["/internal/phase3/claims"]
    trace_id: str
    retryable: Literal[False]


class B3Problem(BaseModel):
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


def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Missing UTC offset")
    return result


def recognize(row: dict[str, Any], error_detail: str | None = None) -> dict[str, Any] | None:
    """Recompute the actual application predicate from bound ordinary observations.

    A negative receipt is a failed research communication, not business success.
    Clean-case refusals, expired/satisfied receipts, unrelated conflicts, transport
    errors and unprovable/corrupt records remain defects. No requests are replayed.
    """
    try:
        if row["arm"] not in ("B3", "P1", "P2") or row["status"] != "FAILED":
            return None
        if row["failure"]["type"] != "RuntimeError":
            return None
        case = row["input"]
        cell = next(c for c in cells() if c["name"] == case["generator_family"])
        if (
            cell["stratum"] == "CLEAN"
            or case["provider"]
            != ScenarioConfig.model_validate(cell["provider"]).model_dump(mode="json")
            or case["fault_schedule"] != cell["hooks"]
        ):
            return None
        failures = [
            c for c in row["http"] if isinstance(c.get("status"), int) and c["status"] >= 400
        ]
        call = failures[-1]
        detail = f"HTTP {call['status']}: {call['path']}: {call['response']}"
        if row["failure"]["detail"] != detail or (
            error_detail is not None and error_detail != detail
        ):
            return None
        if call["status"] != 409 or call["method"] != "POST":
            return None
        workflow = row["workflow_id"]
        history = row["snapshot"]["history"]
        revision = call["request"]["expected_intent_revision"]
        if revision != case["intents"][-1]["revision"] or history["workflow_id"] != workflow:
            return None
        revisions = {r["revision"]: r for r in history["revisions"]}
        desired = revisions[revision]["desired_state_json"]
        accepted = instant(revisions[revision]["accepted_at"])
        sent, received = instant(call["sent_at"]), instant(call["received_at"])
        if accepted > sent:
            return None
        operations = {o["id"]: o for o in history["operations"]}
        current = [
            o
            for o in operations.values()
            if o["intent_revision"] == revision
            and o["applicability"] == "CURRENT"
            and o["effect_knowledge"] == "PRESENT"
        ]
        if len(current) != 1:
            return None
        operation = current[0]
        claim_type = (
            ClaimType.CURRENT_APPOINTMENT if revision == 1 else ClaimType.RESCHEDULED_APPOINTMENT
        )
        receipt_id: str | None = None
        verification_hash: str | None = None
        expected_result: str | None = None
        verification_events: list[dict[str, Any]] = []
        if row["arm"] == "B3":
            if call["path"] != "/internal/phase6/b3/schedule" or call["request"] != {
                "workflow_id": workflow,
                "expected_intent_revision": revision,
            }:
                return None
            wrapper = VoiceProblem.model_validate(call["response"])
            UUID(wrapper.trace_id)
            path = f"/internal/phase6/b3/workflows/{workflow}/synthesis-input"
            prefix = f"Controller rejected GET {path}?revision={revision}: 409 "
            if not wrapper.detail.startswith(prefix):
                return None
            problem = B3Problem.model_validate(json.loads(wrapper.detail[len(prefix) :]))
            if problem.instance != path:
                return None
            backend_trace = problem.trace_id
            observed_from, observed_until = sent, received
        else:
            if call["path"] != "/internal/phase3/claims" or set(call["request"]) != {
                "command_id",
                "receipt_id",
                "expected_intent_revision",
            }:
                return None
            problem2 = ReceiptProblem.model_validate(call["response"])
            backend_trace = problem2.trace_id
            UUID(call["request"]["command_id"])
            receipt_id = call["request"]["receipt_id"]
            UUID(receipt_id)
            verification = next(
                c
                for c in reversed(row["http"][: row["http"].index(call)])
                if c["path"] == "/internal/phase3/verifications"
                and c["response"].get("receipt_id") == receipt_id
            )
            receipt = verification["response"]
            expected_result = receipt["result"]
            if (
                verification["status"] != 201
                or verification["request"]["operation_id"] != operation["id"]
            ):
                return None
            if receipt["claim_type"] != claim_type.value or receipt["intent_revision"] != revision:
                return None
            if (
                verification["request"]["claim_type"] != claim_type.value
                or verification["request"]["expected_intent_revision"] != revision
            ):
                return None
            if expected_result not in ("UNKNOWN", "VIOLATED"):
                return None
            valid_until = instant(receipt["valid_until"])
            if not valid_until - timedelta(seconds=30) <= sent < received < valid_until:
                return None
            observed_from = instant(verification["sent_at"])
            observed_until = instant(verification["received_at"])
            if not accepted <= observed_from <= observed_until <= sent:
                return None
            verification_hash = stable_hash(verification)
            verification_events = [
                e
                for e in row["snapshot"]["raw_provider_events"]
                if e["event_kind"] == "VERIFICATION_READ"
                and e["trace_id"] == verification["trace_id"]
            ]
        UUID(backend_trace)
        fresh = [
            o
            for o in row["snapshot"]["observations"]
            if observed_from <= instant(o["available_at"]) <= observed_until
        ]
        key = row["targets"][-1]["resource_key"]
        resources = [o for o in fresh if o["source_type"] == "SIMULATOR_RESOURCE"]
        statuses = [o for o in fresh if o["source_type"] == "SIMULATOR_OPERATION"]
        if len(resources) != 1 or not 1 <= len(statuses) <= 3 or len(fresh) != 1 + len(statuses):
            return None
        for observation in fresh:
            raw, query = observation["raw"], observation["query"]
            if (
                stable_hash(raw) != observation["raw_hash"]
                or query["scenario_id"] != row["scenario_id"]
            ):
                return None
            if raw["status"] not in (200, 501):
                return None  # An actual provider service error is not this exception.
            if raw["status"] == 501:
                is_resource = observation["source_type"] == "SIMULATOR_RESOURCE"
                flag = "resource_lookup" if is_resource else "status_lookup"
                absent = (
                    "Resource lookup is absent"
                    if is_resource
                    else "Operation status lookup is absent"
                )
                if case["provider"][flag] is not False or raw["body"] != {"detail": absent}:
                    return None
            if observation in resources:
                if observation["source_identifier"] != key or query != {
                    "scenario_id": row["scenario_id"],
                    "operation_id": operation["id"],
                    "resource_key": key,
                }:
                    return None
            elif (
                observation["source_identifier"] not in operations
                or query["operation_id"] != observation["source_identifier"]
            ):
                return None
        # The recorded provider query order is the backend's bounded chain order.
        ordered = resources + sorted(statuses, key=lambda o: instant(o["available_at"]))
        if statuses[0]["source_identifier"] != operation["id"]:
            return None
        observations = [
            Observation(
                o["source_type"],
                o["source_identifier"],
                o["query"],
                o["raw"],
                o["raw"]["body"] if o["raw"]["status"] == 200 else None,
                instant(o["available_at"]),
            )
            for o in ordered
        ]
        verdict = _evaluate(
            claim_type,
            {"desired_state_json": desired},
            {"provider_adapter": "simulator", "normalized_request_json": {"resource_key": key}},
            observations,
            None,
        )
        if verdict.result is Result.SATISFIED or (
            expected_result and verdict.result.value != expected_result
        ):
            return None
        if receipt_id:
            if len(verification_events) != len(fresh) or any(
                e["operation_id"] != operation["id"]
                or e["content_hash"] != stable_hash(e["raw_json"])
                or e["normalized_json"]
                != {"result": verdict.result.value, "claim_type": claim_type.value}
                for e in verification_events
            ):
                return None
            if sorted(stable_hash(e["raw_json"]) for e in verification_events) != sorted(
                o["raw_hash"] for o in fresh
            ):
                return None
            if receipt["observed_resource_version"] != verdict.resource_version:
                return None
        body = {
            "version": VERSION,
            "classification": EXPECTED,
            "raw_driver_status": "FAILED",
            "original_instrument_status": "INFRASTRUCTURE_FAILURE",
            "revised_instrument_status": "COMPLETED",
            "reason": (
                "Bound current claim predicate is not SATISFIED in recorded provider evidence"
            ),
            "call_hash": stable_hash(call),
            "observation_hashes": [stable_hash(o) for o in ordered],
            "verification_hash": verification_hash,
            "verification_event_hashes": [stable_hash(e) for e in verification_events],
            "receipt_id": receipt_id,
            "predicate_result": verdict.result.value,
            "claim_type": claim_type.value,
            "backend_trace_id": backend_trace,
            "workflow_id": workflow,
            "intent_revision": revision,
            "operation_id": operation["id"],
            "retryable": False,
            "retry_performed": False,
            "business_success_inferred_from_refusal": False,
        }
        return {**body, "hash": stable_hash(body)}
    except (KeyError, IndexError, TypeError, ValueError, StopIteration, ValidationError):
        return None


def validate_classification(row: dict[str, Any]) -> bool:
    stored = row.get("driver_classification")
    if stored is None:
        return False
    if stored != recognize(row):
        raise ValueError("REFUSAL_CLASSIFICATION_EVIDENCE_DRIFT")
    return True


def timing_eligible(row: dict[str, Any]) -> bool:
    if (
        not validate_classification(row)
        or row.get("missing_final_anchor")
        or row.get("collection_errors")
        or row.get("source_drift")
    ):
        return False
    anchor = row["external_requests"][-1]
    if anchor["revision"] != row["input"]["intents"][-1]["revision"]:
        return False
    cutoff = instant(row["original_deadline"])
    return (
        (cutoff - instant(anchor["issued_at"])).total_seconds() == 600
        and bool(row.get("polls"))
        and instant(row["polls"][-1]["at"]) >= cutoff
    )
