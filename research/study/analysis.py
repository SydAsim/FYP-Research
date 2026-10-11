"""Planned-slot denominators, paired/cluster inference and explicit missingness."""

import math
import random
from collections import Counter
from statistics import mean
from typing import Any

from research.analysis.pilot import binomial_cdf, exact_interval, noninferiority
from research.arms import Arm
from research.study.models import AnalysisRow, Status, Stratum, StudyCase

VERSION = "phase8-analysis-draft-v3"
PRIMARY = ("correction_success", "unsupported_exposed_claim")
MARGIN = 0.05


def eligible(case: StudyCase, endpoint: str) -> bool:
    if endpoint == "correction_success":
        return case.stratum is not Stratum.CLEAN
    if endpoint == "unsupported_exposed_claim":
        return case.stratum is Stratum.AMBIGUITY
    if endpoint == "clean_task_success":
        return case.stratum is Stratum.CLEAN
    return True


def primary_index(rows: list[AnalysisRow]) -> dict[tuple[str, Arm], AnalysisRow]:
    index = {}
    for row in rows:
        if row.attempt != 1:
            continue  # later attempts stay in the ledger; cannot replace primary
        key = (row.case_id, row.arm)
        if key in index:
            raise ValueError("Duplicate primary record; no outcome-selected repetitions")
        index[key] = row
    return index


def binary(value: Status | None) -> int | None:
    return 1 if value == "TRUE" else 0 if value == "FALSE" else None


def paired(
    cases: list[StudyCase],
    rows: list[AnalysisRow],
    endpoint: str,
    comparison: Arm = Arm.P2,
    *,
    representatives: bool = True,
    reference: Arm = Arm.B3,
) -> dict[str, Any]:
    index = primary_index(rows)
    selected = [
        c
        for c in cases
        if eligible(c, endpoint)
        and comparison in c.arm_order
        and reference in c.arm_order
        and (not representatives or c.cluster_representative)
    ]
    counts = dict.fromkeys(("both_one", "reference_only", "comparison_only", "both_zero"), 0)
    missingness: Counter[str] = Counter()
    lower, upper = 0, 0
    for case in selected:
        values = []
        for arm in (reference, comparison):
            row = index.get((case.case_id, arm))
            value = row.values.get(endpoint, "UNKNOWN") if row else None
            if value == "NOT_APPLICABLE":
                raise ValueError("Structural N/A inside predeclared endpoint denominator")
            missingness[f"{arm}:{value or 'MISSING'}"] += 1
            values.append(binary(value))
        a, b = values
        lower += (b if b is not None else 0) - (a if a is not None else 1)
        upper += (b if b is not None else 1) - (a if a is not None else 0)
        if a is None or b is None:
            continue
        key = (
            "both_one"
            if a and b
            else "reference_only"
            if a
            else ("comparison_only" if b else "both_zero")
        )
        counts[key] += 1
    n = sum(counts.values())
    discordant = counts["reference_only"] + counts["comparison_only"]
    p = (
        min(
            1.0,
            2
            * binomial_cdf(
                min(counts["reference_only"], counts["comparison_only"]), discordant, 0.5
            ),
        )
        if discordant
        else 1.0
    )
    return {
        "endpoint": endpoint,
        "reference_arm": reference.value,
        "comparison_arm": comparison.value,
        "unit": "PREDECLARED_RECIPE_REPRESENTATIVE" if representatives else "TASK_DESCRIPTIVE",
        "planned_n": len(selected),
        "n": n,
        **counts,
        "discordant": discordant,
        "missing_pairs": len(selected) - n,
        "missingness": dict(missingness),
        "risk_difference": (counts["comparison_only"] - counts["reference_only"]) / n
        if n
        else None,
        "planned_denominator_difference_bounds": [lower / len(selected), upper / len(selected)]
        if selected
        else None,
        "exact_mcnemar_p": p if n else None,
        "confirmatory_claim_permitted": False,
        "condition": (
            "Review/freeze and sampling-independence assumptions required; "
            "missing pairs block inference"
        ),
    }


