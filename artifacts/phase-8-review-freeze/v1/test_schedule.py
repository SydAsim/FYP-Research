import copy
from collections import Counter

import pytest
from build_review import REPO, schedule
from transport import load


def source() -> tuple[dict, dict, list]:  # type: ignore[type-arg]
    return (load(REPO / "research/fixtures/phase8_design_v4/inputs.json"),
            load(REPO / "artifacts/phase-8-study-design/v4/execution-order.json"),
            load(REPO / "artifacts/phase-8-study-design/v4/main-slots.json"))


def test_exact_saved_order_and_original_denominators() -> None:
    bank, order, slots = source()
    originals = copy.deepcopy((bank, order, slots))
    rows = schedule(bank, order, slots)
    assert len(rows) == 1500 and len({r["case_id"] for r in rows}) == 500
    assert Counter(r["arm"] for r in rows) == {"B3": 500, "P1": 500, "P2": 500}
    assert [(r["case_id"], r["arm"]) for r in rows] == [
        (p["case_id"], a) for p in order["rows"] for a in p["arm_order"]]
    assert all(r["execution_id"] is None and r["concurrency"] == 1 for r in rows)
    assert (bank, order, slots) == originals


def test_no_running_inputs_or_order_substitutions() -> None:
    bank, order, slots = source()
    slots[0]["execution_id"] = "must-reconcile"
    with pytest.raises(ValueError, match="UNSTARTED"):
        schedule(bank, order, slots)
    bank, order, slots = source()
    order["rows"][1] = order["rows"][0]
    with pytest.raises(ValueError, match="ORDER_DRIFT"):
        schedule(bank, order, slots)
