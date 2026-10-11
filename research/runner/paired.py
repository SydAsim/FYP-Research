"""Run paired live-service correction cases through explicit research arms."""

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from uuid import UUID, uuid4

import structlog

from research.analysis.latency import (
    LATENCY_ANALYSIS_VERSION,
    correction_to_outcome,
    paired_latency,
)
from research.analysis.metrics import metric_rows, paired_counts
from research.arms import PROFILES, Arm
from research.barriers.control import NamedBarrierController
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck, grade
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, WORKER, call
from research.run_store import (
    MIGRATION_VERSION,
    bind_execution,
    create_case,
    create_execution,
    create_run,
    fail_execution,
    finish_run,
    playback_for,
    record_barrier,
    record_fault,
    record_playback,
    record_result,
    release_barrier,
    timing_evidence,
)
from research.runner.baselines import BASELINE_ARMS, execute_baseline_p3
from research.runner.handoff_evidence import handoff_snapshot
from research.scenario_dsl.catalog import (
    CAPABILITY_COVERING,
    CONFLICT_COVERING,
    DELAY_COVERING,
    MANDATORY_HIGH_RISK,
    REFUSAL_COVERING,
    UNAVAILABLE_COVERING,
    VISIBILITY_COVERING,
    case_for,
)
from research.scenario_dsl.models import (
    Barrier,
    FaultFamily,
    ProviderVisibility,
    ScenarioCase,
    stable_hash,
)

logger = structlog.get_logger(__name__)
RUNNER_VERSION = "phase6-paired-runner-v6"
DEFAULT_ARMS = (Arm.B3, Arm.P1, Arm.P2)
ALL_ARMS = (Arm.B0, Arm.B1, Arm.B2, Arm.B3, Arm.P1, Arm.P2)
LIVE_PHASES = frozenset({Barrier.P0, Barrier.P1, Barrier.P2, Barrier.P3, Barrier.P4, Barrier.P5})


def _source_identity() -> tuple[str, str]:
    root = Path(__file__).resolve().parents[2]
    extensions = {".py", ".sql", ".json", ".yaml", ".yml", ".ts", ".tsx", ".css"}
    files = [
        path
        for area in ("apps", "packages", "research", "database", "contracts")
        for path in (root / area).rglob("*")
        if path.is_file() and path.suffix in extensions and "node_modules" not in path.parts
    ]
    files.extend(
        root / name for name in ("compose.yaml", "pyproject.toml", "Dockerfile.python", "uv.lock")
    )
    files.sort()
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    tree_hash = digest.hexdigest()
    check = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    commit = check.stdout.strip() if check.returncode == 0 else f"uncommitted:{tree_hash}"
    return commit, tree_hash


def _container_digests() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    check = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode != 0:
        raise RuntimeError("Container image digests are unavailable for the frozen manifest")
    digests: dict[str, str] = {}
    for line in check.stdout.splitlines():
        row: dict[str, Any] = json.loads(line)
        labels = dict(label.split("=", 1) for label in row["Labels"].split(",") if "=" in label)
        digest = labels.get("com.docker.compose.image")
        if row["State"] == "running" and digest:
            digests[row["Service"]] = digest
    if not {
        "api-controller",
        "durable-worker",
        "provider-simulator",
        "postgres",
        "simulator-postgres",
    }.issubset(digests):
        raise RuntimeError("A required running service has no pinned image digest")
    return digests


def _post(base: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    return call(base, "POST", path, body)


def _desired(fixture: dict[str, Any], start: datetime, timezone: str) -> dict[str, Any]:
    from datetime import timedelta

    return {
        "ticket_id": fixture["ticket_id"],
        "requested_start": start.isoformat(),
        "requested_end": (start + timedelta(hours=1)).isoformat(),
        "timezone": timezone,
    }


def _accept(fixture: dict[str, Any], case: ScenarioCase, revision: int) -> dict[str, Any]:
    start = case.initial_start if revision == 1 else case.final_start
    source = case.initial_transcript if revision == 1 else case.correction_transcript
    return _post(
        API,
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        {
            "command_id": str(uuid4()),
            "expected_revision": revision - 1,
            "change_class": "INITIAL" if revision == 1 else case.revision_type,
            "desired_state": _desired(fixture, start, case.timezone),
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][revision - 1],
                "model": "phase6-frozen-scripted-transcript",
                "prompt_hash": stable_hash({"transcript": source, "version": "phase6-v1"}),
                "transcript_version": 1,
            },
        },
    )


