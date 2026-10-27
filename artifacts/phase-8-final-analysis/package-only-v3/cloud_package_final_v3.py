"""Package already downloaded results, with no AWS/network calls or regrading."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import signal
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, cast

PARENT_V2_SHA = "bdb1ed3791410dbdbeea1c50026d8e90179ea26ea7b2e537a312bf7f8271508d"
CONTROL_SHA = "0ddc42c49c6ff15ae200dccda539afd5ac4247a3246c75c317a237f4d29660ac"
IDENTITY_KEYS = ("sequence", "case_id", "arm", "attempt", "execution_id")
OUTPUT_NAMES = ("all-results.json", "verification.json", "final-records.tar.gz")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def parents() -> tuple[ModuleType, ModuleType]:
    path = Path(__file__).with_name("cloud_recover_final_v2.py")
    if not path.exists():
        path = Path(__file__).parent.parent / "recovery-v2/cloud_recover_final_v2.py"
    if sha(path.read_bytes()) != PARENT_V2_SHA:
        raise ValueError("V2_EXECUTABLE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("retained_recovery_v2", path)
    if spec is None or spec.loader is None:
        raise ValueError("V2_MODULE_REQUIRED")
    v2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v2)
    base = v2.parent_module()  # Verifies v1 hash; does not call main/recover/AWS.
    if base.CONTROL_SHA256 != CONTROL_SHA or v2.CONTROL_SHA != CONTROL_SHA:
        raise ValueError("PARENT_CONTROL_DRIFT")
    return v2, base


def validate_records(v2: ModuleType, packet: dict[str, Any], records: list[Any]) -> None:
    if len(records) != 1500 or len({r["execution_id"] for r in records}) != 1500:
        raise ValueError("EXACT_UNIQUE_ORIGINAL_DENOMINATOR_REQUIRED")
    if records[:735] != packet["cached_originals"]:
        raise ValueError("CACHED_ORIGINALS_CHANGED")
    groups: dict[str, set[str]] = {}
    for identity, record in zip(packet["identities"], records, strict=True):
        if any(record.get(key) != identity[key] for key in IDENTITY_KEYS):
            raise ValueError("ORIGINAL_IDENTITY_OR_ORDER_DRIFT")
        cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
        if record.get("archive_sha256") != cloud["sha256"]:
            raise ValueError("ORIGINAL_ARCHIVE_BINDING_DRIFT")
        if record.get("pinned_version") != cloud["version_id"]:
            raise ValueError("ORIGINAL_PINNED_VERSION_DRIFT")
        if identity["sequence"] > 735:
            # Modern schema MUST retain fixture_hash, row and grade agreement.
            v2.validate_record(record, identity, cloud)
        # Cached objects deliberately remain byte/value identical to the old
        # authenticated derivative. Their fixtures bind via sealed identities;
        # never inject a new field or infer a missing outcome.
        groups.setdefault(identity["case_id"], set()).add(identity["arm"])
    if len(groups) != 500 or any(value != {"B3", "P1", "P2"} for value in groups.values()):
        raise ValueError("COMPLETE_THREE_ARM_INPUT_FRAME_REQUIRED")


def check_outputs_absent(root: Path) -> None:
    for name in OUTPUT_NAMES:
        if (root / name).exists():
            raise FileExistsError("OUTPUT_ALREADY_EXISTS_NO_OVERWRITE:" + name)


def assemble(
    v2: ModuleType,
    base: ModuleType,
    stage: Any,
    root: Path,
    packet: dict[str, Any],
    records: list[Any],
    recovery: dict[str, Any],
    packaging: dict[str, Any],
) -> bytes:
    check_outputs_absent(root)
    validate_records(v2, packet, records)
    payload = canonical(
        {
            "kind": "FINAL_RECORDED_GRADES_NO_REGRADING",
            "records": records,
            "control_sha256": CONTROL_SHA,
            "master_archive_sha256": packet["master_archive_sha256"],
            "transfer_bytes": packet["transfer_bytes"],
            "recovery": recovery,
            "packaging": packaging,
        }
    )
    if len(payload) > 48 * 1024**2:
        raise ValueError("ALL_RESULTS_PAYLOAD_MEMORY_BOUND")
    stage.write(root / "all-results.json", payload)
    listing = v2.stage_inventory(root)
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


def read_complete_stage(
    v2: ModuleType, base: ModuleType, root: Path, packet: dict[str, Any]
) -> tuple[list[Any], dict[str, Any], dict[str, Any]]:
    base.Stage(root)
    check_outputs_absent(root)
    if (root / "package-only-v3/attempt.json").exists():
        raise FileExistsError("PACKAGE_ATTEMPT_EXISTS_NO_AUTOMATIC_RESTART")
    if (root / "cached-originals.json").read_bytes() != canonical(packet["cached_originals"]):
        raise ValueError("CACHED_ORIGINAL_FILE_DRIFT")
    original = v2.read(root / "attempt.json")
    if original != {
        "control_sha256": CONTROL_SHA,
        "deadline_seconds": 14400,
        "gets_planned": 765,
        "max_staging_bytes": 201326592,
        "max_transfer_bytes": 41943356497,
        "no_retries": True,
        "wall_started": v2.ORIGINAL_START,
    }:
        raise ValueError("ORIGINAL_ATTEMPT_DRIFT")
    if v2.read(root / "prerequisites.json") != {
        "account": "803656589923",
        "region": "ap-southeast-2",
        "host": "stopped",
    }:
        raise ValueError("ORIGINAL_PREREQUISITE_DRIFT")
    attempt = v2.read(root / "recovery-v2/attempt.json")
    completion = v2.read(root / "recovery-v2/completion.json")
    failure = v2.read(root / "recovery-v2/failure.json")
    if (
        attempt["source_sha256"] != PARENT_V2_SHA
        or attempt["control_sha256"] != CONTROL_SHA
        or attempt["original_deadline"] != v2.ORIGINAL_DEADLINE
        or attempt["recovery_get_limit"] != 372
        or attempt["recovery_byte_limit"] != 22198827558
        or attempt["aggregate_GET_request_limit"] != 766
        or attempt["aggregate_byte_limit"] != 41994945578
        or attempt["automatic_retries"] != 0
        or attempt["deadline_reset"] is not False
        or attempt["parent_source_sha256"] != v2.PARENT_SHA
    ):
        raise ValueError("RECOVERY_ATTEMPT_BINDING_DRIFT")
    if any(completion.get(key) != value for key, value in attempt.items()):
        raise ValueError("RECOVERY_COMPLETION_ATTEMPT_DRIFT")
    if completion.get("completed_gets") != 372 or completion.get("completed_bytes") != 22198827558:
        raise ValueError("RECOVERY_RETRIEVAL_INCOMPLETE")
    if (
        failure.get("type") != "KeyError"
        or failure.get("detail") != "'fixture_hash'"
        or failure.get("saved_new_records") != 765
    ):
        raise ValueError("UNRECOGNIZED_FAILURE_REQUIRES_INSPECTION")
    fresh = root / "recovery-v2/prerequisites.json"
    if sha(fresh.read_bytes()) != completion["fresh_prerequisites_sha256"]:
        raise ValueError("RECOVERY_PREREQUISITES_HASH_DRIFT")
    fresh_value = v2.read(fresh)
    if any(
        fresh_value.get(key) != value
        for key, value in {
            "account": "803656589923",
            "region": "ap-southeast-2",
            "host": "stopped",
        }.items()
    ):
        raise ValueError("RECOVERY_PREREQUISITES_DRIFT")
    for name, expected in attempt["preserved_files"].items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or sha((root / rel).read_bytes()) != expected:
            raise ValueError("ORIGINAL_PRESERVED_FILE_DRIFT:" + name)
    expected_names = {f"{sequence:04d}.json" for sequence in range(736, 1501)}
    for folder in ("records", "requests"):
        if {p.name for p in (root / folder).iterdir()} != expected_names:
            raise ValueError("EXACT_COMPLETED_FILE_SET_REQUIRED:" + folder)
    records = list(packet["cached_originals"])
    for identity in packet["identities"][735:]:
        sequence = identity["sequence"]
        cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
        v2.validate_request(v2.read(root / "requests" / f"{sequence:04d}.json"), identity, cloud)
        path = root / "records" / f"{sequence:04d}.json"
        record = v2.read(path)
        if path.read_bytes() != canonical(record):
            raise ValueError("PARTIAL_OR_NONCANONICAL_RECORD")
        records.append(record)
    additional = v2.read(root / "recovery-v2/requests/1129.json")
    identity = packet["identities"][1128]
    cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
    v2.validate_request(additional, identity, cloud)
    if additional["prior_transport_completion"] != "UNKNOWN" or additional[
        "prior_request_sha256"
    ] != sha((root / "requests/1129.json").read_bytes()):
        raise ValueError("INTERRUPTED_REQUEST_PROVENANCE_DRIFT")
    validate_records(v2, packet, records)
    return records, completion, failure


def package_only(v2: ModuleType, base: ModuleType) -> None:
    root = Path.home() / v2.ROOT_NAME
    stage = base.Stage(root)
    seconds = min(60, v2.remaining_seconds())

    def stop(_signum: int, _frame: Any) -> None:
        raise TimeoutError("BOUNDED_LOCAL_PACKAGING_STOP")

    signal.signal(signal.SIGALRM, stop)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    signal.alarm(seconds)
    packet = base.control()
    records, recovery, old_failure = read_complete_stage(v2, base, root, packet)
    before = v2.stage_inventory(root)
    bindings = [
        {"execution_id": i["execution_id"], "fixture_hash": i["fixture_hash"]}
        for i in packet["identities"]
    ]
    metadata = {
        "kind": "LOCAL_PACKAGE_ONLY_V3",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "parent_v2_sha256": PARENT_V2_SHA,
        "parent_v1_sha256": v2.PARENT_SHA,
        "control_sha256": CONTROL_SHA,
        "at": time.time(),
        "network_requests": 0,
        "research_executions": 0,
        "records_changed": False,
        "cached_records": 735,
        "downloaded_records": 765,
        "fixture_binding_source": "HASH_BOUND_EXTRACTION_CONTROL_IDENTITIES",
        "fixture_bindings_sha256": sha(canonical(bindings)),
        "prior_packaging_failure": old_failure,
        "prior_packaging_failure_sha256": before["recovery-v2/failure.json"],
        "preserved_files": before,
        "original_deadline": v2.ORIGINAL_DEADLINE,
        "local_packaging_seconds_limit": seconds,
    }
    stage.write(root / "package-only-v3/attempt.json", canonical(metadata))
    try:
        blob = assemble(v2, base, stage, root, packet, records, recovery, metadata)
        for name, expected in before.items():
            if sha((root / name).read_bytes()) != expected:
                raise ValueError("HISTORICAL_FILE_CHANGED:" + name)
        signal.alarm(0)
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "records": 1500,
                    "network_requests": 0,
                    "bundle": str(root / "final-records.tar.gz"),
                    "bytes": len(blob),
                    "sha256": sha(blob),
                }
            ),
            flush=True,
        )
    except Exception as error:
        stage.write(
            root / "package-only-v3/failure.json",
            canonical(
                {
                    "status": "FAILED_NO_RETRY",
                    "type": type(error).__name__,
                    "detail": str(error)[:1500],
                    "network_requests": 0,
                    "at": time.time(),
                }
            ),
            failure=True,
        )
        raise


def offline_controls(v2: ModuleType, base: ModuleType) -> None:
    packet = base.control()
    records = list(packet["cached_originals"])
    for identity in packet["identities"][735:]:
        cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
        records.append(
            dict(
                **{key: identity[key] for key in (*IDENTITY_KEYS, "fixture_hash")},
                archive_sha256=cloud["sha256"],
                pinned_version=cloud["version_id"],
                available=True,
                integrity="FULL_PINNED_ARCHIVE_AND_MANIFEST_MEMBERS",
                regraded=False,
                input={"case_id": identity["case_id"]},
                values={},
                revised_grade={"values": {}},
                analysis_row=dict(identity, values={}),
                export_sha256="a" * 64,
                manifest_sha256="b" * 64,
            )
        )

    class Controls(unittest.TestCase):
        def test_reproduce_actual_cached_schema_keyerror(self) -> None:
            self.assertNotIn("fixture_hash", records[0])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaisesRegex(KeyError, "fixture_hash"):
                    v2.bundle_records(base, base.Stage(root), root, packet, records, {})
                self.assertFalse((root / "all-results.json").exists())

        def test_mixed_schema_complete_bundle_without_record_changes(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)

                def put(name: str, value: Any) -> None:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with path.open("xb") as stream:
                        stream.write(canonical(value))

                put(
                    "attempt.json",
                    {
                        "control_sha256": CONTROL_SHA,
                        "deadline_seconds": 14400,
                        "gets_planned": 765,
                        "max_staging_bytes": 201326592,
                        "max_transfer_bytes": 41943356497,
                        "no_retries": True,
                        "wall_started": v2.ORIGINAL_START,
                    },
                )
                prerequisite = {
                    "account": "803656589923",
                    "region": "ap-southeast-2",
                    "host": "stopped",
                }
                put("prerequisites.json", prerequisite)
                put("cached-originals.json", packet["cached_originals"])
                for original in packet["identities"][735:1129]:
                    sequence = original["sequence"]
                    binding = packet["receipts"][original["execution_id"]]["receipt"]["cloud"]
                    put(
                        f"requests/{sequence:04d}.json",
                        {
                            "identity": original,
                            "cloud": binding,
                            "GET_budget": 1,
                        },
                    )
                    if sequence <= 1128:
                        put(f"records/{sequence:04d}.json", records[sequence - 1])
                retained = v2.stage_inventory(root)
                attempt = {
                    "source_sha256": PARENT_V2_SHA,
                    "control_sha256": CONTROL_SHA,
                    "original_deadline": v2.ORIGINAL_DEADLINE,
                    "recovery_get_limit": 372,
                    "recovery_byte_limit": 22198827558,
                    "aggregate_GET_request_limit": 766,
                    "aggregate_byte_limit": 41994945578,
                    "automatic_retries": 0,
                    "deadline_reset": False,
                    "parent_source_sha256": v2.PARENT_SHA,
                    "preserved_files": retained,
                }
                put("recovery-v2/attempt.json", attempt)
                put("recovery-v2/prerequisites.json", prerequisite)
                for original in packet["identities"][1128:]:
                    sequence = original["sequence"]
                    binding = packet["receipts"][original["execution_id"]]["receipt"]["cloud"]
                    put(f"records/{sequence:04d}.json", records[sequence - 1])
                    request = {"identity": original, "cloud": binding, "GET_budget": 1}
                    if sequence == 1129:
                        request.update(
                            prior_transport_completion="UNKNOWN",
                            prior_request_sha256=sha((root / "requests/1129.json").read_bytes()),
                        )
                        put("recovery-v2/requests/1129.json", request)
                    else:
                        put(f"requests/{sequence:04d}.json", request)
                completion = dict(
                    attempt,
                    completed_gets=372,
                    completed_bytes=22198827558,
                    fresh_prerequisites_sha256=sha(
                        (root / "recovery-v2/prerequisites.json").read_bytes()
                    ),
                )
                put("recovery-v2/completion.json", completion)
                v2.write_failure(base.Stage(root), root, KeyError("fixture_hash"))
                loaded, old_completion, failure = read_complete_stage(v2, base, root, packet)
                self.assertEqual(loaded, records)
                self.assertEqual(old_completion, completion)
                self.assertEqual(failure["detail"], "'fixture_hash'")
                before = v2.stage_inventory(root)
                old_hash = sha(canonical(records))
                blob = assemble(
                    v2,
                    base,
                    base.Stage(root),
                    root,
                    packet,
                    loaded,
                    old_completion,
                    {"offline": True},
                )
                with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
                    self.assertEqual(len(archive.getmembers()), 4)
                    stream = archive.extractfile("all-results.json")
                    assert stream is not None
                    data = stream.read()
                    output = json.loads(data)
                    manifest_stream = archive.extractfile("verification.json")
                    assert manifest_stream is not None
                    manifest = json.load(manifest_stream)
                    self.assertEqual(sha(data), manifest["files"]["all-results.json"])
                    self.assertEqual(sha(canonical(output["records"])), old_hash)
                    self.assertEqual(output["records"][:735], packet["cached_originals"])
                    self.assertNotIn("fixture_hash", output["records"][0])
                self.assertEqual(sha(canonical(records)), old_hash)
                for name, expected in before.items():
                    self.assertEqual(sha((root / name).read_bytes()), expected)

        def test_modified_cached_original_rejected(self) -> None:
            altered = list(records)
            altered[0] = dict(altered[0], raw_status="ALTERED")
            with self.assertRaisesRegex(ValueError, "CACHED_ORIGINALS_CHANGED"):
                validate_records(v2, packet, altered)

        def test_missing_or_wrong_modern_fixture_rejected(self) -> None:
            for changed in (
                {k: value for k, value in records[735].items() if k != "fixture_hash"},
                dict(records[735], fixture_hash="0" * 64),
            ):
                altered = list(records)
                altered[735] = changed
                with self.assertRaisesRegex(ValueError, "IDENTITY"):
                    validate_records(v2, packet, altered)

        def test_missing_duplicate_and_output_collision_rejected(self) -> None:
            for altered in (records[:-1], [*records[:-1], records[0]]):
                with self.assertRaisesRegex(ValueError, "DENOMINATOR"):
                    validate_records(v2, packet, altered)
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                original = b"preserved-existing-output"
                (root / "all-results.json").write_bytes(original)
                (root / "old-failure.json").write_bytes(b"preserve-failure")
                with self.assertRaisesRegex(FileExistsError, "NO_OVERWRITE"):
                    assemble(v2, base, base.Stage(root), root, packet, records, {}, {})
                self.assertEqual((root / "all-results.json").read_bytes(), original)
                self.assertEqual((root / "old-failure.json").read_bytes(), b"preserve-failure")

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    )
    if not result.wasSuccessful():
        raise RuntimeError("OFFLINE_PACKAGING_CONTROLS_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    v2, base = parents()
    if args.self_test:
        offline_controls(v2, base)
    else:
        package_only(v2, base)


if __name__ == "__main__":
    main()