def holm(values: list[float | None]) -> list[float | None]:
    if any(v is None for v in values):
        return [None for _ in values]
    ordered = sorted(enumerate(values), key=lambda p: float(p[1] or 0))
    result: list[float | None] = [None] * len(values)
    previous = 0.0
    for rank, (index, p) in enumerate(ordered):
        previous = min(1.0, max(previous, (len(values) - rank) * float(p or 0)))
        result[index] = previous
    return result


def clean_tolerance(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    table = paired(cases, rows, "clean_task_success")
    bounds = noninferiority(table, MARGIN)
    return {
        "table": table,
        "proposed_margin": MARGIN,
        "known_pair_bound": bounds["one_sided_95_lower_bound"],
        "criterion_on_complete_known_pairs": bounds["criterion_met_descriptive"],
        "eligible_for_claim": table["missing_pairs"] == 0 and table["planned_n"] > 0,
        "claim_permitted": False,
        "best_case_minimum_independent_clean_units": math.floor(math.log(0.025) / math.log(0.95))
        + 1,
        "best_case_bound_with_proposed_clusters": (
            -(1 - 0.025 ** (1 / table["planned_n"])) if table["planned_n"] else None
        ),
        "interpretation": (
            "Margin is a utility design choice; 100 tasks in 10 recipe "
            "clusters cannot establish 5pp NI with this conservative bound"
        ),
    }


def cluster_difference(
    cases: list[StudyCase],
    rows: list[AnalysisRow],
    endpoint: str,
    comparison: Arm = Arm.P2,
    *,
    draws: int = 2000,
    seed: int = 8001,
) -> dict[str, Any]:
    if draws < 1:
        raise ValueError("Positive bootstrap draw count required")
    index = primary_index(rows)
    groups: dict[str, list[tuple[StudyCase, float | None]]] = {}
    for case in cases:
        if not eligible(case, endpoint) or comparison not in case.arm_order:
            continue
        a, b = (index.get((case.case_id, arm)) for arm in (Arm.B3, comparison))
        av, bv = (binary(row.values.get(endpoint)) if row else None for row in (a, b))
        groups.setdefault(case.cluster_id, []).append(
            (case, None if av is None or bv is None else float(bv - av))
        )
    complete: dict[Stratum, list[float]] = {}
    weights: Counter[Stratum] = Counter()
    missing = 0
    for group in groups.values():
        stratum = group[0][0].stratum
        weights[stratum] += len(group)
        if any(v is None for _, v in group):
            missing += 1
            continue
        complete.setdefault(stratum, []).append(mean(float(v) for _, v in group if v is not None))
    total = sum(weights.values())
    estimate, interval = None, None
    if complete and all(complete.get(s) for s in weights):
        estimate = sum(weights[s] / total * mean(complete[s]) for s in weights)
        rng = random.Random(seed)
        boot = sorted(
            sum(
                weights[s] / total * mean(rng.choice(complete[s]) for _ in complete[s])
                for s in weights
            )
            for _ in range(draws)
        )
        interval = [boot[int(0.025 * (draws - 1))], boot[int(0.975 * (draws - 1))]]
    return {
        "endpoint": endpoint,
        "reference_arm": "B3",
        "comparison_arm": comparison.value,
        "planned_clusters": len(groups),
        "incomplete_clusters": missing,
        "observed_complete_clusters": len(groups) - missing,
        "observed_complete_cluster_difference": estimate,
        "bootstrap_95_interval": interval,
        "draws": draws,
        "seed": seed,
        "unit": "RECIPE_CLUSTER_RESAMPLED_WITHIN_STRATUM",
        "claim_permitted": False,
        "limitation": (
            "Complete-cluster sensitivity only; cannot impute unknowns or "
            "establish template population independence"
        ),
    }


def kaplan_meier(rows: list[AnalysisRow], tau: float = 600) -> dict[str, Any]:
    usable = [r for r in rows if r.duration_seconds is not None and r.event_observed is not None]
    if tau <= 0 or any(float(r.duration_seconds or 0) < 0 for r in usable):
        raise ValueError("Nonnegative durations and positive horizon required")
    risk, survival, previous, area = len(usable), 1.0, 0.0, 0.0
    points = []
    for time in sorted({float(r.duration_seconds or 0) for r in usable}):
        if time > tau:
            break
        group = [r for r in usable if r.duration_seconds == time]
        events = sum(bool(r.event_observed) for r in group)
        censored = len(group) - events
        area += survival * (time - previous)
        survival *= 1 - events / risk
        points.append(
            {
                "time": time,
                "at_risk": risk,
                "events": events,
                "censored": censored,
                "survival": survival,
            }
        )
        risk -= len(group)
        previous = time
    identifiable = bool(usable) and (risk > 0 or survival == 0 or previous >= tau)
    rmst = area + survival * (tau - previous) if identifiable else None
    return {
        "n": len(usable),
        "missing_time": len(rows) - len(usable),
        "points": points,
        "tau_seconds": tau,
        "rmst_seconds": rmst,
        "censor_reasons": dict(Counter(r.censor_reason for r in usable if not r.event_observed)),
        "interpretation": (
            "Descriptive right-censoring; independent censoring not proven. "
            "Terminal handoff/lost ACK may be informative, not an event or zero latency"
        ),
    }


def paired_latency(
    cases: list[StudyCase], rows: list[AnalysisRow], *, draws: int = 2000, seed: int = 8002
) -> dict[str, Any]:
    """Whole-recipe bootstrap of completed pairs, explicitly selection conditional."""
    index = primary_index(rows)
    values: dict[Stratum, dict[str, list[float]]] = {}
    incomplete = 0
    for case in cases:
        a, b = (index.get((case.case_id, arm)) for arm in (Arm.B3, Arm.P2))
        if (
            a is None
            or b is None
            or not a.event_observed
            or not b.event_observed
            or a.duration_seconds is None
            or b.duration_seconds is None
        ):
            incomplete += 1
            continue
        values.setdefault(case.stratum, {}).setdefault(case.cluster_id, []).append(
            b.duration_seconds - a.duration_seconds
        )
    means = {s: [mean(v) for v in clusters.values()] for s, clusters in values.items()}
    # Weight by observed completed pairs, not fabricate fixed complete-bank follow-up.
    weights = {s: sum(len(v) for v in clusters.values()) for s, clusters in values.items()}
    total = sum(weights.values())
    estimate, interval = None, None
    if total:
        rng = random.Random(seed)
        estimate = sum(weights[s] / total * mean(means[s]) for s in means)
        boot = sorted(
            sum(weights[s] / total * mean(rng.choice(means[s]) for _ in means[s]) for s in means)
            for _ in range(draws)
        )
        interval = [boot[int(0.025 * (draws - 1))], boot[int(0.975 * (draws - 1))]]
    return {
        "endpoint": "TIME_TO_RECORDED_SUPPORTED_FULL_UPDATE",
        "planned_pairs": len(cases),
        "completed_pairs": total,
        "incomplete_or_censored_pairs": incomplete,
        "completed_pair_difference_seconds": estimate,
        "cluster_bootstrap_95": interval,
        "draws": draws,
        "seed": seed,
        "claim_permitted": False,
        "limitation": (
            "Selected completed-pair sensitivity, not total latency benefit; show censoring"
        ),
    }


def analyze(cases: list[StudyCase], rows: list[AnalysisRow]) -> dict[str, Any]:
    known = {c.case_id: c for c in cases}
    for row in rows:
        case = known.get(row.case_id)
        if (
            case is None
            or row.cluster_id != case.cluster_id
            or row.stratum != case.stratum
            or row.member != case.member
            or row.cluster_representative != case.cluster_representative
            or row.generator_family != case.generator_family
        ):
            raise ValueError("Analysis rows do not match the input catalogue")
        if row.arm not in case.arm_order:
            raise ValueError("Inapplicable arm in analysis")
    if len({r.classification for r in rows}) > 1:
        raise ValueError("Validation and campaign data must not be pooled")
    primary_index(rows)
    tests = [paired(cases, rows, endpoint) for endpoint in PRIMARY]
    adjusted = holm([t["exact_mcnemar_p"] for t in tests])
    for test, adjusted_p in zip(tests, adjusted, strict=True):
        test["holm_adjusted_p"] = adjusted_p
    secondary = [
        paired(cases, rows, e, a) for e in PRIMARY for a in (Arm.P1, Arm.B0, Arm.B1, Arm.B2)
    ]
    secondary.extend(paired(cases, rows, e, Arm.P2, reference=Arm.P1) for e in PRIMARY)
    for table, adjusted_p in zip(
        secondary, holm([t["exact_mcnemar_p"] for t in secondary]), strict=True
    ):
        table["holm_adjusted_p_secondary_family"] = adjusted_p
    index = primary_index(rows)
    endpoints = (
        "correction_success",
        "unsupported_exposed_claim",
        "final_business_state_correct",
        "forbidden_effect",
        "intent_acceptance_correct",
        "incompatible_stale_exposure",
        "correct_final_update",
        "explicit_retraction",
        "clean_task_success",
    )
    status_counts = {
        arm.value: {
            stratum.value: {
                endpoint: dict(
                    Counter(
                        index[(c.case_id, arm)].values.get(endpoint, "UNKNOWN")
                        if (c.case_id, arm) in index
                        else "MISSING"
                        for c in cases
                        if c.stratum is stratum and arm in c.arm_order
                    )
                )
                for endpoint in endpoints
            }
            for stratum in Stratum
        }
        for arm in Arm
    }
    return {
        "version": VERSION,
        "status": "DRAFT_VALIDATION_NOT_CAMPAIGN_RESULTS",
        "planned_inputs": len(cases),
        "planned_clusters": len({c.cluster_id for c in cases}),
        "planned_slots": sum(len(c.arm_order) for c in cases),
        "primary_attempt_rows": sum(r.attempt == 1 for r in rows),
        "additional_attempt_rows_retained": sum(r.attempt != 1 for r in rows),
        "co_primary": tests,
        "task_descriptive": [paired(cases, rows, e, representatives=False) for e in PRIMARY],
        "cluster_sensitivity": [cluster_difference(cases, rows, e) for e in PRIMARY],
        "clean_tolerance": clean_tolerance(cases, rows),
        "paired_latency_sensitivity": paired_latency(cases, rows),
        "survival_by_arm": {
            a.value: kaplan_meier([r for r in rows if r.arm is a and r.attempt == 1])
            for a in (Arm.B3, Arm.P1, Arm.P2)
        },
        "secondary_comparisons": secondary,
        "endpoint_status_counts_by_arm_stratum": status_counts,
        "rare_unsupported_cluster_bounds": {
            a.value: exact_interval(
                sum(
                    r.values.get("unsupported_exposed_claim") == "TRUE"
                    for r in rows
                    if r.arm is a
                    and r.cluster_representative
                    and r.attempt == 1
                    and r.stratum is Stratum.AMBIGUITY
                ),
                sum(
                    r.values.get("unsupported_exposed_claim") in ("TRUE", "FALSE")
                    for r in rows
                    if r.arm is a
                    and r.cluster_representative
                    and r.attempt == 1
                    and r.stratum is Stratum.AMBIGUITY
                ),
            )
            for a in (Arm.B3, Arm.P1, Arm.P2)
        },
        "phase8_started": False,
    }
