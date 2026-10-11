"""Finite evidence-only transport and existing guarded postflight. No case admission."""

from __future__ import annotations

import concurrent.futures as futures
import importlib.util
import shutil
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CONTROL = HERE.parent / "control-v1"
sys.path[:0] = [str(HERE / "sdk"), str(REPO), str(CONTROL)]

import boto3  # noqa: E402
import watch  # noqa: E402
from botocore.config import Config  # noqa: E402

from research.execution_setup.core import (  # noqa: E402
    check_inventory,
    digest,
    immutable,
    load,
    now,
)


def load_report() -> ModuleType:
    spec = importlib.util.spec_from_file_location("p83_saved_report", CONTROL / "report.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("REPORT_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> None:
    check_inventory(load(CONTROL / "seal.json")["files"], CONTROL)
    check_inventory(load(watch.PILOT / "seal.json")["files"], watch.PILOT)
    receipt_path = max(CONTROL.glob("receipt-*.json"), key=lambda p: p.stat().st_mtime_ns)
    receipt = watch.Receipt.model_validate(load(receipt_path))
    config = load(CONTROL / "config.json")
    if (CONTROL / "cleanup-intent.json").exists() or (CONTROL / "verified-backups.json").exists():
        raise RuntimeError("EXISTING_POSTFLIGHT_REQUIRES_RECONCILIATION")
    if watch.owned(config)["State"]["Name"] != "stopped":
        raise RuntimeError("EXPECTED_SAME_STOPPED_HOST")
    session = boto3.Session(profile_name="fyp-research", region_name="ap-southeast-2")
    client = session.client("s3", config=Config(
        connect_timeout=10, read_timeout=30, max_pool_connections=8,
        retries={"total_max_attempts": 1, "mode": "standard"},
    ))
    head = client.head_object(Bucket=watch.BUCKET, Key=receipt.key, ChecksumMode="ENABLED")
    watch.check_head(receipt, head)
    config["primary"] = "E:/fyp-phase83-evidence/recovery-v5"
    config["secondary"] = "D:/P83/recovery-v5"
    immutable(HERE / "config.json", config)
    immutable(HERE / "plan.json", {
        "at": now(), "scope": "EVIDENCE_TRANSPORT_ONLY", "main_started": False,
        "chunk_bytes": 65536, "concurrency": 8, "deadline_seconds": 1800,
        "requests_per_piece": 1, "version_id": receipt.version_id,
        "sha256": receipt.sha256, "bytes": receipt.bytes,
        "prior_attempts": "All earlier partial files, journals and reports retained unchanged",
    })
    folder: Path = Path(config["primary"]) / config["owner"]
    pieces: Path = folder / "retained-pieces"
    pieces.mkdir(parents=True, exist_ok=False)
    jobs = [(i, s, min(s + 65536, receipt.bytes) - 1)
            for i, s in enumerate(range(0, receipt.bytes, 65536))]
    started = time.monotonic()

    def transfer(job: tuple[int, int, int]) -> Path:
        i, start, end = job
        if time.monotonic() - started >= 1800:
            raise TimeoutError("TRANSPORT_WALL_DEADLINE")
        path: Path = pieces / f"{i:04d}.bin"
        immutable(HERE / "requests" / f"{i:04d}.json", {
            "at": now(), "range": f"bytes={start}-{end}", "version": receipt.version_id,
        })
        # One shared SDK client; credentials and signed requests never enter logs.
        response: dict[str, Any] = client.get_object(
            Bucket=watch.BUCKET, Key=receipt.key, VersionId=receipt.version_id,
            Range=f"bytes={start}-{end}",
        )
        with response["Body"] as body, path.open("xb") as output:
            if (response["VersionId"] != receipt.version_id
                    or response["ContentRange"] != f"bytes {start}-{end}/{receipt.bytes}"):
                raise ValueError("RANGE_OR_VERSION_DRIFT")
            data: bytes = body.read()
            output.write(data)
        if path.stat().st_size != end - start + 1:
            raise ValueError("INCOMPLETE_RANGE_RETAIN_PIECE")
        immutable(HERE / "responses" / f"{i:04d}.json", {
            "at": now(), "bytes": path.stat().st_size, "sha256": digest(path),
        })
        return path

    completed: dict[int, Path] = {}
    iterator = iter(jobs)
    with futures.ThreadPoolExecutor(max_workers=8) as pool:
        active = {pool.submit(transfer, job): job[0] for job in [next(iterator) for _ in range(8)]}
        while active:
            done, _ = futures.wait(active, return_when=futures.FIRST_COMPLETED)
            # Validate the whole completed batch before admitting another read.
            results = [(active.pop(future), future.result()) for future in done]
            completed.update(results)
            for _ in results:
                job = next(iterator, None)
                if job is not None:
                    active[pool.submit(transfer, job)] = job[0]
            if len(completed) % 100 < len(results):
                print(f"Evidence pieces verified: {len(completed)}/{len(jobs)}", flush=True)
    archive = folder / (receipt.sha256 + ".tar.gz")
    with archive.open("xb") as output:
        for i, _, _ in jobs:
            with completed[i].open("rb") as incoming:
                shutil.copyfileobj(incoming, output)
    if archive.stat().st_size != receipt.bytes or digest(archive) != receipt.sha256:
        raise ValueError("ASSEMBLED_ARCHIVE_DRIFT_RETAIN_ORIGINAL")
    immutable(HERE / "verified-download.json", {
        "at": now(), "sha256": receipt.sha256, "bytes": receipt.bytes,
        "elapsed_seconds": time.monotonic() - started,
    })
    print("Archive verified; checking backups, grades and guarded cleanup.", flush=True)
    watch.finish(config, receipt)
    proof = load(CONTROL / "verified-backups.json")
    root = archive.parent / ("extracted-" + receipt.sha256)
    accounting = load(root / "fyp-p83-v1/accounting.json")
    report = load_report().render(proof, accounting)
    report += ("\n## Retained postflight failures\n\nThe original endpoint failure, timeout, "
               "and separate interrupted transport attempts remain preserved. This recovery "
               "reassembled ranges of the same S3 version and verified its full SHA-256. "
               "No case was rerun, outcome replaced, or observation window changed. "
               "Local copies share one physical SSD; S3 is separate storage.\n")
    output_path = REPO / "artifacts/phase-8.3-recovered-outcomes.md"
    with output_path.open("x", encoding="utf-8") as output:
        output.write(report)
    immutable(HERE / "complete.json", {
        "at": now(), "exported": sum(s["state"] == "EXPORTED" for s in accounting["slots"]),
        "cleanup": load(CONTROL / "complete.json"), "main_started": False,
        "report": str(output_path),
    })
    print("Pilot outcomes reported; verified backups retained; host and disk removed.", flush=True)


def main() -> None:
    try:
        run()
    except Exception as error:
        immutable(HERE / "failure.json", {
            "at": now(), "type": type(error).__name__,
            "detail": "Evidence recovery stopped; prior files retained; no case replay",
            "main_started": False,
        })
        raise


if __name__ == "__main__":
    main()
