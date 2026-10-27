"""Bounded Sydney deployment-control reconciliation. Read-only AWS calls ONLY.

Uses CloudShell's existing credentials; never reads/prints/uploads signing keys.
No start, stop, send-command, cancel-command, upload, admission or pause clearing.
Return this evidence before the already authorized guarded deployment proceeds.
"""
from __future__ import annotations

import hashlib
import base64
import json
import os
import signal
import subprocess
import sys
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REGION = "ap-southeast-2"
ACCOUNT = "803656589923"
HOST = "i-057344e5372faf62f"
ROOT = "vol-09dbb42bbf607f5de"
BUCKET = "fyp-p82-20261005-018da1d6-803656589923"
PREFIX = "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/"
SOURCE_SHA = "212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37"
SOURCE_KEY = PREFIX + "continuation-v10/deployment/" + SOURCE_SHA + "-v10-complete-continuation.tar.gz"
SOURCE_VERSION = "QmAcYmVhFW5GHo08qBB01sD.laBJlcyo"
PARAMETERS_SHA = "4f562f64821af73d684d016fecbe972c710cadd8375d1005491d0342aa161d5d"
STAGING = Path.home() / "fyp-v10-attempt2-control"
LIMIT = 8 * 1024**2
RESERVE = 256 * 1024
MAX_REQUESTS = 16


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def save(name: str, value: object, *, failure: bool = False) -> None:
    data = json.dumps(value, indent=2, default=str).encode()
    used = sum(p.stat().st_size for p in STAGING.rglob("*") if p.is_file())
    if used + len(data) > LIMIT - (0 if failure else RESERVE):
        raise RuntimeError("CONTROL_STAGING_BOUND_RETAIN_EXISTING")
    with (STAGING / name).open("xb") as f:
        f.write(data)


class Controller:
    def __init__(self) -> None:
        self.started = time.monotonic()
        self.requests = 0

    def call(self, label: str, args: list[str]) -> dict[str, Any]:
        remaining = 570 - (time.monotonic() - self.started)
        if remaining < 45 or self.requests >= MAX_REQUESTS:
            raise RuntimeError("CONTROL_BUDGET_EXHAUSTED_NO_RETRY")
        self.requests += 1
        command = ["aws", *args, "--region", REGION, "--cli-connect-timeout", "5",
                   "--cli-read-timeout", "25", "--output", "json", "--no-cli-pager"]
        save(label + "-request.json", {"at": datetime.now(UTC).isoformat(), "command": command})
        env = {**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_RETRY_MODE": "standard", "AWS_PAGER": ""}
        tick = time.monotonic()
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=45, env=env)
        except subprocess.TimeoutExpired:
            save(label + "-error.json", {"error": "PROCESS_TIMEOUT", "seconds": 45}, failure=True)
            raise RuntimeError("CONTROL_REQUEST_TIMEOUT_NO_RETRY:" + label) from None
        if p.returncode:
            # API errors only; no debug logging, environment, tokens or signed URLs.
            save(label + "-error.json", {"exit": p.returncode, "stderr": p.stderr[:4096]}, failure=True)
            raise RuntimeError("CONTROL_REQUEST_FAILED_NO_RETRY:" + label)
        if len(p.stdout.encode()) > 2 * 1024**2:
            raise RuntimeError("CONTROL_RESPONSE_TOO_LARGE_NO_MORE_CALLS")
        result = json.loads(p.stdout)
        if args[0] == "cloudtrail":
            events = []
            for event in result.get("Events", []):
                raw = json.loads(event["CloudTrailEvent"])
                request = raw.get("requestParameters") or {}
                events.append({"EventId": event["EventId"], "EventTime": event["EventTime"],
                    "region": raw.get("awsRegion"), "eventSource": raw.get("eventSource"),
                    "errorCode": raw.get("errorCode"), "errorMessage": raw.get("errorMessage"),
                    "documentName": request.get("documentName"), "instanceIds": request.get("instanceIds"),
                    "parameters_sha256": hashlib.sha256(canonical(request.get("parameters", {}))).hexdigest(),
                    "timeoutSeconds": request.get("timeoutSeconds"),
                    "commandId": ((raw.get("responseElements") or {}).get("command") or {}).get("commandId")})
            result = {"Events": events, **({"NextToken": result["NextToken"]} if "NextToken" in result else {})}
        save(label + "-result.json", {"result": result, "seconds": time.monotonic()-tick,
                                      "at": datetime.now(UTC).isoformat()})
        return result


