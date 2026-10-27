"""One explicitly invoked, bounded recovery of retained results; no research runs.

Uses the unchanged, hash-pinned v1 archive verifier. Existing files are never
rewritten. The original request 1129 remains UNKNOWN; its extra read is labelled.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, cast

PARENT_SHA = "4890790c30a48f3c7e243e5cf5c50ad3ced1a0fcae4b79065c83f1b7b40f8b50"
CONTROL_SHA = "0ddc42c49c6ff15ae200dccda539afd5ac4247a3246c75c317a237f4d29660ac"
ORIGINAL_START = 1792932005.2491002
ORIGINAL_DEADLINE = ORIGINAL_START + 14400
MAX_EXTRA_BYTES = 51_589_081
RECOVERY_BYTES = 22_198_827_558
AGGREGATE_MAX_BYTES = 41_994_945_578
ROOT_NAME = "fyp-phase8-final-evidence-v1"
KEYS = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read(path: Path, limit: int = 2 * 1024**2) -> dict[str, Any]:
    if path.stat().st_size > limit:
        raise ValueError("LOCAL_METADATA_SIZE_BOUND:" + path.name)
    data = path.read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED:" + path.name)
    return cast(dict[str, Any], value)


def parent_module() -> ModuleType:
    path = Path(__file__).with_name("cloud_extract_final_v1.py")
    if not path.exists():
        path = Path(__file__).parent.parent / "v1/cloud_extract_final_v1.py"
    if sha(path.read_bytes()) != PARENT_SHA:
        raise ValueError("PARENT_EXECUTABLE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("verified_extraction_v1", path)
    if spec is None or spec.loader is None:
        raise ValueError("PARENT_MODULE_REQUIRED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remaining_seconds(now: float | None = None) -> int:
    value = math.floor(ORIGINAL_DEADLINE - (time.time() if now is None else now))
    if value < 1:
        raise TimeoutError("ORIGINAL_EXTRACTION_DEADLINE_EXPIRED_NO_RESET")
    return value


def validate_record(item: dict[str, Any], identity: dict[str, Any], cloud: dict[str, Any]) -> None:
    if any(item.get(key) != identity[key] for key in KEYS):
        raise ValueError("REUSED_RECORD_IDENTITY_MISMATCH")
    if (
        item.get("archive_sha256") != cloud["sha256"]
        or item.get("pinned_version") != cloud["version_id"]
    ):
        raise ValueError("REUSED_RECORD_RECEIPT_MISMATCH")
    if (
        item.get("integrity") != "FULL_PINNED_ARCHIVE_AND_MANIFEST_MEMBERS"
        or item.get("regraded") is not False
    ):
        raise ValueError("REUSED_RECORD_VERIFICATION_REQUIRED")
    if item.get("available") is not True or item["input"]["case_id"] != identity["case_id"]:
        raise ValueError("REUSED_RECORD_INPUT_MISMATCH")
    row, grade = item["analysis_row"], item["revised_grade"]
    if any(row.get(key) != identity[key] for key in ("case_id", "arm", "attempt", "execution_id")):
        raise ValueError("REUSED_ANALYSIS_IDENTITY_MISMATCH")
    if item["values"] != row["values"] or item["values"] != grade["values"]:
        raise ValueError("REUSED_GRADE_DISAGREEMENT")
    for key in ("export_sha256", "manifest_sha256"):
        value = item[key]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("REUSED_HASH_INVALID")


def validate_request(
    request: dict[str, Any], identity: dict[str, Any], cloud: dict[str, Any]
) -> None:
    if (
        request.get("identity") != identity
        or request.get("cloud") != cloud
        or request.get("GET_budget") != 1
    ):
        raise ValueError("RETAINED_REQUEST_BINDING_MISMATCH")


def stage_inventory(root: Path) -> dict[str, str]:
    listing = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("STAGING_SYMLINK_REFUSED")
        if path.is_file():
            if path.stat().st_size > 192 * 1024**2:
                raise ValueError("EXISTING_FILE_BOUND")
            listing[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    return listing


def check_boundary(
    base: ModuleType, root: Path, packet: dict[str, Any]
) -> tuple[list[Any], dict[str, str]]:
    base.Stage(root)  # Account for every pre-existing file before reading payloads.
    old = read(root / "attempt.json")
    if old != {
        "control_sha256": CONTROL_SHA,
        "deadline_seconds": 14400,
        "gets_planned": 765,
        "max_staging_bytes": 192 * 1024**2,
        "max_transfer_bytes": 41_943_356_497,
        "no_retries": True,
        "wall_started": ORIGINAL_START,
    }:
        raise ValueError("ORIGINAL_ATTEMPT_BINDING_MISMATCH")
    if (root / "recovery-v2/attempt.json").exists():
        raise ValueError("RECOVERY_ATTEMPT_EXISTS_NO_AUTOMATIC_RESTART")
    for name in ("failure.json", "verification.json", "all-results.json", "final-records.tar.gz"):
        if (root / name).exists():
            raise ValueError("DIFFERENT_BOUNDARY_REFUSED:" + name)
    if read(root / "prerequisites.json") != {
        "account": "803656589923",
        "region": "ap-southeast-2",
        "host": "stopped",
    }:
        raise ValueError("ORIGINAL_PREREQUISITE_BINDING_MISMATCH")
    cached = (root / "cached-originals.json").read_bytes()
    if cached != canonical(packet["cached_originals"]):
        raise ValueError("CACHED_ORIGINALS_CHANGED")
    records = list(packet["cached_originals"])
    for folder, end in (("records", 1128), ("requests", 1129)):
        names = {path.name for path in (root / folder).iterdir()}
        if names != {f"{sequence:04d}.json" for sequence in range(736, end + 1)}:
            raise ValueError("EXACT_REPORTED_BOUNDARY_REQUIRED:" + folder)
    for identity in packet["identities"][735:1129]:
        sequence = identity["sequence"]
        cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
        validate_request(read(root / "requests" / f"{sequence:04d}.json"), identity, cloud)
        if sequence <= 1128:
            path = root / "records" / f"{sequence:04d}.json"
            item = read(path)
            if path.read_bytes() != canonical(item):
                raise ValueError("INCOMPLETE_OR_NONCANONICAL_REUSED_RECORD")
            validate_record(item, identity, cloud)
            records.append(item)
    if len(records) != 1128:
        raise ValueError("REUSED_RECORD_COUNT_MISMATCH")
    if (
        sum(
            packet["receipts"][i["execution_id"]]["receipt"]["cloud"]["bytes"]
            for i in packet["identities"][1128:]
        )
        != RECOVERY_BYTES
    ):
        raise ValueError("RECOVERY_TRANSFER_PLAN_DRIFT")
    base.Stage(root)  # Reuse the qualified total-stage and failure-reserve check.
    return records, stage_inventory(root)


def fetch_one(
    base: ModuleType,
    stage: Any,
    root: Path,
    s3: Any,
    identity: dict[str, Any],
    cloud: dict[str, Any],
) -> dict[str, Any]:
    sequence = identity["sequence"]
    request = {"identity": identity, "cloud": cloud, "GET_budget": 1, "at": time.time()}
    if sequence == 1129:
        request["prior_request_sha256"] = sha((root / "requests/1129.json").read_bytes())
        request["prior_transport_completion"] = "UNKNOWN"
        request["reason"] = "EXPLICIT_SINGLE_RECOVERY_READ_NOT_AUTOMATIC_RETRY"
        path = root / "recovery-v2/requests/1129.json"
    else:
        path = root / "requests" / f"{sequence:04d}.json"
    stage.write(path, canonical(request))  # Durable request before the only GET.
    reply = s3.get_object(Bucket=cloud["bucket"], Key=cloud["key"], VersionId=cloud["version_id"])
    body = reply["Body"]
    try:
        if reply["VersionId"] != cloud["version_id"] or reply["ContentLength"] != cloud["bytes"]:
            raise ValueError("PINNED_OBJECT_IDENTITY")
        result = base.inspect_archive(body, cloud, identity["execution_id"])
    finally:
        body.close()
    item = base.compact(result, identity, cloud)
    validate_record(item, identity, cloud)
    return cast(dict[str, Any], item)


def write_failure(stage: Any, root: Path, error: Exception) -> None:
    stage.write(
        root / "recovery-v2/failure.json",
        canonical(
            {
                "status": "FAILED_NO_RETRY",
                "type": type(error).__name__,
                "detail": str(error)[:1500],
                "at": time.time(),
                "original_deadline": ORIGINAL_DEADLINE,
                "saved_new_records": len(list((root / "records").glob("*.json"))),
            }
        ),
        failure=True,
    )


def bundle_records(
    base: ModuleType,
    stage: Any,
    root: Path,
    packet: dict[str, Any],
    records: list[Any],
    recovery: dict[str, Any],
) -> bytes:
    if len(records) != 1500 or len({r["execution_id"] for r in records}) != 1500:
        raise ValueError("FINAL_PLANNED_DENOMINATOR")
    for identity, record in zip(packet["identities"], records, strict=True):
        if any(record[key] != identity[key] for key in KEYS):
            raise ValueError("FINAL_IDENTITY_OR_ORDER_DRIFT")
    stage.write(
        root / "all-results.json",
        canonical(
            {
                "kind": "FINAL_RECORDED_GRADES_NO_REGRADING",
                "records": records,
                "control_sha256": CONTROL_SHA,
                "master_archive_sha256": packet["master_archive_sha256"],
                "transfer_bytes": packet["transfer_bytes"],
                "recovery": recovery,
            }
        ),
    )
    listing = stage_inventory(root)
    stage.write(
        root / "verification.json", canonical({"status": "PASS", "records": 1500, "files": listing})
    )
    buf = base.BoundedBuffer()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for name in ("all-results.json", "verification.json", "attempt.json", "prerequisites.json"):
            data = (root / name).read_bytes()
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    bundle = buf.getvalue()
    stage.write(root / "final-records.tar.gz", bundle)
    return cast(bytes, bundle)


def recover(base: ModuleType) -> None:
    import boto3
    from botocore.config import Config

    packet = base.control()
    if base.CONTROL_SHA256 != CONTROL_SHA or len(packet["identities"]) != 1500:
        raise ValueError("CONTROL_BINDING_MISMATCH")
    root = Path.home() / ROOT_NAME
    remaining_seconds()
    if not sys.stdin.isatty():
        raise ValueError("FOREGROUND_INTERACTIVE_CLOUDSHELL_REQUIRED")
    active = subprocess.run(
        ["pgrep", "-f", r"cloud_extract_final_v1\.py[ ]+--run"],
        capture_output=True,
        timeout=3,
        check=False,
    )
    if active.returncode != 1:
        raise ValueError("PARENT_PROCESS_ACTIVE_OR_PROCESS_CHECK_FAILED")
    records, preserved = check_boundary(base, root, packet)
    stage = base.Stage(root)
    if shutil.disk_usage(root).free < base.MAX_STAGE - stage.used + 10 * 1024**2:
        raise ValueError("FILESYSTEM_HEADROOM_REFUSAL")
    # Original absolute bound plus fresh monotonic bound; neither resets the clock.
    started_wall, started_mono = time.time(), time.monotonic()
    monotonic_end = started_mono + remaining_seconds(started_wall)

    def deadline(_signum: int, _frame: Any) -> None:
        raise TimeoutError("ORIGINAL_EXTRACTION_DEADLINE_OR_INTERRUPTION")

    signal.signal(signal.SIGALRM, deadline)
    signal.signal(signal.SIGTERM, deadline)
    signal.signal(signal.SIGINT, deadline)
    signal.alarm(remaining_seconds())
    recovery = {
        "kind": "EXPLICIT_RETRIEVAL_RECOVERY_V2",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "parent_source_sha256": PARENT_SHA,
        "control_sha256": CONTROL_SHA,
        "started_at": started_wall,
        "original_deadline": ORIGINAL_DEADLINE,
        "parent_attempt_sha256": preserved["attempt.json"],
        "preserved_files": preserved,
        "reused_cached_records": 735,
        "reused_streamed_records": 393,
        "recovery_first_sequence": 1129,
        "recovery_get_limit": 372,
        "recovery_byte_limit": RECOVERY_BYTES,
        "unknown_prior_1129_completion": True,
        "additional_1129_read_limit": 1,
        "additional_1129_byte_reserve": MAX_EXTRA_BYTES,
        "aggregate_GET_request_limit": 766,
        "aggregate_byte_limit": AGGREGATE_MAX_BYTES,
        "automatic_retries": 0,
        "automatic_restarts": 0,
        "deadline_reset": False,
    }
    stage.write(root / "recovery-v2/attempt.json", canonical(recovery))
    try:
        config = Config(connect_timeout=5, read_timeout=25, retries={"total_max_attempts": 1})
        session = boto3.Session(region_name="ap-southeast-2")
        sts, ec2, s3 = (session.client(service, config=config) for service in ("sts", "ec2", "s3"))
        project = sts.get_caller_identity()["Account"]
        state = ec2.describe_instances(InstanceIds=["i-057344e5372faf62f"])["Reservations"][0][
            "Instances"
        ][0]["State"]["Name"]
        if (
            project != "803656589923"
            or state != "stopped"
            or session.region_name != "ap-southeast-2"
        ):
            raise ValueError("PROJECT_REGION_STOPPED_HOST_GATE")
        stage.write(
            root / "recovery-v2/prerequisites.json",
            canonical(
                {
                    "account": project,
                    "region": session.region_name,
                    "host": state,
                    "at": time.time(),
                }
            ),
        )
        total, count = 0, 0
        memory = len(canonical(records))
        print("REUSING 1128/1500; recovery 372 GETs; original deadline unchanged", flush=True)
        for identity in packet["identities"][1128:]:
            remaining_seconds()
            if time.monotonic() >= monotonic_end:
                raise TimeoutError("MONOTONIC_ORIGINAL_REMAINING_BOUND")
            cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
            if count >= 372 or total + cloud["bytes"] > RECOVERY_BYTES:
                raise ValueError("RECOVERY_REQUEST_OR_TRANSFER_BOUND")
            item = fetch_one(base, stage, root, s3, identity, cloud)
            count += 1
            total += cloud["bytes"]
            memory += len(canonical(item))
            if memory > 48 * 1024**2:
                raise ValueError("TOTAL_COMPACT_RECORD_MEMORY_BOUND")
            stage.write(root / "records" / f"{identity['sequence']:04d}.json", canonical(item))
            records.append(item)
            print(
                f"VERIFIED {identity['sequence']}/1500; recovery_bytes={total}; "
                f"remaining_s={remaining_seconds()}",
                flush=True,
            )
            if count % 50 == 0:
                input(
                    "CloudShell requires interaction: press Enter to continue "
                    "this same bounded recovery. "
                )
        for name, expected in preserved.items():
            if sha((root / name).read_bytes()) != expected:
                raise ValueError("PRESERVED_FILE_DRIFT:" + name)
        if count != 372 or total != RECOVERY_BYTES:
            raise ValueError("RECOVERY_COMPLETENESS")
        recovery["completed_gets"] = count
        recovery["completed_bytes"] = total
        recovery["actual_elapsed_seconds"] = time.monotonic() - started_mono
        recovery["fresh_prerequisites_sha256"] = sha(
            (root / "recovery-v2/prerequisites.json").read_bytes()
        )
        stage.write(root / "recovery-v2/completion.json", canonical(recovery))
        bundle = bundle_records(base, stage, root, packet, records, recovery)
        signal.alarm(0)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "records": 1500,
                    "bundle": str(root / "final-records.tar.gz"),
                    "bytes": len(bundle),
                    "sha256": sha(bundle),
                    "host_was_not_started": True,
                }
            ),
            flush=True,
        )
    except Exception as error:
        write_failure(stage, root, error)
        print("FAILED_NO_RETRY: recovery-v2/failure.json preserved; do not rerun", flush=True)
        raise


def offline_controls(base: ModuleType) -> None:
    identity = {
        "sequence": 1129,
        "case_id": "control",
        "arm": "P1",
        "attempt": 1,
        "execution_id": "offline-control",
        "fixture_hash": "f" * 64,
    }
    cloud = {
        "bucket": "no-network",
        "key": "control",
        "version_id": "pinned",
        "sha256": "a" * 64,
        "bytes": 1,
    }
    item = dict(
        identity,
        archive_sha256=cloud["sha256"],
        pinned_version="pinned",
        available=True,
        integrity="FULL_PINNED_ARCHIVE_AND_MANIFEST_MEMBERS",
        regraded=False,
        input={"case_id": "control"},
        values={},
        analysis_row=dict(identity, values={}),
        revised_grade={"values": {}},
        export_sha256="b" * 64,
        manifest_sha256="c" * 64,
    )

    class Controls(unittest.TestCase):
        def test_reused_record_binding_without_network(self) -> None:
            validate_record(item, identity, cloud)
            with self.assertRaisesRegex(ValueError, "RECEIPT"):
                validate_record(dict(item, pinned_version="different"), identity, cloud)
            # Exercise the complete reported filesystem boundary on synthetic data.
            packet = base.control()
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "records").mkdir()
                (root / "requests").mkdir()
                (root / "attempt.json").write_bytes(
                    canonical(
                        {
                            "control_sha256": CONTROL_SHA,
                            "deadline_seconds": 14400,
                            "gets_planned": 765,
                            "max_staging_bytes": 192 * 1024**2,
                            "max_transfer_bytes": 41_943_356_497,
                            "no_retries": True,
                            "wall_started": ORIGINAL_START,
                        }
                    )
                )
                (root / "prerequisites.json").write_bytes(
                    canonical(
                        {
                            "account": "803656589923",
                            "region": "ap-southeast-2",
                            "host": "stopped",
                        }
                    )
                )
                (root / "cached-originals.json").write_bytes(canonical(packet["cached_originals"]))
                for original in packet["identities"][735:1129]:
                    binding = packet["receipts"][original["execution_id"]]["receipt"]["cloud"]
                    name = f"{original['sequence']:04d}.json"
                    (root / "requests" / name).write_bytes(
                        canonical(
                            {
                                "identity": original,
                                "cloud": binding,
                                "GET_budget": 1,
                            }
                        )
                    )
                    if original["sequence"] <= 1128:
                        sample = dict(item, **{key: original[key] for key in KEYS})
                        sample.update(
                            archive_sha256=binding["sha256"],
                            pinned_version=binding["version_id"],
                            input={"case_id": original["case_id"]},
                            analysis_row=dict(original, values={}),
                        )
                        (root / "records" / name).write_bytes(canonical(sample))
                records, preserved = check_boundary(base, root, packet)
                self.assertEqual(len(records), 1128)
                self.assertEqual(len(list((root / "requests").iterdir())), 394)
                self.assertIn("requests/1129.json", preserved)

        def test_altered_identity_rejected(self) -> None:
            with self.assertRaisesRegex(ValueError, "IDENTITY"):
                validate_record(dict(item, attempt=2), identity, cloud)

        def test_incomplete_record_preserved(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "partial.json"
                path.write_bytes(b'{"partial":')
                with self.assertRaises(json.JSONDecodeError):
                    read(path)
                self.assertEqual(path.read_bytes(), b'{"partial":')

        def test_unknown_request_exact_binding(self) -> None:
            request = {"identity": identity, "cloud": cloud, "GET_budget": 1}
            validate_request(request, identity, cloud)
            with self.assertRaisesRegex(ValueError, "BINDING"):
                validate_request(dict(request, GET_budget=2), identity, cloud)

        def test_original_deadline_not_reset(self) -> None:
            self.assertEqual(remaining_seconds(ORIGINAL_START + 1200), 13200)
            self.assertEqual(ORIGINAL_DEADLINE, 1792946405.2491002)
            with self.assertRaisesRegex(TimeoutError, "EXPIRED"):
                remaining_seconds(ORIGINAL_DEADLINE)

        def test_genuine_failure_one_request_durable_no_retry(self) -> None:
            class FailingS3:
                calls = 0

                def get_object(self, **_kwargs: Any) -> Any:
                    self.calls += 1
                    raise ConnectionError("OFFLINE_SYNTHETIC_CONNECTION_FAILURE")

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = base.Stage(root)
                stage.write(root / "requests/1129.json", canonical({"original": "preserve"}))
                client = FailingS3()
                try:
                    fetch_one(base, stage, root, client, identity, cloud)
                except ConnectionError as error:
                    write_failure(stage, root, error)
                self.assertEqual(client.calls, 1)
                self.assertTrue((root / "recovery-v2/requests/1129.json").exists())
                self.assertEqual(
                    read(root / "recovery-v2/failure.json")["status"], "FAILED_NO_RETRY"
                )
                self.assertEqual(read(root / "requests/1129.json"), {"original": "preserve"})
                self.assertFalse((root / "records/1129.json").exists())

        def test_collision_never_overwrites(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = base.Stage(root)
                stage.write(root / "recovery-v2/attempt.json", b"original")
                with self.assertRaises(FileExistsError):
                    stage.write(root / "recovery-v2/attempt.json", b"replacement")
                self.assertEqual((root / "recovery-v2/attempt.json").read_bytes(), b"original")

        def test_final_bundle_original_members_and_bound(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = base.Stage(root)
                stage.write(root / "attempt.json", b"{}")
                stage.write(root / "prerequisites.json", b"{}")
                # Fixed final denominator, synthetic identities; no study executions.
                records = [
                    dict(identity, sequence=n, execution_id=f"synthetic-{n}")
                    for n in range(1, 1501)
                ]
                packet = {
                    "identities": records,
                    "master_archive_sha256": "d" * 64,
                    "transfer_bytes": 0,
                }
                blob = bundle_records(base, stage, root, packet, records, {"offline": True})
                with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
                    self.assertEqual(len(archive.getmembers()), 4)
                    manifest_stream = archive.extractfile("verification.json")
                    assert manifest_stream is not None
                    manifest = json.load(manifest_stream)
                    payload_stream = archive.extractfile("all-results.json")
                    assert payload_stream is not None
                    self.assertEqual(
                        sha(payload_stream.read()), manifest["files"]["all-results.json"]
                    )
                buf = base.BoundedBuffer()
                buf.seek(32 * 1024**2)
                with self.assertRaisesRegex(ValueError, "BOUND"):
                    buf.write(b"x")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("OFFLINE_RECOVERY_CONTROLS_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--remaining-seconds", action="store_true")
    action.add_argument("--resume-once", action="store_true")
    parser.add_argument("--recover-request-1129-once", action="store_true")
    args = parser.parse_args()
    if args.resume_once and not args.recover_request_1129_once:
        parser.error("Recovery requires explicitly labelling the one additional pinned 1129 read")
    if args.remaining_seconds:
        print(remaining_seconds())
        return
    base = parent_module()
    if args.self_test:
        offline_controls(base)
    else:
        recover(base)


if __name__ == "__main__":
    main()
