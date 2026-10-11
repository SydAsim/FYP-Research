"""Scenario scheduling, explicit timing barriers, and independent truth grading."""

import hashlib
import wave
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from apps.api_controller.phase1_models import SyntheticFixtureRequest
from apps.api_controller.phase1_service import DomainProblem, create_fixture
from research.analysis.latency import correction_to_outcome, paired_latency
from research.analysis.metrics import clean_paired_difference, paired_counts
from research.arms import PROFILES, Arm
from research.barriers.control import NamedBarrierController
from research.barriers.schedule import schedule
from research.oracle.grade import PlaybackAck, grade, grade_clean
from research.scenario_dsl.catalog import (
    CAPABILITY_COVERING,
    CLEAN_CASES,
    CONFLICT_COVERING,
    DELAY_COVERING,
    MANDATORY_HIGH_RISK,
    REFUSAL_COVERING,
    SECONDARY_COVERING,
    UNAVAILABLE_COVERING,
    VISIBILITY_COVERING,
    case_for,
)
from research.scenario_dsl.models import (
    Barrier,
    FaultFamily,
    ProviderCapability,
    ProviderVisibility,
)


def test_research_arm_fixture_requires_experiment_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXPERIMENT_MODE", raising=False)
    with pytest.raises(DomainProblem) as denied:
        create_fixture(SyntheticFixtureRequest(command_id=uuid4(), research_arm="P1"))
    assert denied.value.status == 403
    assert denied.value.slug == "experiment-only"


def test_catalog_covers_every_named_phase_and_profiles_are_explicit() -> None:
    cases = (*MANDATORY_HIGH_RISK, *SECONDARY_COVERING)
    assert {case.correction_barrier for case in cases} == set(Barrier)
    assert len({case.scenario_key for case in cases}) == 10
    assert len({case.fixture_hash for case in cases}) == 10
    assert set(PROFILES) == set(Arm)
    assert PROFILES[Arm.B3].playback_tracking
    assert not PROFILES[Arm.B3].claim_permits
    assert PROFILES[Arm.P1].claim_permits
    assert not PROFILES[Arm.P1].durable_played_span_repair
    assert PROFILES[Arm.P2].durable_played_span_repair


def test_provider_capability_case_is_a_distinct_executable_scenario() -> None:
    atomic = MANDATORY_HIGH_RISK[2]
    compensation = CAPABILITY_COVERING[0]
    assert compensation.scenario_key != atomic.scenario_key
    assert compensation.fixture_hash != atomic.fixture_hash
    assert compensation.provider_capability is ProviderCapability.COMPENSATE_CANCEL_CREATE
    assert compensation.action_semantics == "CREATE_THEN_COMPENSATE_CANCEL_THEN_CREATE"
    assert compensation.correction_barrier is Barrier.P3
    assert compensation.fault_family is FaultFamily.RESPONSE_LOSS


def test_delayed_visibility_case_is_distinct_and_requires_two_reads() -> None:
    delayed = VISIBILITY_COVERING[0]
    assert delayed.scenario_key != MANDATORY_HIGH_RISK[2].scenario_key
    assert delayed.fixture_hash != MANDATORY_HIGH_RISK[2].fixture_hash
    assert delayed.visibility is ProviderVisibility.DELAYED_TWO_READS
    assert delayed.visibility.simulator_visibility == "DELAYED"
    assert delayed.visibility.visibility_reads == 2


def test_provider_delay_case_has_distinct_precommit_fault_schedule() -> None:
    delayed = DELAY_COVERING[0]
    assert delayed.fixture_hash != case_for(Barrier.P2).fixture_hash
    assert delayed.fault_family is FaultFamily.DELAY
    assert schedule(delayed).target == "BEFORE_COMMIT:1"
    with pytest.raises(ValidationError, match="Pre-commit provider delay"):
        case_for(Barrier.P3, fault=FaultFamily.DELAY)


def test_provider_refusal_case_has_distinct_precommit_fault_schedule() -> None:
    refusal = REFUSAL_COVERING[0]
    assert refusal.fixture_hash != DELAY_COVERING[0].fixture_hash
    assert refusal.fault_family is FaultFamily.PROVIDER_REFUSAL
    assert schedule(refusal).target == "BEFORE_COMMIT:1"
    with pytest.raises(ValidationError, match="Pre-commit provider refusal"):
        case_for(Barrier.P3, fault=FaultFamily.PROVIDER_REFUSAL)


def test_unavailable_visibility_requires_hidden_commit_case() -> None:
    unavailable = UNAVAILABLE_COVERING[0]
    assert unavailable.visibility.simulator_visibility == "UNAVAILABLE"
    assert unavailable.fixture_hash != VISIBILITY_COVERING[0].fixture_hash
    with pytest.raises(ValidationError, match="Unavailable evidence case"):
        case_for(Barrier.P2, visibility=ProviderVisibility.UNAVAILABLE)
    with pytest.raises(ValidationError, match="Unavailable evidence case"):
        case_for(Barrier.P3, visibility=ProviderVisibility.UNAVAILABLE)


