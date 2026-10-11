"""Paired correction-to-outcome latency with explicit right censoring.

Each scenario is the resampling unit. Repeated executions are averaged within
that scenario and never increase its independent sample count.
"""

import random
from datetime import datetime
from statistics import mean
from typing import Any

LATENCY_ANALYSIS_VERSION = "phase6-correction-latency-v1"


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Latency evidence requires an offset timestamp")
    return parsed


def correction_to_outcome(execution: dict[str, Any]) -> dict[str, Any]:
    """Use client playback for the event; otherwise retain observation censoring."""
    start = _instant(execution["correction_scripted_at"])
    end = _instant(execution["observation_ended_at"])
    if end < start:
        raise ValueError("Observation ended before the correction")
    ack = execution.get("playback_ack")
    observed = ack is not None and int(ack["played_ms"]) > 0
    if observed and ack is not None:
        event = _instant(ack["played_at"])
        if event < start or event > end:
            raise ValueError("Playback lies outside the observation window")
    else:
        event = end
    return {
        "duration_ms": round((event - start).total_seconds() * 1000, 3),
        "event_observed": observed,
        "censored": not observed,
    }


def paired_latency(
    executions: list[dict[str, Any]],
    reference_arm: str,
    comparison_arm: str,
    *,
    bootstrap_draws: int = 2000,
    seed: int = 1,
) -> dict[str, Any]:
    """Bootstrap the comparison-minus-reference mean across scenario clusters.

    Censored scenarios remain counted but are excluded from the observed-only
    latency contrast. This is descriptive; survival analysis is still required
    before making a full resolution-time claim.
    """
    if bootstrap_draws < 1 or reference_arm == comparison_arm:
        raise ValueError("Distinct arms and at least one bootstrap draw are required")
    groups: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in executions:
        arm = str(row["arm"])
        if arm in (reference_arm, comparison_arm):
            groups.setdefault(str(row["scenario_key"]), {}).setdefault(arm, []).append(row)
    matched = {
        key: arms
        for key, arms in groups.items()
        if reference_arm in arms and comparison_arm in arms
    }
    differences: list[float] = []
    censored = 0
    for arms in matched.values():
        reference = arms[reference_arm]
        comparison = arms[comparison_arm]
        if any(not bool(item["event_observed"]) for item in (*reference, *comparison)):
            censored += 1
            continue
        differences.append(
            mean(float(item["duration_ms"]) for item in comparison)
            - mean(float(item["duration_ms"]) for item in reference)
        )
    interval: list[float] | None = None
    estimate: float | None = None
    if differences:
        estimate = mean(differences)
    if len(differences) >= 2:
        rng = random.Random(seed)
        draws = sorted(
            mean(rng.choice(differences) for _ in differences) for _ in range(bootstrap_draws)
        )
        interval = [
            draws[int(0.025 * (bootstrap_draws - 1))],
            draws[int(0.975 * (bootstrap_draws - 1))],
        ]
    return {
        "reference_arm": reference_arm,
        "comparison_arm": comparison_arm,
        "independent_scenarios": len(matched),
        "observed_pairs": len(differences),
        "censored_pairs": censored,
        "mean_difference_ms": estimate,
        "bootstrap_95_interval_ms": interval,
        "interpretation": "observed_pairs_only; censored_pairs_retained_in_counts",
    }
