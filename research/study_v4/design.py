"""Conditional protocol-input frame, with independent context draws, not new callers."""

import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from research.arms import Arm
from research.provider_simulator.models import ScenarioConfig
from research.scenario_dsl.models import stable_hash
from research.study.inputs import ZONES, recipes
from research.study.models import Intent, Stratum, StudyCase
from research.study.package import write_json

ROOT = Path("artifacts/phase-8-study-design/v4")
VERSION = "phase8-candidate-v4"
SEED = 8042041
ALLOCATION = {
    Stratum.CLEAN: 300,
    Stratum.AMBIGUITY: 100,
    Stratum.EXPOSURE: 60,
    Stratum.BOUNDARY: 40,
}
ARMS = [Arm.B3, Arm.P1, Arm.P2]


def cells() -> list[dict[str, Any]]:
    result = recipes()
    duplicate = next(r for r in result if r["name"] == "duplicate-response")
    duplicate["name"] = "duplicate-request-delivery"
    duplicate["provider"]["faults"][0]["stage"] = "BEFORE_COMMIT"
    duplicate["hooks"] = ["DUPLICATE_IDEMPOTENT_REPLAY"]
    return result


def case_for(
    cell: dict[str, Any], index: int, rng: random.Random, *, calibration: bool
) -> StudyCase:
    zone = str(cell.get("zone", rng.choice(ZONES)))
    start = datetime(
        2028 if calibration else 2029,
        1,
        1,
        rng.randint(9, 13),
        rng.choice((0, 15, 30)),
        tzinfo=ZoneInfo(zone),
    ) + timedelta(days=rng.randrange(300 if calibration else 3650))
    minutes = int(cell.get("duration", rng.choice((30, 45, 60))))
    starts = [start]
    if cell["stratum"] != "CLEAN":
        starts.append(start + timedelta(hours=rng.choice((1, 2, 3))))
    if cell["name"] == "reconnect-third-revision":
        starts.append(starts[-1] + timedelta(days=1, hours=1))
    issue = rng.choice(
        (
            "tap leak",
            "door hinge",
            "window latch",
            "wall patch",
            "sink seal",
            "cabinet handle",
            "drain inspection",
            "floorboard",
            "vent grille",
        )
    )
    order = list(ARMS)
    rng.shuffle(order)
    prefix = "cal-v4" if calibration else "p8v4"
    return StudyCase(
        case_id=f"{prefix}-{index:04d}",
        stratum=Stratum(cell["stratum"]),
        cluster_id="fixed-cell-" + stable_hash(cell)[:12],
        generator_family=cell["name"],
        member=index % 10,
        cluster_representative=index % 10 == 0,
        seed=rng.getrandbits(31),
        resource_binding="NEW_SYNTHETIC_PROPERTY_MAINTENANCE",
        initial_state="EMPTY_RESOURCE",
        issue=issue,
        intents=[
            Intent(
                revision=i + 1,
                start=value,
                end=value + timedelta(minutes=minutes),
                timezone=zone,
                transcript=(
                    f"Book maintenance for {issue} at " if i == 0 else "Change that visit to "
                )
                + f"{value.isoformat()} in {zone} for {minutes} minutes.",
            )
            for i, value in enumerate(starts)
        ],
        correction_barrier=cell["phase"],
        fault_schedule=cell["hooks"],
        provider=ScenarioConfig.model_validate(cell["provider"]),
        speech_exposure=cell["exposure"],
        media="SCRIPTED_TONE_PROTOCOL_PROXY",
        primary_arms=ARMS,
        secondary_arms=[],
        arm_order=order,
        observation_budget_seconds=600,
    )


def materialize(*, calibration: bool = False) -> list[StudyCase]:
    rng = random.Random(SEED + (1 if calibration else 0))
    frame = cells()
    if calibration:
        return [case_for(cell, i + 1, rng, calibration=True) for i, cell in enumerate(frame)]
    result: list[StudyCase] = []
    for stratum, count in ALLOCATION.items():
        support = [c for c in frame if c["stratum"] == stratum.value]
        for _ in range(count):
            # IID uniform cell selection inside stratum, no outcome-based quota fixing.
            result.append(case_for(rng.choice(support), len(result) + 1, rng, calibration=False))
    if len(result) != 500 or len({c.semantic_hash for c in result}) != 500:
        raise ValueError("Main bank must contain exactly 500 distinct externally specified inputs")
    return result


def package() -> dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    main, calibration = materialize(), materialize(calibration=True)
    body = {
        "version": VERSION,
        "status": "DRAFT_NOT_FROZEN",
        "seed": SEED,
        "instrument_schema": "Reuses v3 strict input record; fixture envelope is version v4",
        "sampling_unit": "INDEPENDENT_CONTEXT_DRAW_FROM_FIXED_PROTOCOL_FRAME",
        "estimand": (
            "Arm difference over fixed simulator recipe mixture and declared context generator"
        ),
        "allocation": {s.value: n for s, n in ALLOCATION.items()},
        "arms": [a.value for a in ARMS],
        "frame": cells(),
        "frame_hash": stable_hash(cells()),
        "main_inputs": [c.model_dump(mode="json") for c in main],
        "calibration_inputs": [c.model_dump(mode="json") for c in calibration],
        "main_executions": 0,
        "review_receipt": None,
        "freeze_hash": None,
        "historical_results_reused": False,
        "cell_counts": dict(Counter(c.generator_family for c in main)),
    }
    body["candidate_hash"] = stable_hash(body)
    fixture = Path("research/fixtures/phase8_design_v4/inputs.json")
    if fixture.exists():
        import json

        if json.loads(fixture.read_text(encoding="utf-8")) != body:
            raise ValueError("Candidate input drift requires a new fixture version")
    write_json(fixture, body)
    write_json(ROOT / "candidate.json", body)
    write_json(
        ROOT / "main-slots.json",
        [
            {
                "case_id": c.case_id,
                "arm": a.value,
                "attempt": 1,
                "status": "NOT_STARTED",
                "execution_id": None,
                "fixture_hash": c.fixture_hash,
            }
            for c in main
            for a in c.arm_order
        ],
    )
    write_json(
        ROOT / "calibration-plan.json",
        {
            "version": VERSION,
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "case_ids": [c.case_id for c in calibration],
            "arms": [a.value for a in ARMS],
            "planned_slots": 150,
            "acceptance": "All named preconditions and fault effects evidenced",
            "failures_retained": True,
            "budgets": {
                "provider": 30,
                "runner": 40,
                "scheduler": 15,
                "barrier": 120,
                "core_lease": 180,
                "repair_lease": 30,
                "reconcile": 8,
                "drain_passes": 30,
                "permit_ttl": 30,
                "recovery": 40,
                "observation": 600,
            },
            "plan_hash": stable_hash([c.model_dump(mode="json") for c in calibration]),
            "main_started": False,
        },
    )
    return {
        "main_inputs": 500,
        "main_slots": 1500,
        "calibration_slots": 150,
        "allocation": body["allocation"],
        "candidate_hash": body["candidate_hash"],
    }


if __name__ == "__main__":
    print(package())