def bundle() -> None:
    target = STAGING / "control-evidence.tar.gz"
    members = [p for p in STAGING.iterdir() if p.is_file() and p.name != target.name]
    used = sum(p.stat().st_size for p in members)
    # Reserve worst-case tar/gzip expansion before the streaming write.
    bound = used + len(members)*2048 + 65536
    if used + bound > LIMIT:
        raise RuntimeError("CONTROL_BUNDLE_CAPACITY_STOP")
    class BoundedWriter:
        def __init__(self, out: Any) -> None:
            self.out = out
            self.written = 0
        def write(self, data: bytes) -> int:
            if used + self.written + len(data) > LIMIT:
                raise RuntimeError("CONTROL_BUNDLE_LIMIT_RETAIN_PARTIAL")
            n = self.out.write(data)
            self.written += n
            return n
        def tell(self) -> int:
            return self.written
        def flush(self) -> None:
            self.out.flush()
    with target.open("xb") as f:
        with tarfile.open(fileobj=BoundedWriter(f), mode="w|gz") as tar:
            for member in members:
                tar.add(member, arcname=member.name, recursive=False)
    with target.open("rb") as f:
        hasher = hashlib.sha256()
        for block in iter(lambda: f.read(1024**2), b""):
            hasher.update(block)
        digest = hasher.hexdigest()
    print(json.dumps({"bundle": str(target), "sha256": digest, "bytes": target.stat().st_size}), flush=True)


def deadline(_number: int, _frame: object) -> None:
    raise TimeoutError("CONTROL_OVERALL_600_SECONDS")


