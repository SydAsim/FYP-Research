"""Design and revised-instrument properties, without executing a campaign input."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from research.arms import Arm
from research.study.analysis import (
    analyze,
    clean_tolerance,
    cluster_difference,
    holm,
    kaplan_meier,
    paired,
    paired_latency,
)
from research.study.campaign import CampaignBlocked, require_reviewed_freeze
from research.study.inputs import materialize
from research.study.models import AnalysisRow, Evidence, Stratum, StudyCase
from research.study.oracle import evaluate
from research.study.pipeline import pipeline
from research.study.validation import adapt_historical


@pytest.fixture
def historic() -> tuple[StudyCase, Evidence]:
    path = next(Path("artifacts/research-remedies/v2/planned").glob("E1-B3-*.json"))
    return adapt_historical(json.loads(path.read_text(encoding="utf-8")))


def row(
    case: StudyCase, arm: Arm, value: str, endpoint: str = "correction_success", **changes: Any
) -> AnalysisRow:
    body = dict(
        classification="VALIDATION_ONLY",
        case_id=case.case_id,
        cluster_id=case.cluster_id,
        generator_family=case.generator_family,
        stratum=case.stratum,
        member=case.member,
        cluster_representative=case.cluster_representative,
        arm=arm,
        attempt=1,
        execution_id=f"validation-{case.case_id}-{arm}",
        values={endpoint: value},
        duration_seconds=None,
        event_observed=None,
        censor_reason="MISSING_TIME",
        oracle_hash="validation",
        phase=case.correction_barrier,
        fault=case.fault_label,
        revision_type="NONE" if case.stratum is Stratum.CLEAN else "PARAMETER_CORRECTION",
        action_class="CREATE",
    )
    body.update(changes)
    return AnalysisRow.model_validate(body)


def test_catalogue_semantic_uniqueness_and_pairing() -> None:
    cases = materialize()
    assert [c.fixture_hash for c in cases] == [c.fixture_hash for c in materialize()]
    assert Counter(c.stratum for c in cases) == {
        Stratum.CLEAN: 100,
        Stratum.AMBIGUITY: 200,
        Stratum.EXPOSURE: 100,
        Stratum.BOUNDARY: 100,
    }
    assert len({c.semantic_hash for c in cases}) == 500
    assert len({c.cluster_id for c in cases}) == 50
    assert sum(c.cluster_representative for c in cases) == 50
    assert sum(len(c.arm_order) for c in cases) == 2700
    assert all(c.speaker_id is None and c.recording_id is None for c in cases)
    changed = cases[0].model_copy(update={"case_id": "renamed"})
    assert changed.semantic_hash == cases[0].semantic_hash


@pytest.mark.parametrize("arm", [Arm.B3, Arm.P1, Arm.P2])
def test_external_equivalence_not_arm_label(historic: tuple[StudyCase, Evidence], arm: Arm) -> None:
    case, original = historic
    evidence = original.model_copy(deep=True, update={"arm": arm})
    for segment in evidence.segments:
        segment.update(claim_permit_id="arbitrary", receipt_result="VIOLATED", research_arm=arm)
    assert evaluate(case, evidence)[0]["values"] == evaluate(case, original)[0]["values"]


def test_missing_ack_and_missing_truth_are_unknown(historic: tuple[StudyCase, Evidence]) -> None:
    case, original = historic
    no_ack = original.model_copy(update={"playback": []})
    grade, _ = evaluate(case, no_ack)
    assert grade["values"]["correct_final_update"] == "UNKNOWN"
    incomplete = original.model_copy(update={"truth_complete": False})
    grade, _ = evaluate(case, incomplete)
    assert grade["values"]["final_business_state_correct"] == "UNKNOWN"
    assert grade["values"]["correction_success"] == "UNKNOWN"


def test_external_final_request_cannot_be_replaced_by_wrong_accepted_intent(
    historic: tuple[StudyCase, Evidence],
) -> None:
    case, original = historic
    changed = original.model_copy(deep=True)
    changed.acceptances[-1].actual_start = case.intents[0].start
    assert evaluate(case, changed)[0]["values"]["intent_acceptance_correct"] == "FALSE"
    changed.acceptances.pop()
    grade, result = evaluate(case, changed)
    assert grade["values"]["correct_final_update"] == "UNKNOWN"
    assert result.duration_seconds is None


def test_duplicate_effect_and_unbound_identity(historic: tuple[StudyCase, Evidence]) -> None:
    case, original = historic
    changed = original.model_copy(deep=True)
    copied = deepcopy(changed.truth[-1])
    copied["sequence"] += 1000
    changed.truth.append(copied)
    assert evaluate(case, changed)[0]["values"]["forbidden_effect"] == "TRUE"
    changed = original.model_copy(deep=True)
    for commit in changed.truth:
        commit.pop("operation_id")
    assert evaluate(case, changed)[0]["values"]["forbidden_effect"] == "UNKNOWN"


def test_invalid_evidence_is_retained_unknown(historic: tuple[StudyCase, Evidence]) -> None:
    case, evidence = historic
    raw = evidence.model_dump(mode="json")
    raw["playback"][0]["request"]["client_time"] = "2100-01-01T00:00:00Z"
    result = pipeline([case], [raw])
    assert len(result["errors"]) == 1
    assert result["rows"][0]["values"]["correction_success"] == "UNKNOWN"
    assert result["errors"][0]["raw_record"] == raw
    assert result["analysis"]["co_primary"][0]["planned_n"] == 1


@pytest.mark.parametrize(
    "manifest",
    [
        {"status": "DRAFT"},
        {"status": "REVIEWED_FROZEN"},
        {
            "status": "REVIEWED_FROZEN",
            "review_receipt": "fake",
            "freeze_hash": "fake",
            "unresolved_decisions": [],
        },
    ],
)
def test_campaign_guard_never_starts(manifest: dict[str, Any]) -> None:
    with pytest.raises(CampaignBlocked):
        require_reviewed_freeze(manifest)


def test_campaign_ingestion_rejected(historic: tuple[StudyCase, Evidence]) -> None:
    case, evidence = historic
    with pytest.raises(ValueError, match="Campaign ingestion disabled"):
        pipeline([case], [evidence.model_dump(mode="json") | {"classification": "CAMPAIGN"}])


def test_exact_mcnemar_and_unknown_bounds() -> None:
    cases = [c for c in materialize()[100:300] if c.cluster_representative][:4]
    rows = [row(c, a, "FALSE" if a is Arm.B3 else "TRUE") for c in cases for a in (Arm.B3, Arm.P2)]
    table = paired(cases, rows, "correction_success")
    assert table["exact_mcnemar_p"] == pytest.approx(0.125)
    assert table["risk_difference"] == 1
    assert paired(cases, rows[:-1], "correction_success")[
        "planned_denominator_difference_bounds"
    ] == [0.75, 1]
    assert holm([0.01, 0.04]) == pytest.approx([0.02, 0.04])
    assert holm([0.01, None]) == [None, None]


def test_clean_tolerance_cannot_use_100_tasks_as_100_independent_units() -> None:
    cases = materialize()[:100]
    rows = [row(c, a, "TRUE", "clean_task_success") for c in cases for a in (Arm.B3, Arm.P2)]
    result = clean_tolerance(cases, rows)
    assert result["table"]["n"] == 10
    assert not result["criterion_on_complete_known_pairs"]
    assert result["known_pair_bound"] == pytest.approx(-0.3084971078)
    assert result["best_case_minimum_independent_clean_units"] == 72
    assert not result["claim_permitted"]


def test_cluster_missingness_and_structural_arm_exclusion() -> None:
    cases = materialize()[300:320]
    rows = [row(c, a, "TRUE") for c in cases for a in (Arm.B3, Arm.P2)]
    result = cluster_difference(cases, rows[:-1], "correction_success", draws=40)
    assert result["planned_clusters"] == 2
    assert result["incomplete_clusters"] == 1
    assert paired(cases, [], "correction_success", Arm.B0)["planned_n"] == 0


def test_later_attempt_cannot_replace_failure_and_duplicate_primary_rejected() -> None:
    case = materialize()[100]
    rows = [
        row(case, Arm.B3, "TRUE"),
        row(case, Arm.P2, "FALSE"),
        row(case, Arm.P2, "TRUE", attempt=2),
    ]
    assert paired([case], rows, "correction_success")["reference_only"] == 1
    with pytest.raises(ValueError, match="Duplicate primary"):
        analyze([case], rows + [rows[1]])


def test_km_right_censoring_ties_and_unknown_tail() -> None:
    case = materialize()[100]
    rows = [
        row(
            case,
            Arm.B3,
            "TRUE",
            duration_seconds=t,
            event_observed=e,
            censor_reason=None if e else "TIMEOUT",
        )
        for t, e in ((2.0, True), (2.0, False), (4.0, True))
    ]
    result = kaplan_meier(rows, tau=6)
    assert result["points"][0]["at_risk"] == 3
    assert result["points"][0]["survival"] == pytest.approx(2 / 3)
    assert result["rmst_seconds"] == pytest.approx(10 / 3)
    censored = [
        row(
            case,
            Arm.B3,
            "UNKNOWN",
            duration_seconds=2.0,
            event_observed=False,
            censor_reason="ACK_MISSING",
        )
    ]
    assert kaplan_meier(censored, tau=6)["rmst_seconds"] is None


def test_fixture_binding_and_catalogue_validation(historic: tuple[StudyCase, Evidence]) -> None:
    case, evidence = historic
    with pytest.raises(ValueError, match="exact externally"):
        evaluate(case, evidence.model_copy(update={"fixture_hash": "other"}))
    with pytest.raises(ValueError, match="input catalogue"):
        analyze([case], [row(case, Arm.P2, "TRUE", cluster_id="unrelated")])


def test_missing_acceptance_payload_is_unknown(historic: tuple[StudyCase, Evidence]) -> None:
    case, evidence = historic
    evidence.acceptances[-1].actual_start = None
    assert evaluate(case, evidence)[0]["values"]["intent_acceptance_correct"] == "UNKNOWN"


def test_paired_latency_keeps_censored_and_missing_denominators() -> None:
    cases = materialize()[100:120]
    rows = [
        row(
            c,
            a,
            "TRUE",
            duration_seconds=10.0 if a is Arm.B3 else 12.0,
            event_observed=True,
            censor_reason=None,
        )
        for c in cases
        for a in (Arm.B3, Arm.P2)
    ]
    rows[-1] = rows[-1].model_copy(update={"event_observed": False, "censor_reason": "TIMEOUT"})
    result = paired_latency(cases, rows, draws=50)
    assert result["planned_pairs"] == 20
    assert result["completed_pairs"] == 19
    assert result["incomplete_or_censored_pairs"] == 1
    assert result["cluster_bootstrap_95"] == [2.0, 2.0]
    assert not result["claim_permitted"]


def test_all_18_historical_traces_pass_new_adapter() -> None:
    count = 0
    for path in Path("artifacts/research-remedies/v2/planned").glob("E?-*.json"):
        trace = json.loads(path.read_text(encoding="utf-8"))
        case, evidence = adapt_historical(trace)
        grade, _ = evaluate(case, evidence)
        for key in (
            "correct_final_update",
            "explicit_retraction",
            "incompatible_stale_exposure",
            "unsupported_exposed_claim",
        ):
            assert grade["values"][key] == trace["grade"][key]
        count += 1
    assert count == 18


def test_repair_telemetry_cannot_assume_delivery_from_database_state() -> None:
    path = next(Path("artifacts/research-remedies/v2/planned").glob("E4-P2-*.json"))
    case, evidence = adapt_historical(json.loads(path.read_text(encoding="utf-8")))
    result, _ = evaluate(case, evidence)
    assert result["repair_mechanism"]["completed_with_playback_evidence"] == 1
    evidence.playback = []
    result, _ = evaluate(case, evidence)
    assert result["repair_mechanism"]["completed_with_playback_evidence"] == 0
    assert result["repair_mechanism"]["completion_unknown"] == 1
    assert evidence.repair_obligations is not None
    evidence.repair_obligations[0]["state"] = "OPEN"
    result, _ = evaluate(case, evidence)
    assert result["repair_mechanism"]["completion_unknown"] == 1
    assert result["repair_mechanism"]["pending_or_escalated"] == 1
