"""Read-only historical review and separate proposed sidecars; no campaign admission."""

from __future__ import annotations

import hashlib
import sqlite3
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from controls import Policy, canonical, hash_file, read, write_new  # noqa: E402
from instrument import evidence_for  # noqa: E402
from refusal import recognize  # noqa: E402

from research.study_v4.design import cells  # noqa: E402
from research.study_v4.oracle import revised_evaluate  # noqa: E402


def sidecars() -> None:
    results = []
    for name in ("first", "second"):
        path = HERE / f"retained-{name}-original.json"
        row = read(path)
        raw_hash = hash_file(path)
        proof = recognize(row)
        if proof is None:
            raise ValueError("ORIGINAL_REFUSAL_UNPROVED")
        row["driver_classification"] = proof
        case, old = evidence_for(row, amended=False)
        _, proposed = evidence_for(row)
        anchors = [a.accepted_at for a in old.acceptances if a.revision > 1 and a.accepted_at]
        challenge = max(anchors) if anchors else None
        old_grade, old_row = revised_evaluate(case, old, challenge_at=challenge)
        new_grade, new_row = revised_evaluate(case, proposed, challenge_at=challenge)
        if old_row.values != new_row.values or new_row.values != row["analysis_row"]["values"]:
            raise ValueError("SIDE_CAR_ENDPOINT_CHANGE")
        body = {
            "status": "PROPOSED_FOR_REVIEW_NOT_ACCEPTED_NOT_FROZEN",
            "execution_id": row["execution_id"],
            "arm": row["arm"],
            "attempt": row["attempt"],
            "original_export_sha256": raw_hash,
            "raw_status": row["status"],
            "original_stored_grades": {
                k: row[k]
                for k in ("grades", "revised_grade", "original_instrument_grade")
                if k in row
            },
            "original_stored_analysis": row["analysis_row"],
            "original_instrument_recomputed_grade": old_grade,
            "proposed_classification": proof,
            "proposed_grade": new_grade,
            "proposed_analysis": new_row.model_dump(mode="json"),
            "business_and_speech_outcome_values_unchanged": True,
            "original_export_unchanged": True,
        }
        write_new(HERE / f"{name}-original-proposed-sidecar.json", body)
        results.append(
            {
                "execution_id": row["execution_id"],
                "hash": raw_hash,
                "predicate": proof["predicate_result"],
                "receipt": proof["receipt_id"],
            }
        )
    write_new(HERE / "original-review.json", results)


def recipe_review() -> None:
    qualification = read(REPO / "artifacts/phase-8-study-design/v4/calibration-qualification.json")
    evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for attempt in qualification["all_attempts"]:
        path = REPO / attempt["path"]
        trace = read(path)
        family = trace["input"]["generator_family"]
        proof = recognize(trace) if trace["status"] == "FAILED" else None
        failures = [
            h for h in trace["http"] if isinstance(h.get("status"), int) and h["status"] >= 400
        ]
        verifications = [h for h in trace["http"] if h["path"] == "/internal/phase3/verifications"]
        item = {
            "trace": str(path.relative_to(REPO)),
            "hash": hash_file(path),
            "execution_id": trace["execution_id"],
            "purpose": attempt["purpose"],
            "raw_status": trace["status"],
            "failure_type": trace.get("failure", {}).get("type"),
            "failure_detail": trace.get("failure", {}).get("detail"),
            "last_refusal": failures[-1] if failures else None,
            "last_receipt": verifications[-1]["response"] if verifications else None,
            "candidate_proof": proof,
            "qualification": attempt["qualification"],
        }
        evidence.setdefault((family, attempt["arm"]), []).append(item)
    rows = []
    for index, cell in enumerate(cells(), 1):
        for arm in ("B3", "P1", "P2"):
            rows.append(
                {
                    "cell": index,
                    "recipe": cell["name"],
                    "arm": arm,
                    "stratum": cell["stratum"],
                    "hooks": cell["hooks"],
                    "provider": cell["provider"],
                    "expected_paths": (
                        "Normal completion or independently graded unsuccessful final outcome. "
                        "Planned stale publication/playback conflicts use allow_failure "
                        "and remain evidence. Ambiguous provider sends reconcile before retry. "
                        "Exact negative-evidence refusals require the candidate proof; "
                        "every other raised refusal/timeout/transport defect pauses."
                    ),
                    "driver": (
                        "research/study_v4/calibration.py:run + research/remedies/runner.py:recover"
                    ),
                    "unrecognized_stop_preserved": True,
                    "historical_attempts": evidence.get((cell["name"], arm), []),
                    "new_full_window_runtime_coverage": cell["name"] == "resource-only",
                    "no_claim_all_recipes_newly_runtime_qualified": True,
                }
            )
    if len(rows) != 150 or any(not r["historical_attempts"] for r in rows):
        raise ValueError("INCOMPLETE_50_BY_3_REVIEW")
    write_new(
        HERE / "recipe-review.json",
        {
            "rows": rows,
            "recipes": 50,
            "arm_paths": 150,
            "retained_attempts": len(qualification["all_attempts"]),
            "historical_status_counts": qualification["driver_status_counts"],
            "note": (
                "Older traces lacking request times/verification event journals cannot "
                "acquire a new evidence proof merely from HTTP 409 or a negative receipt. "
                "Historical outcomes unchanged."
            ),
        },
    )


