"""24 offline controls. No driver commands, oracle invocation or historical writes."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

SOURCE = Path(os.environ.get("P145_SOURCE", "E:/p8v9/source"))
OVERLAY = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete"
sys.path.insert(0, str(SOURCE))
sys.path.insert(1, str(OVERLAY))

from apps.api_controller.phase3_verification_service import Observation, _evaluate  # noqa: E402
from packages.domain.phase3_verification import ClaimType, Result  # noqa: E402
from research.scenario_dsl.models import stable_hash  # noqa: E402


def module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


legacy = module(OVERLAY / "refusal.py", "slot145_frozen_refusal")
candidate = module(Path(__file__).parent / "refusal.py", "slot145_candidate_refusal")
EXPORT = Path(os.environ.get(
    "P145_EXPORT",
    "D:/FYP-ResearchBackups/slot145-diagnosis/verified-cloud-v2/required/executions/"
    "01a11705-11f1-7386-a804-76b957c218d5/export.json",
))


def original() -> dict[str, Any]:
    return json.loads(EXPORT.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def refused(row: dict[str, Any]) -> dict[str, Any]:
    return next(c for c in row["http"] if c["status"] == 409)


def sync_error(row: dict[str, Any]) -> None:
    call = refused(row)
    row["failure"]["detail"] = f"HTTP {call['status']}: {call['path']}: {call['response']}"


def test_frozen_predicate_demonstrates_mismatch() -> None:
    row = original()
    recorded = row["snapshot"]["observations"]
    observations = [
        Observation(
            o["source_type"], o["source_identifier"], o["query"], o["raw"],
            o["raw"]["body"], candidate.instant(o["available_at"]),
        ) for o in recorded
    ]
    args = (
        {"desired_state_json": row["snapshot"]["history"]["desired_state"]},
        {"provider_adapter": "simulator", "normalized_request_json": {
            "resource_key": row["targets"][-1]["resource_key"]}},
        observations, None,
    )
    assert _evaluate(ClaimType.RESCHEDULED_APPOINTMENT, *args).result is Result.VIOLATED
    assert _evaluate(ClaimType.COMPENSATED_APPOINTMENT, *args).result is Result.SATISFIED
    assert legacy.recognize(row) is None


def test_candidate_recognizes_without_mutation_or_regrading() -> None:
    row = original()
    before = stable_hash(row)
    proof = candidate.recognize(row)
    assert proof is not None and proof["predicate_result"] == "VIOLATED"
    assert proof["operation_id"] == "e3f14153-5496-4784-bee8-7fa81b4cb599"
    assert proof["application_behavior_changed"] is False
    assert proof["retry_performed"] is False
    assert stable_hash(row) == before and row["status"] == "FAILED"


@pytest.mark.parametrize("name,arm", [("first", "B3"), ("second", "P1"), ("second", "P2")])
def test_legacy_proof_stays_byte_equivalent(name: str, arm: str) -> None:
    row = json.loads((OVERLAY / f"retained-{name}-original.json").read_text())
    row["arm"] = arm
    assert candidate.recognize(row) == legacy.recognize(row) is not None


def receipt_control(arm: str) -> dict[str, Any]:
    """Synthetic recorded-response control; it is not an execution of either arm."""
    row = original()
    row["arm"] = arm
    row["execution_id"] = "cal-slot145-replacement-" + arm.lower()
    row["input"]["case_id"] = row["execution_id"]
    call = refused(row)
    index = row["http"].index(call)
    identity = "44444444-4444-4444-8444-444444444444"
    trace = "55555555-5555-4555-8555-555555555555"
    verify = copy.deepcopy(call)
    verify.update(path="/internal/phase3/verifications", status=201, trace_id=trace)
    verify["request"] = {
        "command_id": "66666666-6666-4666-8666-666666666666",
        "operation_id": "e3f14153-5496-4784-bee8-7fa81b4cb599",
        "expected_intent_revision": 2, "claim_type": "RESCHEDULED_APPOINTMENT",
    }
    verify["response"] = {
        "receipt_id": identity, "claim_type": "RESCHEDULED_APPOINTMENT",
        "intent_revision": 2, "result": "VIOLATED", "observed_resource_version": "0",
        "valid_until": (candidate.instant(call["sent_at"]) + timedelta(seconds=30)).isoformat(),
    }
    call["path"] = "/internal/phase3/claims"
    call["request"] = {
        "command_id": "77777777-7777-4777-8777-777777777777",
        "receipt_id": identity, "expected_intent_revision": 2,
    }
    call["response"] = {
        "type": "https://example.invalid/problems/receipt-not-applicable",
        "title": "Receipt not applicable", "status": 409,
        "detail": "A current SATISFIED receipt is required", "instance": call["path"],
        "trace_id": "88888888-8888-4888-8888-888888888888", "retryable": False,
    }
    call["sent_at"] = (
        candidate.instant(verify["received_at"]) + timedelta(milliseconds=10)
    ).isoformat()
    call["received_at"] = (
        candidate.instant(call["sent_at"]) + timedelta(milliseconds=10)
    ).isoformat()
    row["http"].insert(index, verify)
    for o in row["snapshot"]["observations"]:
        row["snapshot"]["raw_provider_events"].append({
            "event_kind": "VERIFICATION_READ", "trace_id": trace,
            "operation_id": verify["request"]["operation_id"], "raw_json": o["raw"],
            "content_hash": stable_hash(o["raw"]),
            "normalized_json": {"result": "VIOLATED", "claim_type": "RESCHEDULED_APPOINTMENT"},
        })
    sync_error(row)
    return row


@pytest.mark.parametrize("arm", ["P1", "P2"])
def test_shared_classifier_bound_receipt_controls(arm: str) -> None:
    row = receipt_control(arm)
    assert legacy.recognize(row) is None
    proof = candidate.recognize(row)
    assert proof is not None and proof["receipt_id"] is not None


@pytest.mark.parametrize("change", [
    "unrelated_type", "500", "retryable", "workflow", "revision", "hash",
    "provider_error", "chain_order", "effect_binding", "missing", "extra_operation",
    "undeclared_provider",
])
def test_genuine_or_unprovable_errors_remain_unrecognized(change: str) -> None:
    row = original()
    call = refused(row)
    observations = row["snapshot"]["observations"]
    if change == "unrelated_type":
        call["response"]["type"] = "https://example.invalid/problems/technical-defect"
    elif change == "500":
        call["status"] = 500
    elif change == "retryable":
        prefix, nested = call["response"]["detail"].split(": 409 ", 1)
        problem = json.loads(nested)
        problem["retryable"] = True
        call["response"]["detail"] = prefix + ": 409 " + json.dumps(problem)
    elif change == "workflow":
        call["request"]["workflow_id"] = "wrong"
    elif change == "revision":
        call["request"]["expected_intent_revision"] = 1
    elif change == "hash":
        observations[0]["raw_hash"] = "0" * 64
    elif change == "provider_error":
        observations[1]["raw"]["status"] = 500
        observations[1]["raw_hash"] = stable_hash(observations[1]["raw"])
    elif change == "chain_order":
        observations[1]["available_at"], observations[2]["available_at"] = (
            observations[2]["available_at"], observations[1]["available_at"])
    elif change == "effect_binding":
        row["snapshot"]["history"]["operations"][-1]["target_resource_id"] = "wrong"
    elif change == "missing":
        row["snapshot"]["observations"] = []
    elif change == "extra_operation":
        operation = copy.deepcopy(row["snapshot"]["history"]["operations"][-1])
        operation["id"] = "unrelated"
        row["snapshot"]["history"]["operations"].append(operation)
    else:
        row["input"]["provider"]["supports_reschedule"] = True
    if change != "500":
        sync_error(row)
    else:
        row["failure"]["detail"] = f"HTTP 500: {call['path']}: {call['response']}"
    assert candidate.recognize(row) is None


@pytest.mark.parametrize("condition", ["complete", "poll", "anchor", "gap", "drift"])
def test_collection_proof_is_required(condition: str) -> None:
    row = original()
    row["driver_classification"] = candidate.recognize(row)
    assert row["driver_classification"] is not None
    if condition == "poll":
        row["polls"] = []
    elif condition == "anchor":
        row["missing_final_anchor"] = True
    elif condition == "gap":
        row["collection_errors"] = [{"type": "CLOCK_OR_GAP"}]
    elif condition == "drift":
        row["source_drift"] = "SOURCE_DRIFT"
    assert candidate.timing_eligible(row) == (condition == "complete")
