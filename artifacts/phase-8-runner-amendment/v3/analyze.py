"""Read-only authorized originals analysis; missing originals stay in planned denominators."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from controls import Journal, canonical, hash_file, read, write_new
from handover import FIRST
from instrument import analysis, evaluate_trace
from runner import verify_run

from research.study.models import AnalysisRow, Stratum, StudyCase

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
    from imported_analysis import imported_row

    return imported_row(root, FIRST)


def analyze(root: Path, output: Path) -> None:
    authority = verify_run(root, readonly=True)
    cases = {
        key: StudyCase.model_validate(value)
        for key, value in read(root / "run.json")["cases"].items()
    }
    rows, evidence = [], []
    for slot in Journal(root).rows():
        if (
            slot["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")
            and (root / "handover.json").exists()
        ):
            from imported_analysis import imported_row

            row, provenance = imported_row(root, slot["execution_id"])
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
