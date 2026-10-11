"""Run one fault-free CREATE case under the three speech-policy arms."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from research.analysis.metrics import clean_paired_difference, metric_rows, paired_counts
from research.arms import PROFILES, Arm
from research.oracle.grade import PlaybackAck, grade_clean
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, call
from research.run_store import (
    MIGRATION_VERSION,
    baseline_events_for,
    bind_clean_execution,
    create_case,
    create_execution,
    create_run,
    fail_execution,
    finish_run,
    playback_for,
    record_baseline_event,
    record_playback,
    record_result,
)
from research.runner.paired import (
    _container_digests,
    _desired,
    _post,
    _publish_current,
    _source_identity,
    _step_until_present,
)
from research.scenario_dsl.catalog import CLEAN_CASES
from research.scenario_dsl.models import CleanScenarioCase, stable_hash

ARMS = (Arm.B3, Arm.P1, Arm.P2)
RUNNER_VERSION = "phase6-clean-paired-v2"
CLEAN_ANALYSIS_VERSION = "phase6-clean-v2"


def _execute(
    run_id: UUID,
    case_id: UUID,
    case: CleanScenarioCase,
    arm: Arm,
    voice_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    execution_id = create_execution(run_id, case_id, arm.value, case.repetition)
    trace_id = str(uuid4())
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
                "research_arm": arm.value if arm in ARMS else None,
                "first_transcript": (voice_evidence["transcript"] or case.transcript)
                if voice_evidence
                else case.transcript,
            },
        )
        desired = _desired(fixture, case.final_start, case.timezone)
        if voice_evidence:
            if voice_evidence["proposal"]:
                desired = {**desired, **voice_evidence["proposal"]}
            for event_type in (
                "SpeechStarted",
                "TranscriptFinal",
                "ToolProposalReceived" if voice_evidence["proposal"] else "ClarificationRequired",
            ):
                if event_type == "TranscriptFinal" and not voice_evidence["transcript"]:
                    continue
                normalized: dict[str, Any] = {"audio_hash": case.audio_hash}
                if event_type == "TranscriptFinal":
                    normalized = {
                        "transcript": voice_evidence["transcript"],
                        "transcript_hash": voice_evidence["transcript_hash"],
                    }
                elif event_type == "ToolProposalReceived":
                    normalized = {
                        "desired_state": desired,
                        "candidate_source": {
                            "utterance_id": fixture["utterance_ids"][0],
                            "model": voice_evidence["intent_model_id"],
                            "prompt_hash": voice_evidence["prompt_hash"],
                            "transcript_version": 1,
                        },
                    }
                emitted = _post(
                    API,
                    f"/internal/phase4/calls/{fixture['call_id']}/voice-events",
                    {
                        "event_id": str(uuid4()),
                        "source_event_id": f"phase6:{execution_id}:{event_type}",
                        "event_type": event_type,
                        "occurred_at": datetime.now(UTC).isoformat(),
                        "raw": voice_evidence,
                        "normalized": normalized,
                    },
                )
                if event_type == "TranscriptFinal":
                    fixture["utterance_ids"][0] = emitted["utterance_id"]
            if voice_evidence["status"] == "CLARIFICATION":
                bind_clean_execution(
                    execution_id,
                    UUID(scenario["scenario_id"]),
                    UUID(fixture["workflow_id"]),
                    stable_hash({"fault": "NONE", "correction": False}),
                )
                result = grade_clean(case, [], [])
                record_result(execution_id, case, [], result)
                return {
                    "execution_id": str(execution_id),
                    "arm": arm.value,
                    "scenario_id": scenario["scenario_id"],
                    "workflow_id": fixture["workflow_id"],
                    "operation_id": None,
                    "accepted_revision": None,
                    "receipt_id": None,
                    "permit_id": None,
                    "speech_source": "local_cascade_clarification",
                    "playback_ack": None,
                    "worker_steps": [],
                    "normalized_events": call(
                        API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history"
                    )["events"],
                    "provider_evidence": None,
                    "simulator_truth": [],
                    "oracle_result": result,
                    "metrics": metric_rows(result),
                }
            desired = {**desired, **voice_evidence["proposal"]}
        accepted = _post(
            API,
            f"/v1/workflows/{fixture['workflow_id']}/revisions",
            {
                "command_id": str(uuid4()),
                "expected_revision": 0,
                "change_class": "INITIAL",
                "desired_state": desired,
                "candidate_source": {
                    "utterance_id": fixture["utterance_ids"][0],
                    "model": voice_evidence["intent_model_id"]
                    if voice_evidence
                    else "phase6-frozen-scripted-transcript",
                    "prompt_hash": voice_evidence["prompt_hash"]
                    if voice_evidence
                    else stable_hash({"transcript": case.transcript, "version": "phase6-clean-v1"}),
                    "transcript_version": 1,
                },
            },
        )
        if accepted["revision"] != 1:
            raise AssertionError("Clean task did not accept revision one")
        if arm in (Arm.B0, Arm.B1, Arm.B2):
            from packages.provider_adapters.simulator import resource_state, send_operation
            from research.runner.baselines import _observation, _request

            operation_id = uuid4()
            payload = _request(
                UUID(scenario["scenario_id"]),
                operation_id,
                f"phase6-clean:{execution_id}",
                "CREATE",
                fixture["resource_key"],
                start=datetime.fromisoformat(desired["requested_start"]),
                timezone=case.timezone,
            )
            record_baseline_event(
                execution_id,
                1,
                "REQUEST_SENT",
                payload,
                {"action": "CREATE", "sent": True},
                trace_id,
            )
            response = send_operation(payload)
            record_baseline_event(
                execution_id, 2, "PROVIDER_RESPONSE", response.raw, _observation(response), trace_id
            )
            if response.status != 200:
                raise AssertionError("Fault-free clean baseline failed")
            if arm is not Arm.B0:
                read = resource_state(
                    UUID(scenario["scenario_id"]), operation_id, fixture["resource_key"]
                )
                record_baseline_event(
                    execution_id, 3, "POSTCONDITION_READ", read.raw, _observation(read), trace_id
                )
                if not read.body or not read.body.get("authoritative"):
                    raise AssertionError("Clean baseline postcondition unavailable")
            bind_clean_execution(
                execution_id,
                UUID(scenario["scenario_id"]),
                UUID(fixture["workflow_id"]),
                stable_hash({"fault": "NONE", "correction": False}),
            )
            now = datetime.now(UTC)
            ack = PlaybackAck(
                event_id=str(uuid4()),
                claim_type="CURRENT_APPOINTMENT",
                claim_start=datetime.fromisoformat(desired["requested_start"]),
                intent_revision=1,
                released_at=now,
                played_at=now,
                played_ms=500,
            )
            record_playback(execution_id, ack, case.audio_hash)
            truth = truth_log(UUID(scenario["scenario_id"]))
            result = grade_clean(case, truth, [ack])
            record_result(execution_id, case, truth, result)
            return {
                "execution_id": str(execution_id),
                "arm": arm.value,
                "scenario_id": scenario["scenario_id"],
                "workflow_id": fixture["workflow_id"],
                "operation_id": str(operation_id),
                "accepted_revision": accepted,
                "receipt_id": None,
                "permit_id": None,
                "speech_source": "research_baseline_tool_response",
                "playback_ack": ack.model_dump(mode="json"),
                "worker_steps": [],
                "normalized_events": call(
                    API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history"
                )["events"],
                "provider_evidence": None,
                "baseline_events": baseline_events_for(execution_id),
                "simulator_truth": json.loads(json.dumps(truth, default=str)),
                "oracle_result": result,
                "metrics": metric_rows(result),
            }
        prepared = _post(
            API,
            "/internal/phase2/operations",
            {
                "command_id": str(uuid4()),
                "workflow_id": fixture["workflow_id"],
                "scenario_id": scenario["scenario_id"],
                "expected_intent_revision": 1,
                "expected_resource_version": 0,
                "idempotency_key": f"phase6-clean:{execution_id}:create",
            },
        )
        bind_clean_execution(
            execution_id,
            UUID(scenario["scenario_id"]),
            UUID(fixture["workflow_id"]),
            stable_hash({"fault": "NONE", "correction": False}),
        )
        steps = _step_until_present(prepared["operation_id"])
        receipt_id = None
        permit_id = None
        if PROFILES[arm].claim_permits:
            receipt_id, permit_id, _ = _publish_current(
                prepared["operation_id"], 1, "CURRENT_APPOINTMENT"
            )
        now = datetime.now(UTC)
        ack = PlaybackAck(
            event_id=str(uuid4()),
            claim_type="CURRENT_APPOINTMENT",
            claim_start=datetime.fromisoformat(desired["requested_start"]),
            intent_revision=1,
            released_at=now,
            played_at=now,
            played_ms=500,
            permit_id=permit_id,
        )
        record_playback(execution_id, ack, case.audio_hash)
        truth = truth_log(UUID(scenario["scenario_id"]))
        result = grade_clean(case, truth, playback_for(execution_id))
        record_result(execution_id, case, truth, result)
        history = call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")
        return {
            "execution_id": str(execution_id),
            "arm": arm.value,
            "scenario_id": scenario["scenario_id"],
            "workflow_id": fixture["workflow_id"],
            "operation_id": prepared["operation_id"],
            "accepted_revision": accepted,
            "receipt_id": receipt_id,
            "permit_id": permit_id,
            "speech_source": (
                "controller_revision_bound_permit"
                if permit_id
                else "research_baseline_without_claim_permit"
            ),
            "playback_ack": ack.model_dump(mode="json"),
            "worker_steps": steps,
            "normalized_events": history["events"],
            "provider_evidence": call(API, "GET", f"/v1/operations/{prepared['operation_id']}"),
            "simulator_truth": json.loads(json.dumps(truth, default=str)),
            "oracle_result": result,
            "metrics": metric_rows(result),
        }
    except Exception as exc:
        fail_execution(run_id, execution_id, trace_id, type(exc).__name__)
        raise


def run_clean_paired(
    case: CleanScenarioCase = CLEAN_CASES[0],
    output_dir: Path = Path("artifacts") / "phase-6-replays",
    voice_evidence: dict[str, Any] | None = None,
    arms: tuple[Arm, ...] = ARMS,
) -> dict[str, Any]:
    source_commit, tree_hash = _source_identity()
    no_fault = {"fault": "NONE", "correction": False}
    no_fault["hash"] = stable_hash(no_fault)
    manifest: dict[str, Any] = {
        "name": f"Phase 6 clean paired {case.scenario_key}",
        "runner_version": RUNNER_VERSION,
        "analysis_version": CLEAN_ANALYSIS_VERSION,
        "scenario": case.model_dump(mode="json"),
        "fixture_hash": case.fixture_hash,
        "audio_hash": case.audio_hash,
        "source_commit": source_commit,
        "source_tree_hash": tree_hash,
        "container_digests": _container_digests(),
        "migration_version": MIGRATION_VERSION,
        "model_profile": "phase6-frozen-scripted-transcript",
        "prompt_hash": stable_hash({"transcript": case.transcript, "version": "phase6-clean-v1"}),
        "primary_endpoints": ["correction_success", "unsupported_confirmation"],
        "noninferiority_endpoint": "clean_task_success",
        "fault_schedule": no_fault,
        "arms": {
            arm.value: {
                key: value.value if isinstance(value, Arm) else value
                for key, value in vars(PROFILES[arm]).items()
            }
            for arm in arms
        },
    }
    if voice_evidence is not None:
        from research.runner.acoustic_source import AcousticEvidence

        voice_evidence = AcousticEvidence.model_validate(voice_evidence).model_dump(mode="json")
        if voice_evidence["input_audio_hash"] != case.audio_hash:
            raise ValueError("Local voice input differs from the case audio hash")
        manifest["voice_evidence"] = voice_evidence
        manifest["voice_evidence_hash"] = stable_hash(voice_evidence)
        manifest["model_profile"] = "phase6-local-cascade-v1"
    run_id, manifest_hash, frozen_manifest = create_run(
        manifest, source_commit, CLEAN_ANALYSIS_VERSION
    )
    case_id = create_case(run_id, case, no_fault)
    executions = [_execute(run_id, case_id, case, arm, voice_evidence) for arm in arms]
    finish_run(run_id)
    rows = [
        {
            "scenario_key": case.scenario_key,
            "arm": item["arm"],
            "metrics": {row["metric_name"]: row["numeric_value"] for row in item["metrics"]},
        }
        for item in executions
    ]
    summary = paired_counts(rows, "clean_task_success")
    bundle = {
        "run_id": str(run_id),
        "case_id": str(case_id),
        "manifest": frozen_manifest,
        "manifest_hash": manifest_hash,
        "execution_count": len(executions),
        "independent_scenario_count": 1,
        "paired_summary": summary,
        "noninferiority_descriptive": {
            arm.value: clean_paired_difference(rows, "B3", arm.value)
            for arm in arms
            if arm is not Arm.B3
        },
        "executions": executions,
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"clean-paired-{run_id}.json"
    if path.exists():
        raise FileExistsError("A frozen clean replay bundle cannot be overwritten")
    path.write_text(json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    return {
        "run_id": str(run_id),
        "bundle_path": str(path.resolve()),
        "bundle_hash": bundle["bundle_hash"],
        "paired_summary": summary,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Phase 6 clean-task paired replay")
    parser.parse_args()
    print(json.dumps(run_clean_paired(), indent=2))
