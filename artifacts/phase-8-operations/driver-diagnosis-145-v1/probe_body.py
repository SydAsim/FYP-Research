"""One read-only, pinned 64-KiB retrieval probe; no campaign state changes."""
import json
from pathlib import Path
import boto3
from botocore.config import Config

def main() -> None:
    here = Path(__file__).parent
    proof = json.loads((here / "inspection-receipt.json").read_text())
    client = boto3.Session(profile_name="fyp-research", region_name="ap-southeast-2").client(
        "s3", config=Config(connect_timeout=5, read_timeout=10,
                            retries={"total_max_attempts": 1, "mode": "standard"}))
    response = client.get_object(Bucket=proof["bucket"], Key=proof["key"],
                                 VersionId=proof["version_id"], Range="bytes=0-65535")
    print({"version": response.get("VersionId"), "range": response.get("ContentRange"),
           "length": response.get("ContentLength"), "body_type": type(response["Body"]).__name__}, flush=True)
    with response["Body"] as body:
        data = body.read(65536)
    print({"read_bytes": len(data)}, flush=True)
    with (here / "body-probe.bin").open("xb") as target:
        target.write(data)

if __name__ == "__main__":
    main()
