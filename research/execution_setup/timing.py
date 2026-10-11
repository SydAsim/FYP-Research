"""Paired latency intervals retaining input clusters, censoring and missingness."""

import random
from collections import defaultdict
from statistics import mean
from typing import Any

from research.arms import Arm
from research.study.models import AnalysisRow, StudyCase
from research.study.statistical_models import aft_cluster_bootstrap, lognormal_aft


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    i = int(position)
    return ordered[i] + (ordered[min(i + 1, len(ordered) - 1)] - ordered[i]) * (position - i)


def paired_latency(
    cases: list[StudyCase],
    rows: list[AnalysisRow],
    *,
    comparison: Arm = Arm.P2,
    reference: Arm = Arm.B3,
    repetitions: int = 2000,
    seed: int = 8042051,
) -> dict[str, Any]:
    """Input draws are clusters; recipe IDs are NOT resampling clusters in v4.

    The restricted outcome is time to recorded supported completion, capped at 600s.
    An administrative censor is not a successful completion or a claim of silence.
    Missing evidence remains missing; no complete-case primary interval is substituted.
    """
    index: dict[tuple[str, Arm], AnalysisRow] = {}
    for row in rows:
        if row.attempt != 1:
            continue
        key = row.case_id, row.arm
        if key in index:
            raise ValueError("Duplicate original timing row")
        index[key] = row
    grouped: dict[str, list[float]] = defaultdict(list)
    complete: dict[str, list[float]] = defaultdict(list)
    missing = []
    censored = 0
    for case in cases:
        pair = [index.get((case.case_id, arm)) for arm in (reference, comparison)]
        if any(r is None or r.duration_seconds is None or r.event_observed is None for r in pair):
            missing.append(case.case_id)
            continue
        a, b = pair
        assert a is not None and b is not None
        assert a.duration_seconds is not None and b.duration_seconds is not None
        # An early interrupted collection is missing, not a 600s administrative censor.
        if any(not r.event_observed and float(r.duration_seconds or 0) < 600 for r in (a, b)):
            missing.append(case.case_id)
            continue
        da = min(a.duration_seconds, 600) if a.event_observed else 600
        db = min(b.duration_seconds, 600) if b.event_observed else 600
        grouped[case.stratum.value].append(db - da)
        censored += int(not a.event_observed) + int(not b.event_observed)
        if a.event_observed and b.event_observed:
            complete[case.stratum.value].append(b.duration_seconds - a.duration_seconds)
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[case.stratum.value] += 1
    weights = {key: count / len(cases) for key, count in counts.items()} if cases else {}
    known_sum = sum(sum(v) for v in grouped.values())
    bounds = (
        [
            (known_sum - 600 * len(missing)) / len(cases),
            (known_sum + 600 * len(missing)) / len(cases),
        ]
        if cases
        else None
    )
    result: dict[str, Any] = {
        "method": "STRATIFIED_PAIRED_INPUT_CLUSTER_PERCENTILE_BOOTSTRAP",
        "comparison": f"{comparison}-{reference}",
        "unit": "Independent context input draw",
        "scope": "Time to supported SCRIPTED_ACK completion; restricted at 600 seconds",
        "planned_inputs": len(cases),
        "missing_input_ids": missing,
        "censored_arm_records": censored,
        "missingness_bounds_seconds": bounds,
        "completed_pair_counts_by_stratum": {k: len(v) for k, v in complete.items()},
        "completed_only_mean_differences": {k: mean(v) for k, v in complete.items()},
        "seed": seed,
        "bootstrap_repetitions": repetitions,
        "concurrent_schedule_qualified": False,
    }
    if missing or not grouped or set(grouped) != set(weights):
        return {**result, "status": "UNRESOLVED_MISSING_PAIRED_EVIDENCE", "interval_95": None}
    rng = random.Random(seed)
    samples = [
        sum(weights[k] * mean(rng.choices(v, k=len(v))) for k, v in grouped.items())
        for _ in range(repetitions)
    ]
    return {
        **result,
        "status": "ESTIMATED_CONDITIONAL_ON_INDEPENDENT_INPUTS",
        "restricted_mean_difference_seconds": sum(weights[k] * mean(v) for k, v in grouped.items()),
        "interval_95": [quantile(samples, 0.025), quantile(samples, 0.975)],
        "dependence_limitation": "Shared host/time dependence requires block sensitivity; "
        "no independence proof",
    }


def timing_report(
    cases: list[StudyCase],
    rows: list[AnalysisRow],
    *,
    repetitions: int = 2000,
    aft_repetitions: int = 1000,
) -> dict[str, Any]:
    if any(r.classification == "CAMPAIGN" for r in rows):
        raise ValueError("Main analysis remains guarded until reviewed freeze")
    # Existing identifiable lognormal arm+stratum AFT; replace legacy recipe cluster
    # with the actual independent input ID. Bootstrap retains all arms per draw.
    input_rows = [r.model_copy(update={"cluster_id": r.case_id}) for r in rows if r.attempt == 1]
    fit = lognormal_aft(input_rows)
    aft = aft_cluster_bootstrap(input_rows, draws=aft_repetitions, seed=8042052)
    return {
        "classification": "VALIDATION_ONLY",
        "main_started": False,
        "latency": [
            paired_latency(cases, rows, comparison=a, reference=b, repetitions=repetitions)
            for a, b in ((Arm.P2, Arm.B3), (Arm.P1, Arm.B3), (Arm.P2, Arm.P1))
        ],
        "aft": fit,
        "aft_input_cluster_bootstrap": aft,
        "scope_amendment": "Retain required clustered latency and censored AFT; "
        "supersedes descriptive-only proposal",
    }
