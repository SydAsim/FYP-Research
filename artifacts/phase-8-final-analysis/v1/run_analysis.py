"""Offline closeout: same pure statistical calls/settings as frozen instrument.analysis.

Reads authenticated retained grades. Does not import a driver, execute an oracle,
contact AWS, change an outcome, or create a new campaign authority.
"""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prepare_dataset import HERE, PACKAGE, SOURCE, canonical, read, sha, source_gate


def save(path: Path, value: object) -> None:
    with path.open("xb") as stream:
        stream.write(canonical(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    source_gate()
    proof = read(HERE / "dataset/verification.json")
    authority = read(HERE / "authority-verification.json")
    if proof["status"] != "PASS_DATASET_NOT_ANALYSIS" or proof["originals"] != 1500:
        raise ValueError("COMPLETE_VERIFIED_DATASET_REQUIRED")
    if authority["status"] != "PASS_OFFLINE_EXISTING_AUTHORITY_BINDINGS":
        raise ValueError("EXISTING_AUTHORITY_VERIFICATION_REQUIRED")
    if (
        proof["source_package_hash"] != authority["package_hash"]
        or authority["package_hash"] != PACKAGE
    ):
        raise ValueError("DATASET_SOURCE_AUTHORITY_MISMATCH")
    row_bytes = (HERE / "dataset/analysis-rows.json").read_bytes()
    record_bytes = (HERE / "dataset/recorded-results.json").read_bytes()
    timing_bytes = (HERE / "dataset/accepted-timing-rows.json").read_bytes()
    if sha(row_bytes) != proof["analysis_rows_sha256"]:
        raise ValueError("ANALYSIS_ROW_DRIFT")
    if sha(record_bytes) != proof["recorded_results_sha256"]:
        raise ValueError("RETAINED_RECORD_DRIFT")
    if sha(timing_bytes) != proof["accepted_timing_rows_sha256"]:
        raise ValueError("ACCEPTED_TIMING_VIEW_DRIFT")
    expected = {
        "numpy": "2.3.5",
        "scipy": "1.16.3",
        "pandas": "2.3.3",
        "statsmodels": "0.14.6",
        "patsy": "1.0.2",
    }
    actual = {name: importlib.metadata.version(name) for name in expected}
    if actual != expected or sys.version_info[:3] != (3, 12, 14):
        raise ValueError("QUALIFIED_ANALYSIS_RUNTIME_REQUIRED")
    sys.path.insert(0, str(SOURCE))
    from research.arms import Arm
    from research.execution_setup.timing import paired_latency
    from research.study.models import AnalysisRow, StudyCase
    from research.study.statistical_models import aft_cluster_bootstrap, lognormal_aft
    from research.study_v4.analysis import outcome_report

    rows = [AnalysisRow.model_validate(row) for row in json.loads(row_bytes)]
    timing_rows = [AnalysisRow.model_validate(row) for row in json.loads(timing_bytes)]
    records = json.loads(record_bytes)
    case_map = {
        key: StudyCase.model_validate(value)
        for key, value in read(HERE / "frozen-cases.json").items()
    }
    cases = list(case_map.values())
    if len(cases) != 500 or len(rows) != 1500 or len({(r.case_id, r.arm) for r in rows}) != 1500:
        raise ValueError("FROZEN_PLANNED_DENOMINATOR_REQUIRED")
    if any(r.attempt != 1 or r.classification != "CAMPAIGN" for r in rows):
        raise ValueError("ORIGINAL_CAMPAIGN_ROWS_ONLY")
    folder = HERE / "analysis"
    folder.mkdir(exist_ok=False)
    started = time.monotonic()
    save(
        folder / "started.json",
        {
            "at": datetime.now(UTC).isoformat(),
            "source_package": PACKAGE,
            "settings": {
                "latency_draws": 2000,
                "latency_seed": 8042051,
                "aft_draws": 1000,
                "aft_seed": 8042052,
                "horizon_seconds": 600,
            },
            "runtime": {"python": sys.version, **actual},
            "analysis_rows_sha256": sha(row_bytes),
            "new_regrading": False,
            "new_historical_timing_sidecar": False,
            "existing_first_two_timing_sidecars_reused_in_separate_view": True,
            "accepted_timing_rows_sha256": sha(timing_bytes),
            "authority_check": (
                "Offline signature/identity/readiness verification of retained authority"
            ),
            "method_binding": (
                "Exact pure calls in frozen instrument.analysis; original row values retained"
            ),
        },
    )
    try:
        outcomes = outcome_report(cases, rows)
        outcomes.update(
            status="AUTHORIZED_MAIN_ANALYSIS", main_started=True, classification="CAMPAIGN"
        )
        save(folder / "outcomes.json", outcomes)
        print(
            "Saved paired outcomes, fixed-frame contrasts, clean gate and secondary family",
            flush=True,
        )
        latency = [
            paired_latency(cases, timing_rows, comparison=a, reference=b, repetitions=2000)
            for a, b in ((Arm.P2, Arm.B3), (Arm.P1, Arm.B3), (Arm.P2, Arm.P1))
        ]
        save(folder / "latency.json", latency)
        # Frozen instrument uses the input ID for resampling, keeping all arm rows together.
        input_rows = [r.model_copy(update={"cluster_id": r.case_id}) for r in timing_rows]
        save(folder / "aft.json", lognormal_aft(input_rows))
        print("Saved latency intervals and AFT fit; starting fixed 1000-draw bootstrap", flush=True)
        save(
            folder / "aft-bootstrap.json",
            aft_cluster_bootstrap(input_rows, draws=1000, seed=8042052),
        )
        endpoint_names = sorted({key for row in rows for key in row.values})
        counts = {
            arm.value: {
                endpoint: dict(
                    Counter(row.values.get(endpoint, "MISSING") for row in rows if row.arm == arm)
                )
                for endpoint in endpoint_names
            }
            for arm in (Arm.B3, Arm.P1, Arm.P2)
        }
        summary: dict[str, Any] = {
            "inputs": 500,
            "originals": 1500,
            "per_arm": {a.value: 500 for a in (Arm.B3, Arm.P1, Arm.P2)},
            "values_by_arm": counts,
            "raw_status": dict(Counter(record["raw_status"] for record in records)),
            "censor_reasons": dict(Counter(str(row.censor_reason) for row in rows)),
            "accepted_view_censor_reasons": dict(
                Counter(str(row.censor_reason) for row in timing_rows)
            ),
            "strata": dict(Counter(case.stratum.value for case in cases)),
            "voice_evidence": dict(
                Counter(str(record.get("voice_evidence")) for record in records)
            ),
            "historical_infrastructure_censor_sequences": [
                record["sequence"]
                for record, row in zip(records, rows, strict=True)
                if row.censor_reason == "INFRASTRUCTURE_FAILURE"
            ],
            "missing_timing_records": sum(row.duration_seconds is None for row in rows),
            "zero_timing_records": sum(row.duration_seconds == 0 for row in rows),
            "seconds": time.monotonic() - started,
            "interpretation": [
                "All planned originals retained; raw FAILED is separate from "
                "business/speech outcomes",
                "Conditional fixed-recipe frame; not a population of voices/providers/domains",
                "No actual intelligible speech or human comprehension claim",
                "Shared revision-only claim-selection limitation is unchanged",
                "Historical raw infrastructure-censor labels are preserved; they are not proof "
                "of independent administrative censoring",
                "First-two previously accepted sidecars are reused in a separate timing view; "
                "their numeric times and outcome values are identical; no new sidecar or regrading",
                "Helper claim-permitted fields and missingness limits remain intact; no "
                "automated novelty/superiority declaration",
            ],
        }
        save(folder / "summary.json", summary)
        with (folder / "original-results.csv").open("x", encoding="utf-8", newline="") as stream:
            columns = [
                "sequence",
                "case_id",
                "arm",
                "attempt",
                "execution_id",
                "raw_status",
                "duration_seconds",
                "event_observed",
                "censor_reason",
                *endpoint_names,
            ]
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for record, row in zip(records, rows, strict=True):
                writer.writerow(
                    {
                        **{key: record[key] for key in columns[:6]},
                        "duration_seconds": row.duration_seconds,
                        "event_observed": row.event_observed,
                        "censor_reason": row.censor_reason,
                        **row.values,
                    }
                )
        save(
            folder / "verification.json",
            {
                "status": "PASS_ANALYSIS_EXECUTED_INTERPRETATION_REVIEW_REQUIRED",
                "files": {
                    path.name: sha(path.read_bytes()) for path in folder.iterdir() if path.is_file()
                },
                "input_rows_still_match": sha((HERE / "dataset/analysis-rows.json").read_bytes())
                == sha(row_bytes),
                "original_grades_changed": False,
                "aws_calls": 0,
                "scenario_executions": 0,
            },
        )
        print(
            json.dumps(
                {
                    "status": "ANALYSIS_SAVED_REQUIRES_REVIEW",
                    "path": str(folder),
                    "seconds": time.monotonic() - started,
                }
            ),
            flush=True,
        )
    except Exception as error:
        save(
            folder / "failure.json",
            {
                "type": type(error).__name__,
                "detail": str(error),
                "seconds": time.monotonic() - started,
            },
        )
        raise


if __name__ == "__main__":
    main()
