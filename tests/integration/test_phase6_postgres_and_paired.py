"""PostgreSQL barrier facts and the live paired Phase 6 gate."""

import base64
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from psycopg.errors import RaiseException, UniqueViolation

from apps.api_controller.phase1_service import DomainProblem
from apps.api_controller.phase4_audio_service import segment_audio
from apps.api_controller.phase6_b3_audio import (
    B3AudioRequest,
    publish_b3,
    stage_b3,
    synthesis_input,
)
from research.barriers.schedule import schedule
from research.oracle.p8_witness import grade_p8_witness
from research.oracle.playout_witness import grade_playout
from research.replay.phase4_p8 import run as run_phase4_p8
from research.replay.phase6_p8_witness import run_witness, verify_witness, witness_case
from research.replay.verify_clean_paired import verify_clean_bundle
from research.replay.verify_p8_paired import verify_p8_paired
from research.replay.verify_phase6 import verify_bundle
from research.replay.verify_playout_paired import verify_playout_paired
from research.run_store import (
    connection,
    create_case,
    create_execution,
    create_run,
    record_barrier,
    release_barrier,
)
from research.runner.clean_paired import run_clean_paired
from research.runner.p8_paired import run_p8_paired
from research.runner.paired import ALL_ARMS, run_paired
from research.runner.playout_paired import playout_case, run_playout_paired
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
from research.scenario_dsl.models import Barrier, stable_hash


def test_barrier_reach_and_release_are_durable_and_unique() -> None:
    case = MANDATORY_HIGH_RISK[2]
    run_id, manifest_hash, manifest = create_run({"name": "phase6-barrier-test"}, "test")
    assert manifest_hash
    assert manifest["run_id"] == str(run_id)
    case_id = create_case(run_id, case, schedule(case).__dict__)
    execution_id = create_execution(run_id, case_id, "B3", 1)
    event_id = None
    try:
        event_id = record_barrier(
            execution_id, "P3", f"test:{uuid4()}", datetime.now(UTC), held=True
        )
        with connection() as conn:
            state = conn.execute(
                "SELECT state,reached_at,released_at FROM research_barrier_events WHERE id=%s",
                (event_id,),
            ).fetchone()
        assert state is not None
        assert state["state"] == "REACHED"
        assert state["released_at"] is None
        release_barrier(event_id)
        with connection() as conn:
            released = conn.execute(
                "SELECT state,released_at FROM research_barrier_events WHERE id=%s",
                (event_id,),
            ).fetchone()
        assert released is not None
        assert released["state"] == "RELEASED"
        assert released["released_at"] is not None
        with pytest.raises(ValueError, match="not held"):
            release_barrier(event_id)
        with pytest.raises(UniqueViolation):
            record_barrier(execution_id, "P3", f"test:{uuid4()}", datetime.now(UTC))
    finally:
        with connection() as conn:
            conn.execute(
                "DELETE FROM research_barrier_events WHERE execution_id=%s", (execution_id,)
            )
            conn.execute("DELETE FROM executions WHERE id=%s", (execution_id,))
            conn.execute("DELETE FROM scenario_cases WHERE id=%s", (case_id,))
            conn.execute("DELETE FROM evaluation_runs WHERE id=%s", (run_id,))


def test_same_p3_fault_runs_in_b3_p1_p2_and_replays_offline(tmp_path: Path) -> None:
    outcome = run_paired(output_dir=tmp_path)
    bundle_path = Path(outcome["bundle_path"])
    verified = verify_bundle(bundle_path)
    assert verified["verified_executions"] == 3
    assert verified["independent_scenarios"] == 1
    assert outcome["paired_summary"]["independent_scenarios"] == 1
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    executions = {item["arm"]: item for item in bundle["executions"]}
    assert len({item["fault_placement_hash"] for item in executions.values()}) == 1
    assert executions["B3"]["permit_id"] is None
    assert executions["P1"]["permit_id"] is not None
    assert executions["P2"]["permit_id"] is not None
    assert all(item["oracle_result"]["correction_success"] for item in executions.values())
    assert not any(
        item["oracle_result"]["unsupported_confirmation"] for item in executions.values()
    )


