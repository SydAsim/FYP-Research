"""Research gates: main rejection, fixed design, unchanged windows and resource stops."""

import json
from pathlib import Path

import pytest
from plan import ARMS, FAMILIES, Slot, budget, build, eligible

from research.study.models import StudyCase


def fixtures() -> list[StudyCase]:
    path = Path("research/fixtures/phase8_design_v4/inputs.json")
    return [StudyCase.model_validate(c) for c in json.loads(path.read_text())["calibration_inputs"]]


def test_fixed_references_and_schedule_repetitions() -> None:
    slots = build(fixtures())
    assert len(slots) == 24
    assert slots[0].arm == "B3" and slots[0].case.generator_family == FAMILIES[0]
    originals = {s.slot_id: s for s in slots[:18]}
    assert {(s.case.generator_family, s.arm) for s in originals.values()} == {
        (f, a) for f in FAMILIES for a in ARMS
    }
    for repeat in slots[18:]:
        reference = originals[str(repeat.reference_slot)]
        assert repeat.case.semantic_hash == reference.case.semantic_hash
        assert repeat.case.cluster_id == reference.case.cluster_id
        assert repeat.case.case_id != reference.case.case_id
        assert repeat.label == "PLANNED_SCHEDULE_REPEAT"
    assert [sum(s.block == b for s in slots) for b in (19, 20, 21)] == [2, 2, 2]


def test_main_and_shortened_window_are_rejected() -> None:
    slot = build(fixtures())[0].model_dump(mode="json")
    slot["case"]["case_id"] = "main-v4-0001"
    with pytest.raises(ValueError, match="MAIN_INPUT_GUARD"):
        Slot.model_validate(slot)
    slot["case"]["case_id"] = "cal-v4-linux-v1-p83-v1-test"
    slot["case"]["observation_budget_seconds"] = 599
    with pytest.raises(ValueError, match="UNCHANGED_WINDOW_REQUIRED"):
        Slot.model_validate(slot)


def test_headroom_and_original_deadline_gate() -> None:
    gib = 1024**3
    first = {"minimum_available_memory_bytes": 6 * gib, "peak_used_memory_bytes": 2 * gib}
    current = {
        "available_memory_bytes": 5 * gib,
        "system_free_bytes": 8 * gib,
        "output_free_bytes": 3 * gib,
        "backup_free_bytes": 3 * gib,
    }
    assert eligible(first, current, 1200)
    assert not eligible(first, current, 1199)
    assert not eligible(first, {**current, "available_memory_bytes": 3 * gib}, 1500)
    assert not eligible({**first, "minimum_available_memory_bytes": 3 * gib}, current, 1500)
    assert not eligible(first, {**current, "backup_free_bytes": gib}, 1500)


def test_cost_is_decimal_and_launch_cannot_exceed_ceiling() -> None:
    assert budget("0.1197", "0.005", "0.096")["within_ceiling"] == "True"
    assert budget("1.00", "0.005", "0.096")["within_ceiling"] == "False"
