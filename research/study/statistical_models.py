"""Isolated scientific dependencies; diagnostics, never automatic superiority claims.

Third-party dynamic imports are the sole untyped boundary. Main app dependencies
and historical environments are not upgraded by the study preparation.
"""

import importlib
import random
import warnings
from collections import Counter
from typing import Any

from research.study.models import AnalysisRow, StudyCase


def design_diagnostics(cases: list[StudyCase]) -> dict[str, Any]:
    """Rank of the proposed covariates; constructing a matrix is not an execution."""
    np = importlib.import_module("numpy")
    pd = importlib.import_module("pandas")
    patsy = importlib.import_module("patsy")
    data = pd.DataFrame(
        [
            {
                "arm": arm.value,
                "stratum": case.stratum.value,
                "phase": case.correction_barrier,
                "fault": case.fault_label,
                "revision_type": "NONE" if len(case.intents) == 1 else "PARAMETER_CORRECTION",
                "action_class": "CREATE"
                if len(case.intents) == 1
                else "CREATE_RESCHEDULE"
                if case.provider.supports_reschedule
                else "CREATE_CANCEL_CREATE",
            }
            for case in cases
            for arm in case.primary_arms
        ]
    )
    formulas = {
        "minimal": "1 + C(arm) + C(stratum)",
        "full_contract": ("1 + C(arm) + C(phase) + C(fault) + C(revision_type) + C(action_class)"),
        "extended_with_stratum": (
            "1 + C(arm) + C(stratum) + C(phase) + C(fault) + C(revision_type) + C(action_class)"
        ),
    }
    result = {}
    for name, formula in formulas.items():
        matrix = patsy.dmatrix(formula, data, return_type="dataframe")
        rank = int(np.linalg.matrix_rank(matrix.to_numpy()))
        result[name] = {
            "formula": formula,
            "rank": rank,
            "columns": matrix.shape[1],
            "full_rank": rank == matrix.shape[1],
            "terms": list(matrix.columns),
        }
    return {
        "classification": "DESIGN_MATRIX_ONLY_NO_OUTCOMES",
        "design_rows": len(data),
        "campaign_executions": 0,
        "matrices": result,
        "decision": "Do not silently drop aliased contract covariates; approve parameterization",
    }


def mixed_binary(
    rows: list[AnalysisRow], endpoint: str, *, extended: bool = False
) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    pd = importlib.import_module("pandas")
    patsy = importlib.import_module("patsy")
    module = importlib.import_module("statsmodels.genmod.bayes_mixed_glm")
    usable = [r for r in rows if r.attempt == 1 and r.values.get(endpoint) in ("TRUE", "FALSE")]
    formula = "outcome ~ C(arm) + C(stratum)"
    if extended:
        formula += " + C(phase) + C(fault) + C(revision_type) + C(action_class)"
    if not usable or len({r.values[endpoint] for r in usable}) < 2:
        return {
            "status": "UNIDENTIFIABLE",
            "reason": "No data or no outcome variation",
            "n": len(usable),
            "formula": formula,
        }
    data = pd.DataFrame(
        [
            {**r.model_dump(mode="json"), "outcome": int(r.values[endpoint] == "TRUE")}
            for r in usable
        ]
    )
    design = patsy.dmatrix(formula.split(" ~ ")[1], data, return_type="dataframe")
    rank = int(np.linalg.matrix_rank(design.to_numpy()))
    if rank < design.shape[1]:
        return {
            "status": "UNIDENTIFIABLE",
            "reason": "Rank deficient fixed effects",
            "rank": rank,
            "columns": int(design.shape[1]),
            "formula": formula,
            "n": len(usable),
            "terms": list(design.columns),
        }
    random = {"recipe": "0 + C(cluster_id)"}
    if any(r.speaker_id is not None for r in usable):
        if any(r.speaker_id is None for r in usable):
            return {"status": "UNIDENTIFIABLE", "reason": "Mixed missing speaker identities"}
        random["speaker"] = "0 + C(speaker_id)"
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        model = module.BinomialBayesMixedGLM.from_formula(
            formula, random, data, vcp_p=0.5, fe_p=2.0
        )
        size = model.k_fep + model.k_vcp + model.k_vc
        result = model.fit_vb(mean=np.zeros(size), sd=np.ones(size), minim_opts={"maxiter": 1000})
    return {
        "status": "CONVERGED" if result.optim_retvals.success else "NONCONVERGED",
        "method": "BAYESIAN_MEAN_FIELD_VB_NOT_FREQUENTIST_CI",
        "formula": formula,
        "n": len(usable),
        "excluded_unknown_or_structural": len(rows) - len(usable),
        "fixed_effect_names": model.fep_names,
        "posterior_mean": result.fe_mean.tolist(),
        "posterior_sd": result.fe_sd.tolist(),
        "approximate_95_credible_intervals": np.column_stack(
            (result.fe_mean - 1.96 * result.fe_sd, result.fe_mean + 1.96 * result.fe_sd)
        ).tolist(),
        "log_sd_means": result.vcp_mean.tolist(),
        "random_effects": random,
        "prior_fixed_sd": 2.0,
        "prior_log_random_sd": 0.5,
        "warnings": [str(w.message) for w in captured],
        "claim_permitted": False,
        "limitation": (
            "Approximate posterior; purposive recipe frame and missingness limit inference"
        ),
    }


