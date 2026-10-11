"""Offline historical-trace and artificial-statistical validation, no new app calls."""

import json
import math
import random
from pathlib import Path
from typing import Any

from research.arms import Arm
from research.scenario_dsl.models import stable_hash
from research.study.inputs import materialize
from research.study.models import Acceptance, AnalysisRow, Evidence, Intent, Stratum, StudyCase
from research.study.package import ROOT, write_json
from research.study.pipeline import pipeline
from research.study.statistical_models import (
    aft_cluster_bootstrap,
    design_diagnostics,
    lognormal_aft,
    mixed_binary,
)


def adapt_historical(trace: dict[str, Any]) -> tuple[StudyCase, Evidence]:
    identity = f"validation-historical-{trace['fixture']['id']}"
    base = materialize()[300].model_dump(mode="json")
    targets = trace["targets"]
    base.update(
        {
            "case_id": identity,
            "cluster_id": identity,
            "generator_family": trace["fixture"]["family"],
            "correction_barrier": "HISTORICAL:" + trace["fixture"]["family"],
            "fault_schedule": trace["fixture"]["barriers"],
            "speech_exposure": "HISTORICAL_RECORDED_ACK_PROXY",
            "issue": "HISTORICAL_MAINTENANCE",
            "member": 0,
            "cluster_representative": True,
            "secondary_arms": [],
            "arm_order": ["B3", "P1", "P2"],
            "intents": [
                Intent(
                    revision=t["revision"],
                    start=t["requested_start"],
                    end=t["requested_end"],
                    timezone=t["timezone"],
                    transcript="Historical externally scripted target, validation only",
                ).model_dump(mode="json")
                for t in targets
            ],
        }
    )
    case = StudyCase.model_validate(base)
    revisions = {r["revision"]: r for r in trace["snapshot"]["history"]["revisions"]}
    anchors = []
    for t in targets:
        observed = revisions[t["revision"]]
        actual = observed["desired_state_json"]
        anchors.append(
            Acceptance(
                revision=t["revision"],
                scripted_at=t["scripted_at"],
                accepted_at=observed["accepted_at"],
                actual_start=actual["requested_start"],
                actual_end=actual["requested_end"],
                actual_timezone=actual["timezone"],
            )
        )
    evidence = Evidence.model_validate(
        {
            "classification": "VALIDATION_ONLY",
            "case_id": identity,
            "arm": trace["arm"],
            "attempt": 1,
            "execution_id": "validation-import-" + trace["execution_id"],
            "fixture_hash": case.fixture_hash,
            "started_at": trace["started_at"],
            "ended_at": trace["finished_at"],
            "status": trace["status"],
            "resource_key": trace["fixture_identity"]["resource_key"],
            "acceptances": anchors,
            "truth": trace["snapshot"]["truth"],
            "segments": trace["snapshot"]["segments"],
            "playback": trace["client_playback"],
            "observations": trace["snapshot"]["observations"],
            "truth_complete": True,
            "publication_journal_complete": True,
            "playback_journal_complete": True,
            "independent_truth_source": "SIMULATOR_APPEND_ONLY_ORACLE_EXPORT",
            "raw_trace_hash": trace["trace_hash"],
            "repair_obligations": trace["snapshot"]["obligations"],
            "repair_journal_complete": True,
        }
    )
    return case, evidence


def toy_rows(seed: int = 84006) -> list[AnalysisRow]:
    """Known artificial mechanism, unrelated IDs; not study performance evidence."""
    rng = random.Random(seed)
    rows = []
    for cluster in range(30):
        offset = rng.gauss(0, 0.35)
        for member in range(8):
            for arm in (Arm.B3, Arm.P1, Arm.P2):
                beta = 1.3 if arm is Arm.P2 else 0.4 if arm is Arm.P1 else 0
                outcome = rng.random() < 1 / (1 + math.exp(-(-0.4 + beta + offset)))
                time = math.exp(3 + offset + (0.35 if arm is Arm.P2 else 0) + rng.gauss(0, 0.35))
                horizon = 32.0
                rows.append(
                    AnalysisRow(
                        classification="VALIDATION_ONLY",
                        case_id=f"toy-{cluster}-{member}",
                        cluster_id=f"toy-recipe-{cluster}",
                        generator_family=f"toy-recipe-{cluster}",
                        stratum=Stratum.BOUNDARY,
                        member=member,
                        cluster_representative=member == 0,
                        arm=arm,
                        attempt=1,
                        execution_id=f"toy-{cluster}-{member}-{arm}",
                        values={"correction_success": "TRUE" if outcome else "FALSE"},
                        duration_seconds=min(time, horizon),
                        event_observed=time <= horizon,
                        censor_reason="ADMINISTRATIVE_HORIZON" if time > horizon else None,
                        oracle_hash=stable_hash([seed, cluster, member, arm.value]),
                        phase="P3",
                        fault="HIDDEN_RESPONSE",
                        revision_type="PARAMETER_CORRECTION",
                        action_class="CREATE_RESCHEDULE",
                    )
                )
    return rows


def run() -> dict[str, Any]:
    cases, records, sources, historical_grades = {}, [], [], []
    for path in sorted(Path("artifacts/research-remedies/v2/planned").glob("E?-*.json")):
        trace = json.loads(path.read_text(encoding="utf-8"))
        hashed = dict(trace)
        expected = hashed.pop("trace_hash")
        if stable_hash(hashed) != expected:
            raise ValueError(f"Historical trace changed: {path}")
        case, evidence = adapt_historical(trace)
        cases[case.case_id] = case
        records.append(evidence.model_dump(mode="json"))
        sources.append(
            {
                "path": path.as_posix(),
                "trace_hash": expected,
                "validation_execution_id": evidence.execution_id,
            }
        )
        historical_grades.append(trace["grade"])
    report = pipeline(list(cases.values()), records)
    keys = (
        "correct_final_update",
        "explicit_retraction",
        "incompatible_stale_exposure",
        "unsupported_exposed_claim",
    )
    comparisons: list[dict[str, Any]] = [
        {
            "source": source,
            "same_observable_endpoints": all(old[key] == new["values"][key] for key in keys),
        }
        for source, old, new in zip(sources, historical_grades, report["grades"], strict=True)
    ]
    report["historical_comparisons"] = comparisons
    write_json(ROOT / "validation" / "historical-import.json", report)
    write_json(ROOT / "validation" / "design-matrix.json", design_diagnostics(materialize()))
    rows = toy_rows()
    models: dict[str, Any] = {
        "classification": "ARTIFICIAL_STATISTICAL_VALIDATION_ONLY",
        "rows": len(rows),
        "seed": 84006,
        "known_logit_p2_effect": 1.3,
        "known_log_time_p2_effect": 0.35,
        "mixed": mixed_binary(rows, "correction_success"),
        "extended": mixed_binary(rows, "correction_success", extended=True),
        "aft": lognormal_aft(rows),
        "aft_cluster_sensitivity": aft_cluster_bootstrap(rows, draws=40),
        "campaign_inputs_or_executions": 0,
    }
    write_json(ROOT / "validation" / "artificial-models.json", models)
    write_json(
        ROOT / "validation" / "artificial-rows.json", [r.model_dump(mode="json") for r in rows]
    )
    summary = {
        "historical_traces": len(records),
        "import_errors": len(report["errors"]),
        "observable_matches": sum(c["same_observable_endpoints"] for c in comparisons),
        "scientific_models": {k: models[k]["status"] for k in ("mixed", "extended", "aft")},
        "campaign_executions": 0,
    }
    write_json(ROOT / "validation" / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
