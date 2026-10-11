"""Pre-registered binary endpoints; repetitions never become new scenarios."""

import random
from statistics import mean
from typing import Any

METRIC_VERSION = "phase6-primary-v1"


def metric_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    endpoint = "clean_task_success" if "clean_task_success" in result else "correction_success"
    values = {
        endpoint: bool(result[endpoint]),
        "unsupported_confirmation": bool(result["unsupported_confirmation"]),
        "duplicate_effect": bool(result["duplicate_effect"]),
        "safe_resolution": bool(result["safe_resolution"]),
        "outcome_coverage": bool(result["outcome_coverage"]),
    }
    if "played_span_repair_complete" in result:
        values["played_span_repair_complete"] = bool(result["played_span_repair_complete"])
    return [
        {
            "metric_name": name,
            "metric_version": "phase6-clean-v1"
            if endpoint == "clean_task_success"
            else METRIC_VERSION,
            "numeric_value": int(value),
            "numerator": int(value),
            "denominator": 1,
            "details": {"unit": "independent_scenario_execution"},
        }
        for name, value in values.items()
    ]


def paired_counts(executions: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    """Summarize distinct scenario keys and cluster repetition rows under each key."""
    grouped: dict[str, dict[str, list[int]]] = {}
    for item in executions:
        value = item.get("metrics", {}).get(metric)
        if value is None:
            continue
        grouped.setdefault(item["scenario_key"], {}).setdefault(item["arm"], []).append(int(value))
    arms = sorted({arm for values in grouped.values() for arm in values})
    complete = {
        key: values for key, values in grouped.items() if all(arm in values for arm in arms)
    }
    return {
        "independent_scenarios": len(complete),
        "executions": sum(len(group) for values in complete.values() for group in values.values()),
        "by_arm": {
            arm: {
                "scenarios": len(complete),
                "successes": sum(
                    int(sum(values[arm]) / len(values[arm]) >= 0.5) for values in complete.values()
                ),
            }
            for arm in arms
        },
    }


def clean_paired_difference(
    executions: list[dict[str, Any]],
    reference_arm: str,
    comparison_arm: str,
    *,
    bootstrap_draws: int = 2000,
    seed: int = 1,
) -> dict[str, Any]:
    """Descriptive paired risk difference; Phase 6 sets no NI margin or decision."""
    if reference_arm == comparison_arm or bootstrap_draws < 1:
        raise ValueError("Distinct arms and positive bootstrap draws are required")
    grouped: dict[str, dict[str, list[int]]] = {}
    for row in executions:
        arm = str(row["arm"])
        value = row.get("metrics", {}).get("clean_task_success")
        if arm in (reference_arm, comparison_arm) and value is not None:
            grouped.setdefault(str(row["scenario_key"]), {}).setdefault(arm, []).append(int(value))
    complete = {
        key: values
        for key, values in grouped.items()
        if reference_arm in values and comparison_arm in values
    }
    differences = [
        mean(values[comparison_arm]) - mean(values[reference_arm]) for values in complete.values()
    ]
    estimate = mean(differences) if differences else None
    interval: list[float] | None = None
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
        "independent_scenarios": len(complete),
        "executions": sum(
            len(values[reference_arm]) + len(values[comparison_arm]) for values in complete.values()
        ),
        "risk_difference": estimate,
        "bootstrap_95_interval": interval,
        "noninferiority_margin": None,
        "noninferiority_conclusion": "NOT_TESTED_PHASE6",
    }
