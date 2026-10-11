"""Read-only AWS qualification evidence. No resource creation or main admission."""

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.execution_setup.core import ROOT, immutable, now  # noqa: E402

PACKAGE = ROOT / "artifacts/phase-8-aws-qualification/v1"
AWS = Path("C:/Program Files/Amazon/AWSCLIV2/aws.exe")


def capture(name: str, arguments: list[str], region: str = "ap-southeast-2") -> Any:
    command = [
        str(AWS),
        *arguments,
        "--profile",
        "fyp-research",
        "--region",
        region,
        "--output",
        "json",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    immutable(
        PACKAGE / f"preflight-{name}.json",
        {
            "at": now(),
            "command": command,
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    if name != "dry-run":
        result.check_returncode()
        return json.loads(result.stdout)
    if "(DryRunOperation)" not in result.stderr:
        raise RuntimeError("AWS_LAUNCH_PERMISSION_UNQUALIFIED")
    return {"permission_checked": True, "resources_created": False}


def price(arguments: list[str], name: str) -> Decimal:
    data = capture(
        name,
        ["pricing", "get-products", "--service-code", "AmazonEC2", "--filters", *arguments],
        "us-east-1",
    )
    values = []
    for raw in data["PriceList"]:
        product = json.loads(raw)
        for term in product["terms"]["OnDemand"].values():
            for dimension in term["priceDimensions"].values():
                values.append(Decimal(dimension["pricePerUnit"]["USD"]))
    if len(values) != 1:
        raise ValueError("PRICING_AMBIGUOUS: no spending assumption allowed")
    return values[0]


def main() -> None:
    identity = capture("identity", ["sts", "get-caller-identity"])
    plan = capture("plan", ["freetier", "get-account-plan-state"])
    if identity["Account"] != "803656589923" or plan["accountPlanType"] != "FREE":
        raise ValueError("PROJECT_OR_PLAN_CHANGED: review before provisioning")
    capture("instances", ["ec2", "describe-instances"])
    capture(
        "quota",
        [
            "service-quotas",
            "get-service-quota",
            "--service-code",
            "ec2",
            "--quota-code",
            "L-1216C47A",
        ],
    )
    images = capture(
        "ami",
        [
            "ec2",
            "describe-images",
            "--owners",
            "099720109477",
            "--filters",
            "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*",
            "Name=state,Values=available",
        ],
    )
    latest = max(images["Images"], key=lambda item: item["CreationDate"])
    capture(
        "dry-run",
        [
            "ec2",
            "run-instances",
            "--image-id",
            latest["ImageId"],
            "--instance-type",
            "t3.large",
            "--count",
            "1",
            "--subnet-id",
            "subnet-05c5c729c83dc651b",
            "--dry-run",
        ],
    )
    common = [
        "Type=TERM_MATCH,Field=regionCode,Value=ap-southeast-2",
        "Type=TERM_MATCH,Field=operatingSystem,Value=Linux",
        "Type=TERM_MATCH,Field=tenancy,Value=Shared",
        "Type=TERM_MATCH,Field=preInstalledSw,Value=NA",
        "Type=TERM_MATCH,Field=capacitystatus,Value=Used",
    ]
    compute = price([*common, "Type=TERM_MATCH,Field=instanceType,Value=t3.large"], "compute-price")
    disk = price(
        [
            "Type=TERM_MATCH,Field=regionCode,Value=ap-southeast-2",
            "Type=TERM_MATCH,Field=productFamily,Value=Storage",
            "Type=TERM_MATCH,Field=volumeApiName,Value=gp3",
        ],
        "disk-price",
    )
    ip = Decimal("0.005")  # https://aws.amazon.com/vpc/pricing/, verified 2026-10-05
    four_hours = (compute + ip + 40 * disk / 730) * 4
    retention = 40 * disk / 730 * 24 * 7
    immutable(
        PACKAGE / "cost-decision.json",
        {
            "at": now(),
            "compute_usd_hour": str(compute),
            "disk_usd_gb_month": str(disk),
            "ipv4_usd_hour": str(ip),
            "four_hour_estimate_usd": str(four_hours),
            "seven_day_disk_retention_usd": str(retention),
            "four_hours_plus_retention_usd": str(four_hours + retention),
            "export_api_contingency_usd": "0.50",
            "proposed_ceiling_usd": "2.00",
            "approval": "PENDING",
            "ami_id": latest["ImageId"],
            "main_started": False,
            "resources_created": False,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_READ_ONLY",
                "four_hour_estimate": str(four_hours),
                "with_seven_day_disk_retention": str(four_hours + retention),
                "approval": "PENDING",
                "main_started": False,
            }
        )
    )


if __name__ == "__main__":
    main()
