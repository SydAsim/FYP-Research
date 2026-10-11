"""Independent arithmetic and scenario-counting checks for the frozen pilot."""

import math

import pytest

from research.analysis.pilot import binomial_cdf, exact_interval, noninferiority, paired_table
from research.pilot.plan import pilot_plan
from research.runner.acoustic_source import CONDITIONS


def test_exact_bounds_include_rare_zero_failures() -> None:
    assert exact_interval(0, 0) is None
    assert exact_interval(0, 500) == pytest.approx([0, 1 - 0.025 ** (1 / 500)])
    assert exact_interval(500, 500) == pytest.approx([0.025 ** (1 / 500), 1])
    lower, upper = exact_interval(5, 10)  # type: ignore[misc]
    assert lower == pytest.approx(1 - upper)
    assert lower < 0.5 < upper
    assert binomial_cdf(0, 4, 0.5) == pytest.approx(1 / 16)
    with pytest.raises(ValueError):
        exact_interval(2, 1)


def test_paired_discordance_and_repetition_rejection() -> None:
    rows = [
        {
            "scenario_id": str(i),
            "variant": "PRIMARY",
            "arm": arm,
            "values": {"correction_success": value},
        }
        for i in range(4)
        for arm, value in (("B3", 0), ("P2", 1))
    ]
    table = paired_table(rows, "correction_success", "B3", "P2")
    assert table["n"] == table["comparison_only"] == table["discordant"] == 4
    assert table["exact_mcnemar_p_descriptive"] == pytest.approx(0.125)
    version = {**rows[0], "variant": "LOCAL_NOISE"}
    assert paired_table([*rows, version], "correction_success", "B3", "P2") == table
    with pytest.raises(ValueError, match="repetition"):
        paired_table([*rows, rows[0]], "correction_success", "B3", "P2")


def test_ni_bound_cannot_reward_small_silent_pilot() -> None:
    table = {"n": 5, "risk_difference": 0, "comparison_only": 0, "reference_only": 0}
    assert not noninferiority(table, 0.05)["criterion_met_descriptive"]
    table["n"] = 100
    result = noninferiority(table, 0.05)
    assert result["one_sided_95_lower_bound"] == pytest.approx(-(1 - math.pow(0.025, 0.01)))
    assert result["criterion_met_descriptive"]
    assert result["conclusion"].startswith("PILOT_ONLY")


def test_pilot_has_40_instances_not_267_or_audio_variants() -> None:
    plan = pilot_plan(
        [
            {"condition": condition, "seed": 60 + i, "input_audio_hash": "a" * 64}
            for i, condition in enumerate(CONDITIONS)
        ]
    )
    assert plan["independent_scenario_instances"] == 40
    assert plan["scenario_versions"] == 45
    assert plan["planned_executions"] == 267
    assert len({c["scenario_id"] for c in plan["cases"]}) == 40
    assert sum(c["scenario_id"] == "pilot-clean-acoustic" for c in plan["cases"]) == 6
    assert all(c["case"]["repetition"] == 1 for c in plan["cases"])
    with pytest.raises(ValueError, match="six declared"):
        pilot_plan([])
