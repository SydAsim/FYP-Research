"""Evidence-only, version-pinned transport. No driver, freeze or launch operation."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures as futures
import hashlib
import json
import os
import re
import shutil
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bucket: str = Field(min_length=3)
    key: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0, le=100 * 1024**3)


class Store(Protocol):
    def head(self, receipt: Receipt) -> None: ...
    def read(self, receipt: Receipt, start: int, end: int) -> bytes: ...


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as incoming:
        for block in iter(lambda: incoming.read(1024**2), b""):
            value.update(block)
    return value.hexdigest()


def record(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class S3Store:
    """Any is confined to the boto3 boundary; one shared client per process."""

    def __init__(self, profile: str) -> None:
        import boto3
        from botocore.config import Config

        self.client: Any = boto3.Session(profile_name=profile, region_name="ap-southeast-2").client(
            "s3",
            config=Config(
                connect_timeout=10,
                read_timeout=30,
                max_pool_connections=8,
                retries={"mode": "standard", "total_max_attempts": 3},
            ),
        )

    def head(self, receipt: Receipt) -> None:
        head = self.client.head_object(
            Bucket=receipt.bucket,
            Key=receipt.key,
            VersionId=receipt.version_id,
            ChecksumMode="ENABLED",
        )
        if (
            head.get("VersionId") != receipt.version_id
            or head.get("ContentLength") != receipt.bytes
            or head.get("Metadata", {}).get("sha256") != receipt.sha256
            or base64.b64decode(head.get("ChecksumSHA256", "")).hex() != receipt.sha256
        ):
            raise ValueError("S3_VERSION_SIZE_HASH_DRIFT")

    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        from botocore.exceptions import BotoCoreError

        try:
            response = self.client.get_object(
                Bucket=receipt.bucket,
                Key=receipt.key,
                VersionId=receipt.version_id,
                Range=f"bytes={start}-{end}",
            )
            with response["Body"] as body:
                if (
                    response.get("VersionId") != receipt.version_id
                    or response.get("ContentRange") != f"bytes {start}-{end}/{receipt.bytes}"
                ):
                    raise ValueError("S3_RANGE_OR_VERSION_DRIFT")
                data: bytes = body.read()
        except BotoCoreError as error:
            # Specific network/body error, journalled by the bounded piece retry.
            # ClientError (permission, wrong version, missing object) stops immediately.
            raise OSError(type(error).__name__) from error
        if len(data) != end - start + 1:
            raise ValueError("INCOMPLETE_S3_RANGE")
        return data


def download(
    store: Store,
    receipt: Receipt,
    root: Path,
    *,
    workers: int = 8,
    chunk: int = 65536,
    seconds: int = 1800,
) -> Path:
    if workers not in range(1, 9) or chunk < 1 or seconds < 1:
        raise ValueError("INVALID_TRANSPORT_LIMIT")
    root.mkdir(parents=True, exist_ok=True)
    # Exclusive lock is deliberately not cleared after an abrupt kill. Reconcile
    # the process first and retain/rename that stale lock before a read-only resume.
    lock = root / "transport.lock"
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    try:
        identity: dict[str, Any] = {
            "receipt": receipt.model_dump(),
            "chunk": chunk,
            "deadline": time.time() + seconds,
        }
        checkpoint = root / "identity.json"
        if checkpoint.exists():
            saved = load(checkpoint)
            if saved["receipt"] != identity["receipt"] or saved["chunk"] != chunk:
                raise ValueError("CHECKPOINT_IDENTITY_DRIFT")
            identity = saved  # Original transport deadline, never silently reset.
        else:
            record(checkpoint, identity)
        store.head(receipt)
        archive = root / "e.tar.gz"
        if archive.exists():
            if archive.stat().st_size != receipt.bytes or sha(archive) != receipt.sha256:
                raise ValueError("EXISTING_ARCHIVE_DRIFT_RETAIN_ORIGINAL")
            return archive
        if shutil.disk_usage(root).free < 2 * receipt.bytes + 1024**3:
            raise ValueError("INSUFFICIENT_TRANSPORT_DISK")

        def piece(job: tuple[int, int, int]) -> Path:
            index, start, end = job
            path = root / "pieces" / f"{index:08d}.bin"
            proof = path.with_suffix(".json")
            if path.exists() or proof.exists():
                if (
                    not path.is_file()
                    or not proof.is_file()
                    or path.stat().st_size != end - start + 1
                    or sha(path) != load(proof)["sha256"]
                    or load(proof)["version"] != receipt.version_id
                    or load(proof)["range"] != [start, end]
                ):
                    raise ValueError("PIECE_DRIFT_OR_UNPROVEN_PARTIAL_RETAIN")
                return path
            for attempt in range(1, 4):
                if time.time() >= identity["deadline"]:
                    raise TimeoutError("ORIGINAL_TRANSPORT_DEADLINE")
                journal = root / "reads" / f"{index:08d}-{time.time_ns()}.json"
                try:
                    data = store.read(receipt, start, end)
                except (OSError, TimeoutError) as error:
                    record(
                        journal,
                        {
                            "range": [start, end],
                            "attempt": attempt,
                            "failure": type(error).__name__,
                            "case_rerun": False,
                        },
                    )
                    if attempt == 3:
                        raise
                    continue
                # Botocore network/body errors are converted at its boundary below.
                if len(data) != end - start + 1:
                    raise ValueError("INCOMPLETE_RANGE_RETAIN_FAILURE")
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                record(
                    proof,
                    {
                        "sha256": sha(path),
                        "bytes": len(data),
                        "version": receipt.version_id,
                        "range": [start, end],
                    },
                )
                record(journal, {"range": [start, end], "attempt": attempt, "verified": True})
                return path
            raise RuntimeError("UNREACHABLE_TRANSPORT_ATTEMPT")

        jobs = [
            (i, start, min(start + chunk, receipt.bytes) - 1)
            for i, start in enumerate(range(0, receipt.bytes, chunk))
        ]
        iterator = iter(jobs)
        completed: dict[int, Path] = {}
        with futures.ThreadPoolExecutor(max_workers=workers) as pool:
            active = {}
            for _ in range(min(workers, len(jobs))):
                job = next(iterator)
                active[pool.submit(piece, job)] = job[0]
            while active:
                done, _ = futures.wait(active, return_when=futures.FIRST_COMPLETED)
                results = [(active.pop(f), f.result()) for f in done]
                completed.update(results)
                for _ in results:
                    next_job = next(iterator, None)
                    if next_job is not None:
                        active[pool.submit(piece, next_job)] = next_job[0]
                if len(completed) % 100 < len(results):
                    print(f"Verified evidence pieces {len(completed)}/{len(jobs)}", flush=True)
        # Unique assembly attempts preserve an interrupted assembly, never overwrite.
        partial = root / f"assembly-{time.time_ns()}.partial"
        with partial.open("xb") as output:
            for index, _, _ in jobs:
                with completed[index].open("rb") as incoming:
                    shutil.copyfileobj(incoming, output)
            output.flush()
            os.fsync(output.fileno())
        if partial.stat().st_size != receipt.bytes or sha(partial) != receipt.sha256:
            raise ValueError("ASSEMBLED_HASH_DRIFT_RETAIN_PARTIAL")
        partial.rename(archive)
        record(
            root / f"success-{time.time_ns()}.json",
            {"sha256": receipt.sha256, "bytes": receipt.bytes, "case_rerun": False},
        )
        return archive
    except BaseException as error:
        record(
            root / f"failure-{time.time_ns()}.json",
            {
                "at": datetime.now(UTC).isoformat(),
                "type": type(error).__name__,
                "message": str(error) if isinstance(error, ValueError) else "Transport interrupted",
                "case_rerun": False,
                "retained": True,
            },
        )
        raise
    finally:
        lock.unlink()


def extract(
    archive: Path, destination: Path, expected: str, *, max_bytes: int = 100 * 1024**3
) -> dict[str, object]:
    if sha(archive) != expected:
        raise ValueError("ARCHIVE_HASH_DRIFT")
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("NEW_EXTRACTION_DIRECTORY_REQUIRED_RETAIN_ORIGINAL")
    with tarfile.open(archive, "r:gz") as incoming:
        members = incoming.getmembers()
        seen: set[str] = set()
        total = 0
        for member in members:
            name = member.name
            path = PurePosixPath(name)
            if (
                path.is_absolute()
                or PureWindowsPath(name).drive
                or ".." in path.parts
                or "\\" in name
                or not (member.isfile() or member.isdir())
                or any(re.search(r'[<>:"|?*\x00-\x1f]', part) for part in path.parts)
                or any(part.endswith((" ", ".")) for part in path.parts)
                or any(
                    part.split(".")[0].upper()
                    in {
                        "CON",
                        "PRN",
                        "AUX",
                        "NUL",
                        *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)],
                    }
                    for part in path.parts
                )
            ):
                raise ValueError("UNSAFE_TAR_MEMBER")
            target = destination.joinpath(*path.parts)
            normalized = str(target).casefold()
            if normalized in seen or len(str(target)) >= 240:
                raise ValueError("DUPLICATE_OR_WINDOWS_PATH_BUDGET")
            seen.add(normalized)
            total += member.size
        if total > max_bytes or shutil.disk_usage(destination.parent).free < total + 1024**3:
            raise ValueError("EXTRACTION_CAPACITY_LIMIT")
        destination.mkdir()
        try:
            incoming.extractall(destination, members=members, filter="data")
        except BaseException as error:
            record(
                destination.parent / f"extract-failure-{time.time_ns()}.json",
                {"type": type(error).__name__, "retained_partial": str(destination)},
            )
            raise
    return {
        "sha256": expected,
        "members": len(members),
        "uncompressed_bytes": total,
        "maximum_path_chars": max((len(str(destination / m.name)) for m in members), default=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("--profile", default="fyp-research")
    parser.add_argument("--local-archive", type=Path)
    args = parser.parse_args()
    receipt = Receipt.model_validate(load(args.receipt))
    if args.local_archive:
        archive = args.local_archive
    else:
        archive = download(S3Store(args.profile), receipt, args.root)
    args.root.mkdir(parents=True, exist_ok=True)
    try:
        proof = extract(archive, args.root / "x", receipt.sha256)
        record(args.root / "extraction-verified.json", proof)
        print("Verified evidence extracted. No study case, freeze or cleanup was executed.")
    except BaseException as error:
        record(
            args.root / f"postflight-failure-{time.time_ns()}.json",
            {"type": type(error).__name__, "retained": True, "cleanup_authorized": False},
        )
        raise


if __name__ == "__main__":
    main()
