"""Read-only AWS qualification and deterministic unchanged-policy accounting."""
from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CANDIDATE = REPO / "artifacts/phase-8-runner-amendment/v3"
sys.path.insert(0, str(CANDIDATE))
from controls import read, write_new
from handover import ContinuationPolicy

BUCKET = "fyp-p82-20261005-018da1d6-803656589923"
RUN = "p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"


def cli(name: str, args: list[str], region: str = "ap-southeast-2") -> dict:
    result = subprocess.run(["aws", *args, "--profile", "fyp-research", "--region", region,
                             "--no-cli-pager", "--output", "json"], capture_output=True, text=True, timeout=90)
    record = {"at_utc": datetime.now(UTC).isoformat(), "args": args, "region": region,
              "exit": result.returncode, "stderr": result.stderr, "result": json.loads(result.stdout) if result.returncode == 0 else result.stdout}
    write_new(HERE / (name + ".json"), record)
    if result.returncode:
        raise RuntimeError("AWS_READ_FAILED: " + name)
    return record["result"]


def price(name: str, service: str, filters: dict[str, str]) -> dict:
    return cli(name, ["pricing", "get-products", "--service-code", service, "--filters",
                     json.dumps([{"Type": "TERM_MATCH", "Field": k, "Value": v} for k, v in filters.items()])], "us-east-1")


def rates(value: dict) -> list[float]:
    return sorted({float(d["pricePerUnit"]["USD"]) for raw in value["PriceList"]
                   for offer in json.loads(raw)["terms"].get("OnDemand", {}).values()
                   for d in offer["priceDimensions"].values()})


def main() -> None:
    tasks = {
        "plan": lambda: cli("aws-plan-current", ["freetier", "get-account-plan-state"]),
        "instances": lambda: cli("aws-project-instances", ["ec2", "describe-instances", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "volumes": lambda: cli("aws-project-volumes", ["ec2", "describe-volumes", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "image": lambda: cli("aws-qualified-image", ["ec2", "describe-images", "--image-ids", "ami-090b1140798d2d006"]),
        "network": lambda: cli("aws-qualified-network", ["ec2", "describe-security-groups", "--group-ids", "sg-076d87ac5db0a6f52"]),
        "profile": lambda: cli("aws-qualified-profile", ["iam", "get-instance-profile", "--instance-profile-name", "FYP-" + RUN]),
        "versioning": lambda: cli("aws-evidence-versioning", ["s3api", "get-bucket-versioning", "--bucket", BUCKET]),
        "versions": lambda: cli("aws-evidence-versions", ["s3api", "list-object-versions", "--bucket", BUCKET]),
        "compute": lambda: price("price-compute", "AmazonEC2", {"regionCode":"ap-southeast-2", "instanceType":"m7i-flex.large", "operatingSystem":"Linux", "tenancy":"Shared", "preInstalledSw":"NA", "capacitystatus":"Used"}),
        "disk": lambda: price("price-disk", "AmazonEC2", {"regionCode":"ap-southeast-2", "volumeApiName":"gp3", "productFamily":"Storage"}),
        "ipv4": lambda: price("price-ipv4", "AmazonVPC", {"regionCode":"ap-southeast-2", "usagetype":"APS2-PublicIPv4:InUseAddress"}),
        "s3": lambda: price("price-evidence", "AmazonS3", {"regionCode":"ap-southeast-2", "volumeType":"Standard", "productFamily":"Storage"}),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {name: pool.submit(fn) for name, fn in tasks.items()}
        data = {name: future.result() for name, future in futures.items()}
    measured = {name: rates(data[name]) for name in ("compute", "disk", "ipv4", "s3")}
    expected = {"compute": .1197, "disk": .096, "ipv4": .005, "s3": .025}
    if any(v not in measured[k] for k, v in expected.items()):
        raise ValueError("CURRENT_PRICES_DO_NOT_MATCH_ACCEPTED")
    plan = data["plan"]
    if plan["accountPlanType"] != "FREE" or plan["accountPlanStatus"] != "ACTIVE" or float(plan["accountPlanRemainingCredits"]["amount"]) < 65:
        raise ValueError("PLAN_CREDIT_GATE_FAILED")
    old = next(x for r in data["instances"]["Reservations"] for x in r["Instances"] if x["InstanceId"] == "i-034252c3e9b083abf")
    if old["State"]["Name"] != "stopped" or data["network"]["SecurityGroups"][0]["IpPermissions"]:
        raise ValueError("OLD_HOST_OR_INBOUND_GATE_FAILED")
    if data["versioning"].get("Status") != "Enabled" or data["image"]["Images"][0]["State"] != "available":
        raise ValueError("IMAGE_OR_VERSIONING_GATE_FAILED")
    policy = ContinuationPolicy.model_validate(read(CANDIDATE / "original-launch-policy.json"))
    now = datetime.now(UTC)
    finish = now + timedelta(hours=290)
    conservative = policy.committed_cost(finish + timedelta(minutes=30))
    cloud_bytes = sum(x["Size"] for x in data["versions"].get("Versions", []))
    # Include all retained disks and both previous launch segments. Upper bounds
    # charge each prior host until the next recorded stop or the present time.
    first_start = datetime(2026, 10, 7, 15, 29, 5, tzinfo=UTC)
    first_stop = datetime(2026, 10, 7, 15, 57, 46, tzinfo=UTC)
    second_start = datetime(2026, 10, 7, 20, 26, 9, tzinfo=UTC)
    second_stop = datetime(2026, 10, 7, 21, 5, 38, tzinfo=UTC)
    previous_compute = ((first_stop-first_start)+(second_stop-second_start)).total_seconds()/3600*(.1197+.005)
    first_disk_hours = (datetime(2026,10,7,20,46,0,tzinfo=UTC)-first_start).total_seconds()/3600
    retained_disk_hours = (now-second_start).total_seconds()/3600 + 2
    disks_before = (first_disk_hours+retained_disk_hours)*160*.096/730
    projected_accounted = previous_compute+disks_before+290*(.1197+.005+160*.096/730)+48*160*.096/730+30*.025+5+1.25
    fits = (conservative < 55 and projected_accounted < 55
            and finish < policy.stop_at-timedelta(seconds=policy.admission_cutoff_seconds)
            and cloud_bytes < policy.cloud_limit_bytes)
    record = {"status":"PASS_CONDITIONAL_12_DAY_ALLOWANCE" if fits else "FAIL_DO_NOT_PROVISION",
              "at_utc":now.isoformat(), "deadline":policy.stop_at.isoformat(), "remaining_originals":1498,
              "current_rates":measured,"credits":plan,"old_host":"stopped","original_clock_reset":False,
              "policy_total_usd":65,"admission_guard_usd":55,"reserve_included_usd":1.25,
              "projected_finish_utc":finish.isoformat(),"conservative_elapsed_clock_cost_usd":conservative,
              "previous_compute_ipv4_usd":previous_compute,"previous_and_retained_disk_usd_upper":disks_before,
              "explicit_resource_cost_including_previous_spending_usd":projected_accounted,
              "all_evidence_versions_bytes":cloud_bytes,"limitations":["12 days is an allowance, not guaranteed", "billing lags; no final bill claimed", "all prior costs included conservatively; retained resources counted"]}
    write_new(HERE / "preprovision-feasibility.json", record)
    print(json.dumps(record, indent=2))
    if not fits:
        raise ValueError("UNCHANGED_TIME_OR_COST_DOES_NOT_FIT")


if __name__ == "__main__":
    main()
