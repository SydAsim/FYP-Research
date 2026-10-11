"""Assemble review evidence without writing any historical artifact or main outcome."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from research.remedies.runner import now
from research.study.package import write_json
from research.study_v4.design import ROOT, materialize
from research.study_v4.oracle import adapt_calibration, revised_evaluate
from research.study_v4.runtime import DATABASE


def assemble() -> dict[str, Any]:
    qualification = json.loads(
        (ROOT / "calibration-qualification.json").read_text(encoding="utf-8")
    )
    covered = {
        (e["case_id"], e["arm"])
        for e in qualification["all_attempts"]
        if e["qualification"]["status"] == "QUALIFIED_BOUNDARY"
    }
    expected = {(c.case_id, a.value) for c in materialize(calibration=True) for a in c.primary_arms}
    budget_results = []
    for result in (ROOT / "budget-calibration").glob("*/results.json"):
        budget_results.extend(json.loads(result.read_text(encoding="utf-8")))
    for result in (ROOT / "barrier-calibration").glob("*/results.json"):
        budget_results.append(json.loads(result.read_text(encoding="utf-8")))
    window_evidence = []
    for path in (ROOT / "window-calibration").glob("*/cal-v4-0039-*.json"):
        trace = json.loads(path.read_text(encoding="utf-8"))
        for window in trace.get("observation_windows", []):
            if "elapsed_seconds" in window:
                seconds = window["budget_seconds"]
                budget_results.append(
                    {
                        "budget": "recovery" if seconds == 40 else "observation",
                        "seconds": seconds,
                        "elapsed_seconds": window["elapsed_seconds"],
                        "qualified": seconds <= window["elapsed_seconds"] < seconds + 5,
                        "path": str(path),
                        "outcome": window["outcome"],
                        "scope": "Live PG polling with missing consumer/completion ACK",
                    }
                )
        if trace.get("finished_at"):
            case, evidence = adapt_calibration(trace)
            anchor = evidence.acceptances[-1].accepted_at
            grade, _ = revised_evaluate(case, evidence, challenge_at=anchor)
            window_evidence.append(
                {
                    "path": str(path),
                    "values": grade["values"],
                    "administrative_cap": grade["evidence_hash"],
                }
            )
    with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
        exhausted = conn.execute(
            "SELECT j.*,o.workflow_id FROM reconciliation_jobs j "
            "JOIN operations o ON o.id=j.operation_id WHERE j.job_type='RECONCILE_OPERATION' "
            "AND j.state='HANDOFF' AND j.attempt_count=j.max_attempts AND j.max_attempts=8"
        ).fetchall()
    write_json(
        ROOT / "reconciliation-budget-evidence.json", json.loads(json.dumps(exhausted, default=str))
    )
    budget_results.append(
        {
            "budget": "reconcile",
            "attempts": 8,
            "qualified": bool(exhausted),
            "path": str(ROOT / "reconciliation-budget-evidence.json"),
            "scope": "Real PG exhaustion transitions; no completion inferred",
        }
    )
    budget_results.append(
        {
            "budget": "drain_passes",
            "passes": 30,
            "qualified": True,
            "scope": "Artificial nonprogressing adapter boundary, not a PG transaction test",
            "path": "tests/unit/test_phase8_candidate_v4.py",
            "test": "test_nonprogressing_drain_has_a_bounded_budget",
        }
    )
    write_json(
        ROOT / "budget-qualification.json",
        {
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "budgets": budget_results,
            "window_evidence": window_evidence,
            "main_started": False,
            "qualification_is_scope_specific": True,
        },
    )
    decisions = {
        "status": "PROPOSED_FOR_REVIEW_NOT_FROZEN",
        "written_at": now(),
        "sampling_frame": "Fixed 50-recipe generator with independent context draws within stratum",
        "estimand": "Standardized protocol risk difference, not caller-population performance",
        "independent_unit": "Input draw; arm pair shares input, never increases n",
        "clusters": "Fixed recipe labels and temporal batches; no speaker/recording replication",
        "allocation": {"CLEAN": 300, "HIDDEN_COMMIT": 100, "PLAYOUT": 60, "OTHER_BOUNDARY": 40},
        "arms": ["B3", "P1", "P2"],
        "six_arm_extension_requires_review": True,
        "clean_margin": 0.05,
        "clean_power_assumptions": "Equal risks, <=5% discordance; not pilot estimates",
        "models": "Arm × eligible stratum: correction rank9, hidden rank3, clean rank3",
        "primary_family": "Bonferroni for two co-primary claims; clean gate separately required",
        "corrective_delivery": "Ordinary supported baseline updates receive equal credit",
        "comparison_limit": "Baseline response opportunity versus native P2 repair discovery",
        "speech_limit": "Scripted tones/ACKs, no claim of hearing or comprehension",
        "redis_limit": "Reserved companion-cache flush only; application Redis outage is untested",
        "reorder_limit": "One held ACK crosses revision acceptance; no two-response permutation",
        "budget_limit": "Polling can finish later; grades truncate to external request plus 600s",
        "worst_sequential_observation_hours": 1500 * 600 / 3600,
        "review_required": [
            "Conditional frame and stationarity assumptions",
            "Three-arm comparison scope",
            "5pp clean margin and nuisance sensitivity",
            "Primary/secondary multiplicity rules",
            "Recovery responder opportunities and limits on unattended comparative claims",
            "Observation scheduling, temporal-batch sensitivity and total compute/storage budget",
        ],
        "unattended_comparative_delivery_proven": False,
        "review_receipt": None,
        "freeze_hash": None,
        "main_executions": 0,
    }
    write_json(ROOT / "review-decisions.json", decisions)
    before = json.loads((ROOT / "historical-hashes-before.json").read_text(encoding="utf-8"))
    after = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
    changed = [p for p in before if before[p] != after[p]]
    historical_roots = [
        Path(p)
        for p in (
            "artifacts/phase-7-pilot/v1",
            "artifacts/research-remedies/v2",
            "artifacts/phase-8-study-design/v3",
            "research/fixtures/phase8_design_v3",
        )
    ]
    added = [
        p.as_posix()
        for root in historical_roots
        for p in root.rglob("*")
        if p.is_file() and p.as_posix() not in before
    ]
    write_json(ROOT / "historical-hashes-after.json", after)
    write_json(
        ROOT / "preservation-verification.json",
        {
            "files": len(before),
            "changed": changed,
            "added": added,
            "unchanged": not changed and not added,
        },
    )
    if changed or added:
        raise ValueError("Historical evidence changed: " + str(changed + added))
    slots = json.loads((ROOT / "main-slots.json").read_text(encoding="utf-8"))
    assert len(slots) == 1500 and all(
        s["status"] == "NOT_STARTED" and s["execution_id"] is None for s in slots
    )
    main = materialize()
    write_json(
        ROOT / "readiness-summary.json",
        {
            "verdict": "REVIEWABLE_CANDIDATE_NOT_FROZEN",
            "main_started": False,
            "qualified_boundary_slots": len(covered),
            "boundary_slots": len(expected),
            "remaining_boundary_slots": sorted(expected - covered),
            "all_attempts": len(qualification["all_attempts"]),
            "calibration_statuses": qualification["driver_status_counts"],
            "calibration_oracle_invalid": qualification["oracle_invalid"],
            "qualified_budget_names": sorted(
                {b["budget"] for b in budget_results if b["qualified"]}
            ),
            "recovery_main_inputs": sum(
                c.generator_family
                in {
                    "partial-time",
                    "full-before-correction",
                    "late-decisive-ack",
                    "restart-before-repair",
                    "reconnect-third-revision",
                }
                for c in main
            ),
            "allocation": dict(Counter(c.stratum.value for c in main)),
            "historical_files_unchanged": len(before),
            "review_required": decisions["review_required"],
        },
    )
    return {
        "qualified_boundaries": len(covered),
        "historical_unchanged": len(before),
        "main_executions": 0,
        "verdict": "REVIEWABLE_CANDIDATE_NOT_FROZEN",
    }


if __name__ == "__main__":
    print(assemble())
