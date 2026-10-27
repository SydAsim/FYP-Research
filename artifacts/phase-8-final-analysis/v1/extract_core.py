"""Read retained grades from pinned archives; never run an oracle or driver."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import signal
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, cast

CONTROL_PAYLOAD = "__CONTROL_PAYLOAD__"
CONTROL_SHA256 = "__CONTROL_SHA256__"
MAX_STAGE = 192 * 1024**2
MAX_RECORD = 2 * 1024**2
FAILURE_RESERVE = 2 * 1024**2


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def control() -> dict[str, Any]:
    data = gzip.decompress(base64.b64decode(CONTROL_PAYLOAD))
    if sha(data) != CONTROL_SHA256:
        raise ValueError("CONTROL_HASH_DRIFT")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("CONTROL_OBJECT_REQUIRED")
    return cast(dict[str, Any], value)


class Stage:
    def __init__(self, root: Path, limit: int = MAX_STAGE) -> None:
        self.root, self.limit = root, limit
        root.mkdir(parents=True, exist_ok=True)
        self.used = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
        if self.used > limit - FAILURE_RESERVE:
            raise ValueError("EXISTING_STAGE_CAPACITY_REFUSAL")

    def write(self, path: Path, data: bytes, *, failure: bool = False) -> None:
        self.used = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        reserve = 0 if failure else FAILURE_RESERVE
        if self.used + len(data) > self.limit - reserve:
            raise ValueError("STAGING_BOUND_BEFORE_WRITE")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            for offset in range(0, len(data), 65536):
                piece = data[offset : offset + 65536]
                if self.used + len(piece) > self.limit - reserve:
                    raise ValueError("STAGING_BOUND_DURING_WRITE")
                stream.write(piece)
                self.used += len(piece)


class BoundedBuffer(io.BytesIO):
    # Binary-buffer interface is an isolated stdlib I/O boundary.
    def write(self, data: Any) -> int:
        if self.tell() + len(data) > 32 * 1024**2:
            raise ValueError("BUNDLE_MEMORY_BOUND_BEFORE_WRITE")
        return super().write(data)


class HashingReader:
    def __init__(self, source: BinaryIO, size: int) -> None:
        self.source, self.size = source, size
        self.digest = hashlib.sha256()
        self.count = 0

    def read(self, amount: int = -1) -> bytes:
        amount = 1024**2 if amount < 0 else min(amount, 1024**2)
        data = self.source.read(amount)
        self.count += len(data)
        if self.count > self.size:
            raise ValueError("OBJECT_SIZE_EXCEEDED")
        self.digest.update(data)
        return data


def inspect_archive(source: BinaryIO, cloud: dict[str, Any], execution: str) -> dict[str, Any]:
    """Stream once; authenticate compressed bytes and all manifest-listed members."""
    reader = HashingReader(source, cloud["bytes"])
    hashes: dict[str, str] = {}
    manifest: dict[str, Any] | None = None
    trace: dict[str, Any] | None = None
    target = f"executions/{execution}/export.json"
    expanded = 0
    # Streaming tar mode requires read(), not seek()/write() from BinaryIO's full type.
    with tarfile.open(fileobj=cast(Any, reader), mode="r|gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != "slot"
            ):
                raise ValueError("UNSAFE_ARCHIVE_MEMBER")
            if member.isdir():
                continue
            if not member.isfile() or member.size > 256 * 1024**2:
                raise ValueError("UNSUPPORTED_OR_OVERSIZE_MEMBER")
            rel = str(PurePosixPath(*path.parts[1:]))
            if rel in hashes:
                raise ValueError("DUPLICATE_MEMBER")
            expanded += member.size
            if expanded > 4 * 1024**3 or len(hashes) > 12000:
                raise ValueError("EXPANDED_ARCHIVE_BOUND")
            capture = rel in ("manifest.json", target)
            if capture and member.size > 32 * 1024**2:
                raise ValueError("SELECTED_RECORD_MEMORY_BOUND")
            digest = hashlib.sha256()
            parts = []
            stream = archive.extractfile(member)
            assert stream is not None
            while piece := stream.read(1024**2):
                digest.update(piece)
                if capture:
                    parts.append(piece)
            hashes[rel] = digest.hexdigest()
            if rel == "manifest.json":
                manifest = json.loads(b"".join(parts))
            elif rel == target:
                trace = json.loads(b"".join(parts))
    while reader.read(1024**2):
        pass
    if reader.count != cloud["bytes"] or reader.digest.hexdigest() != cloud["sha256"]:
        raise ValueError("FULL_ARCHIVE_HASH_OR_SIZE_MISMATCH")
    if manifest is None or trace is None:
        raise ValueError("REQUIRED_MANIFEST_OR_EXPORT_MISSING")
    for name, expected in manifest["files"].items():
        if hashes.get(name) != expected:
            raise ValueError("MANIFEST_MEMBER_HASH_MISMATCH:" + name)
    if manifest["files"].get(target) != hashes[target]:
        raise ValueError("EXPORT_NOT_COMMITTED_BY_MANIFEST")
    return {
        "trace": trace,
        "export_sha256": hashes[target],
        "manifest_sha256": hashes["manifest.json"],
        "members_verified": len(manifest["files"]),
        "compressed_bytes_verified": reader.count,
        "expanded_bytes_hashed": expanded,
    }


def compact(
    result: dict[str, Any], identity: dict[str, Any], cloud: dict[str, Any]
) -> dict[str, Any]:
    trace = result["trace"]
    for key in ("execution_id", "arm", "attempt", "fixture_hash"):
        if trace[key] != identity[key]:
            raise ValueError("EXPORT_IDENTITY_MISMATCH:" + key)
    if trace["input"]["case_id"] != identity["case_id"]:
        raise ValueError("EXPORT_CASE_MISMATCH")
    grade, analysis = trace["revised_grade"], trace["analysis_row"]
    if grade["values"] != analysis["values"]:
        raise ValueError("GRADE_ROW_DISAGREEMENT")
    if any(analysis[key] != identity[key] for key in ("case_id", "arm", "attempt", "execution_id")):
        raise ValueError("ANALYSIS_IDENTITY_MISMATCH")
    small = {
        k: identity[k]
        for k in ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
    }
    small.update(
        available=True,
        analysis_row=analysis,
        revised_grade=grade,
        raw_status=trace["status"],
        values=grade["values"],
        stratum=trace["input"]["stratum"],
        generator_family=trace["input"]["generator_family"],
        cluster_id=trace["input"]["cluster_id"],
        input=trace["input"],
        export_sha256=result["export_sha256"],
        archive_sha256=cloud["sha256"],
        pinned_version=cloud["version_id"],
        manifest_sha256=result["manifest_sha256"],
        members_verified=result["members_verified"],
        voice_evidence=grade.get("observable", {}).get("voice_evidence"),
        duration_seconds=analysis.get("duration_seconds"),
        event_observed=analysis.get("event_observed"),
        censor_reason=analysis.get("censor_reason"),
        driver_classification=trace.get("driver_classification"),
        failure=trace.get("failure"),
        collection_errors=trace.get("collection_errors"),
        observations_count=len(trace.get("observations") or []),
        checkpoint=trace.get("collector_checkpoint"),
        source_provenance={
            k: v
            for k, v in trace.items()
            if k
            in ("version", "source", "source_hashes", "instrument_version", "source_inventory_hash")
        },
        integrity="FULL_PINNED_ARCHIVE_AND_MANIFEST_MEMBERS",
        regraded=False,
    )
    if len(canonical(small)) > MAX_RECORD:
        raise ValueError("COMPACT_RECORD_BOUND")
    return small


def offline_controls() -> None:
    import unittest

    class Controls(unittest.TestCase):
        def sample(
            self, *, omit: bool = False, corrupt: bool = False
        ) -> tuple[bytes, dict[str, Any]]:
            raw = canonical({"execution_id": "control", "analysis_row": {}})
            manifest = canonical({"files": {"executions/control/export.json": sha(raw)}})
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as t:
                for name, data in [("manifest.json", manifest)] + (
                    []
                    if omit
                    else [("executions/control/export.json", raw + (b" " if corrupt else b""))]
                ):
                    item = tarfile.TarInfo("slot/" + name)
                    item.size = len(data)
                    t.addfile(item, io.BytesIO(data))
            data = buf.getvalue()
            return data, {"bytes": len(data), "sha256": sha(data)}

        def test_normal(self) -> None:
            data, cloud = self.sample()
            self.assertEqual(
                inspect_archive(io.BytesIO(data), cloud, "control")["trace"]["execution_id"],
                "control",
            )

        def test_archive_hash_rejected(self) -> None:
            data, cloud = self.sample()
            cloud["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "FULL_ARCHIVE_HASH"):
                inspect_archive(io.BytesIO(data), cloud, "control")

        def test_member_hash_rejected(self) -> None:
            data, cloud = self.sample(corrupt=True)
            with self.assertRaisesRegex(ValueError, "MEMBER_HASH"):
                inspect_archive(io.BytesIO(data), cloud, "control")

        def test_missing_export_rejected(self) -> None:
            data, cloud = self.sample(omit=True)
            with self.assertRaisesRegex(ValueError, "REQUIRED_MANIFEST"):
                inspect_archive(io.BytesIO(data), cloud, "control")

        def test_existing_staging_counted(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "old").write_bytes(b"x" * 12)
                stage = Stage(root, FAILURE_RESERVE + 20)
                with self.assertRaisesRegex(ValueError, "BEFORE_WRITE"):
                    stage.write(root / "new", b"x" * 9)
                self.assertFalse((root / "new").exists())

        def test_collision_preserved(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = Stage(root)
                stage.write(root / "old", b"original")
                with self.assertRaises(FileExistsError):
                    stage.write(root / "old", b"changed")
                self.assertEqual((root / "old").read_bytes(), b"original")

        def test_external_log_growth_counted(self) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = Stage(root, FAILURE_RESERVE + 20)
                (root / "console.log").write_bytes(b"x" * 15)
                with self.assertRaisesRegex(ValueError, "BEFORE_WRITE"):
                    stage.write(root / "new", b"x" * 6)

        def test_bundle_write_bound(self) -> None:
            buf = BoundedBuffer()
            buf.seek(32 * 1024**2)
            with self.assertRaisesRegex(ValueError, "BEFORE_WRITE"):
                buf.write(b"x")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("OFFLINE_CONTROLS_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        offline_controls()
        return
    if not args.run:
        parser.error("Choose --self-test or --run")
    import boto3
    from botocore.config import Config

    packet = control()
    root = Path.home() / "fyp-phase8-final-evidence-v1"
    stage = Stage(root)
    if (root / "attempt.json").exists():
        raise ValueError("EXISTING_ATTEMPT_PRESERVED_NO_AUTOMATIC_RESTART")
    config = Config(connect_timeout=5, read_timeout=25, retries={"total_max_attempts": 1})
    session = boto3.Session(region_name="ap-southeast-2")
    sts, ec2, s3 = (session.client(s, config=config) for s in ("sts", "ec2", "s3"))
    started = time.monotonic()

    def deadline(_signum: int, _frame: Any) -> None:
        raise TimeoutError("FIXED_EXTRACTION_DEADLINE")

    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(packet["deadline_seconds"])
    stage.write(
        root / "attempt.json",
        canonical(
            {
                "control_sha256": CONTROL_SHA256,
                "wall_started": time.time(),
                "deadline_seconds": packet["deadline_seconds"],
                "gets_planned": packet["remaining_gets"],
                "max_transfer_bytes": packet["transfer_bytes"],
                "max_staging_bytes": MAX_STAGE,
                "no_retries": True,
            }
        ),
    )
    try:
        account = sts.get_caller_identity()["Account"]
        host = ec2.describe_instances(InstanceIds=["i-057344e5372faf62f"])["Reservations"][0][
            "Instances"
        ][0]["State"]["Name"]
        if account != "803656589923" or host != "stopped":
            raise ValueError("ACCOUNT_OR_STOPPED_HOST_PREREQUISITE")
        stage.write(
            root / "prerequisites.json",
            canonical({"account": account, "region": session.region_name, "host": host}),
        )
        records = list(packet["cached_originals"])
        retained_record_bytes = len(canonical(records))
        stage.write(root / "cached-originals.json", canonical(records))
        transferred = 0
        for identity in packet["identities"][735:]:
            cloud = packet["receipts"][identity["execution_id"]]["receipt"]["cloud"]
            stage.write(
                root / "requests" / f"{identity['sequence']:04d}.json",
                canonical(
                    {"identity": identity, "cloud": cloud, "GET_budget": 1, "at": time.time()}
                ),
            )
            if transferred + cloud["bytes"] > packet["transfer_bytes"]:
                raise ValueError("TOTAL_TRANSFER_BOUND")
            reply = s3.get_object(
                Bucket=cloud["bucket"], Key=cloud["key"], VersionId=cloud["version_id"]
            )
            if (
                reply["VersionId"] != cloud["version_id"]
                or reply["ContentLength"] != cloud["bytes"]
            ):
                reply["Body"].close()
                raise ValueError("PINNED_OBJECT_IDENTITY")
            try:
                extracted = inspect_archive(reply["Body"], cloud, identity["execution_id"])
            finally:
                reply["Body"].close()
            transferred += cloud["bytes"]
            item = compact(extracted, identity, cloud)
            retained_record_bytes += len(canonical(item))
            if retained_record_bytes > 48 * 1024**2:
                raise ValueError("TOTAL_COMPACT_RECORD_MEMORY_BOUND")
            stage.write(root / "records" / f"{identity['sequence']:04d}.json", canonical(item))
            records.append(item)
            print(
                f"VERIFIED {identity['sequence']}/1500; bytes={transferred}; "
                f"elapsed={time.monotonic() - started:.1f}s",
                flush=True,
            )
        if len(records) != 1500 or len({r["execution_id"] for r in records}) != 1500:
            raise ValueError("FINAL_PLANNED_DENOMINATOR")
        stage.write(
            root / "all-results.json",
            canonical(
                {
                    "kind": "FINAL_RECORDED_GRADES_NO_REGRADING",
                    "records": records,
                    "control_sha256": CONTROL_SHA256,
                    "master_archive_sha256": packet["master_archive_sha256"],
                    "transfer_bytes": transferred,
                    "elapsed_seconds": time.monotonic() - started,
                }
            ),
        )
        listing = {
            str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()
        }
        stage.write(
            root / "verification.json",
            canonical({"status": "PASS", "records": 1500, "files": listing}),
        )
        buf = BoundedBuffer()
        with tarfile.open(fileobj=buf, mode="w:gz") as archive:
            for name in (
                "all-results.json",
                "verification.json",
                "attempt.json",
                "prerequisites.json",
            ):
                data = (root / name).read_bytes()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
                if buf.tell() > 32 * 1024**2:
                    raise ValueError("BUNDLE_MEMORY_BOUND")
        bundle = buf.getvalue()
        if len(bundle) > 32 * 1024**2:
            raise ValueError("BUNDLE_BOUND")
        stage.write(root / "final-records.tar.gz", bundle)
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
        stage.write(
            root / "failure.json",
            canonical(
                {
                    "status": "FAILED_NO_RETRY",
                    "type": type(error).__name__,
                    "detail": str(error)[:1500],
                    "elapsed_seconds": time.monotonic() - started,
                    "retained_records": len(list((root / "records").glob("*.json"))),
                }
            ),
            failure=True,
        )
        print("FAILED_NO_RETRY; evidence retained at " + str(root), flush=True)
        raise


if __name__ == "__main__":
    main()