def feasibility() -> None:
    at = datetime.now(UTC)
    policy = Policy(
        scope="CAMPAIGN",
        run_id="p85-01a116f7-3b82-7a79-8653-3aee62dc99e9",
        host_started_at=datetime.fromisoformat("2026-10-07T15:24:23.810674+00:00"),
    )
    rate = (
        policy.compute_usd_hour
        + policy.ipv4_usd_hour
        + policy.volume_gib * policy.disk_usd_gib_month / 730
    )
    fixed = policy.committed_cost(policy.host_started_at) + 1.25
    cost_cutoff = policy.host_started_at + timedelta(hours=(55 - fixed) / rate)
    uri = Path("C:/p8c1/m/x/slot/campaign.sqlite3").as_uri() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(r) for r in db.execute("SELECT * FROM slots ORDER BY sequence")]
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("RETAINED_LEDGER_CORRUPTION")
    states = Counter(r["state"] for r in rows)
    if states != {"BACKED_UP": 2, "PLANNED": 1498}:
        raise ValueError("ORIGINAL_IDENTITY_STATE_CHANGE")
    bindings = read(Path("C:/p8c1/m/x/slot/bindings.json"))
    saved = read(REPO / "artifacts/phase-8-continuation/v1/saved-identities.json")
    # Both files retain the exact original identity objects, including sequence/attempt.
    saved_rows = saved["rows"] if isinstance(saved, dict) and "rows" in saved else saved
    if isinstance(saved_rows, dict):
        saved_rows = saved_rows["identities"]
    if len(saved_rows) != len(rows) or any(
        original["execution_id"] != actual["execution_id"]
        or original["sequence"] != actual["sequence"]
        or original["case_id"] != actual["case_id"]
        or original["arm"] != actual["arm"]
        or original["attempt"] != actual["attempt"]
        for original, actual in zip(saved_rows, rows, strict=True)
    ):
        raise ValueError("ORIGINAL_SAVED_ORDER_DRIFT")
    for binding, row in zip(bindings, rows, strict=True):
        if any(binding[k] != row[k] for k in binding):
            raise ValueError("RETAINED_BINDING_DRIFT")
    estimates = {}
    for label, duration in (
        ("observation_only_lower_bound", 1498 * 600 / 3600),
        ("planning_12_days", 288),
        ("planning_13_days", 312),
    ):
        finish = at + timedelta(hours=duration + 2)
        cost = policy.committed_cost(finish + timedelta(minutes=30)) + 1.25
        estimates[label] = {
            "execution_hours": duration,
            "setup_allowance_hours": 2,
            "finish_utc": finish,
            "committed_usd_with_reserve": cost,
            "fits_55": cost < 55,
            "fits_65": cost <= 65,
            "fits_original_deadline": finish + timedelta(minutes=30) <= policy.stop_at,
            "latest_setup_begin_utc": cost_cutoff - timedelta(hours=duration + 2, minutes=30),
        }
    write_new(
        HERE / "feasibility.json",
        {
            "as_of_utc": at,
            "original_deadline": policy.stop_at,
            "cost_guard_cutoff": cost_cutoff,
            "clock_not_reset": True,
            "limits_not_increased": True,
            "states": dict(states),
            "remaining": 1498,
            "estimates": estimates,
            "next_original": rows[2],
            "bindings_hash": hash_file(Path("C:/p8c1/m/x/slot/bindings.json")),
            "saved_identities_hash": hash_file(
                REPO / "artifacts/phase-8-continuation/v1/saved-identities.json"
            ),
            "current_credits_read": read(HERE / "aws-plan-read.json"),
            "conclusion": (
                "12-day fit is conditional; 13-day conservative allowance already misses $55. "
                "Review delay and deployment readiness consume the unchanged clock."
            ),
            "billing_limits": (
                "Conservative accepted elapsed-clock estimate, not real-time billing; "
                "retained disks/S3 continue costing while compute is stopped."
            ),
        },
    )


def preservation() -> None:
    before = read(HERE / "preservation-before.json")
    drift = [p for p, expected in before.items() if hash_file(Path(p)) != expected]
    write_new(
        HERE / "preservation-after.json",
        {
            "status": "PASS" if not drift else "FAIL",
            "files": len(before),
            "drift": drift,
            "before_manifest_hash": hash_file(HERE / "preservation-before.json"),
            "aggregate_before": hashlib.sha256(canonical(before)).hexdigest(),
            "after": datetime.now(UTC),
        },
    )
    if drift:
        raise ValueError("HISTORICAL_OR_SOURCE_HASH_DRIFT")


if __name__ == "__main__":
    {
        "sidecars": sidecars,
        "recipes": recipe_review,
        "feasibility": feasibility,
        "preservation": preservation,
    }[sys.argv[1]]()