def main() -> int:
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(600)
    if STAGING.exists():
        print("REFUSED_EXISTING_ATTEMPT_PRESERVE_IT_DO_NOT_RETRY", flush=True)
        return 2
    STAGING.mkdir(mode=0o700)
    save("plan.json", {"max_requests": MAX_REQUESTS, "max_process_seconds": 45,
        "overall_seconds": 600, "automatic_retries": 0, "AWS_mutations": 0,
        "max_staging_bytes": LIMIT, "failure_reserve_bytes": RESERVE,
        "host": HOST, "expected_root": ROOT, "source_version": SOURCE_VERSION,
        "ambiguous_request_at": "2026-10-12T16:27:20.228195Z", "parameters_sha256": PARAMETERS_SHA,
        "at": datetime.now(UTC).isoformat()})
    c = Controller()
    try:
        identity = c.call("identity", ["sts", "get-caller-identity"])
        if identity["Account"] != ACCOUNT:
            raise RuntimeError("WRONG_PROJECT_STOP")
        hosts = c.call("host", ["ec2", "describe-instances", "--instance-ids", HOST])
        instance = hosts["Reservations"][0]["Instances"][0]
        if hosts["Reservations"][0]["OwnerId"] != ACCOUNT or instance["State"]["Name"] != "stopped":
            raise RuntimeError("HOST_NOT_OWNED_STOPPED_NO_ACTION")
        if not any(b["Ebs"]["VolumeId"] == ROOT and not b["Ebs"]["DeleteOnTermination"] for b in instance["BlockDeviceMappings"]):
            raise RuntimeError("ROOT_BINDING_DRIFT")
        matches: list[dict[str, Any]] = []
        args = ["ssm", "list-commands", "--instance-id", HOST, "--max-results", "50", "--no-paginate"]
        for page in range(2):
            data = c.call(f"commands-{page+1}", args)
            for command in data.get("Commands", []):
                if (command.get("DocumentName") == "AWS-RunShellScript"
                    and hashlib.sha256(canonical(command.get("Parameters", {}))).hexdigest() == PARAMETERS_SHA):
                    matches.append(command)
            if not data.get("NextToken"):
                break
            args = args[:args.index("--next-token")] if "--next-token" in args else args
            args = [*args, "--next-token", data["NextToken"]]
        else:
            raise RuntimeError("COMMAND_HISTORY_PAGINATION_INCOMPLETE")
        invocations = c.call("invocations", ["ssm", "list-command-invocations", "--instance-id", HOST,
            "--filters", "key=InvokedAfter,value=2026-10-12T16:20:00Z",
            "key=InvokedBefore,value=2026-10-12T16:45:00Z", "--details", "--max-results", "50", "--no-paginate"])
        if invocations.get("NextToken"):
            raise RuntimeError("INVOCATION_HISTORY_PAGINATION_INCOMPLETE")
        args = ["cloudtrail", "lookup-events", "--lookup-attributes", "AttributeKey=EventName,AttributeValue=SendCommand",
            "--start-time", "2026-10-12T16:20:00Z", "--end-time", "2026-10-12T16:45:00Z",
            "--max-results", "50", "--no-paginate"]
        cloud_matches: list[dict[str, Any]] = []
        for page in range(2):
            data = c.call(f"cloudtrail-{page+1}", args)
            cloud_matches.extend(e for e in data["Events"] if HOST in (e.get("instanceIds") or [])
                                 and e["parameters_sha256"] == PARAMETERS_SHA)
            if not data.get("NextToken"):
                break
            args = args[:args.index("--next-token")] if "--next-token" in args else args
            args = [*args, "--next-token", data["NextToken"]]
        else:
            raise RuntimeError("CLOUDTRAIL_PAGINATION_INCOMPLETE")
        ids = {m["CommandId"] for m in matches}
        ids.update(m["commandId"] for m in cloud_matches if m.get("commandId"))
        if len(ids) > 1:
            raise RuntimeError("MULTIPLE_MATCHING_MUTATIONS_REQUIRES_REVIEW")
        details = []
        for command_id in ids:
            details.append(c.call("matched-invocation", ["ssm", "get-command-invocation", "--instance-id", HOST, "--command-id", command_id]))
        source = c.call("source-head", ["s3api", "head-object", "--bucket", BUCKET, "--key", SOURCE_KEY,
                                       "--version-id", SOURCE_VERSION, "--checksum-mode", "ENABLED"])
        if (source["ContentLength"] != 292118202 or source["Metadata"].get("sha256") != SOURCE_SHA
            or source.get("VersionId") != SOURCE_VERSION
            or source.get("ChecksumSHA256") != base64.b64encode(bytes.fromhex(SOURCE_SHA)).decode()):
            raise RuntimeError("PINNED_SOURCE_DRIFT")
        cloud_bytes = 0
        versions = 0
        args = ["s3api", "list-object-versions", "--bucket", BUCKET, "--prefix", PREFIX,
                "--max-keys", "1000", "--no-paginate"]
        for page in range(2):
            data = c.call(f"versions-{page+1}", args)
            cloud_bytes += sum(v["Size"] for v in data.get("Versions", []))
            versions += len(data.get("Versions", []))
            if not data.get("IsTruncated"):
                break
            args = [*args, "--key-marker", data["NextKeyMarker"], "--version-id-marker", data["NextVersionIdMarker"]]
        else:
            raise RuntimeError("ALL_VERSION_STORAGE_UNVERIFIED")
        plan = c.call("account-plan", ["freetier", "get-account-plan-state"])
        guard = c.call("absolute-guard", ["scheduler", "get-schedule", "--group-name", "fyp-p85-v5",
                                         "--name", "retained-host-v10-absolute-stop-20261025"])
        if (guard["State"] != "ENABLED" or guard["ScheduleExpression"] != "at(2026-10-25T15:24:23)"
            or guard["ScheduleExpressionTimezone"] != "UTC" or guard["FlexibleTimeWindow"] != {"Mode": "OFF"}
            or guard["Target"]["Arn"] != "arn:aws:scheduler:::aws-sdk:ec2:stopInstances"
            or guard["Target"]["RoleArn"] != "arn:aws:iam::803656589923:role/FYP-p85-v5-preparation-stop"
            or guard["Target"]["RetryPolicy"] != {"MaximumEventAgeInSeconds": 300, "MaximumRetryAttempts": 3}
            or json.loads(guard["Target"]["Input"]) != {"InstanceIds": [HOST]}):
            raise RuntimeError("ABSOLUTE_GUARD_DRIFT")
        pending = [d for d in details if d["Status"] in ("Pending", "InProgress", "Delayed", "Cancelling")]
        summary = {"status": "READ_ONLY_CONTROL_EVIDENCE_COMPLETE_RETURN_FOR_RECONCILIATION",
            "host_state": "stopped", "original_parameters_sha256": PARAMETERS_SHA,
            "matched_command_ids": sorted(ids), "matched_invocations": details,
            "cloudtrail_matches": cloud_matches, "unresolved_active_commands": pending,
            "historical_execution_unknown_if_no_match": not bool(ids),
            "listing_absence_is_not_proof_of_nonexecution": True,
            "cloud_all_versions_bytes": cloud_bytes, "cloud_versions": versions, "plan": plan,
            "source_version_verified": SOURCE_VERSION, "actual_admission": None,
            "next_sequence": 146, "remaining": 1355, "no_boot_or_resend_performed": True,
            "requires_local_review_and_explicit_expiry_fence_then_guarded_root_inspection": True,
            "requests_used": c.requests, "at": datetime.now(UTC).isoformat()}
        save("summary.json", summary)
        print(json.dumps({"status": summary["status"], "host": "stopped", "matched_command_ids": sorted(ids),
                          "historical_execution_unknown": not bool(ids), "requests": c.requests}), flush=True)
        bundle()
        return 0
    except (RuntimeError, KeyError, ValueError, OSError, TimeoutError) as exc:
        save("failure.json", {"status": "FAILED_PREREQUISITE_NO_BOOT", "type": type(exc).__name__,
            "detail": str(exc), "requests": c.requests, "at": datetime.now(UTC).isoformat()}, failure=True)
        print(json.dumps({"status": "FAILED_PREREQUISITE_NO_BOOT", "detail": str(exc)}), flush=True)
        bundle()
        return 1


if __name__ == "__main__":
    sys.exit(main())
