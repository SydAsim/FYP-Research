"""Common live provider boundary driver with explicit B0/B1/B2 mechanisms."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

from packages.provider_adapters.simulator import (
    Exchange,
    operation_status,
    resource_state,
    send_operation,
)
from research.analysis.latency import correction_to_outcome
from research.analysis.metrics import metric_rows
from research.arms import Arm
from research.barriers.control import NamedBarrierController
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck, grade
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, call
from research.run_store import (
    baseline_events_for,
    bind_execution,
    create_execution,
    fail_execution,
    record_barrier,
    record_baseline_event,
    record_fault,
    record_playback,
    record_result,
    release_barrier,
    timing_evidence,
)
from research.runner.baselines import _accept, _observation, _post, _request, logger
from research.scenario_dsl.models import Barrier, FaultFamily, ScenarioCase


def execute_covering(run_id: UUID, case_id: UUID, case: ScenarioCase, arm: Arm) -> dict[str, Any]:
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
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

    def status_for(scenario_id: UUID, operation_id: UUID) -> dict[str, Any] | None:
        for _ in range(8):
            response = operation_status(scenario_id, operation_id)
            observed("STATUS_LOOKUP", response.raw, _observation(response))
            if response.body and response.body.get("authoritative"):
                return response.body
        return None

    try:
        stage = case.correction_barrier
        provider_held = stage in (Barrier.P2, Barrier.P3, Barrier.P4)
        kind = {
            FaultFamily.RESPONSE_LOSS: "DROP_RESPONSE",
            FaultFamily.REDIS_LOSS: "DROP_RESPONSE",
            FaultFamily.DELAY: "DELAY",
            FaultFamily.PROVIDER_REFUSAL: "RETURN_5XX",
            FaultFamily.PARTIAL_EFFECT: "PARTIAL_EFFECT",
        }.get(case.fault_family)
        config = {
            "idempotency": True,
            "status_lookup": True,
            "resource_lookup": True,
            "visibility": case.visibility.simulator_visibility,
            "visibility_reads": case.visibility.visibility_reads,
            "supports_reschedule": case.provider_capability.supports_reschedule,
            "held_barriers": [placement.target] if provider_held else [],
            "faults": [
                {
                    "request_index": 1,
                    "stage": "AFTER_COMMIT_BEFORE_RESPONSE"
                    if kind == "DROP_RESPONSE"
                    else "BEFORE_COMMIT",
                    "kind": kind,
                }
            ]
            if kind
            else [],
        }
        scenario_id = UUID(_post(SIMULATOR, "/internal/scenarios", config)["scenario_id"])
        fixture = _post(
            API,
            "/internal/phase1/fixtures",
            {
                "command_id": str(uuid4()),
                "first_transcript": case.initial_transcript,
                "second_transcript": case.correction_transcript,
            },
        )
        pre_accept = None
        accepted = None
        if stage is not Barrier.P0:
            _accept(fixture, case, 1)
        else:
            pre_accept = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
            pre_accept["read_at"] = datetime.now(UTC).isoformat()

        def correction() -> datetime:
            nonlocal accepted
            moment = datetime.now(UTC)
            if stage is Barrier.P0:
                # The existing acceptance port accepts the corrected first intent.
                from research.runner.paired import _desired
                from research.scenario_dsl.models import stable_hash

                accepted = _post(
                    API,
                    f"/v1/workflows/{fixture['workflow_id']}/revisions",
                    {
                        "command_id": str(uuid4()),
                        "expected_revision": 0,
                        "change_class": "INITIAL",
                        "desired_state": _desired(fixture, case.final_start, case.timezone),
                        "candidate_source": {
                            "utterance_id": fixture["utterance_ids"][1],
                            "model": "phase6-frozen-scripted-transcript",
                            "prompt_hash": stable_hash(case.correction_transcript),
                            "transcript_version": 1,
                        },
                    },
                )
            else:
                accepted = _accept(fixture, case, 2)
            return moment

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
        barrier_id: UUID
        first_response: Exchange | None = None
        redis_evidence = None
        if provider_held:
            observed("REQUEST_SENT", first, {"action": "CREATE", "sent": True})
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(send_operation, first)
                reached = call(
                    SIMULATOR,
                    "GET",
                    f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}?wait=true",
                )
                if not reached.get("reached_at"):
                    raise AssertionError("Baseline did not reach provider barrier")
                barrier_id = record_barrier(
                    execution_id,
                    stage.value,
                    placement.target,
                    datetime.fromisoformat(reached["reached_at"]),
                    held=True,
                )
                try:
                    corrected_at = correction()
                    if case.workflow_shape == "TWO_WORKFLOWS_TWO_TICKETS_TWO_RESOURCES":
                        secondary = _post(
                            API,
                            "/internal/phase1/fixtures",
                            {
                                "command_id": str(uuid4()),
                                "first_transcript": "Book separate maintenance on November sixth "
                                "at three P M.",
                            },
                        )
                        secondary_case = case.model_copy(
                            update={"initial_start": case.initial_start + timedelta(days=1)}
                        )
                        _accept(secondary, secondary_case, 1)
                        side_id = uuid4()
                        side_result = write(
                            _request(
                                scenario_id,
                                side_id,
                                f"phase6:{execution_id}:secondary",
                                "CREATE",
                                secondary["resource_key"],
                                start=secondary_case.initial_start,
                                timezone=case.timezone,
                            )
                        )
                        if side_result.status != 200:
                            raise AssertionError("Independent secondary booking failed")
                    if case.fault_family is FaultFamily.REDIS_LOSS:
                        from research.runner.redis_loss import wipe_cache

                        redis_evidence = wipe_cache(UUID(fixture["workflow_id"]))
                finally:
                    _post(
                        SIMULATOR,
                        f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}/release",
                        {},
                    )
                    release_barrier(barrier_id)
                first_response = pending.result(timeout=40)
            observed("PROVIDER_RESPONSE", first_response.raw, _observation(first_response))
        else:
            if stage is Barrier.P5:
                first_response = write(first)
                if arm is not Arm.B0:
                    status_for(scenario_id, first_id)
            controller = NamedBarrierController(execution_id, {stage})
            with ThreadPoolExecutor(max_workers=1) as pool:
                paused = pool.submit(controller.reach, stage, placement.target)
                barrier_id = controller.wait_reached(stage)
                try:
                    corrected_at = correction()
                finally:
                    controller.release(stage)
                paused.result(timeout=40)
        target = {
            "barrier": stage.value,
            "fault": placement.fault.value,
            "request_index": placement.request_index,
            "target": placement.target,
        }
        fault_id = (
            record_fault(execution_id, stage.value, placement.fault.value, target, barrier_id)
            if kind
            else None
        )
        bind_execution(
            execution_id, scenario_id, UUID(fixture["workflow_id"]), placement.hash, corrected_at
        )
        first_status = None
        if first_response is not None:
            if arm is Arm.B0:
                if (
                    first_response.status == 200
                    and first_response.body
                    and first_response.body.get("outcome") == "PRESENT"
                ):
                    first_status = first_response.body
            else:
                first_status = status_for(scenario_id, first_id)
        elif stage in (Barrier.P0, Barrier.P1):
            first_status = {"outcome": "ABSENT", "authoritative": True}
        stopped = first_status is None or first_status.get("outcome") not in ("PRESENT", "ABSENT")
        final_id: UUID | None = None
        ack = None
        if not stopped:
            assert first_status is not None
            facts = first_status.get("facts")
            retraction = case.revision_type == "RETRACTION"
            additive = case.revision_type == "ADDITIVE_COMPATIBLE"
            if additive and facts:
                final_id = first_id
            else:
                use_reschedule = (
                    facts is not None
                    and arm is Arm.B2
                    and case.provider_capability.supports_reschedule
                    and not retraction
                )
                if facts and not use_reschedule:
                    final_id = uuid4()
                    cancelled = write(
                        _request(
                            scenario_id,
                            final_id,
                            f"phase6:{execution_id}:cancel",
                            "CANCEL",
                            fixture["resource_key"],
                            appointment_id=facts["appointment_id"],
                            expected_version=int(facts["version"]),
                            timezone=case.timezone,
                        )
                    )
                    stopped = cancelled.status != 200
                if not stopped and not retraction:
                    final_id = uuid4()
                    result = write(
                        _request(
                            scenario_id,
                            final_id,
                            f"phase6:{execution_id}:corrected",
                            "RESCHEDULE" if use_reschedule else "CREATE",
                            fixture["resource_key"],
                            start=case.final_start,
                            appointment_id=facts["appointment_id"]
                            if use_reschedule and facts
                            else None,
                            expected_version=int(facts["version"])
                            if use_reschedule and facts
                            else None,
                            timezone=case.timezone,
                        )
                    )
                    stopped = result.status != 200
            if not stopped and final_id and not retraction:
                ready = arm is Arm.B0
                if arm is not Arm.B0:
                    for _ in range(8):
                        resource = resource_state(scenario_id, final_id, fixture["resource_key"])
                        observed("POSTCONDITION_READ", resource.raw, _observation(resource))
                        if resource.body and resource.body.get("authoritative"):
                            ready = True
                            break
                if ready:
                    now = datetime.now(UTC)
                    ack = PlaybackAck(
                        event_id=str(uuid4()),
                        claim_type="CURRENT_APPOINTMENT",
                        claim_start=case.final_start,
                        intent_revision=1 if stage is Barrier.P0 else 2,
                        released_at=now,
                        played_at=now,
                        played_ms=500,
                    )
                    record_playback(execution_id, ack, case.audio_hash)
        if stopped:
            observed(
                "UNRESOLVED_STOP",
                first_response.raw if first_response else {},
                {"outcome": "UNKNOWN", "reason": "NO_SAFE_RETRY_PROOF"},
            )
        truth = truth_log(scenario_id)
        read_only_evidence = None
        if case.action_semantics == "CREATE_READ_REUSE":
            read = resource_state(scenario_id, final_id or first_id, fixture["resource_key"])
            observed("POSTCONDITION_READ", read.raw, _observation(read))
            read_only_evidence = {
                "raw": read.raw,
                "truth_before": json.loads(json.dumps(truth, default=str)),
                "truth_after": json.loads(json.dumps(truth_log(scenario_id), default=str)),
            }
        oracle_result = grade(case, truth, [ack] if ack else [], corrected_at)
        record_result(execution_id, case, truth, oracle_result)
        execution = {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": str(scenario_id),
            "workflow_id": fixture["workflow_id"],
            "first_operation_id": str(first_id) if first_response else None,
            "current_operation_id": str(final_id) if final_id else None,
            "fault_occurrence_id": str(fault_id) if fault_id else None,
            "fault_placement_hash": placement.hash,
            "speech_source": "research_baseline_tool_response"
            if ack
            else "research_baseline_uncertainty",
            "receipt_id": None,
            "permit_id": None,
            "playback_ack": ack.model_dump(mode="json") if ack else None,
            "correction_scripted_at": corrected_at.isoformat(),
            "observation_ended_at": datetime.now(UTC).isoformat(),
            "worker_steps": [],
            "normalized_events": call(
                API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history"
            )["events"],
            "provider_evidence": [],
            "baseline_events": baseline_events_for(execution_id),
            "baseline_simulator_config": config,
            "timing_evidence": timing_evidence(execution_id),
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": oracle_result,
            "metrics": metric_rows(oracle_result),
        }
        if pre_accept is not None and accepted is not None:
            execution.update(pre_accept_history=pre_accept, accepted_correction=accepted)
        if redis_evidence is not None:
            execution["redis_loss_evidence"] = redis_evidence
        if read_only_evidence is not None:
            execution["read_only_evidence"] = read_only_evidence
        execution["correction_to_outcome_latency"] = correction_to_outcome(execution)
        return execution
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        logger.exception(
            "research_baseline_covering_failed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            execution_id=str(execution_id),
            arm=arm.value,
        )
        raise
