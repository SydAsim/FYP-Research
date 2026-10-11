"""Explicit stage approval and fresh AWS preflight before one finite pilot host."""

import argparse
import base64
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from aws import call
from plan import budget, validate_plan

from research.execution_setup.core import check_inventory, digest, immutable, load

HERE = Path(__file__).parent.resolve()
REPO = HERE.parents[2]
BUCKET = "fyp-p82-20261005-018da1d6-803656589923"
PROFILE = "FYP-p82-20261005-018da1d6"
GROUP = "sg-097f19e71cbd37f2d"
SUBNET = "subnet-05c5c729c83dc651b"
AMI = "ami-090b1140798d2d006"


def approve(value: dict[str, Any]) -> None:
    expected = {
        "stage": "8.3", "limit_usd": "2.00", "planned_executions": 24,
        "max_powered_hours": 6, "main_authorized": False,
        "cleanup": "REMOVE_AFTER_TWO_VERIFIED_LOCAL_COPIES_AND_S3",
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ValueError("NEW_HUMAN_STAGE_APPROVAL_REQUIRED")
    if value.get("decision") != "APPROVED_BY_USER" or not value.get("user_message"):
        raise ValueError("RETAIN_ACTUAL_USER_AUTHORIZATION_DO_NOT_SYNTHESIZE")


def price_rows(data: dict[str, Any], unit: str, usage: str | None = None) -> str:
    prices: set[str] = set()
    for raw in data["PriceList"]:
        product = json.loads(raw)
        if usage and usage not in product["product"]["attributes"].get("usagetype", ""):
            continue
        for term in product["terms"].get("OnDemand", {}).values():
            for dimension in term["priceDimensions"].values():
                if dimension["unit"] == unit and float(dimension["pricePerUnit"]["USD"]) > 0:
                    prices.add(str(dimension["pricePerUnit"]["USD"]))
    if len(prices) != 1:
        raise ValueError("FRESH_UNAMBIGUOUS_ON_DEMAND_RATE_REQUIRED")
    return prices.pop()


def preflight(prefix: str) -> dict[str, Any]:
    identity = call(prefix + "-identity", ["sts", "get-caller-identity"])
    if identity["Account"] != "803656589923":
        raise ValueError("WRONG_PROJECT")
    state = call(prefix + "-plan", ["freetier", "get-account-plan-state"])
    if state.get("accountPlanType") != "FREE":
        raise ValueError("PLAN_CHANGE_REQUIRES_REVIEW_NO_UPGRADE")
    group = call(prefix + "-group", ["ec2", "describe-security-groups", "--group-ids", GROUP])
    if group["SecurityGroups"][0]["IpPermissions"]:
        raise ValueError("INBOUND_ACCESS_NOT_IN_APPROVED_PLAN")
    images = call(prefix + "-image", ["ec2", "describe-images", "--image-ids", AMI])
    image = images["Images"][0]
    if image["State"] != "available" or image["Architecture"] != "x86_64":
        raise ValueError("IMAGE_CHANGED")
    kinds = call(prefix + "-type", ["ec2", "describe-instance-types", "--instance-types",
                                   "m7i-flex.large"])
    if not kinds["InstanceTypes"][0].get("FreeTierEligible"):
        raise ValueError("FREE_PLAN_INSTANCE_ELIGIBILITY_REQUIRED")
    filters = ["Type=TERM_MATCH,Field=regionCode,Value=ap-southeast-2"]
    def pricing(name: str, service: str, extra: list[str]) -> dict[str, Any]:
        response: dict[str, Any] = call(
            prefix + "-" + name, ["pricing", "get-products", "--service-code", service,
            "--filters", *filters, *extra], region="us-east-1")
        return response  # AWS JSON boundary; exact unambiguous prices are required below.
    compute = price_rows(pricing("compute", "AmazonEC2", [
        "Type=TERM_MATCH,Field=instanceType,Value=m7i-flex.large",
        "Type=TERM_MATCH,Field=operatingSystem,Value=Linux",
        "Type=TERM_MATCH,Field=tenancy,Value=Shared",
        "Type=TERM_MATCH,Field=preInstalledSw,Value=NA",
        "Type=TERM_MATCH,Field=capacitystatus,Value=Used",
    ]), "Hrs")
    disk = price_rows(pricing("disk", "AmazonEC2", [
        "Type=TERM_MATCH,Field=productFamily,Value=Storage",
        "Type=TERM_MATCH,Field=volumeApiName,Value=gp3",
    ]), "GB-Mo")
    ipv4 = price_rows(pricing("ipv4", "AmazonVPC", []), "Hrs", "PublicIPv4:InUseAddress")
    amounts = budget(compute, ipv4, disk)
    if amounts["within_ceiling"] != "True":
        raise ValueError("PRICE_EXCEEDS_APPROVED_CEILING_STOP")
    return {"identity": identity, "plan": state, "budget": amounts,
            "rates": {"compute": compute, "ipv4": ipv4, "disk": disk},
            "root_device": image["RootDeviceName"]}


def launch(approval: Path) -> None:
    approve(load(approval))
    if (HERE / "launch-intent.json").exists():
        raise ValueError("EXISTING_LAUNCH_RECONCILE_CLIENT_TOKEN_NO_NEW_HOST")
    validate_plan(HERE / "slots.json")
    check_inventory(load(HERE / "preserved-before.json"), REPO)
    check_inventory(load(HERE / "seal.json")["files"], HERE)
    stamp = "launch-" + str(time.time_ns())
    checked = preflight(stamp)
    archive = HERE / "pilot-v1.zip"
    checksum = digest(archive)
    key = "source/phase83-pilot-v1-" + checksum + ".zip"
    call(stamp + "-upload", ["s3api", "put-object", "--bucket", BUCKET, "--key", key,
         "--body", str(archive), "--checksum-algorithm", "SHA256",
         "--metadata", "sha256=" + checksum])
    head = call(stamp + "-head", ["s3api", "head-object", "--bucket", BUCKET, "--key", key,
                               "--checksum-mode", "ENABLED"])
    if base64.b64decode(head["ChecksumSHA256"]).hex() != checksum:
        raise ValueError("UPLOADED_PACKAGE_DRIFT")
    hard = datetime.now(UTC) + timedelta(hours=6)
    owner = "p83-" + uuid4().hex[:12]
    source = HERE / "bootstrap.sh"
    replacements = {
        "STOP_CALENDAR": hard.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "STOP_ISO": hard.isoformat(), "BUCKET": BUCKET,
        "P83_KEY": key, "P83_SHA": checksum,
        "V2_SHA": digest(REPO / "artifacts/phase-8-aws-qualification/v2/qualification-v2.zip"),
        "V31_SHA": digest(REPO / "artifacts/phase-8-aws-qualification/v3.1/integrity-v3.1.zip"),
    }
    script = source.read_text(encoding="utf-8")
    for token, value in replacements.items():
        script = script.replace("@" + token + "@", value)
    tags = [{"Key": "research.owner", "Value": owner}, {"Key": "research.stage", "Value": "8.3"}]
    request = {
        "ImageId": AMI, "InstanceType": "m7i-flex.large", "MinCount": 1, "MaxCount": 1,
        "ClientToken": owner, "IamInstanceProfile": {"Name": PROFILE},
        "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1},
        "InstanceInitiatedShutdownBehavior": "stop", "Monitoring": {"Enabled": False},
        "NetworkInterfaces": [{"DeviceIndex": 0, "SubnetId": SUBNET,
                               "AssociatePublicIpAddress": True, "Groups": [GROUP]}],
        "BlockDeviceMappings": [{"DeviceName": checked["root_device"], "Ebs": {
            "VolumeSize": 40, "VolumeType": "gp3", "Encrypted": True,
            "DeleteOnTermination": True}}],
        "TagSpecifications": [{"ResourceType": kind, "Tags": tags}
                              for kind in ("instance", "volume")],
        "UserData": base64.b64encode(script.encode()).decode(),
    }
    immutable(HERE / "launch-intent.json", {"owner": owner, "deadline": hard.isoformat(),
              "approval": load(approval), "preflight": checked, "main_started": False})
    immutable(HERE / "launch-request.json", request)
    # If this call is ambiguous, inspect this exact client token; never mint a replacement.
    result = call(stamp + "-instance", ["ec2", "run-instances", "--cli-input-json",
                                      "file://" + str(HERE / "launch-request.json")])
    immutable(HERE / "launched.json", {"owner": owner, "instance_id": result["Instances"][0][
        "InstanceId"], "main_started": False, "deadline": hard.isoformat()})
    print(json.dumps(load(HERE / "launched.json")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", type=Path, required=True)
    args = parser.parse_args()
    launch(args.approval)
