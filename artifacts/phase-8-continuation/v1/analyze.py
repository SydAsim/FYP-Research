"""Read-only authorized originals analysis; missing originals stay in planned denominators."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from controls import Journal, canonical, hash_file, read, write_new
from handover import FIRST, FIRST_HASH, REPO, verify_imported_first
from instrument import analysis, evaluate_trace, evidence_for
from refusal import recognize, timing_eligible
from runner import verify_run

from research.study.models import AnalysisRow, Stratum, StudyCase
from research.study_v4.oracle import revised_evaluate

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
    "corrective_delivery_after_challenge",
    "withdrawal_and_corrective_delivery",
    "complete_corrective_communication",
)


def unavailable(case: StudyCase, slot: dict[str, Any], scope: str, reason: str) -> AnalysisRow:
    import hashlib

    return AnalysisRow(
        classification="CAMPAIGN" if scope == "CAMPAIGN" else "VALIDATION_ONLY",
        case_id=case.case_id,
        cluster_id=case.cluster_id,
        generator_family=case.generator_family,
        stratum=case.stratum,
        member=case.member,
        cluster_representative=case.cluster_representative,
        arm=slot["arm"],
        attempt=1,
        execution_id=slot["execution_id"],
        values={key: "UNKNOWN" for key in ENDPOINTS},
        duration_seconds=None,
        event_observed=None,
        censor_reason=reason,
        oracle_hash=hashlib.sha256(
            canonical({"execution_id": slot["execution_id"], "reason": reason})
        ).hexdigest(),
        phase=case.correction_barrier,
        fault=case.fault_label,
        revision_type="NONE" if case.stratum is Stratum.CLEAN else "PARAMETER_CORRECTION",
        action_class="CREATE"
        if case.stratum is Stratum.CLEAN
        else "CREATE_RESCHEDULE"
        if case.provider.supports_reschedule
        else "CREATE_CANCEL_CREATE",
    )


def imported_first_row(root: Path) -> tuple[AnalysisRow, dict[str, Any]]:
    verify_imported_first(root)
    export = root / "historical/first-slot/executions" / FIRST / "export.json"
    if hash_file(export) != FIRST_HASH:
        raise ValueError("FIRST_ORIGINAL_ANALYSIS_HASH_DRIFT")
    trace = read(export)
    side = read(REPO / "artifacts/phase-8-runner-amendment/v1/first-original-sidecar.json")
    case, old_evidence = evidence_for(trace, amended=False)
    anchors = [a.accepted_at for a in old_evidence.acceptances if a.revision > 1 and a.accepted_at]
    challenge = max(anchors) if anchors else None
    old_grade, old_row = revised_evaluate(case, old_evidence, challenge_at=challenge)
    if (
        old_grade != side["original_grade"]
        or old_row.model_dump(mode="json") != (side["original_analysis_row"])
    ):
        raise ValueError("FIRST_ORIGINAL_ORACLE_REPLAY_DRIFT")
    proof = recognize(trace)
    if proof != side["proposed_classification"]:
        raise ValueError("FIRST_ORIGINAL_CLASSIFICATION_DRIFT")
    trace["driver_classification"] = proof  # In memory only; raw FAILED export is preserved.
    if not timing_eligible(trace):
        raise ValueError("FIRST_ORIGINAL_WINDOW_INCOMPLETE")
    _, new_evidence = evidence_for(trace)
    grade, row = revised_evaluate(case, new_evidence, challenge_at=challenge)
    if (
        grade != side["proposed_grade"]
        or row.model_dump(mode="json") != (side["proposed_analysis_row"])
    ):
        raise ValueError("ACCEPTED_FIRST_SIDECAR_REPLAY_DRIFT")
    return row, {
        "execution_id": FIRST,
        "status": "ORIGINAL_PLUS_VERIFIED_TIMING_SIDECAR",
        "export_hash": FIRST_HASH,
        "raw_status": "FAILED",
        "sidecar_sha256": hash_file(
            REPO / "artifacts/phase-8-runner-amendment/v1/first-original-sidecar.json"
        ),
        "original_analysis_row": old_row.model_dump(mode="json"),
        "replacement_or_driver_replay": False,
    }


def analyze(root: Path, output: Path) -> None:
    authority = verify_run(root, readonly=True)
    cases = {
        key: StudyCase.model_validate(value)
        for key, value in read(root / "run.json")["cases"].items()
    }
    rows, evidence = [], []
    for slot in Journal(root).rows():
        if slot["execution_id"] == FIRST and (root / "handover.json").exists():
            row, provenance = imported_first_row(root)
            rows.append(row)
            evidence.append(provenance)
            continue
        case = cases[slot["case_id"]]
        export = (
            root
            / "slots"
            / f"{slot['sequence']:04d}"
            / "executions"
            / slot["execution_id"]
            / "export.json"
        )
        if not export.is_file():
            rows.append(
                unavailable(
                    case,
                    slot,
                    authority.policy.scope,
                    "ORIGINAL_" + slot["state"] + "_NO_VERIFIED_EXPORT",
                )
            )
            evidence.append({"execution_id": slot["execution_id"], "status": "MISSING_RETAINED"})
            continue
        from research.execution_setup.core import Ledger

        Ledger(export.parents[2]).verify()
        trace = read(export)
        if (
            trace["execution_id"] != slot["execution_id"]
            or trace["arm"] != slot["arm"]
            or trace["attempt"] != 1
            or StudyCase.model_validate(trace["input"]).fixture_hash != slot["fixture_hash"]
        ):
            raise ValueError("ORIGINAL_ANALYSIS_BINDING_DRIFT")
        try:
            _, row = evaluate_trace(trace, authority)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            row = unavailable(case, slot, authority.policy.scope, "ORIGINAL_ORACLE_FAILURE")
            evidence.append(
                {
                    "execution_id": slot["execution_id"],
                    "status": "ORACLE_FAILURE_RETAINED",
                    "type": type(error).__name__,
                }
            )
        else:
            evidence.append(
                {
                    "execution_id": slot["execution_id"],
                    "status": "REPLAYED",
                    "export_hash": hash_file(export),
                }
            )
        rows.append(row)
    # Canonical scientific settings; no partial-study resampling or optional extension.
    report = analysis(list(cases.values()), rows, authority)
    write_new(
        output,
        {
            "planned_originals": len(Journal(root).rows()),
            "rows": [r.model_dump(mode="json") for r in rows],
            "evidence": evidence,
            "analysis": report,
            "diagnostic_reruns_included": False,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("new_output", type=Path)
    arguments = parser.parse_args()
    analyze(arguments.root, arguments.new_output)
