"""One bounded, pinned read-only HTTPS download; never log its signed URL."""
import hashlib
import json
import subprocess
from pathlib import Path
import boto3

def main() -> None:
    here = Path(__file__).parent
    proof = json.loads((here / "inspection-receipt.json").read_text())
    client = boto3.Session(profile_name="fyp-research", region_name="ap-southeast-2").client("s3")
    url = client.generate_presigned_url("get_object", Params={"Bucket": proof["bucket"],
        "Key": proof["key"], "VersionId": proof["version_id"]}, ExpiresIn=300)
    target = Path("E:/p8driver145v1/curl-inspection.partial")
    assert not target.exists()
    result = subprocess.run(["curl.exe", "--fail", "--silent", "--show-error", "--connect-timeout", "10",
        "--max-time", "180", "--output", str(target), url], capture_output=True, text=True, timeout=190)
    record = {"exit": result.returncode, "stderr": result.stderr, "receipt": proof,
              "partial_retained": str(target), "url_logged": False, "read_only": True}
    if result.returncode == 0:
        with target.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        assert target.stat().st_size == proof["bytes"] and digest == proof["sha256"]
        record["sha256"] = digest
        record["status"] = "PASS"
    with (here / "curl-retrieval-result.json").open("x") as output:
        json.dump(record, output, indent=2)
    print(json.dumps(record))

if __name__ == "__main__":
    main()