def lognormal_aft(rows: list[AnalysisRow]) -> dict[str, Any]:
    """Right-censored lognormal MLE; cluster resampling belongs to the caller.

    No artificial epsilon for zero/missing time and no treating handoffs as successes.
    The unclustered Hessian is deliberately not presented as a study confidence interval.
    """
    np = importlib.import_module("numpy")
    scipy = importlib.import_module("scipy")
    pd = importlib.import_module("pandas")
    patsy = importlib.import_module("patsy")
    usable = [
        r
        for r in rows
        if r.attempt == 1
        and r.duration_seconds is not None
        and r.duration_seconds > 0
        and r.event_observed is not None
    ]
    if not usable or not any(r.event_observed for r in usable):
        return {"status": "UNIDENTIFIABLE", "reason": "No positive times with observed events"}
    data = pd.DataFrame([r.model_dump(mode="json") for r in usable])
    design = patsy.dmatrix("1 + C(arm) + C(stratum)", data, return_type="dataframe")
    x = design.to_numpy()
    if np.linalg.matrix_rank(x) < x.shape[1]:
        return {"status": "UNIDENTIFIABLE", "reason": "Rank deficient AFT fixed effects"}
    times = np.array([r.duration_seconds for r in usable], dtype=float)
    logt = np.log(times)
    observed = np.array([r.event_observed for r in usable], dtype=bool)

    def loss(parameters: Any) -> float:
        beta, sigma = parameters[:-1], np.exp(parameters[-1])
        z = (logt - x @ beta) / sigma
        loglik = np.where(
            observed, scipy.stats.norm.logpdf(z) - np.log(sigma) - logt, scipy.stats.norm.logsf(z)
        )
        return float(-loglik.sum())

    initial = np.zeros(x.shape[1] + 1)
    initial[0] = np.median(logt[observed])
    initial[-1] = np.log(max(float(np.std(logt[observed])), 0.1))
    result = scipy.optimize.minimize(
        loss, initial, method="L-BFGS-B", bounds=[(None, None)] * x.shape[1] + [(-6, 4)]
    )
    return {
        "status": "CONVERGED" if result.success else "NONCONVERGED",
        "method": "RIGHT_CENSORED_LOGNORMAL_AFT_MLE",
        "formula": "1 + C(arm) + C(stratum)",
        "n": len(usable),
        "events": int(observed.sum()),
        "excluded_missing_or_zero_times": len(rows) - len(usable),
        "terms": list(design.columns),
        "beta": result.x[:-1].tolist(),
        "time_ratios": np.exp(result.x[:-1]).tolist(),
        "sigma": float(np.exp(result.x[-1])),
        "negative_log_likelihood": float(result.fun),
        "optimizer_message": str(result.message),
        "censor_reasons": dict(Counter(r.censor_reason for r in usable if not r.event_observed)),
        "claim_permitted": False,
        "limitation": "Independent censoring and lognormal form unproven; no iid standard errors",
    }


def aft_cluster_bootstrap(
    rows: list[AnalysisRow], *, draws: int = 2000, seed: int = 8003
) -> dict[str, Any]:
    """Resample complete paired recipe clusters, retaining every failed fit."""
    if draws < 1:
        raise ValueError("Positive draw count required")
    groups: dict[str, dict[str, list[AnalysisRow]]] = {}
    for row in rows:
        if row.attempt == 1:
            groups.setdefault(row.stratum.value, {}).setdefault(row.cluster_id, []).append(row)
    estimate = lognormal_aft(rows)
    rng = random.Random(seed)
    successful, failures = [], []
    if estimate["status"] == "CONVERGED":
        for draw in range(draws):
            sample = [
                r
                for clusters in groups.values()
                for _ in clusters
                for r in rng.choice(list(clusters.values()))
            ]
            fit = lognormal_aft(sample)
            if fit["status"] == "CONVERGED" and fit["terms"] == estimate["terms"]:
                successful.append(fit["beta"])
            else:
                failures.append({"draw": draw, "fit": fit})
    intervals = None
    if successful:
        np = importlib.import_module("numpy")
        intervals = np.quantile(np.array(successful), [0.025, 0.975], axis=0).T.tolist()
    return {
        "estimate": estimate,
        "planned_draws": draws,
        "completed_draws": len(successful),
        "failed_draws": failures,
        "seed": seed,
        "clustered_beta_95_intervals": intervals,
        "claim_permitted": False,
        "limitation": "Censoring assumptions and failed-draw sensitivity required; not iid CI",
    }