def test_provider_conflict_targets_second_write_after_p5() -> None:
    case = CONFLICT_COVERING[0]
    assert case.action_semantics == "CREATE_THEN_BLOCKED_RESCHEDULE"
    assert schedule(case).request_index == 2
    assert schedule(case).target == "BEFORE_COMMIT:2"
    with pytest.raises(ValidationError, match="Provider conflict requires"):
        case_for(Barrier.P2, fault=FaultFamily.PROVIDER_CONFLICT)


def test_clean_audio_fixture_has_exact_wave_length_and_hash() -> None:
    path = Path(__file__).resolve().parents[2] / "research/fixtures/audio/clean_booking.wav"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == CLEAN_CASES[0].audio_hash
    with wave.open(str(path), "rb") as reader:
        assert reader.getnchannels() == 1
        assert reader.getframerate() == 22050
        assert reader.getnframes() < reader.getframerate() * 10
        frames = reader.readframes(reader.getnframes())
        assert len(frames) == reader.getnframes() * reader.getsampwidth()


def test_fault_schedule_is_stable_and_rejects_wrong_phase() -> None:
    case = case_for(Barrier.P3, fault=FaultFamily.RESPONSE_LOSS)
    first, second = schedule(case), schedule(case)
    assert first.hash == second.hash
    assert first.target == "AFTER_COMMIT_BEFORE_RESPONSE:1"
    assert schedule(case_for(Barrier.P2)).target == "BEFORE_COMMIT:1"
    assert schedule(case_for(Barrier.P4)).target == "AFTER_RESPONSE:1"
    assert schedule(case_for(Barrier.P8, fault=FaultFamily.PARTIAL_PLAYBACK)).target == "P8:1"
    with pytest.raises(ValidationError, match="Post-commit response loss"):
        case_for(Barrier.P2, fault=FaultFamily.RESPONSE_LOSS)


