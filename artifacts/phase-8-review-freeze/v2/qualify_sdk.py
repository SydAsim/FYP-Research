"""Pinned botocore model/stub qualification; explicit fake credentials, zero network."""

import argparse
import base64
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from controls import hash_file, write_new
from storage import S3Cloud


def qualify(output: Path) -> None:
    import boto3
    from botocore.config import Config
    from botocore.stub import ANY, Stubber

    output.mkdir(parents=True, exist_ok=False)
    path = output / "calibration-only.dat"
    path.write_bytes(b"phase84-sdk-control-no-scientific-execution\n")
    digest = hash_file(path)
    checksum = base64.b64encode(bytes.fromhex(digest)).decode()
    bucket, key = "calibration-not-main", "cal-only/receipt"
    original: Any = boto3.Session
    session = original(
        aws_access_key_id="SYNTHETIC_CALIBRATION_ONLY",
        aws_secret_access_key="SYNTHETIC_NEVER_NETWORK",
        region_name="ap-southeast-2",
    )
    client = session.client(
        "s3", config=Config(connect_timeout=10, read_timeout=30, retries={"total_max_attempts": 1})
    )
    head = {
        "VersionId": "cal-version-1",
        "ContentLength": path.stat().st_size,
        "Metadata": {"sha256": digest},
        "ChecksumSHA256": checksum,
    }
    params = {"Bucket": bucket, "Key": key, "VersionId": "cal-version-1", "ChecksumMode": "ENABLED"}
    with Stubber(client) as stub:
        stub.add_response(
            "get_bucket_location", {"LocationConstraint": "ap-southeast-2"}, {"Bucket": bucket}
        )
        stub.add_response("get_bucket_versioning", {"Status": "Enabled"}, {"Bucket": bucket})
        stub.add_response(
            "put_object",
            {"VersionId": "cal-version-1", "ChecksumSHA256": checksum},
            {
                "Bucket": bucket,
                "Key": key,
                "Body": ANY,
                "ContentLength": path.stat().st_size,
                "ServerSideEncryption": "AES256",
                "Metadata": {"sha256": digest},
                "ChecksumSHA256": checksum,
                "IfNoneMatch": "*",
            },
        )
        stub.add_response("head_object", head, params)
        stub.add_response(
            "list_object_versions",
            {
                "IsTruncated": False,
                "Versions": [
                    {"Key": key, "VersionId": "cal-version-1", "Size": path.stat().st_size}
                ],
            },
            {"Bucket": bucket, "Prefix": "cal-only/"},
        )
        stub.add_response(
            "list_object_versions",
            {
                "IsTruncated": False,
                "Versions": [
                    {"Key": key, "VersionId": "cal-version-1", "Size": path.stat().st_size}
                ],
            },
            {"Bucket": bucket, "Prefix": key},
        )
        stub.add_response("head_object", head, params)
        try:
            boto3.Session = lambda **kwargs: SimpleNamespace(client=lambda *a, **kw: client)
            cloud = S3Cloud(bucket, "cal-only/")
            proof = cloud.put(path, key)
            assert cloud.inventory() == path.stat().st_size
            assert cloud.find(key, digest, path.stat().st_size) == proof
            stub.assert_no_pending_responses()
        finally:
            boto3.Session = original
    write_new(
        output / "result.json",
        {
            "status": "PASS",
            "classification": "SDK_MODEL_STUB_ONLY",
            "boto3": boto3.__version__,
            "cloud_network_calls": 0,
            "cloud_spending_usd": 0,
            "main_executions": 0,
            "checks": [
                "conditional single PUT request model",
                "pinned checksum HEAD",
                "all-version inventory",
                "read-only unique-version reconciliation",
                "Sydney/versioning checks",
            ],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_output", type=Path)
    qualify(parser.parse_args().new_output)


if __name__ == "__main__":
    main()
