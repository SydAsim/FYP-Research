"""V4 estimand: paired task draws conditional on a fixed protocol-input frame."""

import importlib
import json
import math
from typing import Any

from research.analysis.pilot import exact_interval, noninferiority
from research.arms import Arm
from research.scenario_dsl.models import stable_hash
from research.study.analysis import eligible, holm, paired, primary_index
from research.study.models import AnalysisRow, Stratum, StudyCase
from research.study_v4.design import ROOT, materialize

RECOVERY_FAMILIES = frozenset(
    {
        "partial-time",
        "full-before-correction",
        "late-decisive-ack",
        "restart-before-repair",
        "reconnect-third-revision",
    }
)


def marginal_model(
    cases: list[StudyCase], rows: list[AnalysisRow], endpoint: str, *, alpha: float = 0.05
) -> dict[str, Any]:
    """Saturated marginal model; no separation-prone latent coefficients."""
    index = primary_index(rows)
    cells_out = []
    for s in Stratum:
        selected = [c for c in cases if c.stratum is s and eligible(c, endpoint)]
        if not selected:
            continue
        for a in (Arm.B3, Arm.P1, Arm.P2):
            values = [
                index[(c.case_id, a)].values.get(endpoint) if (c.case_id, a) in index else None
                for c in selected
            ]
            known = [int(v == "TRUE") for v in values if v in ("TRUE", "FALSE")]
            cells_out.append(
                {
                    "arm": a.value,
                    "stratum": s.value,
                    "planned": len(values),
                    "known": len(known),
                    "mean": sum(known) / len(known) if known else None,
                    "missing": len(values) - len(known),
                }
            )
    contrasts = []
    weights = {Stratum.AMBIGUITY: 0.5, Stratum.EXPOSURE: 0.3, Stratum.BOUNDARY: 0.2}
    for a in (Arm.P1, Arm.P2):
        total_lower = total_upper = estimate = variance = 0.0
        identified = True
        components: list[dict[str, Any]] = []
        for s, weight in weights.items():
            selected = [c for c in cases if c.stratum is s]
            pairs = []
            lo = hi = 0.0
            for c in selected:
                vals = [
                    index[(c.case_id, arm)].values.get(endpoint)
                    if (c.case_id, arm) in index
                    else None
                    for arm in (Arm.B3, a)
                ]
                b, p = [int(v == "TRUE") if v in ("TRUE", "FALSE") else None for v in vals]
                lo += (p if p is not None else 0) - (b if b is not None else 1)
                hi += (p if p is not None else 1) - (b if b is not None else 0)
                if b is not None and p is not None:
                    pairs.append(p - b)
            n = len(selected)
            if not n:
                identified = False
                continue
            total_lower += weight * lo / n
            total_upper += weight * hi / n
            complete = len(pairs) == n
            identified &= complete
            avg = sum(pairs) / n if complete else None
            bound = None
            if complete:
                estimate += weight * float(avg or 0)
                # Simultaneous component CP intervals, union bound across six probabilities.
                wins = exact_interval(pairs.count(1), n, alpha=alpha / 6)
                losses = exact_interval(pairs.count(-1), n, alpha=alpha / 6)
                assert wins is not None and losses is not None
                bound = [wins[0] - losses[1], wins[1] - losses[0]]
                variance += (
                    weight**2 * sum((d - float(avg or 0)) ** 2 for d in pairs) / (n * (n - 1))
                    if n > 1
                    else 0.0
                )
            components.append(
                {
                    "stratum": s.value,
                    "weight": weight,
                    "n": n,
                    "complete_pairs": len(pairs),
                    "difference": avg,
                    "simultaneous_component_interval": bound,
                }
            )
        interval = (
            [
                sum(c["weight"] * c["simultaneous_component_interval"][i] for c in components)
                for i in (0, 1)
            ]
            if identified
            else None
        )
        contrasts.append(
            {
                "arm": a.value,
                "reference": "B3",
                "identified": identified,
                "difference": estimate if identified else None,
                "paired_standard_error": math.sqrt(variance) if identified else None,
                "conservative_95_interval": interval if alpha == 0.05 else None,
                "conservative_interval": interval,
                "coverage": 1 - alpha,
                "missingness_bounds": [total_lower, total_upper],
                "components": components,
            }
        )
    return {
        "model": "Saturated arm-by-stratum marginal cell means",
        "endpoint": endpoint,
        "cells": cells_out,
        "standardized_contrasts": contrasts,
        "uncertainty": "Exact simultaneous component bounds; paired variance descriptive",
    }