def _drain(workflow_id: str, *, expect_handoff: bool = False) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for _ in range(30):
        history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
        operations = history["operations"]
        for item in operations:
            value = _post(
                WORKER,
                "/internal/phase2/step",
                {"owner": "phase6-runner", "operation_id": item["id"]},
            )
            steps.append(value)
        if expect_handoff:
            if handoff_snapshot(UUID(workflow_id))["workflow"]["resolution_status"] == "HANDOFF":
                return steps
            continue
        if any(
            item.get("applicability") == "REUSABLE" and item["effect_knowledge"] == "PRESENT"
            for item in operations
        ):
            return steps
        current = next((item for item in operations if item["intent_revision"] == 2), None)
        if current is not None and current["effect_knowledge"] == "PRESENT":
            return steps
    raise AssertionError("Durable worker did not reach the expected endpoint in 30 transitions")


def _step_until_present(operation_id: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for _ in range(8):
        value = _post(
            WORKER,
            "/internal/phase2/step",
            {"owner": "phase6-runner", "operation_id": operation_id},
        )
        steps.append(value)
        detail = call(API, "GET", f"/v1/operations/{operation_id}")["operation"]
        if detail["effect_knowledge"] == "PRESENT":
            return steps
        if value["action"] == "idle":
            break
    raise AssertionError("Original provider effect was not verified before P5")


def _publish_current(operation_id: str, revision: int, claim_type: str) -> tuple[str, str, str]:
    receipt = _post(
        API,
        "/internal/phase3/verifications",
        {
            "command_id": str(uuid4()),
            "operation_id": operation_id,
            "expected_intent_revision": revision,
            "claim_type": claim_type,
        },
    )
    if receipt["result"] != "SATISFIED":
        raise AssertionError(f"Current final claim lacks evidence: {receipt['result']}")
    claim = _post(
        API,
        "/internal/phase3/claims",
        {
            "command_id": str(uuid4()),
            "receipt_id": receipt["receipt_id"],
            "expected_intent_revision": revision,
        },
    )
    permit_id = claim["permit_id"]
    _post(
        API,
        f"/internal/phase3/permits/{permit_id}/queue",
        {"command_id": str(uuid4()), "expected_intent_revision": revision},
    )
    published = _post(
        API,
        f"/internal/phase3/permits/{permit_id}/publish",
        {"command_id": str(uuid4()), "expected_intent_revision": revision},
    )
    return receipt["receipt_id"], permit_id, published["text"]


def _execute_p0(run_id: UUID, case_id: UUID, case: ScenarioCase, arm: Arm) -> dict[str, Any]:
    """Correction is accepted as revision one before the original proposal commits."""
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
    try:
        scenario = _post(
            SIMULATOR,
            "/internal/scenarios",
            {
                "idempotency": PROFILES[arm].durable_idempotency,
                "status_lookup": True,
                "resource_lookup": True,
                "visibility": case.visibility.simulator_visibility,
                "visibility_reads": case.visibility.visibility_reads,
                "supports_reschedule": case.provider_capability.supports_reschedule,
            },
        )
        fixture = _post(
            API,
            "/internal/phase1/fixtures",
            {
                "command_id": str(uuid4()),
                "research_arm": arm.value,
                "first_transcript": case.initial_transcript,
                "second_transcript": case.correction_transcript,
            },
        )
        workflow_id = fixture["workflow_id"]
        pre_accept = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
        if pre_accept["current_revision"] != 0 or pre_accept["operations"]:
            raise AssertionError("P0 requires no accepted intent or provider operation")
        controller = NamedBarrierController(execution_id, {Barrier.P0})
        with ThreadPoolExecutor(max_workers=1) as pool:
            paused = pool.submit(controller.reach, Barrier.P0, placement.target)
            barrier_id = controller.wait_reached(Barrier.P0)
            try:
                scripted_at = datetime.now(UTC)
                accepted = _post(
                    API,
                    f"/v1/workflows/{workflow_id}/revisions",
                    {
                        "command_id": str(uuid4()),
                        "expected_revision": 0,
                        "change_class": "INITIAL",
                        "desired_state": _desired(fixture, case.final_start, case.timezone),
                        "candidate_source": {
                            "utterance_id": fixture["utterance_ids"][1],
                            "model": "phase6-frozen-scripted-transcript",
                            "prompt_hash": stable_hash(
                                {"transcript": case.correction_transcript, "version": "phase6-v1"}
                            ),
                            "transcript_version": 1,
                        },
                    },
                )
            finally:
                controller.release(Barrier.P0)
            if paused.result(timeout=40) != barrier_id:
                raise AssertionError("P0 reach/release identity changed")
        if accepted["revision"] != 1:
            raise AssertionError("P0 correction did not become the first accepted revision")
        prepared = _post(
            API,
            "/internal/phase2/operations",
            {
                "command_id": str(uuid4()),
                "workflow_id": workflow_id,
                "scenario_id": scenario["scenario_id"],
                "expected_intent_revision": 1,
                "expected_resource_version": 0,
                "idempotency_key": f"phase6:{execution_id}:preaccept-corrected",
            },
        )
        bind_execution(
            execution_id,
            UUID(scenario["scenario_id"]),
            UUID(workflow_id),
            placement.hash,
            scripted_at,
        )
        steps = _step_until_present(prepared["operation_id"])
        receipt_id = None
        permit_id = None
        speech_source = "research_baseline_without_claim_permit"
        if PROFILES[arm].claim_permits:
            receipt_id, permit_id, _ = _publish_current(
                prepared["operation_id"], 1, "CURRENT_APPOINTMENT"
            )
            speech_source = "controller_revision_bound_permit"
        now = datetime.now(UTC)
        ack = PlaybackAck(
            event_id=str(uuid4()),
            claim_type="CURRENT_APPOINTMENT",
            claim_start=case.final_start,
            intent_revision=1,
            released_at=now,
            played_at=now,
            played_ms=500,
            permit_id=permit_id,
        )
        record_playback(execution_id, ack, case.audio_hash)
        truth = truth_log(UUID(scenario["scenario_id"]))
        history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
        result = grade(case, truth, playback_for(execution_id), scripted_at)
        record_result(execution_id, case, truth, result)
        observation_ended_at = datetime.now(UTC).isoformat()
        execution = {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": scenario["scenario_id"],
            "workflow_id": workflow_id,
            "first_operation_id": None,
            "current_operation_id": prepared["operation_id"],
            "fault_occurrence_id": None,
            "fault_placement_hash": placement.hash,
            "speech_source": speech_source,
            "receipt_id": receipt_id,
            "permit_id": permit_id,
            "playback_ack": ack.model_dump(mode="json"),
            "correction_scripted_at": scripted_at.isoformat(),
            "observation_ended_at": observation_ended_at,
            "pre_correction_receipt_id": None,
            "pre_accept_history": pre_accept,
            "accepted_correction": accepted,
            "initial_worker_steps": [],
            "worker_steps": steps,
            "normalized_events": history["events"],
            "provider_evidence": [call(API, "GET", f"/v1/operations/{prepared['operation_id']}")],
            "timing_evidence": timing_evidence(execution_id),
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
        execution["correction_to_outcome_latency"] = correction_to_outcome(execution)
        return execution
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        raise


def _secondary_workflow(
    scenario_id: UUID, case: ScenarioCase, execution_id: UUID
) -> dict[str, Any]:
    start = case.initial_start + timedelta(days=1)
    fixture = _post(
        API,
        "/internal/phase1/fixtures",
        {
            "command_id": str(uuid4()),
            "first_transcript": f"Book separate maintenance at {start.isoformat()}.",
        },
    )
    accepted = _post(
        API,
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        {
            "command_id": str(uuid4()),
            "expected_revision": 0,
            "change_class": "INITIAL",
            "desired_state": _desired(fixture, start, case.timezone),
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][0],
                "model": "phase6-frozen-scripted-transcript",
                "prompt_hash": stable_hash({"task": "secondary-booking", "start": start}),
                "transcript_version": 1,
            },
        },
    )
    prepared = _post(
        API,
        "/internal/phase2/operations",
        {
            "command_id": str(uuid4()),
            "workflow_id": fixture["workflow_id"],
            "scenario_id": str(scenario_id),
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase6:{execution_id}:secondary",
        },
    )
    steps = _step_until_present(prepared["operation_id"])
    return {
        "fixture": fixture,
        "accepted": accepted,
        "operation": prepared,
        "worker_steps": steps,
        "detail": call(API, "GET", f"/v1/operations/{prepared['operation_id']}"),
    }


