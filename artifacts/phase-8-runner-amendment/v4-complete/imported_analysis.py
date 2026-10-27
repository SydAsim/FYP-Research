"""Two retained originals join unchanged analysis through separately hashed sidecars."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from controls import hash_file, read
from handover import verify_imported_first
from instrument import evidence_for
from refusal import recognize, timing_eligible

from research.study.models import AnalysisRow
from research.study_v4.oracle import revised_evaluate


def imported_row(root: Path, execution_id: str) -> tuple[AnalysisRow, dict[str, Any]]:
    verify_imported_first(root)
    record = read(root / "handover.json")
    closed = next(
        p for p in record["closed_originals"] if p["identity"]["execution_id"] == execution_id
    )
    if closed["identity"]["sequence"] > 2:
        path = (
            root
            / "historical/boundary/exports"
            / f"{closed['identity']['sequence']:04d}"
            / "export.json"
        )
        trace = read(path)
        if hash_file(path) != closed["export_sha256"]:
            raise ValueError("IMPORTED_ORIGINAL_EXPORT_DRIFT")
        return AnalysisRow.model_validate(trace["analysis_row"]), {
            "execution_id": execution_id,
            "raw_status": trace["status"],
            "export_hash": closed["export_sha256"],
            "original_analysis_row": trace["analysis_row"],
            "replacement_or_driver_replay": False,
            "status": "IMMUTABLE_RECORDED_V3_ANALYSIS",
        }
    proof = next(
        p for p in read(root / "handover.json")["originals"] if p["execution_id"] == execution_id
    )
    from handover import FIRST

    label = "first" if execution_id == FIRST else "second"
    export = root / "historical" / (label + "-slot") / "executions" / execution_id / "export.json"
    side_path = root / "historical/timing-sidecars" / (label + "-original-proposed-sidecar.json")
    side, trace = read(side_path), read(export)
    if (
        hash_file(export) != proof["export_sha256"]
        or hash_file(side_path) != proof["sidecar_sha256"]
    ):
        raise ValueError("ORIGINAL_ANALYSIS_HASH_DRIFT")
    if (
        trace["analysis_row"] != side["original_stored_analysis"]
        or trace["revised_grade"] != side["original_stored_grades"]["revised_grade"]
    ):
        raise ValueError("ORIGINAL_GRADES_DRIFT")
    trace["driver_classification"] = recognize(trace)  # memory only; raw FAILED never rewritten
    if trace["driver_classification"] != side["proposed_classification"] or not timing_eligible(
        trace
    ):
        raise ValueError("ORIGINAL_SIDECAR_PROOF_DRIFT")
    case, evidence = evidence_for(trace)
    anchors = [a.accepted_at for a in evidence.acceptances if a.revision > 1 and a.accepted_at]
    grade, row = revised_evaluate(case, evidence, challenge_at=max(anchors))
    if grade != side["proposed_grade"] or row.model_dump(mode="json") != side["proposed_analysis"]:
        raise ValueError("ORIGINAL_SIDECAR_ORACLE_DRIFT")
    return row, {
        "execution_id": execution_id,
        "raw_status": "FAILED",
        "export_hash": hash_file(export),
        "sidecar_sha256": hash_file(side_path),
        "original_analysis_row": side["original_stored_analysis"],
        "replacement_or_driver_replay": False,
        "status": "ORIGINAL_PLUS_REVIEW_TIMING_SIDECAR",
    }