def test_p0_preaccept_correction_has_one_final_intent_create(tmp_path: Path) -> None:
    outcome = run_paired(case_for(Barrier.P0), output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert execution["pre_accept_history"]["current_revision"] == 0
        assert execution["pre_accept_history"]["operations"] == []
        assert execution["accepted_correction"]["revision"] == 1
        assert [item["action"] for item in execution["simulator_truth"]] == ["CREATE"]
        assert execution["oracle_result"]["correction_success"]
    changed = deepcopy(bundle)
    changed["executions"][0]["pre_accept_history"]["current_revision"] = 1
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="P0 accepted"):
        verify_bundle(path)


def test_p3_live_baselines_share_fault_and_keep_raw_provider_events(tmp_path: Path) -> None:
    outcome = run_paired(arms=ALL_ARMS, output_dir=tmp_path)
    bundle = json.loads(Path(outcome["bundle_path"]).read_text(encoding="utf-8"))
    assert verify_bundle(Path(outcome["bundle_path"]))["verified_executions"] == 6
    executions = {item["arm"]: item for item in bundle["executions"]}
    assert len({item["fault_placement_hash"] for item in executions.values()}) == 1
    assert all(executions[arm]["baseline_events"] for arm in ("B0", "B1", "B2"))
    assert all(
        executions[arm]["baseline_events"][0]["event_kind"] == "REQUEST_SENT"
        for arm in ("B0", "B1", "B2")
    )
    assert not executions["B0"]["oracle_result"]["correction_success"]
    assert not executions["B0"]["oracle_result"]["unsupported_confirmation"]
    assert not executions["B0"]["oracle_result"]["outcome_coverage"]
    assert executions["B0"]["playback_ack"] is None
    assert len(executions["B0"]["simulator_truth"]) == 1
    assert [event["event_kind"] for event in executions["B0"]["baseline_events"]] == [
        "REQUEST_SENT",
        "PROVIDER_RESPONSE",
        "UNRESOLVED_STOP",
    ]
    assert executions["B1"]["oracle_result"]["correction_success"]
    assert executions["B2"]["oracle_result"]["correction_success"]
    assert all(executions[arm]["oracle_result"]["correction_success"] for arm in ("B3", "P1", "P2"))
    assert executions["B0"]["correction_to_outcome_latency"]["censored"]
    assert bundle["latency_summary"]["B0"]["censored_pairs"] == 1
    assert bundle["latency_summary"]["B0"]["mean_difference_ms"] is None
    assert bundle["latency_summary"]["P2"]["bootstrap_95_interval_ms"] is None
    changed = deepcopy(bundle)
    changed["executions"][0]["correction_to_outcome_latency"]["duration_ms"] += 1
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-latency.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Latency evidence"):
        verify_bundle(tampered)


def test_non_atomic_provider_uses_compensation_in_all_paired_arms(tmp_path: Path) -> None:
    outcome = run_paired(CAPABILITY_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert [item["action"] for item in execution["simulator_truth"]] == [
            "CREATE",
            "CANCEL",
            "CREATE",
        ]
        assert execution["oracle_result"]["correction_success"]
        assert len(execution["oracle_result"]["active_final_truth"]) == 1
    changed = deepcopy(bundle)
    changed["executions"][0]["simulator_truth"][1]["action"] = "RESCHEDULE"
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-compensation.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="compensation path"):
        verify_bundle(tampered)


