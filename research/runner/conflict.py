"""Live version conflict on the linked reschedule after a P5 correction."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from uuid import UUID, uuid4

from research.analysis.latency import correction_to_outcome
from research.analysis.metrics import metric_rows
from research.arms import Arm
from research.barriers.control import NamedBarrierController
from research.barriers.schedule import schedule
from research.oracle.grade import grade
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, WORKER, call
from research.run_store import (
    bind_execution,
    create_execution,
    fail_execution,
    record_barrier,
    record_fault,
    record_result,
    release_barrier,
    timing_evidence,
)
from research.runner.handoff_evidence import handoff_snapshot
from research.runner.paired import _accept, _drain, _post, _step_until_present, logger
from research.scenario_dsl.models import Barrier, ScenarioCase


def execute_conflict(run_id: UUID, case_id: UUID, case: ScenarioCase, arm: Arm) -> dict[str, Any]:
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
    try:
        scenario = _post(
            SIMULATOR,
            "/internal/scenarios",
            {
                "held_barriers": [placement.target],
                "faults": [
                    {"request_index": 2, "stage": "BEFORE_COMMIT", "kind": "CONFLICTING_CHANGE"}
                ],
            },
        )
        scenario_id = UUID(scenario["scenario_id"])
        fixture = _post(
            API,
            "/internal/phase1/fixtures",
            {
                "command_id": str(uuid4()),
                "first_transcript": case.initial_transcript,
                "second_transcript": case.correction_transcript,
            },
        )
        _accept(fixture, case, 1)
        first = _post(
            API,
            "/internal/phase2/operations",
            {
                "command_id": str(uuid4()),
                "workflow_id": fixture["workflow_id"],
                "scenario_id": str(scenario_id),
                "expected_intent_revision": 1,
                "expected_resource_version": 0,
                "idempotency_key": f"phase6:{execution_id}:original",
            },
        )
        initial_steps = _step_until_present(first["operation_id"])
        verified = _post(
            API,
            "/internal/phase3/verifications",
            {
                "command_id": str(uuid4()),
                "operation_id": first["operation_id"],
                "expected_intent_revision": 1,
                "claim_type": "CURRENT_APPOINTMENT",
            },
        )
        if verified["result"] != "SATISFIED":
            raise AssertionError("P5 conflict requires a verified original appointment")
        controller = NamedBarrierController(execution_id, {Barrier.P5})
        with ThreadPoolExecutor(max_workers=1) as pool:
            paused = pool.submit(controller.reach, Barrier.P5, verified["receipt_id"])
            controller.wait_reached(Barrier.P5)
            try:
                corrected_at = datetime.now(UTC)
                _accept(fixture, case, 2)
            finally:
                controller.release(Barrier.P5)
            paused.result(timeout=40)
        bind_execution(
            execution_id, scenario_id, UUID(fixture["workflow_id"]), placement.hash, corrected_at
        )
        steps = []
        for _ in range(8):
            history = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
            current = next(
                (item for item in history["operations"] if item["intent_revision"] == 2), None
            )
            if current is not None:
                break
            steps.append(
                _post(
                    WORKER,
                    "/internal/phase2/step",
                    {"owner": str(execution_id), "operation_id": first["operation_id"]},
                )
            )
        else:
            raise AssertionError("Correction did not create a linked reschedule")
        assert current is not None
        with ThreadPoolExecutor(max_workers=1) as pool:
            dispatched = pool.submit(
                _post,
                WORKER,
                "/internal/phase2/step",
                {"owner": str(execution_id), "operation_id": current["id"]},
            )
            held = call(
                SIMULATOR,
                "GET",
                f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}?wait=true",
            )
            if held.get("state") != "REACHED":
                raise AssertionError("Corrected provider request did not reach held fault barrier")
            event_id = record_barrier(
                execution_id,
                Barrier.P2.value,
                placement.target,
                datetime.fromisoformat(held["reached_at"]),
                held=True,
            )
            try:
                truth_while_held = truth_log(scenario_id)
            finally:
                _post(
                    SIMULATOR,
                    f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}/release",
                    {},
                )
                release_barrier(event_id)
            steps.append(dispatched.result(timeout=40))
        target = {
            "barrier": placement.barrier.value,
            "fault": placement.fault.value,
            "request_index": placement.request_index,
            "target": placement.target,
        }
        fault_id = record_fault(
            execution_id, Barrier.P2.value, placement.fault.value, target, event_id
        )
        steps.extend(_drain(fixture["workflow_id"], expect_handoff=True))
        history = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
        receipt = _post(
            API,
            "/internal/phase3/verifications",
            {
                "command_id": str(uuid4()),
                "operation_id": current["id"],
                "expected_intent_revision": 2,
                "claim_type": "CURRENT_APPOINTMENT",
            },
        )
        if receipt["result"] != "VIOLATED":
            raise AssertionError("Conflicted current booking must not have satisfied evidence")
        try:
            _post(
                API,
                "/internal/phase3/claims",
                {
                    "command_id": str(uuid4()),
                    "receipt_id": receipt["receipt_id"],
                    "expected_intent_revision": 2,
                },
            )
        except HTTPError as denied:
            problem = json.load(denied)
            if denied.code != 409 or not problem["type"].endswith("receipt-not-applicable"):
                raise
            denial = {"status": denied.code, "problem": problem}
        else:
            raise AssertionError("Conflicted booking unexpectedly authorized speech")
        truth = truth_log(scenario_id)
        result = grade(case, truth, [], corrected_at)
        record_result(execution_id, case, truth, result)
        execution = {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": str(scenario_id),
            "workflow_id": fixture["workflow_id"],
            "first_operation_id": first["operation_id"],
            "current_operation_id": current["id"],
            "fault_occurrence_id": str(fault_id),
            "fault_placement_hash": placement.hash,
            "speech_source": "withheld_provider_version_conflict",
            "receipt_id": None,
            "permit_id": None,
            "playback_ack": None,
            "correction_scripted_at": corrected_at.isoformat(),
            "observation_ended_at": datetime.now(UTC).isoformat(),
            "pre_correction_receipt_id": verified["receipt_id"],
            "initial_worker_steps": initial_steps,
            "worker_steps": steps,
            "normalized_events": history["events"],
            "provider_evidence": [
                call(API, "GET", f"/v1/operations/{item['id']}") for item in history["operations"]
            ],
            "timing_evidence": timing_evidence(execution_id),
            "conflict_evidence": {
                "simulator_config": call(SIMULATOR, "GET", f"/internal/scenarios/{scenario_id}")[
                    "config"
                ],
                "truth_while_held": json.loads(json.dumps(truth_while_held, default=str)),
                "initial_receipt": verified,
                "violated_receipt": receipt,
                "claim_denial": denial,
                "handoff_snapshot": handoff_snapshot(UUID(fixture["workflow_id"])),
            },
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
        execution["correction_to_outcome_latency"] = correction_to_outcome(execution)
        logger.info(
            "research_conflict_execution_completed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            workflow_id=fixture["workflow_id"],
            operation_id=current["id"],
            intent_revision=2,
            arm=arm.value,
        )
        return execution
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        logger.exception(
            "research_conflict_execution_failed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            execution_id=str(execution_id),
        )
        raise
