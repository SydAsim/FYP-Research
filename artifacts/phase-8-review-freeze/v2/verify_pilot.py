"""Regrade saved traces only; no driver, admission, cloud API or outcome replacement."""

import argparse
from pathlib import Path

from controls import hash_file, read, write_new
from instrument import analysis, evaluate_trace
from test_controls import calibration

from research.study.models import StudyCase
from research.study_v4.analysis import outcome_report


def verify(pilot: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    records, rows = [], []
    cases: dict[str, StudyCase] = {}
    for path in sorted(pilot.rglob("export.json")):
        trace = read(path)
        grade, row = evaluate_trace(trace)
        if grade != trace["revised_grade"] or row.model_dump(mode="json") != trace["analysis_row"]:
            raise ValueError("ORIGINAL_REPLAY_DRIFT_RETAIN_OUTCOME")
        records.append(
            {
                "trace": str(path.resolve()),
                "sha256": hash_file(path),
                "execution_id": trace["execution_id"],
                "grade": "IDENTICAL",
                "analysis_row": "IDENTICAL",
            }
        )
        case = StudyCase.model_validate(trace["input"])
        if case.case_id in cases and cases[case.case_id].fixture_hash != case.fixture_hash:
            raise ValueError("CASE_HASH_DRIFT")
        cases[case.case_id] = case
        rows.append(row)
    if len(records) != 24:
        raise ValueError("EXACT_RETAINED_PILOT_REQUIRED")
    # Reduced bootstrap draws here qualify plumbing only; main stays 2000/1000.
    _, authority = calibration(output / "control-authority")
    result = analysis(list(cases.values()), rows, authority, draws=20, aft_draws=8)
    original = outcome_report(list(cases.values()), rows)
    assert {
        k: v
        for k, v in result["outcomes"].items()
        if k not in ("status", "main_started", "classification")
    } == {
        k: v for k, v in original.items() if k not in ("status", "main_started", "classification")
    }
    assert all(r.classification == "VALIDATION_ONLY" for r in rows)
    write_new(
        output / "replay.json",
        {
            "classification": "RETAINED_CALIBRATION_READ_ONLY",
            "main_executions": 0,
            "traces": records,
            "count": len(records),
            "analysis_outcomes": "IDENTICAL",
            "analysis_draws_qualification_only": {"latency": 20, "aft": 8},
            "analysis": result,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verify(args.pilot, args.output)
