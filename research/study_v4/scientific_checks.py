"""Scientific-environment design validation; no application executions."""

from research.analysis.pilot import exact_interval
from research.study_v4.analysis import exact_clean_design, identifiable_matrix
from research.study_v4.design import materialize


def test_identified_matrices_respect_structural_eligibility() -> None:
    result = identifiable_matrix(materialize())
    assert result["full_rank"] and result["rank"] == result["columns"] == 9
    for endpoint in ("unsupported_exposed_claim", "clean_task_success"):
        matrix = identifiable_matrix(materialize(), endpoint)
        assert matrix["full_rank"] and matrix["rank"] == matrix["columns"] == 3


def test_exact_power_grid_and_mass() -> None:
    result = exact_clean_design()
    equal_five = next(
        r for r in result["grid"] if r["discordance"] == 0.05 and r["true_difference"] == 0
    )
    equal_ten = next(
        r for r in result["grid"] if r["discordance"] == 0.10 and r["true_difference"] == 0
    )
    assert 0.80 < equal_five["exact_power"] < 0.81
    assert equal_ten["exact_power"] < 0.8
    assert all(abs(r["enumerated_probability"] - 1) < 1e-10 for r in result["grid"])
    bound = exact_interval(0, 300)
    assert bound is not None
    assert abs(result["all_ties_lower_bound"] + bound[1]) < 1e-10