def clean_gate(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    table = paired(cases, rows, "clean_task_success", representatives=False)
    result = noninferiority(table, 0.05)
    result.update(
        planned_n=table["planned_n"],
        complete_pairs=table["n"],
        missing_pairs=table["missing_pairs"],
        planned_missingness_bounds=table["planned_denominator_difference_bounds"],
        conclusion="DRAFT_NO_CONFIRMATORY_CLAIM",
        criterion_met_descriptive=(
            result["criterion_met_descriptive"] and table["missing_pairs"] == 0
        ),
    )
    return result


def primary_bounds(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    correction = marginal_model(cases, rows, "correction_success", alpha=0.025)
    table = paired(cases, rows, "unsupported_exposed_claim", representatives=False)
    bound = None
    if table["n"] and not table["missing_pairs"]:
        wins = exact_interval(table["comparison_only"], table["n"], alpha=0.025 / 2)
        losses = exact_interval(table["reference_only"], table["n"], alpha=0.025 / 2)
        assert wins is not None and losses is not None
        bound = [wins[0] - losses[1], wins[1] - losses[0]]
    return {
        "rule": "Bonferroni: .025 per co-primary comparison; no candidate claims permitted",
        "correction": correction["standardized_contrasts"][1],
        "hidden_exposure": {"table": table, "conservative_interval": bound, "coverage": 0.975},
        "confirmatory_claim_permitted": False,
    }


def batch_sensitivity(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    order_path = ROOT / "execution-order.json"
    if not order_path.exists() or any(not c.case_id.startswith("p8v4-") for c in cases):
        return {"status": "NOT_APPLICABLE_TO_CALIBRATION_OR_UNPLANNED_ORDER"}
    order = json.loads(order_path.read_text(encoding="utf-8"))["rows"]
    batches = {r["case_id"]: r["batch_id"] for r in order}
    index = primary_index(rows)
    estimates = []
    for batch in sorted(set(batches.values())):
        estimate = 0.0
        known = True
        for stratum, weight in (
            (Stratum.AMBIGUITY, 0.5),
            (Stratum.EXPOSURE, 0.3),
            (Stratum.BOUNDARY, 0.2),
        ):
            selected = [c for c in cases if c.stratum is stratum and batches[c.case_id] != batch]
            differences = []
            for c in selected:
                values = [
                    index[(c.case_id, a)].values.get("correction_success")
                    if (c.case_id, a) in index
                    else None
                    for a in (Arm.B3, Arm.P2)
                ]
                if any(v not in ("TRUE", "FALSE") for v in values):
                    known = False
                    continue
                differences.append(int(values[1] == "TRUE") - int(values[0] == "TRUE"))
            if not selected:
                known = False
            else:
                estimate += weight * sum(differences) / len(selected)
        estimates.append({"omitted_batch": batch, "difference": estimate if known else None})
    return {
        "method": "Fixed temporal-block omission, descriptive stationarity sensitivity",
        "independent_batches_assumed": False,
        "estimates": estimates,
    }


def secondary_family(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    endpoints = (
        "correction_success",
        "unsupported_exposed_claim",
        "corrective_delivery_after_challenge",
        "complete_corrective_communication",
    )
    tables = []
    for comparison, reference in ((Arm.P1, Arm.B3), (Arm.P2, Arm.P1), (Arm.P2, Arm.B3)):
        for endpoint in (
            endpoints if reference is not Arm.B3 or comparison is Arm.P1 else endpoints[2:]
        ):
            selected = (
                [c for c in cases if c.generator_family in RECOVERY_FAMILIES]
                if endpoint in endpoints[2:]
                else cases
            )
            table = paired(
                selected, rows, endpoint, comparison, representatives=False, reference=reference
            )
            table["null_scope"] = (
                "Diagnostic stratum-wise paired exchangeability; not weak average equality"
            )
            tables.append(table)
    adjusted = holm([t["exact_mcnemar_p"] for t in tables])
    return {
        "comparisons": [
            {**t, "holm_diagnostic_p": p} for t, p in zip(tables, adjusted, strict=True)
        ],
        "count": len(tables),
        "confirmatory_claim_permitted": False,
        "missing_family_rule": "Unavailable p-value leaves family adjustment unresolved",
        "effect_interpretation": "Interpret effects through standardized bounds",
    }


def exact_clean_design(n: int = 300) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    stats = importlib.import_module("scipy.stats")
    win_lower = np.array(
        [0.0 if w == 0 else stats.beta.ppf(0.025, w, n - w + 1) for w in range(n + 1)]
    )
    loss_upper = np.array(
        [1.0 if loss == n else stats.beta.ppf(0.975, loss + 1, n - loss) for loss in range(n + 1)]
    )
    rows = []
    for q in (0.0, 0.01, 0.03, 0.05, 0.10):
        for delta in (0.0, -0.01):
            if q < abs(delta):
                continue
            power, mass_kept = 0.0, 0.0
            for discordant in range(n + 1):
                mass = float(stats.binom.pmf(discordant, n, q))
                if mass < 1e-14:
                    continue
                for wins in range(discordant + 1):
                    probability = 0.5 if q == 0 else (q + delta) / (2 * q)
                    value = mass * float(stats.binom.pmf(wins, discordant, probability))
                    mass_kept += value
                    power += value * bool(win_lower[wins] - loss_upper[discordant - wins] > -0.05)
            rows.append(
                {
                    "discordance": q,
                    "true_difference": delta,
                    "exact_power": power,
                    "enumerated_probability": mass_kept,
                    "paired_standard_error": math.sqrt((q - delta**2) / n),
                    "normal_95_halfwidth_for_precision_only": 1.96 * math.sqrt((q - delta**2) / n),
                }
            )
    return {
        "classification": "DESIGN_CALCULATION_NOT_OBSERVED_DATA",
        "n": n,
        "margin": 0.05,
        "alpha_tail": 0.025,
        "all_ties_lower_bound": -loss_upper[0],
        "grid": rows,
        "criterion": "300 tasks targets >80% at equal risks, discordance <=5%",
        "limitation": "Assumed nuisance rates, not pilot estimates; higher rates reduce power",
    }


def identifiable_matrix(
    cases: list[StudyCase], endpoint: str = "correction_success"
) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    pd = importlib.import_module("pandas")
    patsy = importlib.import_module("patsy")
    data = pd.DataFrame(
        [
            {"arm": a.value, "stratum": c.stratum.value}
            for c in cases
            if eligible(c, endpoint)
            for a in c.primary_arms
        ]
    )
    matrix = patsy.dmatrix("1 + C(arm) * C(stratum)", data, return_type="dataframe")
    rank = int(np.linalg.matrix_rank(matrix.to_numpy()))
    return {
        "formula": "outcome ~ C(arm) * C(stratum)",
        "endpoint": endpoint,
        "rank": rank,
        "columns": matrix.shape[1],
        "full_rank": rank == matrix.shape[1],
        "terms": list(matrix.columns),
        "rows_are_design_only": True,
        "model": "Identifiable marginal arm/stratum cell model; pair by input ID",
        "omitted_separate_terms": ["phase", "fault", "revision_type", "action_class"],
        "reason": "Frame-encoded factors do not have separate identifiable causal coefficients",
        "repeated_voice_extension": "Requires separate version and identified random-effects model",
    }


def outcome_report(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    """No legacy member-zero selection, no latent random-recipe population claim."""
    index = primary_index(rows)
    return {
        "status": "DRAFT_NOT_MAIN_RESULTS",
        "sampling_unit": "INPUT_DRAW",
        "inputs": len(cases),
        "correction_by_stratum": [
            paired(
                [c for c in cases if c.stratum is s],
                rows,
                "correction_success",
                representatives=False,
            )
            for s in (Stratum.AMBIGUITY, Stratum.EXPOSURE, Stratum.BOUNDARY)
        ],
        "hidden_commit": paired(cases, rows, "unsupported_exposed_claim", representatives=False),
        "clean_table": paired(cases, rows, "clean_task_success", representatives=False),
        "repair_opportunities_predeclared": sum(
            c.generator_family in RECOVERY_FAMILIES for c in cases
        ),
        "ordinary_updates_creditable": True,
        "known_rows": len(index),
        "unknown_not_imputed": True,
        "main_started": False,
        "identified_marginal_analysis": marginal_model(cases, rows, "correction_success"),
        "clean_noninferiority": clean_gate(cases, rows),
        "recovery_secondary": [
            paired(
                [c for c in cases if c.generator_family in RECOVERY_FAMILIES],
                rows,
                e,
                representatives=False,
            )
            for e in ("corrective_delivery_after_challenge", "complete_corrective_communication")
        ],
        "primary_family_rule": "Bonferroni across two co-primary claims; .025 per bound",
        "primary_bounds": primary_bounds(cases, rows),
        "temporal_batch_sensitivity": batch_sensitivity(cases, rows),
        "secondary_family": secondary_family(cases, rows),
    }


def prepare_analysis() -> dict[str, Any]:
    from research.study.package import write_json

    cases = materialize()
    output: dict[str, Any] = {
        "power": exact_clean_design(),
        "matrix": identifiable_matrix(cases),
        "endpoint_matrices": [
            identifiable_matrix(cases, e)
            for e in ("correction_success", "unsupported_exposed_claim", "clean_task_success")
        ],
        "empty_analysis": outcome_report(cases, []),
    }
    output["hash"] = stable_hash(output)
    write_json(ROOT / "analysis-design.json", output)
    return {
        "power_at_5pct_discordance": next(
            r["exact_power"]
            for r in output["power"]["grid"]
            if r["discordance"] == 0.05 and r["true_difference"] == 0
        ),
        "model_full_rank": output["matrix"]["full_rank"],
    }


if __name__ == "__main__":
    print(prepare_analysis())
