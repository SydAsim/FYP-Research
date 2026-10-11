"""Bounded deployment operations; immutable local request/result records."""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "artifacts/phase-8-runner-amendment/v3"))
from controls import hash_file, read, write_new

BUCKET = "fyp-p82-20261005-018da1d6-803656589923"
PREFIX = "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/combined-v3/deployment/"


def aws(label: str, arguments: list[str], timeout: int = 90) -> dict:
    write_new(HERE / (label + "-request.json"), {"at_utc":datetime.now(UTC).isoformat(), "arguments":arguments})
    p = subprocess.run(["aws", *arguments, "--profile", "fyp-research", "--region", "ap-southeast-2", "--no-cli-pager", "--output", "json"], capture_output=True, text=True, timeout=timeout)
    result = {"exit":p.returncode,"stderr":p.stderr,"result":json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else p.stdout}
    write_new(HERE / (label + "-result.json"), result)
    if p.returncode:
        raise RuntimeError("AWS_OPERATION_FAILED_RETAIN_ATTEMPT: " + label)
    return result["result"]


def upload(path: Path, label: str) -> dict:
    digest = hash_file(path)
    key = PREFIX + digest + "-" + path.name
    checksum = base64.b64encode(bytes.fromhex(digest)).decode()
    result = aws(label + "-put", ["s3api","put-object","--bucket",BUCKET,"--key",key,"--body",str(path),"--server-side-encryption","AES256","--checksum-sha256",checksum,"--metadata",json.dumps({"sha256":digest}),"--if-none-match","*"], 180)
    proof = {"bucket":BUCKET,"key":key,"version_id":result["VersionId"],"sha256":digest,"bytes":path.stat().st_size}
    head = aws(label + "-head", ["s3api","head-object","--bucket",BUCKET,"--key",key,"--version-id",proof["version_id"],"--checksum-mode","ENABLED"])
    if head["ContentLength"] != proof["bytes"] or head["Metadata"]["sha256"] != digest or head["ChecksumSHA256"] != checksum:
        raise ValueError("UPLOAD_VERIFICATION_FAILED")
    write_new(HERE / (label + "-proof.json"), proof)
    return proof


def send(path: Path, label: str) -> dict:
    instance = read(HERE / "actual-deployment-binding.json")["instance_id"]
    packed = base64.b64encode(gzip.compress(path.read_bytes())).decode()
    target = "/var/lib/p8-combined/deployment/" + label + ".sh"
    commands = ["set -eu", "umask 077", "python3 - <<'TRANSFER'\nimport base64,gzip\nfrom pathlib import Path\np=Path('"+target+"')\nwith p.open('xb') as f:f.write(gzip.decompress(base64.b64decode('"+packed+"')))\nTRANSFER", "bash '"+target+"'"]
    params = HERE / (label + "-ssm-parameters.json")
    write_new(params, {"commands":commands,"executionTimeout":["1200"]})
    return aws(label + "-ssm", ["ssm","send-command","--instance-ids",instance,"--document-name","AWS-RunShellScript","--parameters","file://"+str(params),"--timeout-seconds","60"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("upload","send","poll"))
    parser.add_argument("argument")
    parser.add_argument("label")
    args = parser.parse_args()
    if args.action == "upload":
        output = upload(Path(args.argument).resolve(), args.label)
    elif args.action == "send":
        output = send(Path(args.argument).resolve(), args.label)
    else:
        instance = read(HERE / "actual-deployment-binding.json")["instance_id"]
        output = aws(args.label, ["ssm","get-command-invocation","--instance-id",instance,"--command-id",args.argument])
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
