"""Live P3 provider drivers for the ordinary and established recovery baselines."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import structlog

from packages.provider_adapters.simulator import (
    Exchange,
    operation_status,
    resource_state,
    send_operation,
)
from research.analysis.latency import correction_to_outcome
from research.analysis.metrics import metric_rows
from research.arms import Arm
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck, grade
from research.provider_simulator.models import ProviderOperation
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, call
from research.run_store import (
    baseline_events_for,
    bind_execution,
    create_execution,
    fail_execution,
    playback_for,
    record_barrier,
    record_baseline_event,
    record_fault,
    record_playback,
    record_result,
    release_barrier,
    timing_evidence,
)
from research.scenario_dsl.models import Barrier, FaultFamily, ScenarioCase, stable_hash

logger = structlog.get_logger(__name__)
BASELINE_ARMS = frozenset({Arm.B0, Arm.B1, Arm.B2})


def _post(base: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    return call(base, "POST", path, body)


def _accept(fixture: dict[str, Any], case: ScenarioCase, revision: int) -> dict[str, Any]:
    start = case.initial_start if revision == 1 else case.final_start
    transcript = case.initial_transcript if revision == 1 else case.correction_transcript
    return _post(
        API,
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        {
            "command_id": str(uuid4()),
            "expected_revision": revision - 1,
            "change_class": "INITIAL" if revision == 1 else case.revision_type,
            "desired_state": {
                "ticket_id": fixture["ticket_id"],
                "requested_start": start.isoformat(),
                "requested_end": (start + timedelta(hours=1)).isoformat(),
                "timezone": case.timezone,
            },
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][revision - 1],
                "model": "phase6-frozen-scripted-transcript",
                "prompt_hash": stable_hash({"transcript": transcript, "version": "phase6-v1"}),
                "transcript_version": 1,
            },
        },
    )


def _request(
    scenario_id: UUID,
    operation_id: UUID,
    key: str,
    action: str,
    resource_key: str,
    *,
    start: datetime | None = None,
    appointment_id: str | None = None,
    expected_version: int | None = None,
    timezone: str,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "action": action,
        "resource_key": resource_key,
        "requested_start": start.isoformat() if start else None,
        "requested_end": (start + timedelta(hours=1)).isoformat() if start else None,
        "timezone": timezone if start else None,
        "appointment_id": appointment_id,
        "expected_resource_version": expected_version,
    }
    payload = {
        "scenario_id": str(scenario_id),
        "operation_id": str(operation_id),
        "idempotency_key": key,
        "request_hash": stable_hash(normalized),
        **normalized,
    }
    return ProviderOperation.model_validate(payload).model_dump(mode="json", exclude_none=True)


def _observation(exchange: Exchange) -> dict[str, Any]:
    return {
        "status": exchange.status,
        "transport_error": exchange.transport_error,
        "outcome": exchange.body.get("outcome") if exchange.body else "UNKNOWN",
        "authoritative": exchange.body.get("authoritative") if exchange.body else False,
    }


def execute_baseline_p3(
    run_id: UUID,
    case_id: UUID,
    case: ScenarioCase,
    arm: Arm,
) -> dict[str, Any]:
    if arm not in BASELINE_ARMS or case.correction_barrier is not Barrier.P3:
        raise ValueError("B0-B2 live baseline drivers require the P3 case")
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
    target = {
        "barrier": placement.barrier.value,
        "fault": placement.fault.value,
        "request_index": placement.request_index,
        "target": placement.target,
    }
    ordinal = 0

    def observed(kind: str, raw: dict[str, Any], normalized: dict[str, Any]) -> None:
        nonlocal ordinal
        ordinal += 1
        record_baseline_event(execution_id, ordinal, kind, raw, normalized, trace_id)

    def write(payload: dict[str, Any]) -> Exchange:
        observed("REQUEST_SENT", payload, {"action": payload["action"], "sent": True})
        response = send_operation(payload)
        observed("PROVIDER_RESPONSE", response.raw, _observation(response))
        return response

    try:
        scenario = _post(
            SIMULATOR,
            "/internal/scenarios",
            {
                "idempotency": True,
                "status_lookup": True,
                "resource_lookup": True,
                "visibility": case.visibility,
                "supports_reschedule": True,
                "held_barriers": [placement.target],
                "faults": [
                    {
                        "request_index": 1,
                        "stage": "AFTER_COMMIT_BEFORE_RESPONSE",
                        "kind": "DROP_RESPONSE",
                    }
                ]
                if case.fault_family is FaultFamily.RESPONSE_LOSS
                else [],
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
        first_id = uuid4()
        first = _request(
            scenario_id,
            first_id,
            f"phase6:{execution_id}:original",
            "CREATE",
            fixture["resource_key"],
            start=case.initial_start,
            timezone=case.timezone,
        )
        # The provider holds the first request at its durable post-commit boundary.
        observed("REQUEST_SENT", first, {"action": "CREATE", "sent": True})
        with ThreadPoolExecutor(max_workers=1) as pool:
            dispatch = pool.submit(send_operation, first)
            reached = call(
                SIMULATOR,
                "GET",
                f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}?wait=true",
            )
            if reached.get("reached_at") is None:
                raise AssertionError("Baseline did not reach the P3 provider barrier")
            barrier_id = record_barrier(
                execution_id,
                "P3",
                placement.target,
                datetime.fromisoformat(reached["reached_at"]),
                held=True,
            )
            try:
                scripted_at = datetime.now(UTC)
                _accept(fixture, case, 2)
            finally:
                _post(
                    SIMULATOR,
                    f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}/release",
                    {},
                )
                release_barrier(barrier_id)
            first_response = dispatch.result(timeout=40)
        observed("PROVIDER_RESPONSE", first_response.raw, _observation(first_response))
        if case.fault_family is FaultFamily.RESPONSE_LOSS and not first_response.transport_error:
            raise AssertionError("The scheduled response-loss fault did not occur")
        fault_id = (
            record_fault(execution_id, "P3", placement.fault.value, target, barrier_id)
            if placement.fault is not FaultFamily.NONE
            else None
        )
        bind_execution(
            execution_id,
            scenario_id,
            UUID(fixture["workflow_id"]),
            placement.hash,
            scripted_at,
        )

        first_facts: dict[str, Any] | None = None
        if arm is Arm.B0:
            observed(
                "UNRESOLVED_STOP",
                first_response.raw,
                {"outcome": "UNKNOWN", "reason": "NO_SAFE_RETRY_PROOF"},
            )
        else:
            status = operation_status(scenario_id, first_id)
            observed("STATUS_LOOKUP", status.raw, _observation(status))
            if status.status != 200 or not status.body or not status.body.get("authoritative"):
                raise AssertionError("Baseline cannot act without authoritative status evidence")
            if status.body.get("outcome") != "PRESENT":
                raise AssertionError("P3 commit was not found by baseline status lookup")
            first_facts = status.body["facts"]

        if arm is Arm.B1:
            assert first_facts is not None
            cancel = _request(
                scenario_id,
                uuid4(),
                f"phase6:{execution_id}:cancel",
                "CANCEL",
                fixture["resource_key"],
                appointment_id=first_facts["appointment_id"],
                expected_version=int(first_facts["version"]),
                timezone=case.timezone,
            )
            cancel_response = write(cancel)
            if cancel_response.status != 200:
                raise AssertionError("B1 best-effort cancellation did not complete")

        last_id = first_id if arm is Arm.B0 else uuid4()
        if arm is not Arm.B0:
            action = "RESCHEDULE" if arm is Arm.B2 else "CREATE"
            corrected = _request(
                scenario_id,
                last_id,
                f"phase6:{execution_id}:corrected",
                action,
                fixture["resource_key"],
                start=case.final_start,
                appointment_id=first_facts["appointment_id"]
                if arm is Arm.B2 and first_facts
                else None,
                expected_version=int(first_facts["version"])
                if arm is Arm.B2 and first_facts
                else None,
                timezone=case.timezone,
            )
            corrected_response = write(corrected)
            if corrected_response.status != 200:
                raise AssertionError("Baseline correction write failed")
            resource = resource_state(scenario_id, last_id, fixture["resource_key"])
            observed("POSTCONDITION_READ", resource.raw, _observation(resource))
            if (
                resource.status != 200
                or not resource.body
                or not resource.body.get("authoritative")
            ):
                raise AssertionError("Baseline postcondition was not authoritative")

        ack: PlaybackAck | None = None
        if arm is not Arm.B0:
            now = datetime.now(UTC)
            ack = PlaybackAck(
                event_id=str(uuid4()),
                claim_type="RESCHEDULED_APPOINTMENT" if arm is Arm.B2 else "CURRENT_APPOINTMENT",
                claim_start=case.final_start,
                intent_revision=2,
                released_at=now,
                played_at=now,
                played_ms=500,
            )
            record_playback(execution_id, ack, case.audio_hash)
        truth = truth_log(scenario_id)
        result = grade(case, truth, playback_for(execution_id), scripted_at)
        record_result(execution_id, case, truth, result)
        history = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
        observation_ended_at = datetime.now(UTC).isoformat()
        logger.info(
            "research_baseline_completed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            workflow_id=fixture["workflow_id"],
            operation_id=str(last_id),
            intent_revision=2,
            arm=arm.value,
        )
        execution = {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": str(scenario_id),
            "workflow_id": fixture["workflow_id"],
            "first_operation_id": str(first_id),
            "current_operation_id": str(last_id),
            "fault_occurrence_id": str(fault_id) if fault_id else None,
            "fault_placement_hash": placement.hash,
            "speech_source": (
                "research_baseline_uncertainty"
                if arm is Arm.B0
                else "research_baseline_tool_response"
            ),
            "receipt_id": None,
            "permit_id": None,
            "playback_ack": ack.model_dump(mode="json") if ack else None,
            "correction_scripted_at": scripted_at.isoformat(),
            "observation_ended_at": observation_ended_at,
            "worker_steps": [],
            "normalized_events": history["events"],
            "provider_evidence": [],
            "baseline_events": baseline_events_for(execution_id),
            "timing_evidence": timing_evidence(execution_id),
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
        execution["correction_to_outcome_latency"] = correction_to_outcome(execution)
        return execution
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        logger.exception(
            "research_baseline_failed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            execution_id=str(execution_id),
            arm=arm.value,
        )
        raise
