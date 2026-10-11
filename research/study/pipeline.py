"""Offline planned-input -> independent observable grade -> analysis integration."""

from typing import Any

from pydantic import ValidationError

from research.scenario_dsl.models import stable_hash
from research.study.analysis import analyze
from research.study.models import AnalysisRow, Evidence, StudyCase
from research.study.oracle import ORACLE_VERSION, evaluate

ENDPOINTS = (
    "final_business_state_correct",
    "forbidden_effect",
    "intent_acceptance_correct",
    "correction_success",
    "correct_final_update",
    "explicit_retraction",
    "unsupported_exposed_claim",
    "incompatible_stale_exposure",
    "clean_task_success",
)


def pipeline(cases: list[StudyCase], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validation only. Campaign ingestion needs a separate reviewed frozen manifest.

    A malformed but identifiable slot becomes UNKNOWN and an error is retained.
    Unidentifiable records are retained in errors; planned slots remain missing.
    Integrity errors block inference, never an exclusion that improves an arm's grade.
    """
    if any(r.get("classification") != "VALIDATION_ONLY" for r in records):
        raise ValueError(
            "Campaign ingestion disabled until review, freeze and driver qualification"
        )
    catalogue = {c.case_id: c for c in cases}
    if len(catalogue) != len(cases):
        raise ValueError("Duplicate input identity")
    rows: list[AnalysisRow] = []
    grades, errors = [], []
    for raw in records:
        case = catalogue.get(str(raw.get("case_id")))
        try:
            if case is None:
                raise ValueError("Record not in supplied input catalogue")
            evidence = Evidence.model_validate(raw)
            grade, row = evaluate(case, evidence)
            grades.append(grade)
            rows.append(row)
        except (ValidationError, ValueError, KeyError, TypeError, OverflowError) as error:
            record_hash = stable_hash(raw)
            diagnostic = {
                "record_hash": record_hash,
                "case_id": raw.get("case_id"),
                "execution_id": raw.get("execution_id"),
                "exception": type(error).__name__,
                "detail": str(error),
                "raw_record": raw,
            }
            errors.append(diagnostic)
            # Parse the outer record separately to avoid inventing missing identifiers.
            if case is not None:
                try:
                    outer = Evidence.model_validate(raw)
                except ValidationError:
                    continue
                if outer.arm not in case.arm_order:
                    continue
                rows.append(
                    AnalysisRow(
                        classification="VALIDATION_ONLY",
                        case_id=case.case_id,
                        cluster_id=case.cluster_id,
                        generator_family=case.generator_family,
                        stratum=case.stratum,
                        member=case.member,
                        cluster_representative=case.cluster_representative,
                        arm=outer.arm,
                        attempt=outer.attempt,
                        execution_id=outer.execution_id,
                        values=dict.fromkeys(ENDPOINTS, "UNKNOWN"),
                        duration_seconds=None,
                        event_observed=None,
                        censor_reason="EVIDENCE_INVALID",
                        oracle_hash=stable_hash(diagnostic),
                        phase=case.correction_barrier,
                        fault=case.fault_label,
                        revision_type="NONE" if len(case.intents) == 1 else "PARAMETER_CORRECTION",
                        action_class="CREATE"
                        if len(case.intents) == 1
                        else "CREATE_RESCHEDULE"
                        if case.provider.supports_reschedule
                        else "CREATE_CANCEL_CREATE",
                    )
                )
    analysis = analyze(cases, rows)
    return {
        "classification": "VALIDATION_ONLY",
        "oracle_version": ORACLE_VERSION,
        "grades": grades,
        "rows": [r.model_dump(mode="json") for r in rows],
        "errors": errors,
        "analysis": analysis,
        "phase8_started": False,
        "valid_for_campaign": False,
    }
