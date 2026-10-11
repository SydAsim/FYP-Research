"""Exact paired counts and conservative paired non-inferiority bounds."""

import math
from typing import Any

from research.scenario_dsl.models import stable_hash

VERSION = "phase7-analysis-v1"


def binomial_cdf(k: int, n: int, probability: float) -> float:
    if not 0 <= probability <= 1 or not 0 <= n:
        raise ValueError("Invalid binomial parameters")
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if probability == 0:
        return 1.0
    if probability == 1:
        return 0.0
    return min(
        1.0,
        math.fsum(
            math.exp(
                math.lgamma(n + 1)
                - math.lgamma(i + 1)
                - math.lgamma(n - i + 1)
                + i * math.log(probability)
                + (n - i) * math.log1p(-probability)
            )
            for i in range(k + 1)
        ),
    )


def _root(k: int, n: int, target: float) -> float:
    left, right = 0.0, 1.0
    for _ in range(60):
        middle = (left + right) / 2
        if binomial_cdf(k, n, middle) > target:
            left = middle
        else:
            right = middle
    return (left + right) / 2


def exact_interval(successes: int, n: int, alpha: float = 0.05) -> list[float] | None:
    if not 0 <= successes <= n or not 0 < alpha < 1:
        raise ValueError("Invalid count or confidence level")
    if not n:
        return None
    return [
        0.0 if successes == 0 else _root(successes - 1, n, 1 - alpha / 2),
        1.0 if successes == n else _root(successes, n, alpha / 2),
    ]


def paired_table(
    rows: list[dict[str, Any]], endpoint: str, reference: str, arm: str
) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for row in rows:
        if row["variant"] != "PRIMARY" or row["arm"] not in (reference, arm):
            continue
        value = row["values"].get(endpoint)
        if value is None:
            continue
        by_arm = grouped.setdefault(row["scenario_id"], {})
        if row["arm"] in by_arm:
            raise ValueError("A repetition cannot become a second primary observation")
        by_arm[row["arm"]] = int(value)
    cells = {"both_one": 0, "reference_only": 0, "comparison_only": 0, "both_zero": 0}
    for values in grouped.values():
        if reference not in values or arm not in values:
            continue
        key = (
            "both_one"
            if values[reference] and values[arm]
            else "reference_only"
            if values[reference]
            else "comparison_only"
            if values[arm]
            else "both_zero"
        )
        cells[key] += 1
    n = sum(cells.values())
    discordant = cells["reference_only"] + cells["comparison_only"]
    return {
        "reference_arm": reference,
        "comparison_arm": arm,
        "endpoint": endpoint,
        "n": n,
        **cells,
        "discordant": discordant,
        "discordance_estimate": discordant / n if n else None,
        "discordance_exact_95_interval": exact_interval(discordant, n),
        "risk_difference": (cells["comparison_only"] - cells["reference_only"]) / n if n else None,
        "exact_mcnemar_p_descriptive": min(
            1.0,
            2
            * binomial_cdf(min(cells["reference_only"], cells["comparison_only"]), discordant, 0.5),
        )
        if discordant
        else 1.0,
        "incomplete_pairs": sum(len(values) != 2 for values in grouped.values()),
    }


def noninferiority(table: dict[str, Any], margin: float) -> dict[str, Any]:
    n = table["n"]
    lower: float | None = None
    if n:
        # Bonferroni: each one-sided tail has alpha .025; joint coverage >= .95.
        wins = table["comparison_only"]
        losses = table["reference_only"]
        win_lower = 0.0 if wins == 0 else _root(wins - 1, n, 0.975)
        loss_upper = 1.0 if losses == n else _root(losses, n, 0.025)
        lower = win_lower - loss_upper
    return {
        "margin": margin,
        "risk_difference": table["risk_difference"],
        "one_sided_95_lower_bound": lower,
        "method": "Bonferroni paired win/loss exact binomial bounds",
        "criterion_met_descriptive": lower is not None and lower > -margin,
        "conclusion": "PILOT_ONLY_NO_CONFIRMATORY_NONINFERIORITY_CLAIM",
    }


def analyze(rows: list[dict[str, Any]], margin: float) -> dict[str, Any]:
    endpoints = (
        "correction_success",
        "unsupported_confirmation",
        "clean_task_success",
        "duplicate_effect",
        "safe_resolution",
        "outcome_coverage",
        "played_span_repair_complete",
    )
    primary = [r for r in rows if r["variant"] == "PRIMARY"]
    counts = {}
    for arm in ("B0", "B1", "B2", "B3", "P1", "P2"):
        selected = [r for r in primary if r["arm"] == arm]
        counts[arm] = {
            endpoint: {
                "numerator": sum(
                    int(r["values"][endpoint]) for r in selected if endpoint in r["values"]
                ),
                "denominator": sum(endpoint in r["values"] for r in selected),
            }
            for endpoint in endpoints
        }
    comparisons = []
    for endpoint in ("correction_success", "unsupported_confirmation"):
        eligible = [
            r for r in rows if endpoint != "unsupported_confirmation" or r["postcommit_ambiguity"]
        ]
        for arm in ("P1", "P2"):
            comparisons.append(paired_table(eligible, endpoint, "B3", arm))
    clean = paired_table(rows, "clean_task_success", "B3", "P2")
    result = {
        "version": VERSION,
        "scope": "DESCRIPTIVE_PILOT_NO_FINAL_EVIDENCE",
        "raw_counts": counts,
        "paired_primary_endpoints": comparisons,
        "clean_noninferiority": {"table": clean, **noninferiority(clean, margin)},
        "acoustic_versions": [r for r in rows if r["scenario_id"] == "pilot-clean-acoustic"],
        "sample_justification": {
            "planned_phase8_scenarios": 500,
            "pilot_scenarios": 40,
            "independence_limit": (
                "Purposive scenarios share templates; n is not population independence"
            ),
            "expected_discordant_at_500": [
                {
                    "endpoint": t["endpoint"],
                    "arm": t["comparison_arm"],
                    "estimate": t["discordance_estimate"] * 500 if t["n"] else None,
                    "interval": [v * 500 for v in t["discordance_exact_95_interval"]]
                    if t["n"]
                    else None,
                }
                for t in comparisons
            ],
            "zero_failures_at_500_exact_95_upper": exact_interval(0, 500)[1],  # type: ignore[index]
            "power_claim": "No guaranteed power from pilot discordance or repeated templates",
            "allocation_condition": (
                "500 total is not 500 per stratum; freeze clean and ambiguity counts before Phase 8"
            ),
        },
    }
    result["hash"] = stable_hash(result)
    return result
