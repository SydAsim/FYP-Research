"""Reproducible planning estimates, never a launch or billing guarantee."""

from datetime import timedelta
from pathlib import Path
from typing import Any

from controls import read, utc, write_new
from handover import HERE, REPO, ContinuationPolicy


def calculate() -> dict[str, Any]:
    policy = ContinuationPolicy.model_validate(
        read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json")
    )
    at = utc()
    pilot = read(REPO / "artifacts/phase-8-review-freeze/v2/measurements.json")
    qualified = read(REPO / "artifacts/phase-8-runner-amendment/v1/live-attempt2/result.json")
    rows = read(HERE / "saved-identities.json")["rows"]
    remaining = sum(r["state"] == "PLANNED" for r in rows)
    slope = (
        policy.compute_usd_hour
        + policy.ipv4_usd_hour
        + (policy.volume_gib * policy.disk_usd_gib_month / 730)
    )
    intercept = policy.committed_cost(policy.host_started_at)
    cost_stop = policy.host_started_at + timedelta(hours=(55 - intercept) / slope - 0.5)
    time_cutoff = policy.stop_at - timedelta(seconds=policy.admission_cutoff_seconds)
    binding_cutoff = min(cost_stop, time_cutoff)
    references = {
        "historical_pilot_median_reference": remaining * pilot["serial_median_seconds"] / 3600,
        "four_local_amendment_mean_reference": remaining * qualified["elapsed_seconds"] / 4 / 3600,
        "planning_12_days": 288.0,
        "planning_13_days_conservative": 312.0,
    }
    estimates = {}
    for name, hours in references.items():
        finish = at + timedelta(hours=2 + hours)
        cost = policy.committed_cost(finish + timedelta(minutes=30))
        estimates[name] = {
            "remaining_execution_hours": hours,
            "setup_hours_allowance": 2,
            "finish_if_setup_begins_as_of_utc": finish.isoformat(),
            "conservative_committed_usd_at_finish_plus_30min": cost,
            "fits_cost_admission_guard": cost < 55,
            "fits_original_time_cutoff": finish < time_cutoff,
            "latest_setup_start_utc_conservative": (
                binding_cutoff - timedelta(hours=2 + hours)
            ).isoformat(),
        }
    pricing = read(HERE / "pricing-read.json")
    current_rates = {}
    for name, data in pricing["return_value"].items():
        dimensions = [
            d
            for p in data["products"]
            for t in p["terms"]["OnDemand"].values()
            for d in t["priceDimensions"].values()
            if d.get("beginRange") == "0"
        ]
        rates = {float(d["pricePerUnit"]["USD"]) for d in dimensions}
        if len(rates) != 1:
            raise ValueError("AMBIGUOUS_PRICE_RATE")
        current_rates[name] = rates.pop()
    expected = {
        "compute": policy.compute_usd_hour,
        "disk": policy.disk_usd_gib_month,
        "ipv4": policy.ipv4_usd_hour,
        "s3": policy.s3_usd_gib_month,
    }
    if current_rates != expected:
        raise ValueError("REVIEWED_PRICE_DRIFT")
    aws = read(HERE / "aws-read-attempt2.json")["return_value"]
    return {
        "kind": "REVIEW_ESTIMATE_NOT_LAUNCH_OR_FINAL_BILL",
        "as_of_utc": at.isoformat(),
        "original_start_utc": policy.host_started_at.isoformat(),
        "operational_deadline_utc": policy.stop_at.isoformat(),
        "original_time_admission_cutoff_utc": time_cutoff.isoformat(),
        "conservative_cost_admission_cutoff_utc": cost_stop.isoformat(),
        "remaining_hours_to_hard_deadline": (policy.stop_at - at).total_seconds() / 3600,
        "remaining_originals": remaining,
        "unchanged_budget_usd": 65,
        "unchanged_admission_guard_usd": 55,
        "cold_handover_reserve_usd": 1.25,
        "host_scope": "one fresh m7i-flex.large/160GiB plus original stopped disk <=48h",
        "current_rates": current_rates,
        "rates_match_accepted": True,
        "aws_readonly_calls": 7,
        "aws_mutations": 0,
        "original_host_state": aws["host"]["Reservations"][0]["Instances"][0]["State"]["Name"],
        "reported_credit_usd": aws["credits"]["accountPlanRemainingCredits"]["amount"],
        "plan": aws["credits"]["accountPlanType"],
        "maximum_original_360h_conservative_usd": policy.committed_cost(policy.stop_at),
        "estimates": estimates,
        "storage_gib": {
            "raw_projection_remaining": pilot["raw_projected_bytes"] * remaining / 1500 / 1024**3,
            "backup_projection_remaining": pilot["backup_projected_bytes"]
            * remaining
            / 1500
            / 1024**3,
            "archive_projection_remaining": pilot["archive_projected_bytes"]
            * remaining
            / 1500
            / 1024**3,
            "working_allowance": 50,
            "backup_allowance": 50,
            "os_images": 25,
            "headroom": 35,
            "cloud_versions_limit": 30,
        },
        "limitations": [
            "Pilot median and four-calibration mean are references, not whole-bank measurements.",
            "12-13 days remains a planning range; no completion guarantee or limit extension.",
            "Elapsed-clock cost accounting conservatively charges paused time; do not reset it.",
            "Old disk/early-host spending stays reserved inside the existing guard; no new budget.",
            "Retained disk review: 2026-10-09T15:57:46Z. Indefinite retention is not funded.",
            "Credits/billing can lag; prices, credits and fit need a fresh predeployment check.",
            "Request/transfer allowance remains $5; taxes and unrelated project costs excluded.",
        ],
    }


if __name__ == "__main__":
    import sys

    destination = Path(sys.argv[1])
    write_new(destination, calculate())
    print(destination)
