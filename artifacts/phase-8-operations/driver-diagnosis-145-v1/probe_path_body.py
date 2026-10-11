"""One alternate regional S3 path-style read, pinned to the retained version."""
import json
from pathlib import Path
import boto3
from botocore.config import Config

def main() -> None:
    here = Path(__file__).parent
    proof = json.loads((here / "inspection-receipt.json").read_text())
    client = boto3.Session(profile_name="fyp-research", region_name="ap-southeast-2").client(
        "s3", config=Config(connect_timeout=5, read_timeout=10, s3={"addressing_style": "path"},
                            retries={"total_max_attempts": 1, "mode": "standard"}))
    response = client.get_object(Bucket=proof["bucket"], Key=proof["key"],
                                 VersionId=proof["version_id"], Range="bytes=0-65535")
    print({"version": response.get("VersionId"), "range": response.get("ContentRange"),
           "length": response.get("ContentLength")}, flush=True)
    with response["Body"] as body:
        data = body.read(65536)
    assert len(data) == 65536 and response["VersionId"] == proof["version_id"]
    with (here / "path-body-probe.bin").open("xb") as target:
        target.write(data)
    print({"read_bytes": len(data)}, flush=True)

if __name__ == "__main__":
    main()