@pytest.mark.parametrize("barrier", list(Barrier))
def test_every_named_barrier_waits_for_explicit_release(barrier: Barrier) -> None:
    events: dict[UUID, str] = {}

    def persist_reach(
        _execution_id: UUID,
        name: str,
        _source_event_id: str,
        _reached_at: datetime,
        *,
        held: bool,
    ) -> UUID:
        assert held
        event_id = uuid4()
        events[event_id] = name
        return event_id

    def persist_release(event_id: UUID) -> None:
        assert event_id in events
        events[event_id] = "released"

    controller = NamedBarrierController(
        uuid4(), {barrier}, persist_reach=persist_reach, persist_release=persist_release
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        reached = pool.submit(controller.reach, barrier, f"source:{barrier.value}")
        event_id = controller.wait_reached(barrier)
        assert not reached.done()
        assert events[event_id] == barrier.value
        controller.release(barrier)
        assert reached.result(timeout=2) == event_id
        assert events[event_id] == "released"
    with pytest.raises(ValueError, match="not held"):
        controller.release(barrier)


def _commit(sequence: int, operation_id: str, time: datetime, start: datetime) -> dict[str, object]:
    return {
        "sequence": sequence,
        "operation_id": operation_id,
        "committed_at": time,
        "after_facts": {
            "appointment_id": "one-appointment",
            "status": "CONFIRMED",
            "starts_at": start.isoformat(),
            "timezone": "Asia/Karachi",
        },
    }


def test_oracle_disagrees_with_a_permitted_claim_when_provider_truth_disagrees() -> None:
    case = case_for(Barrier.P3, fault=FaultFamily.RESPONSE_LOSS)
    base = datetime(2026, 9, 28, 12, tzinfo=UTC)
    truth = [_commit(1, "first", base, case.initial_start)]
    ack = PlaybackAck(
        event_id="misleading",
        claim_type="RESCHEDULED_APPOINTMENT",
        claim_start=case.final_start,
        intent_revision=2,
        released_at=base + timedelta(seconds=2),
        played_at=base + timedelta(seconds=3),
        played_ms=500,
        permit_id=str(uuid4()),
    )
    result = grade(case, truth, [ack], base + timedelta(seconds=1))
    assert not result["correction_success"]
    assert result["unsupported_confirmation"]
    assert result["unsupported_event_ids"] == ["misleading"]
    assert not result["safe_resolution"]


def test_oracle_checks_truth_at_release_and_play() -> None:
    case = case_for(Barrier.P3, fault=FaultFamily.RESPONSE_LOSS)
    base = datetime(2026, 9, 28, 12, tzinfo=UTC)
    truth = [
        _commit(1, "first", base, case.initial_start),
        _commit(2, "second", base + timedelta(seconds=3), case.final_start),
    ]
    ack = PlaybackAck(
        event_id="too-early",
        claim_type="RESCHEDULED_APPOINTMENT",
        claim_start=case.final_start,
        intent_revision=2,
        released_at=base + timedelta(seconds=2),
        played_at=base + timedelta(seconds=4),
        played_ms=500,
    )
    result = grade(case, truth, [ack], base + timedelta(seconds=1))
    assert result["correction_success"]
    assert result["unsupported_confirmation"]


def test_repetitions_do_not_increase_independent_scenario_count() -> None:
    rows = [
        {"scenario_key": "case-1", "arm": arm, "metrics": {"correction_success": 1}}
        for arm in ("B3", "P1", "P2")
        for _ in range(2)
    ]
    summary = paired_counts(rows, "correction_success")
    assert summary["independent_scenarios"] == 1
    assert summary["executions"] == 6
    assert all(item["scenarios"] == 1 for item in summary["by_arm"].values())


def test_correction_latency_censors_silent_arm_at_observation_end() -> None:
    start = datetime(2026, 9, 28, 12, tzinfo=UTC)
    end = start + timedelta(seconds=5)
    base = {
        "correction_scripted_at": start.isoformat(),
        "observation_ended_at": end.isoformat(),
    }
    assert correction_to_outcome({**base, "playback_ack": None}) == {
        "duration_ms": 5000.0,
        "event_observed": False,
        "censored": True,
    }
    assert (
        correction_to_outcome(
            {
                **base,
                "playback_ack": {
                    "played_at": (start + timedelta(seconds=2)).isoformat(),
                    "played_ms": 500,
                },
            }
        )["duration_ms"]
        == 2000.0
    )
    with pytest.raises(ValueError, match="outside"):
        correction_to_outcome(
            {
                **base,
                "playback_ack": {
                    "played_at": (end + timedelta(seconds=1)).isoformat(),
                    "played_ms": 500,
                },
            }
        )


def test_latency_bootstrap_clusters_repetitions_and_reports_censoring() -> None:
    rows = [
        {"scenario_key": "one", "arm": "B3", "duration_ms": 1000, "event_observed": True},
        {"scenario_key": "one", "arm": "B3", "duration_ms": 2000, "event_observed": True},
        {"scenario_key": "one", "arm": "P1", "duration_ms": 2000, "event_observed": True},
        {"scenario_key": "one", "arm": "P1", "duration_ms": 3000, "event_observed": True},
        {"scenario_key": "two", "arm": "B3", "duration_ms": 5000, "event_observed": False},
        {"scenario_key": "two", "arm": "P1", "duration_ms": 3000, "event_observed": True},
    ]
    result = paired_latency(rows, "B3", "P1", bootstrap_draws=100)
    assert result["independent_scenarios"] == 2
    assert result["observed_pairs"] == 1
    assert result["censored_pairs"] == 1
    assert result["mean_difference_ms"] == 1000
    assert result["bootstrap_95_interval_ms"] is None


def test_clean_oracle_requires_provider_truth_and_useful_supported_speech() -> None:
    case = CLEAN_CASES[0]
    start = datetime(2026, 9, 28, 12, tzinfo=UTC)
    truth = [_commit(1, "clean-op", start, case.final_start)]
    truth[0]["action"] = "CREATE"
    silent = grade_clean(case, truth, [])
    assert not silent["clean_task_success"]
    assert silent["safe_resolution"]
    assert not silent["outcome_coverage"]
    ack = PlaybackAck(
        event_id="clean-claim",
        claim_type="CURRENT_APPOINTMENT",
        claim_start=case.final_start,
        intent_revision=1,
        released_at=start + timedelta(seconds=1),
        played_at=start + timedelta(seconds=2),
        played_ms=500,
    )
    assert grade_clean(case, truth, [ack])["clean_task_success"]
    wrong_truth = [_commit(1, "clean-op", start, case.final_start + timedelta(hours=1))]
    wrong_truth[0]["action"] = "CREATE"
    wrong = grade_clean(case, wrong_truth, [ack])
    assert not wrong["clean_task_success"]
    assert wrong["unsupported_confirmation"]


def test_clean_noninferiority_summary_clusters_repetitions_without_a_phase6_decision() -> None:
    rows = [
        {"scenario_key": "one", "arm": arm, "metrics": {"clean_task_success": value}}
        for arm, value in (("B3", 1), ("B3", 1), ("P1", 1), ("P1", 0))
    ]
    summary = clean_paired_difference(rows, "B3", "P1")
    assert summary["independent_scenarios"] == 1
    assert summary["executions"] == 4
    assert summary["risk_difference"] == -0.5
    assert summary["bootstrap_95_interval"] is None
    assert summary["noninferiority_margin"] is None
    assert summary["noninferiority_conclusion"] == "NOT_TESTED_PHASE6"
