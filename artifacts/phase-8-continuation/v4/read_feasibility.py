"""Read-only AWS state/prices and deterministic unchanged-clock feasibility."""
from __future__ import annotations

import concurrent.futures
import json
import os
import sqlite3
import statistics
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNTIME = Path("E:/p8v4/source/artifacts/phase-8-runner-amendment/v4-complete")
sys.path.insert(0, str(RUNTIME))
from controls import read, write_new  # noqa: E402
from handover import ContinuationPolicy  # noqa: E402

RUN = "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"
BUCKET = "fyp-p82-20261005-018da1d6-803656589923"


def call(name: str, args: list[str], region: str = "ap-southeast-2") -> Any:
    if "--reuse-reads" in sys.argv:
        saved = read(HERE / "read-only-aws" / (name + ".json"))
        assert saved["exit"] == 0 and saved["args"] == args and saved["region"] == region
        return json.loads(saved["result"])
    reply = subprocess.run(["aws", *args, "--profile", "fyp-research", "--region", region, "--output", "json", "--no-cli-pager"], capture_output=True, encoding="utf-8", timeout=90, env={**os.environ, "PYTHONUTF8": "1"})
    write_new(HERE / "read-only-aws" / (name + ".json"), {"at_utc": datetime.now(UTC).isoformat(), "args": args, "region": region, "exit": reply.returncode, "stderr": reply.stderr, "result": reply.stdout})
    if reply.returncode:
        raise RuntimeError("AWS_READ_FAILED: " + name)
    return json.loads(reply.stdout)


