"""Independent scenario instances; acoustic variants remain within one scenario."""

from datetime import timedelta
from typing import Any

from research.replay.phase6_p8_witness import witness_case
from research.runner.acoustic import acoustic_case
from research.runner.acoustic_source import CONDITIONS
from research.runner.paired import ALL_ARMS, DEFAULT_ARMS
from research.runner.playout_paired import playout_case
from research.scenario_dsl.catalog import (
    CLEAN_CASES,
    CONFLICT_COVERING,
    DELAY_COVERING,
    PARTIAL_COVERING,
    READ_COVERING,
    REDIS_COVERING,
    REFUSAL_COVERING,
    case_for,
)
from research.scenario_dsl.covering import covering_array
from research.scenario_dsl.models import Barrier, CleanScenarioCase, ScenarioCase, stable_hash

VERSION = "phase7-pilot-plan-v1"


def pilot_plan(acoustic: list[dict[str, Any]]) -> dict[str, Any]:
    if {e["condition"] for e in acoustic} != set(CONDITIONS) or len(acoustic) != 6:
        raise ValueError("Pilot requires exactly the six declared acoustic versions")
    rows: list[dict[str, Any]] = []

    def add(
        case: ScenarioCase | CleanScenarioCase,
        kind: str,
        *,
        arms: tuple[str, ...] = tuple(a.value for a in ALL_ARMS),
        group: str | None = None,
        variant: str = "PRIMARY",
        voice: dict[str, Any] | None = None,
    ) -> None:
        rows.append(
            {
                "scenario_id": group or case.scenario_key,
                "template_id": case.scenario_key,
                "variant": variant,
                "kind": kind,
                "arms": arms,
                "case": case.model_dump(mode="json"),
                "fixture_hash": case.fixture_hash,
                "voice_evidence": voice,
            }
        )

    for index, source in enumerate(covering_array()):
        body = source.model_dump(mode="json")
        # Distinct pre-specified inputs, rather than reruns distinguished only by seed.
        offset = timedelta(days=10 + index)
        initial, final = source.initial_start + offset, source.final_start + offset
        body.update(
            fixture_version=VERSION,
            scenario_key=f"pilot-secondary-{index + 1:02d}",
            initial_start=initial.isoformat(),
            final_start=final.isoformat(),
            initial_transcript=f"Book maintenance at {initial.isoformat()} in {source.timezone}.",
            correction_transcript=(
                "Cancel this appointment."
                if source.revision_type == "RETRACTION"
                else f"My final maintenance request is {final.isoformat()} in {source.timezone}."
            ),
        )
        add(ScenarioCase.model_validate(body), "provider")
    for boundary in (Barrier.P0, Barrier.P1, Barrier.P2, Barrier.P4, Barrier.P5):
        add(case_for(boundary, key=f"pilot-{boundary.value.lower()}"), "provider")
    for case in (
        DELAY_COVERING[0],
        REFUSAL_COVERING[0],
        PARTIAL_COVERING[0],
        REDIS_COVERING[0],
        READ_COVERING[0],
    ):
        add(case, "provider")
    add(CONFLICT_COVERING[0], "provider", arms=tuple(a.value for a in DEFAULT_ARMS))
    for boundary in (Barrier.P6, Barrier.P7, Barrier.P9):
        add(playout_case(boundary), "playout")
    add(witness_case(), "p8")
    for index in range(4):
        body = CLEAN_CASES[0].model_dump(mode="json")
        start = CLEAN_CASES[0].final_start + timedelta(days=40 + index, hours=index)
        body.update(
            fixture_version=VERSION,
            scenario_key=f"pilot-clean-{index + 1:02d}",
            final_start=start.isoformat(),
            transcript=f"Book maintenance at {start.isoformat()} in Asia/Karachi.",
        )
        add(CleanScenarioCase.model_validate(body), "clean")
    for evidence in acoustic:
        condition = evidence["condition"]
        add(
            acoustic_case(evidence),
            "clean",
            group="pilot-clean-acoustic",
            variant="PRIMARY" if condition == "LOCAL_RECORDED_CLEAN" else condition,
            voice=evidence,
        )
    primary = [row for row in rows if row["variant"] == "PRIMARY"]
    if len(primary) != 40 or len({row["scenario_id"] for row in primary}) != 40:
        raise ValueError("Pilot must have exactly 40 distinct primary scenario instances")
    result = {
        "version": VERSION,
        "scope": "PROTOCOL_DEBUGGING_NOT_FINAL_EVIDENCE",
        "independent_scenario_instances": 40,
        "scenario_versions": len(rows),
        "planned_executions": sum(len(row["arms"]) for row in rows),
        "repetition_policy": "Acoustic variants share one scenario; never increase independent n",
        "sampling": (
            "Purposive structural coverage; template dependence limits population inference"
        ),
        "cases": rows,
    }
    result["hash"] = stable_hash(result)
    return result
