"""Finite, journalled AWS CLI setup; no application behaviour or main-study launch."""

import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.execution_setup.core import (  # noqa: E402
    ROOT,
    check_inventory,
    digest,
    immutable,
    load,
    now,
)

PACKAGE = ROOT / "artifacts/phase-8-aws-qualification/v1"
AWS = "C:/Program Files/Amazon/AWSCLIV2/aws.exe"
REGION = "ap-southeast-2"


def command(name: str, arguments: list[str]) -> Any:
    argv = [AWS, *arguments, "--profile", "fyp-research", "--region", REGION, "--output", "json"]
    immutable(PACKAGE / f"aws-request-{name}.json", {"at": now(), "arguments": argv})
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        immutable(
            PACKAGE / f"aws-response-{name}.json",
            {
                "at": now(),
                "status": "UNKNOWN_TIMEOUT",
                "new_admissions_stopped": True,
                "instruction": "Inspect named resource/client token before any retry",
            },
        )
        raise
    immutable(
        PACKAGE / f"aws-response-{name}.json",
        {
            "at": now(),
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    result.check_returncode()
    return json.loads(result.stdout) if result.stdout.strip() else {}


def write(name: str, value: Any) -> str:
    immutable(PACKAGE / name, value)
    return "file://" + str((PACKAGE / name).resolve())


def main() -> None:
    approval = load(PACKAGE / "spending-approval.json")
    if approval["approved_usd"] != "2.00" or approval["main_launch_authorized"] is not False:
        raise ValueError("FINITE_SPENDING_APPROVAL_REQUIRED")
    check_inventory(load(PACKAGE / "preserved-before.json"))
    ident = command("identity", ["sts", "get-caller-identity"])
    plan = command("plan", ["freetier", "get-account-plan-state"])
    if ident["Account"] != "803656589923" or plan["accountPlanType"] != "FREE":
        raise ValueError("PROJECT_OR_PLAN_CHANGED")
    owner = "p82-20261005-" + uuid4().hex[:8]
    bucket = "fyp-" + owner + "-803656589923"
    role = "FYP-" + owner
    tag = [{"Key": "research.owner", "Value": owner}, {"Key": "research.stage", "Value": "8.2"}]
    deployment = {
        "owner": owner,
        "bucket": bucket,
        "role": role,
        "region": REGION,
        "limit_usd": "2.00",
        "max_powered_hours": 4,
        "main_started": False,
    }
    immutable(PACKAGE / "deployment-plan.json", deployment)
    command(
        "bucket",
        [
            "s3api",
            "create-bucket",
            "--bucket",
            bucket,
            "--create-bucket-configuration",
            "LocationConstraint=" + REGION,
        ],
    )
    command(
        "bucket-tags",
        [
            "s3api",
            "put-bucket-tagging",
            "--bucket",
            bucket,
            "--tagging",
            write("bucket-tags.json", {"TagSet": tag}),
        ],
    )
    command(
        "bucket-private",
        [
            "s3api",
            "put-public-access-block",
            "--bucket",
            bucket,
            "--public-access-block-configuration",
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
        ],
    )
    command(
        "bucket-encryption",
        [
            "s3api",
            "put-bucket-encryption",
            "--bucket",
            bucket,
            "--server-side-encryption-configuration",
            write(
                "bucket-encryption.json",
                {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]},
            ),
        ],
    )
    command(
        "bucket-versioning",
        [
            "s3api",
            "put-bucket-versioning",
            "--bucket",
            bucket,
            "--versioning-configuration",
            "Status=Enabled",
        ],
    )
    trust = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    command(
        "role",
        [
            "iam",
            "create-role",
            "--role-name",
            role,
            "--tags",
            json.dumps(tag),
            "--assume-role-policy-document",
            write("role-trust.json", trust),
        ],
    )
    command(
        "ssm-policy",
        [
            "iam",
            "attach-role-policy",
            "--role-name",
            role,
            "--policy-arn",
            "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        ],
    )
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/source/*",
            },
            {
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/exports/*", f"arn:aws:s3:::{bucket}/ssm/*"],
            },
            {
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": f"arn:aws:s3:::{bucket}",
                "Condition": {"StringLike": {"s3:prefix": ["source/*", "exports/*", "ssm/*"]}},
            },
        ],
    }
    command(
        "research-policy",
        [
            "iam",
            "put-role-policy",
            "--role-name",
            role,
            "--policy-name",
            "ResearchTransferOnly",
            "--policy-document",
            write("role-policy.json", policy),
        ],
    )
    command(
        "instance-profile",
        [
            "iam",
            "create-instance-profile",
            "--instance-profile-name",
            role,
            "--tags",
            json.dumps(tag),
        ],
    )
    command(
        "add-role",
        [
            "iam",
            "add-role-to-instance-profile",
            "--instance-profile-name",
            role,
            "--role-name",
            role,
        ],
    )
    command(
        "upload-capsule",
        [
            "s3api",
            "put-object",
            "--bucket",
            bucket,
            "--key",
            "source/linux-source.tar.gz",
            "--body",
            str(ROOT / "artifacts/phase-8-linux-setup/v1/linux-source.tar.gz"),
        ],
    )
    command(
        "upload-addon",
        [
            "s3api",
            "put-object",
            "--bucket",
            bucket,
            "--key",
            "source/qualification.zip",
            "--body",
            str(PACKAGE / "qualification.zip"),
        ],
    )
    sg = command(
        "security-group",
        [
            "ec2",
            "create-security-group",
            "--group-name",
            owner,
            "--description",
            "Phase 8.2 calibration: no inbound ports",
            "--vpc-id",
            "vpc-0c74e59331cbc1caa",
            "--tag-specifications",
            json.dumps([{"ResourceType": "security-group", "Tags": tag}]),
        ],
    )["GroupId"]
    userdata = (PACKAGE / "user-data.sh").read_text().replace("@BUCKET@", bucket)
    userdata = userdata.replace("@ADDON_SHA@", digest(PACKAGE / "qualification.zip"))
    launch = {
        "ImageId": load(PACKAGE / "cost-decision.json")["ami_id"],
        "InstanceType": "t3.large",
        "MinCount": 1,
        "MaxCount": 1,
        "ClientToken": owner,
        "IamInstanceProfile": {"Name": role},
        "CreditSpecification": {"CpuCredits": "standard"},
        "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 1},
        "InstanceInitiatedShutdownBehavior": "stop",
        "Monitoring": {"Enabled": False},
        "NetworkInterfaces": [
            {
                "DeviceIndex": 0,
                "SubnetId": "subnet-05c5c729c83dc651b",
                "AssociatePublicIpAddress": True,
                "Groups": [sg],
            }
        ],
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 40,
                    "VolumeType": "gp3",
                    "Encrypted": True,
                    "DeleteOnTermination": True,
                },
            }
        ],
        "TagSpecifications": [
            {"ResourceType": kind, "Tags": tag} for kind in ("instance", "volume")
        ],
        "UserData": base64.b64encode(userdata.encode()).decode(),
    }
    # The request token and full launch request are durable before the AWS call.
    uri = write("launch-request.json", launch)
    # Wait for profile propagation by observing it; do not loop mutative launches.
    command("profile-ready", ["iam", "get-instance-profile", "--instance-profile-name", role])
    instance = command("launch", ["ec2", "run-instances", "--cli-input-json", uri])["Instances"][0]
    immutable(
        PACKAGE / "created-resources.json",
        {
            **deployment,
            "instance_id": instance["InstanceId"],
            "security_group": sg,
            "at": now(),
            "main_started": False,
        },
    )
    print(
        json.dumps(
            {
                "instance_id": instance["InstanceId"],
                "owner": owner,
                "bucket": bucket,
                "main_started": False,
            }
        )
    )


if __name__ == "__main__":
    main()