def price(name: str, service: str, filters: dict[str, str]) -> Any:
    return call(name, ["pricing", "get-products", "--service-code", service, "--filters", json.dumps([{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items()])], "us-east-1")


def rates(data: Any) -> list[float]:
    return sorted({float(d["pricePerUnit"]["USD"]) for p in data["PriceList"] for t in json.loads(p)["terms"].get("OnDemand", {}).values() for d in t["priceDimensions"].values()})


def main() -> None:
    jobs = {
        "plan": lambda: call("plan", ["freetier", "get-account-plan-state"]),
        "hosts": lambda: call("hosts", ["ec2", "describe-instances", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "volumes": lambda: call("volumes", ["ec2", "describe-volumes", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "versions": lambda: call("versions", ["s3api", "list-object-versions", "--bucket", BUCKET, "--prefix", "exports/phase8/" + RUN + "/"]),
        "compute": lambda: price("compute", "AmazonEC2", {"regionCode": "ap-southeast-2", "instanceType": "m7i-flex.large", "operatingSystem": "Linux", "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"}),
        "disk": lambda: price("disk", "AmazonEC2", {"regionCode": "ap-southeast-2", "volumeApiName": "gp3", "productFamily": "Storage"}),
        "ipv4": lambda: price("ipv4", "AmazonVPC", {"regionCode": "ap-southeast-2", "usagetype": "APS2-PublicIPv4:InUseAddress"}),
        "s3": lambda: price("s3", "AmazonS3", {"regionCode": "ap-southeast-2", "volumeType": "Standard", "productFamily": "Storage"}),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        running = {name: pool.submit(fn) for name, fn in jobs.items()}
        data = {name: future.result() for name, future in running.items()}
    actual_rates = {name: rates(data[name]) for name in ("compute", "disk", "ipv4", "s3")}
    expected = {"compute": .1197, "disk": .096, "ipv4": .005, "s3": .025}
    assert all(v in actual_rates[k] for k, v in expected.items())
    hosts = [i for r in data["hosts"]["Reservations"] for i in r["Instances"]]
    current = next(h for h in hosts if h["InstanceId"] == "i-002b63326e1566005")
    assert current["State"]["Name"] == "stopped"
    assert not any(h["State"]["Name"] in ("running", "pending") for h in hosts)
    assert data["plan"]["accountPlanType"] == "FREE" and data["plan"]["accountPlanStatus"] == "ACTIVE"
    assert float(data["plan"]["accountPlanRemainingCredits"]["amount"]) >= 65
    policy = ContinuationPolicy.model_validate(read(RUNTIME / "original-launch-policy.json"))
    now = datetime.now(UTC)
    with sqlite3.connect(RUNTIME / "boundary/campaign.sqlite3") as connection:
        notices = [json.loads(r[0]) for r in connection.execute("SELECT body FROM notices ORDER BY n")]
    rows = read(RUNTIME / "saved-boundary.json")["rows"]
    admitted = {n["execution_id"]: datetime.fromisoformat(n["at"]) for n in notices if n["kind"] == "ADMITTED"}
    done = {n["execution_id"]: datetime.fromisoformat(n["at"]) for n in notices if n["kind"] == "TRANSITION" and n.get("state") == "BACKED_UP"}
    durations = [(done[r["execution_id"]] - admitted[r["execution_id"]]).total_seconds() for r in rows[2:38]]
    cadence = [(admitted[b["execution_id"]] - admitted[a["execution_id"]]).total_seconds() for a, b in zip(rows[2:37], rows[3:38], strict=True)]
    measured_hours = 1462 * statistics.mean(cadence) / 3600
    # Preserve v3's reviewed 290-hour / 1498-slot planning allowance, scaled only
    # by the number genuinely completed. Do not promise all recipe runtimes tie.
    allowance_hours = 290 * 1462 / 1498
    finish = now + timedelta(hours=allowance_hours)
    shutdown_finish = finish + timedelta(minutes=30)
    conservative = policy.committed_cost(shutdown_finish)
    # Actual prior segments and disks separately estimated, including the stopped
    # current root through its unchanged 48-hour decision bound, then fresh disk.
    segments = [
        (datetime(2026, 10, 7, 15, 29, 5, tzinfo=UTC), datetime(2026, 10, 7, 15, 57, 46, tzinfo=UTC)),
        (datetime(2026, 10, 7, 20, 26, 9, tzinfo=UTC), datetime(2026, 10, 7, 21, 5, 38, tzinfo=UTC)),
        (datetime(2026, 10, 8, 7, 5, 46, tzinfo=UTC), datetime(2026, 10, 8, 17, 15, 30, tzinfo=UTC)),
    ]
    prior_compute = sum((b-a).total_seconds()/3600 for a,b in segments) * (.1197 + .005)
    disk_hours = ((datetime(2026,10,7,20,46,tzinfo=UTC)-segments[0][0]).total_seconds()
                  + (datetime(2026,10,8,7,26,tzinfo=UTC)-segments[1][0]).total_seconds()
                  + (datetime(2026,10,10,17,14,53,76527,tzinfo=UTC)-segments[2][0]).total_seconds()) / 3600
    prior_disk = disk_hours * 160 * .096 / 730
    explicit = prior_compute + prior_disk + (allowance_hours+.5) * (.1197+.005+160*.096/730) + 48*160*.096/730 + 30*.025 + 5 + 1.25
    storage = sum(v["Size"] for v in data["versions"].get("Versions", []))
    archive_sizes = [p["cloud"]["bytes"] for p in read(RUNTIME / "retained-slot-proofs.json")]
    threshold_time = policy.host_started_at + timedelta(hours=(55-1.25-.75-5-(48/730*160*.096))/(.1197+.005+160*.096/730))
    result = {
        "status": "PASS_CONDITIONAL" if conservative < 55 and explicit < 55 and finish < policy.stop_at-timedelta(minutes=30) else "FAIL_DO_NOT_PROVISION",
        "at_utc": now.isoformat(), "original_deadline": policy.stop_at.isoformat(), "clock_reset": False,
        "remaining_originals": 1462, "independent_inputs": 500, "arms": ["B3","P1","P2"],
        "measured_36_slot_seconds": {"min": min(durations), "mean": statistics.mean(durations), "max": max(durations)},
        "measured_35_admission_intervals_seconds": {"min": min(cadence), "mean": statistics.mean(cadence), "max": max(cadence)},
        "throughput_projection_hours": measured_hours, "reviewed_allowance_remaining_hours": allowance_hours,
        "allowance_finish_utc_if_started_now": finish.isoformat(), "absolute_available_hours": (policy.stop_at-now).total_seconds()/3600,
        "conservative_original_elapsed_clock_cost_usd": conservative, "explicit_resources_cost_usd": explicit,
        "prior_compute_ipv4_usd": prior_compute, "prior_disk_through_original_retention_bound_usd": prior_disk,
        "guard_usd": 55, "total_policy_usd": 65, "handover_reserve_within_limits_usd": 1.25,
        "conservative_guard_time_utc": threshold_time.isoformat(), "review_and_deployment_slack_hours": (threshold_time-shutdown_finish).total_seconds()/3600,
        "rates": actual_rates, "plan": data["plan"], "current_host": {"id":current["InstanceId"],"state":current["State"]["Name"]},
        "retained_volumes": data["volumes"], "all_version_evidence_bytes": storage,
        "cloud_cap_bytes": policy.cloud_limit_bytes, "observed_backup_mean_bytes": statistics.mean(archive_sizes), "observed_backup_max_bytes": max(archive_sizes),
        "limitations": ["35 cadence intervals cover only the first 13 distinct inputs, not all 50 recipes", "No speedup or shorter window assumed", "Additional v4 history verification overhead is bounded locally but fresh-host throughput is not yet measured", "The cost guard is an estimate, not a real-time AWS invoice cap", "Stopped root retention decision remains due 2026-10-10T17:14:53.076527Z; deletion is not authorized here", "Feasibility must be recalculated after review and before provisioning/admission"],
        "new_compute_or_cloud_writes": False,
    }
    write_new(HERE / "feasibility.json", result)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