def _execute_one(
    run_id: UUID,
    case_id: UUID,
    case: ScenarioCase,
    arm: Arm,
) -> dict[str, Any]:
    if arm in BASELINE_ARMS:
        if (
            case.correction_barrier is Barrier.P3
            and case.visibility is ProviderVisibility.IMMEDIATE
            and case.provider_capability.supports_reschedule
            and case.revision_type == "PARAMETER_CORRECTION"
            and case.workflow_shape == "ONE_TICKET_ONE_APPOINTMENT"
            and case.fault_family in (FaultFamily.NONE, FaultFamily.RESPONSE_LOSS)
        ):
            return execute_baseline_p3(run_id, case_id, case, arm)
        from research.runner.baseline_covering import execute_covering

        return execute_covering(run_id, case_id, case, arm)
    if case.fault_family is FaultFamily.PROVIDER_CONFLICT:
        from research.runner.conflict import execute_conflict

        return execute_conflict(run_id, case_id, case, arm)
    if case.correction_barrier is Barrier.P0:
        return _execute_p0(run_id, case_id, case, arm)
    if case.correction_barrier not in LIVE_PHASES:
        raise ValueError("The paired live-service driver currently supports P0-P5")
    if arm not in DEFAULT_ARMS:
        raise ValueError("The paired live-service driver currently supports B3, P1, P2")
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
    placement = schedule(case)
    target = {
        "barrier": placement.barrier.value,
        "fault": placement.fault.value,
        "request_index": placement.request_index,
        "target": placement.target,
    }
    try:
        provider_barrier = case.correction_barrier in (Barrier.P2, Barrier.P3, Barrier.P4)
        scenario = _post(
            SIMULATOR,
            "/internal/scenarios",
            {
                "idempotency": PROFILES[arm].durable_idempotency,
                "status_lookup": True,
                "resource_lookup": True,
                "visibility": case.visibility.simulator_visibility,
                "visibility_reads": case.visibility.visibility_reads,
                "supports_reschedule": case.provider_capability.supports_reschedule,
                "held_barriers": [placement.target] if provider_barrier else [],
                "faults": [
                    {
                        "request_index": 1,
                        "stage": "AFTER_COMMIT_BEFORE_RESPONSE",
                        "kind": "DROP_RESPONSE",
                    }
                ]
                if case.fault_family in (FaultFamily.RESPONSE_LOSS, FaultFamily.REDIS_LOSS)
                else [
                    {
                        "request_index": 1,
                        "stage": "BEFORE_COMMIT",
                        "kind": "DELAY",
                    }
                ]
                if case.fault_family is FaultFamily.DELAY
                else [
                    {
                        "request_index": 1,
                        "stage": "BEFORE_COMMIT",
                        "kind": "RETURN_5XX",
                    }
                ]
                if case.fault_family is FaultFamily.PROVIDER_REFUSAL
                else [{"request_index": 1, "stage": "BEFORE_COMMIT", "kind": "PARTIAL_EFFECT"}]
                if case.fault_family is FaultFamily.PARTIAL_EFFECT
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
        prepared: dict[str, Any] | None = None
        pre_correction_receipt_id: str | None = None
        initial_steps: list[dict[str, Any]] = []
        provider_delay_evidence: dict[str, Any] | None = None
        provider_refusal_evidence: dict[str, Any] | None = None
        redis_evidence: dict[str, Any] | None = None
        secondary_evidence: dict[str, Any] | None = None
        if case.correction_barrier is Barrier.P1:
            controller = NamedBarrierController(execution_id, {Barrier.P1})
            with ThreadPoolExecutor(max_workers=1) as pool:
                paused = pool.submit(controller.reach, Barrier.P1, placement.target)
                barrier_id = controller.wait_reached(Barrier.P1)
                try:
                    scripted_at = datetime.now(UTC)
                    _accept(fixture, case, 2)
                finally:
                    controller.release(Barrier.P1)
                if paused.result(timeout=40) != barrier_id:
                    raise AssertionError("P1 reach/release identity changed")
            prepared = _post(
                API,
                "/internal/phase2/operations",
                {
                    "command_id": str(uuid4()),
                    "workflow_id": fixture["workflow_id"],
                    "scenario_id": str(scenario_id),
                    "expected_intent_revision": 2,
                    "expected_resource_version": 0,
                    "idempotency_key": f"phase6:{execution_id}:corrected",
                },
            )
        else:
            prepared = _post(
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
            if provider_barrier:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    dispatch = pool.submit(
                        _post,
                        WORKER,
                        "/internal/phase2/step",
                        {"owner": str(execution_id), "operation_id": prepared["operation_id"]},
                    )
                    reached = call(
                        SIMULATOR,
                        "GET",
                        f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}?wait=true",
                    )
                    if reached.get("reached_at") is None:
                        raise AssertionError("Named provider barrier was not reached")
                    if case.fault_family is FaultFamily.DELAY:
                        configured = call(SIMULATOR, "GET", f"/internal/scenarios/{scenario_id}")
                        provider_delay_evidence = {
                            "simulator_config": configured["config"],
                            "held_barrier": reached,
                            "truth_while_held": json.loads(
                                json.dumps(truth_log(scenario_id), default=str)
                            ),
                        }
                    if case.fault_family is FaultFamily.PROVIDER_REFUSAL:
                        configured = call(SIMULATOR, "GET", f"/internal/scenarios/{scenario_id}")
                        provider_refusal_evidence = {
                            "simulator_config": configured["config"],
                            "held_barrier": reached,
                            "truth_while_held": json.loads(
                                json.dumps(truth_log(scenario_id), default=str)
                            ),
                        }
                    barrier_id = record_barrier(
                        execution_id,
                        case.correction_barrier.value,
                        placement.target,
                        datetime.fromisoformat(reached["reached_at"]),
                        held=True,
                    )
                    try:
                        scripted_at = datetime.now(UTC)
                        _accept(fixture, case, 2)
                        if case.workflow_shape == "TWO_WORKFLOWS_TWO_TICKETS_TWO_RESOURCES":
                            secondary_evidence = _secondary_workflow(
                                scenario_id, case, execution_id
                            )
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
                    initial_steps.append(dispatch.result(timeout=40))
                    if provider_delay_evidence is not None:
                        provider_delay_evidence["released_barrier"] = call(
                            SIMULATOR,
                            "GET",
                            f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}",
                        )
                    if provider_refusal_evidence is not None:
                        provider_refusal_evidence["truth_after_refusal"] = json.loads(
                            json.dumps(truth_log(scenario_id), default=str)
                        )
                        provider_refusal_evidence["released_barrier"] = call(
                            SIMULATOR,
                            "GET",
                            f"/internal/scenarios/{scenario_id}/barriers/{quote(placement.target)}",
                        )
            else:
                initial_steps = _step_until_present(prepared["operation_id"])
                receipt = _post(
                    API,
                    "/internal/phase3/verifications",
                    {
                        "command_id": str(uuid4()),
                        "operation_id": prepared["operation_id"],
                        "expected_intent_revision": 1,
                        "claim_type": "CURRENT_APPOINTMENT",
                    },
                )
                if receipt["result"] != "SATISFIED":
                    raise AssertionError("P5 requires completed initial verification")
                pre_correction_receipt_id = receipt["receipt_id"]
                controller = NamedBarrierController(execution_id, {Barrier.P5})
                with ThreadPoolExecutor(max_workers=1) as pool:
                    paused = pool.submit(controller.reach, Barrier.P5, placement.target)
                    barrier_id = controller.wait_reached(Barrier.P5)
                    try:
                        scripted_at = datetime.now(UTC)
                        _accept(fixture, case, 2)
                    finally:
                        controller.release(Barrier.P5)
                    if paused.result(timeout=40) != barrier_id:
                        raise AssertionError("P5 reach/release identity changed")
        fault_id = (
            record_fault(
                execution_id,
                case.correction_barrier.value,
                placement.fault.value,
                target,
                barrier_id,
            )
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
        partial = case.fault_family is FaultFamily.PARTIAL_EFFECT
        unavailable = case.visibility is ProviderVisibility.UNAVAILABLE or partial
        steps = _drain(fixture["workflow_id"], expect_handoff=unavailable)
        history = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
        current_id: str | None = None
        permit_id = None
        receipt_id = None
        ack: PlaybackAck | None = None
        unavailable_evidence: dict[str, Any] | None = None
        if unavailable:
            receipt = _post(
                API,
                "/internal/phase3/verifications",
                {
                    "command_id": str(uuid4()),
                    "operation_id": prepared["operation_id"],
                    "expected_intent_revision": 2,
                    "claim_type": "HISTORICAL_EFFECT",
                },
            )
            if receipt["result"] != ("VIOLATED" if partial else "UNKNOWN"):
                raise AssertionError("Unresolved effect must not yield satisfied evidence")
            claim_request = {
                "command_id": str(uuid4()),
                "receipt_id": receipt["receipt_id"],
                "expected_intent_revision": 2,
            }
            try:
                _post(API, "/internal/phase3/claims", claim_request)
            except HTTPError as denied:
                problem = json.load(denied)
                if denied.code != 409 or not problem["type"].endswith("receipt-not-applicable"):
                    raise
                denial = {"status": denied.code, "problem": problem}
            else:
                raise AssertionError("UNKNOWN receipt unexpectedly authorized decisive speech")
            unavailable_evidence = {
                "simulator_config": call(SIMULATOR, "GET", f"/internal/scenarios/{scenario_id}")[
                    "config"
                ],
                "handoff_snapshot": handoff_snapshot(UUID(fixture["workflow_id"])),
                "unknown_receipt": receipt,
                "claim_request": claim_request,
                "claim_denial": denial,
            }
            speech_source = (
                "withheld_partial_provider_effect"
                if partial
                else "withheld_unknown_provider_evidence"
            )
        else:
            current = next(
                (item for item in history["operations"] if item["intent_revision"] == 2),
                history["operations"][0],
            )
            if current["effect_knowledge"] != "PRESENT":
                raise AssertionError("Revision-2 provider effect was not resolved")
            current_id = current["id"]
            current_detail = call(API, "GET", f"/v1/operations/{current_id}")["operation"]
            proposed_start = datetime.fromisoformat(
                current_detail["normalized_request_json"]["desired_state"]["requested_start"]
            )
            claim_type = (
                "RESCHEDULED_APPOINTMENT"
                if current_detail["normalized_request_json"]["action"] == "RESCHEDULE"
                else "CURRENT_APPOINTMENT"
            )
            speech_source = "research_baseline_without_claim_permit"
            if PROFILES[arm].claim_permits and case.revision_type != "RETRACTION":
                receipt_id, permit_id, _ = _publish_current(current_id, 2, claim_type)
                speech_source = "controller_revision_bound_permit"
            now = datetime.now(UTC)
            ack = PlaybackAck(
                event_id=str(uuid4()),
                claim_type=claim_type,
                claim_start=proposed_start,
                intent_revision=2,
                released_at=now,
                played_at=now,
                played_ms=500,
                permit_id=permit_id,
            )
            if case.revision_type == "RETRACTION":
                ack = None
                speech_source = "withheld_no_cancellation_speech_contract"
            else:
                record_playback(execution_id, ack, case.audio_hash)
        truth = truth_log(scenario_id)
        observed = playback_for(execution_id)
        result = grade(case, truth, observed, scripted_at)
        record_result(execution_id, case, truth, result)
        observation_ended_at = datetime.now(UTC).isoformat()
        logger.info(
            "research_execution_completed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            workflow_id=fixture["workflow_id"],
            operation_id=current_id,
            intent_revision=2,
            arm=arm.value,
        )
        execution = {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": str(scenario_id),
            "workflow_id": fixture["workflow_id"],
            "first_operation_id": (
                prepared["operation_id"] if case.correction_barrier is not Barrier.P1 else None
            ),
            "current_operation_id": current_id,
            "fault_occurrence_id": str(fault_id) if fault_id else None,
            "fault_placement_hash": placement.hash,
            "speech_source": speech_source,
            "receipt_id": receipt_id,
            "permit_id": permit_id,
            "playback_ack": ack.model_dump(mode="json") if ack is not None else None,
            "correction_scripted_at": scripted_at.isoformat(),
            "observation_ended_at": observation_ended_at,
            "pre_correction_receipt_id": pre_correction_receipt_id,
            "initial_worker_steps": initial_steps,
            "worker_steps": steps,
            "normalized_events": history["events"],
            "provider_evidence": [
                call(API, "GET", f"/v1/operations/{item['id']}") for item in history["operations"]
            ],
            "timing_evidence": timing_evidence(execution_id),
            "provider_delay_evidence": provider_delay_evidence,
            "provider_refusal_evidence": provider_refusal_evidence,
            "unavailable_evidence": unavailable_evidence,
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
        execution["correction_to_outcome_latency"] = correction_to_outcome(execution)
        if redis_evidence is not None:
            execution["redis_loss_evidence"] = redis_evidence
        if partial:
            execution["partial_effect_evidence"] = unavailable_evidence
        if secondary_evidence is not None:
            execution["secondary_workflow_evidence"] = secondary_evidence
        if case.action_semantics == "CREATE_READ_REUSE":
            from packages.provider_adapters.simulator import resource_state

            before_read = truth_log(scenario_id)
            read = resource_state(scenario_id, UUID(current_id), fixture["resource_key"])
            execution["read_only_evidence"] = {
                "raw": read.raw,
                "truth_before": json.loads(json.dumps(before_read, default=str)),
                "truth_after": json.loads(json.dumps(truth_log(scenario_id), default=str)),
            }
        return execution
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        logger.exception(
            "research_execution_failed",
            trace_id=trace_id,
            experiment_run_id=str(run_id),
            execution_id=str(execution_id),
            arm=arm.value,
        )
        raise


def run_paired(
    case: ScenarioCase | None = None,
    arms: tuple[Arm, ...] = DEFAULT_ARMS,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    selected = case or MANDATORY_HIGH_RISK[2]
    if selected.correction_barrier not in LIVE_PHASES:
        raise ValueError("Phase 6 live-service pairing currently supports P0-P5")
    if (
        selected.visibility is not ProviderVisibility.IMMEDIATE
        and selected.correction_barrier is not Barrier.P3
    ):
        raise ValueError("Non-immediate visibility live drivers currently support P3 only")
    if len(arms) < 2 or len(set(arms)) != len(arms) or any(arm not in ALL_ARMS for arm in arms):
        raise ValueError("Choose at least two distinct declared research arms")
    if (
        any(arm in BASELINE_ARMS for arm in arms)
        and selected.fault_family is FaultFamily.PROVIDER_CONFLICT
    ):
        raise ValueError("The post-verification conflict ablation uses B3/P1/P2")
    source_commit, tree_hash = _source_identity()
    placement = schedule(selected)
    manifest: dict[str, Any] = {
        "name": f"Phase 6 paired {selected.scenario_key}",
        "runner_version": RUNNER_VERSION,
        "latency_analysis_version": LATENCY_ANALYSIS_VERSION,
        "scenario": selected.model_dump(mode="json"),
        "fixture_hash": selected.fixture_hash,
        "audio_hash": selected.audio_hash,
        "source_tree_hash": tree_hash,
        "source_commit": source_commit,
        "container_digests": _container_digests(),
        "migration_version": MIGRATION_VERSION,
        "model_profile": "phase6-frozen-scripted-transcript",
        "prompt_hashes": [
            stable_hash({"transcript": text, "version": "phase6-v1"})
            for text in (selected.initial_transcript, selected.correction_transcript)
        ],
        "retry_budget": 8,
        "provider_timeout_seconds": 40,
        "primary_endpoints": ["correction_success", "unsupported_confirmation"],
        "speech_policy_version": "phase3-policy-v1",
        "fault_schedule": {
            "barrier": placement.barrier.value,
            "fault": placement.fault.value,
            "request_index": placement.request_index,
            "target": placement.target,
            "hash": placement.hash,
        },
    }
    manifest["arms"] = {
        arm.value: {
            key: value.value if isinstance(value, Arm) else value
            for key, value in vars(PROFILES[arm]).items()
        }
        for arm in arms
    }
    run_id, manifest_hash, frozen_manifest = create_run(manifest, source_commit)
    case_id = create_case(run_id, selected, manifest["fault_schedule"])
    executions = [_execute_one(run_id, case_id, selected, arm) for arm in arms]
    if len({item["fault_placement_hash"] for item in executions}) != 1:
        raise AssertionError("Paired arms did not receive identical fault placement")
    finish_run(run_id)
    paired = paired_counts(
        [
            {
                "scenario_key": selected.scenario_key,
                "arm": item["arm"],
                "metrics": {
                    metric["metric_name"]: metric["numeric_value"] for metric in item["metrics"]
                },
            }
            for item in executions
        ],
        "correction_success",
    )
    bundle = {
        "run_id": str(run_id),
        "case_id": str(case_id),
        "manifest": frozen_manifest,
        "manifest_hash": manifest_hash,
        "execution_count": len(executions),
        "independent_scenario_count": 1,
        "paired_summary": paired,
        "executions": executions,
    }
    bundle["latency_summary"] = {
        arm.value: paired_latency(
            [
                {
                    "scenario_key": selected.scenario_key,
                    "arm": item["arm"],
                    **item["correction_to_outcome_latency"],
                }
                for item in executions
            ],
            "B3",
            arm.value,
        )
        for arm in arms
        if Arm.B3 in arms and arm is not Arm.B3
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    destination = output_dir or Path("artifacts") / "phase-6-replays"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{run_id}.json"
    if path.exists():
        raise FileExistsError("A frozen replay bundle cannot be overwritten")
    path.write_text(json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "run_id": str(run_id),
        "bundle_path": str(path.resolve()),
        "bundle_hash": bundle["bundle_hash"],
        "paired_summary": paired,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a live Phase 6 paired replay")
    parser.add_argument(
        "--phase",
        choices=sorted(phase.value for phase in LIVE_PHASES),
        default=Barrier.P3.value,
    )
    parser.add_argument("--all-arms", action="store_true", help="Include B0, B1, and B2 at P3")
    parser.add_argument(
        "--compensation-case",
        action="store_true",
        help="Run the P3 non-atomic cancel-then-create provider case under B3/P1/P2",
    )
    parser.add_argument(
        "--delayed-visibility-case",
        action="store_true",
        help="Run P3 with two inconclusive provider reads under B3/P1/P2",
    )
    parser.add_argument(
        "--provider-delay-case",
        action="store_true",
        help="Run P2 with a held pre-commit provider delay under B3/P1/P2",
    )
    parser.add_argument(
        "--provider-refusal-case",
        action="store_true",
        help="Run P2 with a pre-commit provider 5xx under B3/P1/P2",
    )
    parser.add_argument(
        "--unavailable-evidence-case",
        action="store_true",
        help="Run P3 with unavailable evidence until durable handoff under B3/P1/P2",
    )
    parser.add_argument(
        "--provider-conflict-case",
        action="store_true",
        help="Run P5 with a version conflict before the corrected reschedule under B3/P1/P2",
    )
    args = parser.parse_args()
    phase = Barrier(args.phase)
    if (
        sum(
            (
                args.compensation_case,
                args.delayed_visibility_case,
                args.provider_delay_case,
                args.provider_refusal_case,
                args.unavailable_evidence_case,
                args.provider_conflict_case,
            )
        )
        > 1
    ):
        parser.error("Choose one case variant")
    if args.unavailable_evidence_case and (phase is not Barrier.P3 or args.all_arms):
        parser.error("--unavailable-evidence-case requires P3 and the B3/P1/P2 arm set")
    if args.provider_conflict_case and (phase is not Barrier.P5 or args.all_arms):
        parser.error("--provider-conflict-case requires P5 and the B3/P1/P2 arm set")
    if args.compensation_case and (phase is not Barrier.P3 or args.all_arms):
        parser.error("--compensation-case requires P3 and the B3/P1/P2 arm set")
    if args.delayed_visibility_case and (
        phase is not Barrier.P3
        or args.all_arms
        or args.compensation_case
        or args.provider_delay_case
        or args.provider_refusal_case
    ):
        parser.error("--delayed-visibility-case requires P3 and the B3/P1/P2 arm set")
    if args.provider_delay_case and (
        phase is not Barrier.P2
        or args.all_arms
        or args.compensation_case
        or args.delayed_visibility_case
        or args.provider_refusal_case
    ):
        parser.error("--provider-delay-case requires P2 and the B3/P1/P2 arm set")
    if args.provider_refusal_case and (
        phase is not Barrier.P2
        or args.all_arms
        or args.compensation_case
        or args.delayed_visibility_case
        or args.provider_delay_case
    ):
        parser.error("--provider-refusal-case requires P2 and the B3/P1/P2 arm set")
    selected = (
        CAPABILITY_COVERING[0]
        if args.compensation_case
        else VISIBILITY_COVERING[0]
        if args.delayed_visibility_case
        else DELAY_COVERING[0]
        if args.provider_delay_case
        else REFUSAL_COVERING[0]
        if args.provider_refusal_case
        else UNAVAILABLE_COVERING[0]
        if args.unavailable_evidence_case
        else CONFLICT_COVERING[0]
        if args.provider_conflict_case
        else MANDATORY_HIGH_RISK[2]
        if phase is Barrier.P3
        else case_for(phase)
    )
    print(json.dumps(run_paired(selected, ALL_ARMS if args.all_arms else DEFAULT_ARMS), indent=2))
