"""A deterministic constrained pairwise selection; never a Cartesian execution."""

from itertools import combinations, product
from typing import Any

from research.scenario_dsl.catalog import MULTI_COVERING, REVISION_COVERING, case_for
from research.scenario_dsl.models import (
    Barrier,
    FaultFamily,
    ProviderCapability,
    ProviderVisibility,
    ScenarioCase,
    stable_hash,
)

DIMENSIONS = (
    "revision_type",
    "action_semantics",
    "workflow_shape",
    "acoustic_condition",
    "provider_capability",
    "visibility",
    "speech_exposure",
    "fault_family",
)


def pairs(case: ScenarioCase) -> set[tuple[str, str, str, str]]:
    row = case.model_dump(mode="json")
    return {
        (left, str(row[left]), right, str(row[right]))
        for left, right in combinations(DIMENSIONS, 2)
    }


def candidates() -> tuple[ScenarioCase, ...]:
    revisions = (case_for(Barrier.P3, fault=FaultFamily.RESPONSE_LOSS), *REVISION_COVERING)
    rows = []
    for revision, capability, visibility, multi in product(
        revisions, ProviderCapability, ProviderVisibility, (False, True)
    ):
        # A permanently unavailable provider cannot finish the independent side booking.
        if multi and visibility is ProviderVisibility.UNAVAILABLE:
            continue
        body = {
            **revision.model_dump(mode="json"),
            "fixture_version": "phase6-secondary-pairwise-v3",
            "provider_capability": capability.value,
            "visibility": visibility.value,
            "workflow_shape": MULTI_COVERING[0].workflow_shape
            if multi
            else "ONE_TICKET_ONE_APPOINTMENT",
        }
        body["scenario_key"] = f"secondary-{stable_hash(body)[:16]}"
        rows.append(ScenarioCase.model_validate(body))
    return tuple(rows)


def covering_array() -> tuple[ScenarioCase, ...]:
    pool = list(candidates())
    uncovered = set().union(*(pairs(case) for case in pool))
    selected = []
    while uncovered:
        best = max(pool, key=lambda case: (len(pairs(case) & uncovered), case.scenario_key))
        if not pairs(best) & uncovered:
            raise AssertionError("Constrained pair coverage cannot be completed")
        selected.append(best)
        uncovered -= pairs(best)
        pool.remove(best)
    return tuple(selected)


def coverage_manifest() -> dict[str, Any]:
    pool = candidates()
    selected = covering_array()
    feasible = set().union(*(pairs(case) for case in pool))
    covered = set().union(*(pairs(case) for case in selected))
    return {
        "version": "phase6-secondary-pairwise-v3",
        "dimensions": DIMENSIONS,
        "candidate_count": len(pool),
        "selected_count": len(selected),
        "feasible_pair_count": len(feasible),
        "covered_pair_count": len(covered),
        "uncovered_pairs": sorted(feasible - covered),
        "constraints": [
            "Secondary combinations fix P3 hidden-commit response loss and scripted recognition",
            "Multi-workflow with permanently unavailable evidence is infeasible "
            "for side completion",
            "Acoustic and other fault levels use their separately mandatory covering fixtures",
        ],
        "scenarios": [case.model_dump(mode="json") for case in selected],
    }
