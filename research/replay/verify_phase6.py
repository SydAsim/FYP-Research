"""Offline integrity and independent-oracle replay for a Phase 6 bundle."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from research.analysis.latency import (
    LATENCY_ANALYSIS_VERSION,
    correction_to_outcome,
    paired_latency,
)
from research.analysis.metrics import metric_rows, paired_counts
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck, grade
from research.replay.baseline_evidence import verify_baseline
from research.replay.conflict_evidence import verify_conflict
from research.replay.recovery_evidence import verify_recovery
from research.scenario_dsl.models import (
    Barrier,
    FaultFamily,
    ProviderVisibility,
    ScenarioCase,
    stable_hash,
)


def _verify_unavailable(execution: dict[str, Any], case: ScenarioCase) -> None:
    evidence = execution.get("unavailable_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("Unavailable evidence case lacks its mechanism trace")
    config = evidence["simulator_config"]
    snapshot = evidence["handoff_snapshot"]
    handoffs = snapshot["handoffs"]
    jobs = [item for item in snapshot["jobs"] if item["job_type"] == "RECONCILE_OPERATION"]
    details = execution["provider_evidence"]
    if len(details) != 1:
        raise ValueError("Unavailable evidence must not create a follow-up operation")
    original = details[0]
    writes = [item for item in original["attempts"] if item["attempt_type"] == "WRITE"]
    reads = [item for item in original["attempts"] if item["attempt_type"] == "STATUS_LOOKUP"]
    receipt = evidence["unknown_receipt"]
    denial = evidence["claim_denial"]
    truth = execution["simulator_truth"]
    if (
        config["visibility"] != "UNAVAILABLE"
        or config["faults"]
        != [{"request_index": 1, "stage": "AFTER_COMMIT_BEFORE_RESPONSE", "kind": "DROP_RESPONSE"}]
        or original["operation"]["id"] != execution["first_operation_id"]
        or original["operation"]["effect_knowledge"] != "UNKNOWN"
        or len(writes) != 1
        or writes[0]["normalized_result_json"].get("outcome") != "UNKNOWN"
        or not writes[0]["raw_response_json"].get("transport_error")
        or not reads
        or any(
            item["normalized_result_json"] != {"outcome": "UNKNOWN", "authoritative": False}
            or item["raw_response_json"]["status"]["status"] != 503
            or item["raw_response_json"]["resource"]["status"] != 503
            for item in reads
        )
        or snapshot["workflow"] != {"current_revision": 2, "resolution_status": "HANDOFF"}
        or len(handoffs) != 1
        or handoffs[0]["reason_code"] != "RECONCILIATION_BUDGET_EXHAUSTED"
        or handoffs[0]["state"] != "OPEN"
        or handoffs[0]["unknown_facts"].get("effect_outcome") != "UNKNOWN"
        or handoffs[0]["linked_operation_ids"] != [execution["first_operation_id"]]
        or len(jobs) != 1
        or jobs[0]["state"] != "HANDOFF"
        or jobs[0]["attempt_count"] != jobs[0]["max_attempts"]
        or len(reads) != jobs[0]["max_attempts"]
        or snapshot["counts"] != {"claims": 0, "claim_permits": 0, "audio_segments": 0}
        or receipt["result"] != "UNKNOWN"
        or receipt["claim_type"] != "HISTORICAL_EFFECT"
        or receipt["intent_revision"] != 2
        or evidence["claim_request"]["receipt_id"] != receipt["receipt_id"]
        or evidence["claim_request"]["expected_intent_revision"] != 2
        or denial["status"] != 409
        or not denial["problem"]["type"].endswith("receipt-not-applicable")
        or not denial["problem"].get("trace_id")
        or execution["current_operation_id"] is not None
        or execution["permit_id"] is not None
        or execution["playback_ack"] is not None
        or execution["speech_source"] != "withheld_unknown_provider_evidence"
        or len(truth) != 1
        or truth[0]["action"] != "CREATE"
        or truth[0]["operation_id"] != execution["first_operation_id"]
        or datetime.fromisoformat(truth[0]["after_facts"]["starts_at"]) != case.initial_start
        or not execution["correction_to_outcome_latency"]["censored"]
    ):
        raise ValueError(
            "Unavailable evidence did not retain UNKNOWN and withhold follow-up writes"
        )


def verify_bundle(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    saved_bundle_hash = bundle["bundle_hash"]
    body = {key: value for key, value in bundle.items() if key != "bundle_hash"}
    if stable_hash(body) != saved_bundle_hash:
        raise ValueError("Replay bundle hash does not match its contents")
    manifest = bundle["manifest"]
    if (
        "latency_summary" in bundle
        and manifest.get("latency_analysis_version") != LATENCY_ANALYSIS_VERSION
    ):
        raise ValueError("Latency analysis version differs from the current definition")
    if stable_hash(manifest) != bundle["manifest_hash"]:
        raise ValueError("Frozen manifest hash does not match its contents")
    case = ScenarioCase.model_validate(manifest["scenario"])
    if case.fixture_hash != manifest["fixture_hash"]:
        raise ValueError("Scenario fixture hash does not match its contents")
    if case.audio_hash != manifest["audio_hash"]:
        raise ValueError("Audio hash differs from scenario fixture")
    placement = manifest["fault_schedule"]
    placement_hash = stable_hash(
        {key: placement[key] for key in ("barrier", "fault", "request_index", "target")}
    )
    if placement_hash != placement["hash"]:
        raise ValueError("Fault schedule hash does not match its contents")
    expected = schedule(case)
    if placement_hash != expected.hash:
        raise ValueError("Fault schedule differs from the named case boundary")
    executions = bundle["executions"]
    if len(executions) != bundle["execution_count"]:
        raise ValueError("Execution count differs from replay rows")
    if {item["arm"] for item in executions} != set(manifest["arms"]):
        raise ValueError("Replay arms differ from the frozen manifest")
    rows: list[dict[str, Any]] = []
    for execution in executions:
        baseline = execution["arm"] in ("B0", "B1", "B2")
        if baseline:
            verify_baseline(execution, case)
        else:
            verify_recovery(execution, case)
        conflict = case.fault_family is FaultFamily.PROVIDER_CONFLICT
        if conflict:
            verify_conflict(execution, case)
        if case.visibility is ProviderVisibility.UNAVAILABLE and not baseline:
            _verify_unavailable(execution, case)
        if case.fault_family is FaultFamily.PROVIDER_REFUSAL and not baseline:
            evidence = execution.get("provider_refusal_evidence")
            if not isinstance(evidence, dict):
                raise ValueError("Provider refusal lacks simulator evidence")
            config = evidence["simulator_config"]
            held = evidence["held_barrier"]
            released = evidence["released_barrier"]
            details = {item["operation"]["id"]: item for item in execution["provider_evidence"]}
            first = details.get(execution["first_operation_id"])
            current = details.get(execution["current_operation_id"])
            if first is None or current is None:
                raise ValueError("Provider refusal lacks both operation histories")
            first_writes = [item for item in first["attempts"] if item["attempt_type"] == "WRITE"]
            first_reads = [
                item for item in first["attempts"] if item["attempt_type"] == "STATUS_LOOKUP"
            ]
            current_writes = [
                item for item in current["attempts"] if item["attempt_type"] == "WRITE"
            ]
            if (
                config["faults"]
                != [{"request_index": 1, "stage": "BEFORE_COMMIT", "kind": "RETURN_5XX"}]
                or expected.target not in config["held_barriers"]
                or held["state"] != "REACHED"
                or held["released_at"] is not None
                or released["state"] != "RELEASED"
                or held["reached_at"] != released["reached_at"]
                or evidence["truth_while_held"]
                or evidence["truth_after_refusal"]
                or datetime.fromisoformat(execution["correction_scripted_at"])
                > datetime.fromisoformat(released["released_at"])
                or first["operation"]["effect_knowledge"] != "ABSENT"
                or len(first_writes) != 1
                or first_writes[0]["raw_response_json"].get("status") != 503
                or first_writes[0]["normalized_result_json"].get("outcome") != "UNKNOWN"
                or not first_reads
                or first_reads[0]["normalized_result_json"].get("outcome") != "ABSENT"
                or first_reads[0]["normalized_result_json"].get("authoritative") is not True
                or len(current_writes) != 1
                or datetime.fromisoformat(first_reads[0]["response_received_at"])
                > datetime.fromisoformat(current_writes[0]["request_sent_at"])
                or current["operation"]["normalized_request_json"]["action"] != "CREATE"
                or [item["action"] for item in execution["simulator_truth"]] != ["CREATE"]
                or execution["simulator_truth"][0]["operation_id"]
                != execution["current_operation_id"]
                or datetime.fromisoformat(
                    execution["simulator_truth"][0]["after_facts"]["starts_at"]
                )
                != case.final_start
            ):
                raise ValueError(
                    "Provider refusal did not reconcile absence before corrected write"
                )
        if case.fault_family is FaultFamily.DELAY and not baseline:
            evidence = execution.get("provider_delay_evidence")
            if not isinstance(evidence, dict):
                raise ValueError("Provider delay lacks simulator barrier evidence")
            config = evidence["simulator_config"]
            held = evidence["held_barrier"]
            released = evidence["released_barrier"]
            release_at = datetime.fromisoformat(released["released_at"])
            commits = execution["simulator_truth"]
            if (
                config["faults"]
                != [{"request_index": 1, "stage": "BEFORE_COMMIT", "kind": "DELAY"}]
                or expected.target not in config["held_barriers"]
                or held["state"] != "REACHED"
                or held["released_at"] is not None
                or released["state"] != "RELEASED"
                or held["reached_at"] != released["reached_at"]
                or evidence["truth_while_held"]
                or datetime.fromisoformat(execution["correction_scripted_at"]) > release_at
                or [item["action"] for item in commits] != ["CREATE", "RESCHEDULE"]
                or commits[0]["operation_id"] != execution["first_operation_id"]
                or datetime.fromisoformat(commits[0]["committed_at"]) < release_at
            ):
                raise ValueError("Provider delay did not hold the first commit until release")
        if case.visibility is ProviderVisibility.DELAYED_TWO_READS and not baseline:
            original = next(
                (
                    detail
                    for detail in execution["provider_evidence"]
                    if detail["operation"]["id"] == execution["first_operation_id"]
                ),
                None,
            )
            if original is None:
                raise ValueError("Delayed visibility lacks original operation evidence")
            attempts = original["attempts"]
            writes = [item for item in attempts if item["attempt_type"] == "WRITE"]
            lookups = [
                item["normalized_result_json"]["outcome"]
                for item in attempts
                if item["attempt_type"] == "STATUS_LOOKUP"
            ]
            if (
                len(writes) != 1
                or lookups[:2] != ["UNKNOWN", "UNKNOWN"]
                or "PRESENT" not in lookups[2:]
            ):
                raise ValueError("Delayed visibility did not reconcile before the second write")
        if (
            not case.provider_capability.supports_reschedule
            and case.correction_barrier is not Barrier.P0
            and (not baseline or execution["arm"] != "B0")
            and case.revision_type not in ("RETRACTION", "ADDITIVE_COMPATIBLE")
            and case.visibility is not ProviderVisibility.UNAVAILABLE
            and case.fault_family is not FaultFamily.PARTIAL_EFFECT
        ):
            commits = execution["simulator_truth"]
            actions = [
                item["action"]
                for item in commits
                if item["resource_key"] == commits[0]["resource_key"]
            ]
            if actions != ["CREATE", "CANCEL", "CREATE"]:
                raise ValueError("Non-atomic provider case lacks the required compensation path")
        if case.correction_barrier is Barrier.P0:
            pre_accept = execution["pre_accept_history"]
            accepted = execution["accepted_correction"]
            truth = execution["simulator_truth"]
            if (
                pre_accept["current_revision"] != 0
                or pre_accept["revisions"]
                or pre_accept["operations"]
                or execution["first_operation_id"] is not None
                or accepted["revision"] != 1
                or accepted["desired_state"]["requested_start"] != case.final_start.isoformat()
                or not (
                    datetime.fromisoformat(pre_accept["read_at"])
                    <= datetime.fromisoformat(execution["correction_scripted_at"])
                    <= datetime.fromisoformat(accepted["accepted_at"])
                )
                or len(truth) != 1
                or truth[0]["action"] != "CREATE"
                or datetime.fromisoformat(truth[0]["after_facts"]["starts_at"]) != case.final_start
            ):
                raise ValueError("P0 accepted or provider state differs from pre-accept correction")
            ack = execution["playback_ack"]
            if (
                ack is None
                or ack["intent_revision"] != 1
                or ack["claim_type"] != "CURRENT_APPOINTMENT"
                or datetime.fromisoformat(ack["claim_start"]) != case.final_start
            ):
                raise ValueError("P0 playback is not bound to corrected revision one")
        baseline_events = execution.get("baseline_events", [])
        if execution["arm"] in ("B0", "B1", "B2") and not baseline_events:
            raise ValueError("Baseline provider observations are missing")
        for ordinal, event in enumerate(baseline_events, start=1):
            if event["ordinal"] != ordinal:
                raise ValueError("Baseline provider observations are not ordered")
            if (
                stable_hash(
                    {
                        "event_kind": event["event_kind"],
                        "raw": event["raw_json"],
                        "normalized": event["normalized_json"],
                    }
                )
                != event["content_hash"]
            ):
                raise ValueError("Baseline provider observation hash differs")
        if execution["fault_placement_hash"] != placement_hash:
            raise ValueError("Paired execution received a different fault placement")
        timing = execution["timing_evidence"]
        if len(timing["barriers"]) != (2 if conflict else 1):
            raise ValueError("Unexpected durable named barrier count")
        barrier = timing["barriers"][0]
        if (
            barrier["barrier_name"] != case.correction_barrier.value
            or barrier["state"] != "RELEASED"
        ):
            raise ValueError("Named barrier did not reach and release")
        correction_source = execution["pre_correction_receipt_id"] if conflict else expected.target
        if barrier["source_event_id"] != correction_source:
            raise ValueError("Barrier did not observe the scheduled source event")
        fault_barrier = timing["barriers"][1] if conflict else barrier
        if conflict and (
            fault_barrier["barrier_name"] != "P2"
            or fault_barrier["source_event_id"] != expected.target
            or fault_barrier["state"] != "RELEASED"
            or datetime.fromisoformat(fault_barrier["reached_at"])
            < datetime.fromisoformat(execution["correction_scripted_at"])
        ):
            raise ValueError("Provider conflict lacks its second-request barrier")
        expected_faults = 0 if expected.fault is FaultFamily.NONE else 1
        if len(timing["faults"]) != expected_faults:
            raise ValueError("Fault occurrence count differs from the schedule")
        if expected_faults:
            fault = timing["faults"][0]
            if fault["actual_event_id"] != fault_barrier["id"]:
                raise ValueError("Fault is not linked to its barrier event")
            if fault["scheduled_target"] != {
                key: placement[key] for key in ("barrier", "fault", "request_index", "target")
            }:
                raise ValueError("Injected fault differs from scheduled target")
        result = grade(
            case,
            execution["simulator_truth"],
            [PlaybackAck.model_validate(execution["playback_ack"])]
            if execution["playback_ack"] is not None
            else [],
            datetime.fromisoformat(execution["correction_scripted_at"]),
        )
        if result != execution["oracle_result"]:
            raise ValueError(f"Independent oracle result differs for {execution['arm']}")
        if metric_rows(result) != execution["metrics"]:
            raise ValueError(f"Metric rows differ for {execution['arm']}")
        if "correction_to_outcome_latency" in execution:
            if correction_to_outcome(execution) != execution["correction_to_outcome_latency"]:
                raise ValueError(f"Latency evidence differs for {execution['arm']}")
        rows.append(
            {
                "scenario_key": case.scenario_key,
                "arm": execution["arm"],
                "metrics": {
                    item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                },
            }
        )
    summary = paired_counts(rows, "correction_success")
    if summary != bundle["paired_summary"]:
        raise ValueError("Paired summary differs from metric rows")
    if summary["independent_scenarios"] != bundle["independent_scenario_count"]:
        raise ValueError("Independent scenario count differs from case rows")
    if "latency_summary" in bundle:
        if any("correction_to_outcome_latency" not in item for item in executions):
            raise ValueError("Latency summary lacks execution evidence")
        latency_rows = [
            {
                "scenario_key": case.scenario_key,
                "arm": item["arm"],
                **item["correction_to_outcome_latency"],
            }
            for item in executions
        ]
        expected_latency = {
            arm: paired_latency(latency_rows, "B3", arm)
            for arm in manifest["arms"]
            if "B3" in manifest["arms"] and arm != "B3"
        }
        if expected_latency != bundle["latency_summary"]:
            raise ValueError("Paired latency summary differs from execution evidence")
    return {
        "run_id": bundle["run_id"],
        "bundle_hash": saved_bundle_hash,
        "verified_executions": len(executions),
        "independent_scenarios": summary["independent_scenarios"],
    }


if __name__ == "__main__":
    print(json.dumps(verify_bundle(Path(sys.argv[1])), indent=2))