def test_delayed_visibility_reconciles_unknown_without_duplicate_write(tmp_path: Path) -> None:
    outcome = run_paired(VISIBILITY_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert [item["action"] for item in execution["simulator_truth"]] == [
            "CREATE",
            "RESCHEDULE",
        ]
        assert execution["oracle_result"]["correction_success"]
        assert sum(step.get("outcome") == "UNKNOWN" for step in execution["worker_steps"]) >= 2
    changed = deepcopy(bundle)
    first = changed["executions"][0]
    original = next(
        item
        for item in first["provider_evidence"]
        if item["operation"]["id"] == first["first_operation_id"]
    )
    lookup = next(item for item in original["attempts"] if item["attempt_type"] == "STATUS_LOOKUP")
    lookup["normalized_result_json"]["outcome"] = "PRESENT"
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-visibility.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Delayed visibility"):
        verify_bundle(tampered)


def test_provider_delay_holds_first_commit_until_after_correction(tmp_path: Path) -> None:
    outcome = run_paired(DELAY_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        evidence = execution["provider_delay_evidence"]
        assert evidence["held_barrier"]["state"] == "REACHED"
        assert evidence["truth_while_held"] == []
        assert evidence["released_barrier"]["state"] == "RELEASED"
        assert [row["action"] for row in execution["simulator_truth"]] == [
            "CREATE",
            "RESCHEDULE",
        ]
        assert execution["oracle_result"]["correction_success"]
    changed = deepcopy(bundle)
    changed["executions"][0]["provider_delay_evidence"]["truth_while_held"] = [
        changed["executions"][0]["simulator_truth"][0]
    ]
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-provider-delay.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Provider delay"):
        verify_bundle(tampered)


def test_provider_refusal_reconciles_absence_before_corrected_create(tmp_path: Path) -> None:
    outcome = run_paired(REFUSAL_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        evidence = execution["provider_refusal_evidence"]
        assert evidence["truth_after_refusal"] == []
        assert [row["action"] for row in execution["simulator_truth"]] == ["CREATE"]
        assert execution["oracle_result"]["correction_success"]
        first = next(
            item
            for item in execution["provider_evidence"]
            if item["operation"]["id"] == execution["first_operation_id"]
        )
        writes = [item for item in first["attempts"] if item["attempt_type"] == "WRITE"]
        assert len(writes) == 1
        assert writes[0]["raw_response_json"]["status"] == 503
    changed = deepcopy(bundle)
    first = next(
        item
        for item in changed["executions"][0]["provider_evidence"]
        if item["operation"]["id"] == changed["executions"][0]["first_operation_id"]
    )
    lookup = next(item for item in first["attempts"] if item["attempt_type"] == "STATUS_LOOKUP")
    lookup["normalized_result_json"]["authoritative"] = False
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-provider-refusal.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Provider refusal"):
        verify_bundle(tampered)


def test_unavailable_provider_evidence_hands_off_without_retry_or_claim(tmp_path: Path) -> None:
    outcome = run_paired(UNAVAILABLE_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert not execution["oracle_result"]["correction_success"]
        assert not execution["oracle_result"]["unsupported_confirmation"]
        assert not execution["oracle_result"]["safe_resolution"]
        assert execution["playback_ack"] is None
        assert execution["correction_to_outcome_latency"]["censored"]
        assert len(execution["simulator_truth"]) == 1
        assert execution["unavailable_evidence"]["claim_denial"]["status"] == 409
        with connection() as conn:
            durable = conn.execute(
                "SELECT w.resolution_status,o.effect_knowledge FROM workflows w "
                "JOIN operations o ON o.workflow_id=w.id WHERE w.id=%s",
                (execution["workflow_id"],),
            ).fetchone()
        assert durable is not None
        assert durable == {"resolution_status": "HANDOFF", "effect_knowledge": "UNKNOWN"}
    for tamper in ("authoritative-absence", "claim-authorized", "hidden-extra-write"):
        changed = deepcopy(bundle)
        execution = changed["executions"][0]
        if tamper == "authoritative-absence":
            lookup = next(
                item
                for item in execution["provider_evidence"][0]["attempts"]
                if item["attempt_type"] == "STATUS_LOOKUP"
            )
            lookup["normalized_result_json"] = {"outcome": "ABSENT", "authoritative": True}
        elif tamper == "claim-authorized":
            execution["unavailable_evidence"]["claim_denial"]["status"] = 201
        else:
            execution["simulator_truth"].append(deepcopy(execution["simulator_truth"][0]))
        changed["bundle_hash"] = stable_hash(
            {key: value for key, value in changed.items() if key != "bundle_hash"}
        )
        tampered = tmp_path / f"tampered-unavailable-{tamper}.json"
        tampered.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="Unavailable evidence"):
            verify_bundle(tampered)


def test_provider_version_conflict_preserves_other_writer_and_hands_off(tmp_path: Path) -> None:
    outcome = run_paired(CONFLICT_COVERING[0], output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert not execution["oracle_result"]["correction_success"]
        assert not execution["oracle_result"]["unsupported_confirmation"]
        assert execution["playback_ack"] is None
        assert [item["action"] for item in execution["simulator_truth"]] == [
            "CREATE",
            "CONCURRENT_CHANGE",
        ]
        current = next(
            detail
            for detail in execution["provider_evidence"]
            if detail["operation"]["id"] == execution["current_operation_id"]
        )
        assert current["operation"]["effect_knowledge"] == "ABSENT"
        assert len(execution["timing_evidence"]["barriers"]) == 2
    for tamper in ("lost-absence", "overwrite-version", "wrong-fault-event"):
        changed = deepcopy(bundle)
        execution = changed["executions"][0]
        if tamper == "lost-absence":
            current = next(
                detail
                for detail in execution["provider_evidence"]
                if detail["operation"]["id"] == execution["current_operation_id"]
            )
            current["operation"]["effect_knowledge"] = "UNKNOWN"
        elif tamper == "overwrite-version":
            execution["simulator_truth"][-1]["after_facts"]["version"] = 0
        else:
            execution["timing_evidence"]["faults"][0]["actual_event_id"] = execution[
                "timing_evidence"
            ]["barriers"][0]["id"]
        changed["bundle_hash"] = stable_hash(
            {key: value for key, value in changed.items() if key != "bundle_hash"}
        )
        tampered = tmp_path / f"tampered-conflict-{tamper}.json"
        tampered.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ValueError, match="Provider conflict|Fault is not linked"):
            verify_bundle(tampered)


def test_clean_task_is_paired_and_regrades_from_provider_truth(tmp_path: Path) -> None:
    outcome = run_clean_paired(output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_clean_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["paired_summary"]["independent_scenarios"] == 1
    assert bundle["noninferiority_descriptive"]["P1"]["risk_difference"] == 0
    assert bundle["noninferiority_descriptive"]["P1"]["noninferiority_conclusion"] == (
        "NOT_TESTED_PHASE6"
    )
    for execution in bundle["executions"]:
        assert [item["action"] for item in execution["simulator_truth"]] == ["CREATE"]
        assert execution["oracle_result"]["clean_task_success"]
        assert "clean_task_success" in {item["metric_name"] for item in execution["metrics"]}
    changed = deepcopy(bundle)
    changed["executions"][0]["simulator_truth"][0]["after_facts"]["starts_at"] = (
        "2026-11-05T16:00:00+05:00"
    )
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    tampered = tmp_path / "tampered-clean.json"
    tampered.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Clean independent oracle"):
        verify_clean_bundle(tampered)


def test_p8_live_p2_witness_regrades_without_controller_repair_state(tmp_path: Path) -> None:
    outcome = run_witness(tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_witness(path)["played_span_repair_complete"]
    bundle = json.loads(path.read_text(encoding="utf-8"))
    trace = bundle["trace"]
    case = witness_case()
    assert grade_p8_witness(trace, case)["played_span_repair_complete"]

    controller_only = deepcopy(trace)
    controller_only["repair_played"]["state"] = "OPEN"
    assert grade_p8_witness(controller_only, case) == bundle["oracle_result"]

    missing_frames = deepcopy(trace)
    for event in missing_frames["client_playback_evidence"]:
        if event["request"]["event_type"] == "COMPLETED":
            event["request"]["last_frame"] -= 1
    assert not grade_p8_witness(missing_frames, case)["played_span_repair_complete"]

    wrong_truth = deepcopy(trace)
    wrong_truth["simulator_truth_log"][-1]["after_facts"]["starts_at"] = (
        case.initial_start.isoformat()
    )
    assert not grade_p8_witness(wrong_truth, case)["correction_success"]


def test_p8_b3_p1_p2_live_ablation_uses_same_client_fault(tmp_path: Path) -> None:
    outcome = run_p8_paired(tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_p8_paired(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    arms = {item["arm"]: item for item in bundle["executions"]}
    assert len({item["fault_placement_hash"] for item in arms.values()}) == 1
    assert arms["B3"]["oracle_result"]["correction_success"]
    assert not arms["B3"]["oracle_result"]["played_span_repair_complete"]
    assert arms["B3"]["trace"]["first_claim"]["permit"] is None
    assert arms["B3"]["trace"]["corrected_claim"]["permit"] is None
    assert arms["B3"]["trace"]["corrected_segment"]["research_unpermitted"]
    assert arms["P1"]["oracle_result"]["correction_success"]
    assert arms["P2"]["oracle_result"]["correction_success"]
    assert not arms["P1"]["oracle_result"]["played_span_repair_complete"]
    assert arms["P2"]["oracle_result"]["played_span_repair_complete"]
    assert arms["P1"]["trace"]["repair_played"] is None
    assert arms["P2"]["trace"]["repair_played"]["state"] == "REPAIR_PLAYED"
    assert not any(
        event["event_name"] == "RepairRequired"
        for event in arms["P1"]["trace"]["normalized_timeline"]
    )
    assert any(
        event["event_name"] == "RepairRequired"
        for event in arms["P2"]["trace"]["normalized_timeline"]
    )
    changed = deepcopy(bundle)
    changed["executions"][0]["trace"]["simulator_truth_log"][-1]["after_facts"]["starts_at"] = (
        witness_case().initial_start.isoformat()
    )
    changed_body = {key: value for key, value in changed.items() if key != "bundle_hash"}
    changed["bundle_hash"] = stable_hash(changed_body)
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="oracle"):
        verify_p8_paired(path)


def test_postgres_rejects_unpermitted_outcome_on_non_b3_workflow() -> None:
    with connection() as conn:
        segment = conn.execute(
            "SELECT s.id FROM audio_segments s JOIN workflows w ON w.id=s.workflow_id "
            "WHERE w.research_arm='P1' AND s.segment_class='OUTCOME' LIMIT 1"
        ).fetchone()
        assert segment is not None
        with pytest.raises(RaiseException, match="B3 research workflow"):
            conn.execute(
                "UPDATE audio_segments SET claim_id=NULL,claim_permit_id=NULL,"
                "research_unpermitted=true WHERE id=%s",
                (segment["id"],),
            )


def test_b3_audio_command_replay_stale_revision_and_experiment_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = run_phase4_p8(research_arm="B3")
    workflow_id = trace["workflow_id"]
    segment_id = trace["corrected_claim"]["scheduled"]["segment_id"]
    with connection() as conn:
        row = conn.execute(
            "SELECT s.audio_data,s.audio_hash,s.content_hash,s.tts_model_id,s.tts_config_hash,"
            "r.command_id FROM audio_segments s JOIN command_receipts r "
            "ON r.workflow_id=s.workflow_id AND r.command_type='publish_b3_audio' "
            "AND r.response_json->>'segment_id'=s.id::text WHERE s.id=%s",
            (segment_id,),
        ).fetchone()
    assert row is not None
    with pytest.raises(DomainProblem, match="Baseline audio is not live-playable"):
        segment_audio(segment_id)
    body = B3AudioRequest(
        command_id=row["command_id"],
        workflow_id=workflow_id,
        expected_intent_revision=2,
        audio_base64=base64.b64encode(row["audio_data"]).decode("ascii"),
        audio_hash=row["audio_hash"],
        text_hash=row["content_hash"],
        tts_model_id=row["tts_model_id"],
        tts_config_hash=row["tts_config_hash"],
    )
    monkeypatch.setenv("EXPERIMENT_MODE", "true")
    assert publish_b3(body, "replay-test")["segment_id"] == segment_id
    with pytest.raises(DomainProblem, match="Command ID was reused"):
        publish_b3(body.model_copy(update={"audio_hash": "0" * 64}), "duplicate-test")
    with pytest.raises(DomainProblem, match="No current B3 research revision"):
        synthesis_input(body.workflow_id, 1)
    monkeypatch.setenv("EXPERIMENT_MODE", "false")
    with pytest.raises(DomainProblem, match="Unavailable"):
        publish_b3(body, "disabled-test")


def test_b3_generated_audio_stage_replays_and_cannot_publish_after_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace = run_phase4_p8(research_arm="B3", boundary=Barrier.P6)
    workflow_id = trace["workflow_id"]
    segment_id = trace["first_claim"]["scheduled"]["segment_id"]
    with connection() as conn:
        row = conn.execute(
            "SELECT s.audio_data,s.audio_hash,s.content_hash,s.tts_model_id,s.tts_config_hash,"
            "r.command_id FROM audio_segments s JOIN command_receipts r "
            "ON r.workflow_id=s.workflow_id AND r.command_type='stage_b3_audio' "
            "AND r.response_json->>'segment_id'=s.id::text WHERE s.id=%s",
            (segment_id,),
        ).fetchone()
    assert row is not None
    body = B3AudioRequest(
        command_id=row["command_id"],
        workflow_id=workflow_id,
        expected_intent_revision=1,
        audio_base64=base64.b64encode(row["audio_data"]).decode("ascii"),
        audio_hash=row["audio_hash"],
        text_hash=row["content_hash"],
        tts_model_id=row["tts_model_id"],
        tts_config_hash=row["tts_config_hash"],
    )
    monkeypatch.setenv("EXPERIMENT_MODE", "true")
    assert stage_b3(body, "replay-test")["state"] == "GENERATED"
    with pytest.raises(DomainProblem, match="Command ID was reused"):
        stage_b3(body.model_copy(update={"audio_hash": "0" * 64}), "duplicate-test")
    with pytest.raises(DomainProblem, match="No current B3 research revision"):
        stage_b3(body.model_copy(update={"command_id": uuid4()}), "stale-test")
    monkeypatch.setenv("EXPERIMENT_MODE", "false")
    with pytest.raises(DomainProblem, match="Unavailable"):
        stage_b3(body, "disabled-test")


@pytest.mark.parametrize("boundary", [Barrier.P6, Barrier.P7, Barrier.P9])
def test_p6_p7_p9_live_playout_pairs_use_client_truth(boundary: Barrier, tmp_path: Path) -> None:
    outcome = run_playout_paired(boundary, tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_playout_paired(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    arms = {item["arm"]: item for item in bundle["executions"]}
    assert len({item["fault_placement_hash"] for item in arms.values()}) == 1
    assert all(item["oracle_result"]["correction_success"] for item in arms.values())
    if boundary in (Barrier.P6, Barrier.P7):
        assert all(item["oracle_result"]["safe_resolution"] for item in arms.values())
        if boundary is Barrier.P6:
            assert all(
                item["trace"]["first_claim"]["scheduled"]["state"] == "GENERATED"
                for item in arms.values()
            )
            assert all(
                item["trace"]["stale_segment"]["published_at"] is None for item in arms.values()
            )
        changed = deepcopy(arms["P2"]["trace"])
        stale_event = deepcopy(changed["client_playback_evidence"][0])
        stale_event["request"]["segment_id"] = changed["first_claim"]["scheduled"]["segment_id"]
        changed["client_playback_evidence"].append(stale_event)
        with pytest.raises(ValueError, match="stale audio has a client acknowledgement"):
            grade_playout(changed, playout_case(boundary))
    else:
        assert not arms["B3"]["oracle_result"]["safe_resolution"]
        assert not arms["P1"]["oracle_result"]["safe_resolution"]
        assert arms["P2"]["oracle_result"]["played_span_repair_complete"]
        changed = deepcopy(arms["P2"]["trace"])
        changed["repair_played"]["state"] = "OPEN"
        assert grade_playout(changed, playout_case(boundary)) == arms["P2"]["oracle_result"]
        changed["research_arm"] = "P1"
        assert grade_playout(changed, playout_case(boundary)) == arms["P2"]["oracle_result"]
    changed_bundle = deepcopy(bundle)
    changed_bundle["executions"][0]["trace"]["simulator_truth_log"][-1]["after_facts"][
        "starts_at"
    ] = playout_case(boundary).initial_start.isoformat()
    changed_bundle["bundle_hash"] = stable_hash(
        {key: value for key, value in changed_bundle.items() if key != "bundle_hash"}
    )
    path.write_text(json.dumps(changed_bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="oracle"):
        verify_playout_paired(path)


@pytest.mark.parametrize("phase", [Barrier.P1, Barrier.P2, Barrier.P4, Barrier.P5])
def test_named_correction_boundaries_replay_offline(phase: Barrier, tmp_path: Path) -> None:
    outcome = run_paired(case_for(phase), output_dir=tmp_path)
    bundle = json.loads(Path(outcome["bundle_path"]).read_text(encoding="utf-8"))
    assert verify_bundle(Path(outcome["bundle_path"]))["verified_executions"] == 3
    assert {item["arm"] for item in bundle["executions"]} == {"B3", "P1", "P2"}
    assert all(item["oracle_result"]["correction_success"] for item in bundle["executions"])
    assert all(item["fault_occurrence_id"] is None for item in bundle["executions"])
    assert all(
        item["timing_evidence"]["barriers"][0]["barrier_name"] == phase.value
        for item in bundle["executions"]
    )
    if phase is Barrier.P1:
        assert all(item["first_operation_id"] is None for item in bundle["executions"])
        assert all(len(item["simulator_truth"]) == 1 for item in bundle["executions"])
    else:
        assert all(item["first_operation_id"] is not None for item in bundle["executions"])
        assert all(len(item["simulator_truth"]) == 2 for item in bundle["executions"])
    if phase is Barrier.P5:
        assert all(item["pre_correction_receipt_id"] for item in bundle["executions"])
