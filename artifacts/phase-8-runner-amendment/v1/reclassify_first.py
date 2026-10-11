"""Read-only sidecar of the retained original; no commands or ledger transitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from controls import hash_file, read, utc, write_new
from instrument import evidence_for
from refusal import recognize, timing_eligible

from research.study_v4.oracle import revised_evaluate

HERE = Path(__file__).resolve().parent
EXPECTED_HASH = "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"


def sidecar(destination: Path) -> None:
    source = HERE / "retained-first-original.json"
    if hash_file(source) != EXPECTED_HASH:
        raise ValueError("FIRST_ORIGINAL_HASH_DRIFT")
    row: dict[str, Any] = read(source)
    old_case, old_evidence = evidence_for(row, amended=False)
    accepted = [a.accepted_at for a in old_evidence.acceptances if a.revision > 1 and a.accepted_at]
    challenge = max(accepted) if accepted else None
    original_grade, original_analysis = revised_evaluate(
        old_case, old_evidence, challenge_at=challenge
    )
    if (
        original_grade != row["revised_grade"]
        or original_analysis.model_dump(mode="json") != row["analysis_row"]
    ):
        raise ValueError("ORIGINAL_ORACLE_REPLAY_DRIFT")
    proof = recognize(row)
    if proof is None:
        raise ValueError("FIRST_ORIGINAL_NOT_SPECIFIC_EXPECTED_REFUSAL")
    row["driver_classification"] = proof  # in memory only; raw evidence never overwritten
    if not timing_eligible(row):
        raise ValueError("FIRST_ORIGINAL_OBSERVATION_INCOMPLETE")
    case, evidence = evidence_for(row)
    grade, analysis = revised_evaluate(case, evidence, challenge_at=challenge)
    if (
        original_analysis.values != analysis.values
        or original_analysis.duration_seconds != analysis.duration_seconds
        or original_analysis.event_observed != analysis.event_observed
    ):
        raise ValueError("UNAUTHORIZED_ENDPOINT_OR_TIMING_CHANGE")
    write_new(
        destination,
        {
            "version": "phase85-refusal-amendment-v1",
            "status": "REVIEW_CANDIDATE_ONLY",
            "at": utc(),
            "source": str(source),
            "source_sha256": EXPECTED_HASH,
            "execution_id": row["execution_id"],
            "attempt": 1,
            "raw_status": row["status"],
            "original_grade": original_grade,
            "original_analysis_row": original_analysis.model_dump(mode="json"),
            "proposed_classification": proof,
            "proposed_grade": grade,
            "proposed_analysis_row": analysis.model_dump(mode="json"),
            "outcome_values_identical": True,
            "numeric_timing_identical": True,
            "timing_change": "600s administrative censor NO_SUPPORTED_COMPLETION, not an event",
            "business_correction": "SUCCEEDED_FROM_INDEPENDENT_TRUTH",
            "spoken_confirmation": "NOT_PUBLISHED_OR_DELIVERED_IN_COMPLETE_PROTOCOL_JOURNALS",
            "scope": "SCRIPTED_PROTOCOL_ONLY_NOT_HUMAN_UNDERSTANDING",
            "accepted": False,
            "frozen": False,
            "launch_authorized": False,
            "original_execution_rerun": False,
            "outcome_replaced": False,
        },
    )


if __name__ == "__main__":
    import sys

    sidecar(Path(sys.argv[1]))
