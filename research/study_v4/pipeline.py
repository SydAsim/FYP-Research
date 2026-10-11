"""Integrated candidate analysis; explicitly refuses main evidence before freeze."""

from typing import Any

from research.study.models import AnalysisRow, Evidence, StudyCase
from research.study_v4.analysis import outcome_report
from research.study_v4.oracle import revised_evaluate


def pipeline(cases: list[StudyCase], evidence: list[Evidence]) -> dict[str, Any]:
    if any(e.classification == "CAMPAIGN" for e in evidence):
        raise ValueError("Candidate v4 has no reviewed freeze; campaign analysis is blocked")
    mapping = {c.case_id: c for c in cases}
    if len(mapping) != len(cases):
        raise ValueError("Duplicate independent input ID")
    rows: list[AnalysisRow] = []
    grades = []
    for e in evidence:
        if e.case_id not in mapping:
            raise ValueError("Evidence is outside the planned input frame")
        anchors = [a.accepted_at for a in e.acceptances if a.revision > 1 and a.accepted_at]
        grade, row = revised_evaluate(
            mapping[e.case_id], e, challenge_at=max(anchors) if anchors else None
        )
        rows.append(row)
        grades.append(grade)
    return {
        "classification": "VALIDATION_ONLY",
        "main_started": False,
        "grades": grades,
        "analysis": outcome_report(cases, rows),
    }
