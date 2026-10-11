"""Generate a proposal, never an acceptance, freeze, execution ledger or launch."""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from transport import load, record, sha

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PILOT = Path("E:/P83R7/p83-c525d267c8ec/x/fyp-p83-v1")


def schedule(bank: dict[str, Any], order: dict[str, Any],
             slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = {case["case_id"]: case for case in bank["main_inputs"]}
    originals = {(slot["case_id"], slot["arm"]): slot for slot in slots}
    if (len(cases) != 500 or len(originals) != 1500 or len(order["rows"]) != 500
            or {slot["status"] for slot in slots} != {"NOT_STARTED"}
            or any(slot["execution_id"] is not None for slot in slots)):
        raise ValueError("UNCHANGED_UNSTARTED_500_INPUT_SCOPE_REQUIRED")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position in order["rows"]:
        case = cases[position["case_id"]]
        if case["case_id"] in seen or position["arm_order"] != case["arm_order"]:
            raise ValueError("SAVED_INPUT_OR_ARM_ORDER_DRIFT")
        seen.add(case["case_id"])
        for arm in position["arm_order"]:
            original = originals[case["case_id"], arm]
            rows.append({
                "sequence": len(rows) + 1, "input_order": position["order"],
                "batch_id": position["batch_id"], "case_id": case["case_id"], "arm": arm,
                "stratum": case["stratum"], "recipe": case["generator_family"],
                "fixture_hash": original["fixture_hash"], "lane": "A", "concurrency": 1,
                "window_seconds": 600, "attempt": 1, "status": "NOT_STARTED",
                "execution_id": None,
            })
    if len(rows) != 1500 or len(seen) != 500:
        raise ValueError("PLANNED_DENOMINATOR_DRIFT")
    return rows


def prices(label: str) -> list[dict[str, Any]]:
    response = load(HERE / f"pricing-{label}-response.json")
    if response.get("exit") != 0:
        raise ValueError("FRESH_PRICE_LOOKUP_REQUIRED")
    result = []
    for text in json.loads(response["stdout"])["PriceList"]:
        product = json.loads(text)
        for term in product["terms"]["OnDemand"].values():
            for price in term["priceDimensions"].values():
                result.append({"usage": product["product"]["attributes"].get("usagetype"),
                               **price})
    return result


def main() -> None:
    bank_path = REPO / "research/fixtures/phase8_design_v4/inputs.json"
    order_path = REPO / "artifacts/phase-8-study-design/v4/execution-order.json"
    slots_path = REPO / "artifacts/phase-8-study-design/v4/main-slots.json"
    bank, order, slots = load(bank_path), load(order_path), load(slots_path)
    rows = schedule(bank, order, slots)
    record(HERE / "schedule.json", {"status": "REVIEW_ONLY_NOT_FROZEN", "rows": rows})
    with (HERE / "schedule.csv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    pilot = load(PILOT / "accounting.json")
    compute = float(prices("compute")[0]["pricePerUnit"]["USD"])
    disk = float(prices("disk")[0]["pricePerUnit"]["USD"])
    ipv4 = next(float(p["pricePerUnit"]["USD"]) for p in prices("ipv4")
                if p["usage"] == "APS2-PublicIPv4:InUseAddress")
    s3 = next(float(p["pricePerUnit"]["USD"]) for p in prices("s3")
              if p["beginRange"] == "0")
    budget = {}
    for name, hours in [("reference", pilot["serial_1500_reference_hours"]),
                        ("planning_13_days", 312), ("maximum_15_days", 360)]:
        compute_cost = hours * compute
        address_cost = hours * ipv4
        disk_cost = (hours + 48) / 730 * 160 * disk
        storage_cost = 30 * s3  # one month, 30 GiB includes all retained object versions
        budget[name] = {"running_hours": hours, "compute_usd": compute_cost,
                        "ipv4_usd": address_cost, "disk_usd_including_48h_retention": disk_cost,
                        "s3_30gib_month_usd": storage_cost,
                        "request_transfer_monitoring_allowance_usd": 5,
                        "total_usd": compute_cost + address_cost + disk_cost + storage_cost + 5}
    record(HERE / "budget.json", {
        "status": "PROPOSED_NOT_AUTHORIZED", "currency": "USD", "ceiling": 65,
        "rates": {"compute_per_hour": compute, "ipv4_per_hour": ipv4,
                  "gp3_gib_month": disk, "s3_standard_gib_month": s3},
        "estimates": budget, "exclude": "Other project resources, taxes and exchange rates",
        "plan_state": json.loads(load(HERE / "pricing-plan-response.json")["stdout"]),
        "credit_or_discount_assumed": False,
        "controls": "360h absolute compute lifetime; <=48h stopped disk; 30GiB S3 version cap; "
                    "estimated committed-cost admission stop at USD55; USD10 safety reserve. "
                    "AWS billing alerts are delayed notices, not a hard spending lock.",
    })
    specials = {"restart-before-repair", "redis-loss"}
    qualified_adjacent = [(a["sequence"], b["sequence"]) for a, b in
                          zip(rows, rows[1:], strict=False)
                          if {a["recipe"], b["recipe"]} == specials and a["arm"] == b["arm"]]
    record(HERE / "measurements.json", {
        "at": datetime.now(UTC).isoformat(), "classification": "CALIBRATION_PROJECTION_NOT_MAIN",
        "pilot_slots": 24, "serial_median_seconds": pilot["serial_block_median_seconds"],
        "pair_median_seconds": pilot["paired_block_median_seconds"],
        "reference_hours": pilot["serial_1500_reference_hours"],
        "planning_days": [12, 13], "maximum_days": 15,
        "raw_projected_bytes": pilot["raw_directory_bytes"] * 1500 / 24,
        "backup_projected_bytes": pilot["backup_directory_bytes"] * 1500 / 24,
        "archive_projected_bytes": 95449610 * 1500 / 24,
        "growth_caveat": "Pilot mix is not a whole-bank capacity bound; WAL allocation "
                          "is not write throughput; enforce free-space/growth gates",
        "pair_peak_used_bytes": max(b["peak_used_memory_bytes"] for b in pilot["blocks"]
                                    if len(b["slots"]) == 2),
        "pair_min_available_bytes": min(b["minimum_available_memory_bytes"]
                                        for b in pilot["blocks"] if len(b["slots"]) == 2),
        "pair_max_cpu_fraction": max(b["maximum_cpu_fraction"] for b in pilot["blocks"]
                                     if len(b["slots"]) == 2),
        "maximum_poll_gap_seconds": max(s["measurement"]["maximum_start_gap_seconds"]
                                        for s in pilot["slots"]),
        "special_main_slots": sum(r["recipe"] in specials for r in rows),
        "eligible_adjacent_saved_order_pairs": qualified_adjacent,
        "stratum_input_counts": dict(Counter(c["stratum"] for c in bank["main_inputs"])),
        "arm_slot_counts": dict(Counter(r["arm"] for r in rows)),
    })
    record(HERE / "acceptance-status.json", {
        "stage": "REVIEW", "review_accepted": False, "review_receipt": None,
        "freeze_hash": None, "launch_authorization": None, "main_started": False,
        "main_executions": 0, "new_aws_resources_created": 0,
        "source_references": {str(p.relative_to(REPO)): sha(p)
                              for p in [bank_path, order_path, slots_path]},
    })
    print("Review schedule prepared: 500 inputs, 1500 serial slots; no freeze or launch.")


if __name__ == "__main__":
    main()
