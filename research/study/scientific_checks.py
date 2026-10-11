"""Artificial known-parameter checks; run in the isolated scientific environment."""

import pytest

from research.study.statistical_models import aft_cluster_bootstrap, lognormal_aft, mixed_binary
from research.study.validation import toy_rows


def test_vb_mixed_model_recovers_direction_without_frequentist_claim() -> None:
    result = mixed_binary(toy_rows(), "correction_success")
    assert result["status"] == "CONVERGED"
    index = result["fixed_effect_names"].index("C(arm)[T.P2]")
    assert result["posterior_mean"][index] == pytest.approx(1.3, abs=0.55)
    assert result["method"] == "BAYESIAN_MEAN_FIELD_VB_NOT_FREQUENTIST_CI"
    assert "speaker" not in result["random_effects"]
    assert not result["claim_permitted"]


def test_censored_aft_known_time_ratio() -> None:
    result = lognormal_aft(toy_rows())
    assert result["status"] == "CONVERGED"
    index = result["terms"].index("C(arm)[T.P2]")
    assert result["beta"][index] == pytest.approx(0.35, abs=0.12)
    assert result["events"] < result["n"]
    assert not result["claim_permitted"]


def test_no_events_or_outcome_variation_not_hidden() -> None:
    rows = [
        r.model_copy(
            update={
                "event_observed": False,
                "censor_reason": "ACK_MISSING",
                "values": {"correction_success": "TRUE"},
            }
        )
        for r in toy_rows()
    ]
    assert lognormal_aft(rows)["status"] == "UNIDENTIFIABLE"
    assert mixed_binary(rows, "correction_success")["status"] == "UNIDENTIFIABLE"


def test_extended_aliased_covariates_rejected() -> None:
    rows = [
        r.model_copy(update={"phase": "P3" if r.arm.value == "P2" else "P1"}) for r in toy_rows()
    ]
    result = mixed_binary(rows, "correction_success", extended=True)
    assert result["status"] == "UNIDENTIFIABLE"
    assert result["reason"] == "Rank deficient fixed effects"


def test_aft_resamples_recipe_clusters_and_retains_fit_failures() -> None:
    result = aft_cluster_bootstrap(toy_rows(), draws=8)
    assert result["completed_draws"] + len(result["failed_draws"]) == 8
    assert result["clustered_beta_95_intervals"] is not None
    assert not result["claim_permitted"]
