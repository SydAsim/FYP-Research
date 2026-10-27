"""Diagnostic v2: one pinned read; bounded, exclusively created evidence files.

The parent writes startup metadata, then the child alone writes staging data.
Logs are bounded in memory until the child exits. No concurrent script writers.
The byte budget conservatively rounds files and counts directories, existing
allocated blocks and the uploaded script. It is not a CloudShell-wide quota.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable

MIB = 1024 * 1024
CAP = 128 * MIB
FAILURE_RESERVE = MIB
RAW_LIMIT = 16 * MIB
DERIVED_LIMIT = 16 * MIB
BUNDLE_LIMIT = 16 * MIB
LOG_LIMIT = 32 * 1024
CONTROL_LIMIT = 16 * 1024
ACCOUNT = "803656589923"
REGION = "ap-southeast-2"
HOST = "i-057344e5372faf62f"
ROOT = Path.home() / "p145-diagnostic"
ORIGINAL_SCRIPT_SHA256 = "b2f7815dcffdaf9a98012dcc2039754b9936e690ea5bdfc33836ae19172b3740"


@dataclass(frozen=True)
class ObjectSpec:
    bucket: str
    key: str
    version: str
    size: int
    sha256: str
    execution: str


SPEC = ObjectSpec(
    "fyp-p82-20261005-018da1d6-803656589923",
    "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/"
    "8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24.tar.gz",
    "RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM", 37906551,
    "8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24",
    "01a11705-11f1-7386-a804-76b957c218d5",
)


class Stop(RuntimeError):
    """A safe code, never a raw provider response or credential."""


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(MIB), b""):
            h.update(block)
    return h.hexdigest()


def charge(size: int, allocated: int = 0) -> int:
    # Additional 4 KiB per file is a conservative metadata allowance.
    return max(((size + 4095) // 4096) * 4096, allocated) + 4096


class Budget:
    def __init__(self, root: Path, cap: int = CAP, reserve: int = FAILURE_RESERVE,
                 extras: Iterable[Path] = (), deadline: float | None = None):
        self.root, self.cap, self.reserve = root, cap, reserve
        self.extras, self.deadline = tuple(extras), deadline
        if root.is_symlink() or cap <= reserve + 4096:
            raise Stop("INVALID_STAGING_ROOT_OR_BUDGET")
        if not root.exists():
            root.mkdir()  # Only the canonical root, never recursive external staging.
        if not root.is_dir():
            raise Stop("INVALID_STAGING_ROOT")
        self.initial_usage = self.usage()
        if self.initial_usage > cap - reserve:
            raise Stop("EXISTING_CONTENTS_LEAVE_NO_FAILURE_RESERVE")

    def tick(self) -> None:
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise Stop("PROCESS_DEADLINE")

    def target(self, relative: str) -> Path:
        name = Path(relative)
        if name.is_absolute() or ".." in name.parts:
            raise Stop("UNSAFE_STAGING_PATH")
        p = self.root / name
        for ancestor in (p, *p.parents):
            if ancestor == self.root.parent:
                break
            if ancestor.is_symlink():
                raise Stop("STAGING_SYMLINK_REJECTED")
        return p

    def usage(self) -> int:
        total = 0
        for folder, dirs, files in os.walk(self.root, followlinks=False):
            self.tick()
            d = Path(folder).lstat()
            total += max(4096, d.st_size, getattr(d, "st_blocks", 0) * 512)
            for name in dirs + files:
                p = Path(folder) / name
                s = p.lstat()
                if stat.S_ISLNK(s.st_mode) or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)):
                    raise Stop("UNSUPPORTED_EXISTING_STAGING_ENTRY")
                if stat.S_ISREG(s.st_mode):
                    total += charge(s.st_size, getattr(s, "st_blocks", 0) * 512)
        for p in self.extras:
            if p.resolve().is_relative_to(self.root.resolve()):
                continue
            s = p.lstat()
            if not stat.S_ISREG(s.st_mode):
                raise Stop("INVALID_UPLOADED_SCRIPT")
            total += charge(s.st_size, getattr(s, "st_blocks", 0) * 512)
        return total

    def check(self, growth: int, emergency: bool = False) -> None:
        if not emergency:
            self.tick()
        # Emergency writes remain bounded; counting after deadline is permitted.
        old_deadline = self.deadline
        if emergency:
            self.deadline = None
        try:
            used = self.usage()
        finally:
            self.deadline = old_deadline
        ceiling = self.cap if emergency else self.cap - self.reserve
        if used + growth > ceiling:
            raise Stop("STAGING_BUDGET_BEFORE_WRITE")

    def mkdir(self, relative: str) -> Path:
        p = self.target(relative)
        missing = []
        for q in (p, *p.parents):
            if q == self.root or q.exists():
                break
            missing.append(q)
        self.check(4096 * len(missing))
        for q in reversed(missing):
            q.mkdir()
        return p

    def open(self, relative: str, maximum: int, emergency: bool = False) -> GuardedWriter:
        p = self.target(relative)
        if not p.parent.is_dir():
            self.mkdir(p.parent.relative_to(self.root).as_posix())
        if p.exists():
            raise Stop("EXISTING_RECORD_NEVER_OVERWRITTEN")
        self.check(charge(0), emergency)
        f = p.open("xb", buffering=0)
        return GuardedWriter(self, p, f, maximum, emergency)

    def json(self, relative: str, value: Any, maximum: int = CONTROL_LIMIT,
             emergency: bool = False, group: ByteGroup | None = None) -> None:
        with self.open(relative, maximum, emergency) as f:
            for text in json.JSONEncoder(indent=2).iterencode(value):
                data = text.encode("utf-8")
                if group:
                    group.take(len(data))
                f.write(data)

    def array(self, relative: str, values: Iterable[Any], group: ByteGroup) -> None:
        with self.open(relative, DERIVED_LIMIT) as f:
            def put(data: bytes) -> None:
                group.take(len(data))
                f.write(data)
            put(b"[")
            for i, value in enumerate(values):
                if i:
                    put(b",")
                for text in json.JSONEncoder(indent=2).iterencode(value):
                    put(text.encode("utf-8"))
            put(b"]")


class ByteGroup:
    def __init__(self, maximum: int):
        self.maximum, self.used = maximum, 0

    def take(self, amount: int) -> None:
        if self.used + amount > self.maximum:
            raise Stop("GENERATED_RECORD_GROUP_BOUND_BEFORE_WRITE")
        self.used += amount


class GuardedWriter(io.RawIOBase):
    def __init__(self, budget: Budget, path: Path, file: BinaryIO,
                 maximum: int, emergency: bool):
        self.budget, self.path, self.file = budget, path, file
        self.maximum, self.emergency = maximum, emergency

    def writable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.file.tell()

    def write(self, data: bytes) -> int:
        end = self.file.tell() + len(data)
        if end > self.maximum:
            raise Stop("FILE_BOUND_BEFORE_WRITE")
        s = self.path.stat()
        if (s.st_ino, s.st_dev, s.st_size) != (os.fstat(self.file.fileno()).st_ino,
                                             os.fstat(self.file.fileno()).st_dev, self.file.tell()):
            raise Stop("STAGING_WRITER_DRIFT")
        allocated = getattr(s, "st_blocks", 0) * 512
        growth = charge(end, allocated) - charge(s.st_size, allocated)
        self.budget.check(growth, self.emergency)
        # The reservation remains held through this unbuffered, sole-writer write.
        wrote = self.file.write(data)
        if wrote != len(data):
            raise Stop("SHORT_STAGING_WRITE")
        return wrote

    def flush(self) -> None:
        if not self.file.closed:
            self.file.flush()

    def close(self) -> None:
        if not self.closed:
            self.flush()
            super().close()
            self.file.close()


def refuse_existing_attempt(budget: Budget) -> None:
    for name in ("attempt.json", "original145.partial", "original145.tar.gz", "required",
                 "worker-result.json", "process-result.json", "parent-failure.json", "required-records.tar.gz"):
        if budget.target(name).exists():
            raise Stop("EXISTING_ATTEMPT_REQUIRES_REVIEW_NO_RETRY")


def extract_archive(budget: Budget, spec: ObjectSpec = SPEC) -> dict[str, Any]:
    archive = budget.target("original145.tar.gz")
    if archive.stat().st_size != spec.size or file_hash(archive) != spec.sha256:
        raise Stop("COMPLETE_ARCHIVE_HASH_OR_LENGTH_FAILED")
    members = ["ledger.sqlite3", f"executions/{spec.execution}/export.json",
               f"executions/{spec.execution}/checkpoint.json"]
    proof: dict[str, Any] = {"archive_sha256": spec.sha256, "archive_bytes": spec.size,
                            "bucket": spec.bucket, "key": spec.key, "version_id": spec.version,
                            "execution_id": spec.execution, "members": {}}
    budget.mkdir("required")
    with tarfile.open(archive, "r:gz") as tar:
        names = ["slot/manifest.json"] + ["slot/" + n for n in members]
        selected = {n: [] for n in names}
        for item in tar:
            budget.tick()
            if item.name in selected:
                selected[item.name].append(item)
        if any(len(items) != 1 or not items[0].isfile() for items in selected.values()):
            raise Stop("REQUIRED_MEMBER_MISSING_DUPLICATED_OR_NOT_REGULAR")
        manifest_item = selected["slot/manifest.json"][0]
        raw_total = manifest_item.size + sum(selected["slot/" + n][0].size for n in members)
        if manifest_item.size > 2 * MIB or raw_total > RAW_LIMIT:
            raise Stop("DIAGNOSTIC_RAW_RECORD_BOUND")
        budget.check(sum(charge(selected[n][0].size) for n in names) + 8 * 4096)
        manifest_data = tar.extractfile(manifest_item).read()
        manifest = json.loads(manifest_data)["files"]
        with budget.open("required/manifest.json", 2 * MIB) as out:
            out.write(manifest_data)
        proof["manifest_sha256"] = hashlib.sha256(manifest_data).hexdigest()
        for name in members:
            item = selected["slot/" + name][0]
            h = hashlib.sha256()
            source = tar.extractfile(item)
            with source, budget.open("required/" + name, item.size) as out:
                for data in iter(lambda: source.read(65536), b""):
                    out.write(data)
                    h.update(data)
            if h.hexdigest() != manifest[name]:
                raise Stop("REQUIRED_MEMBER_HASH")
            proof["members"][name] = h.hexdigest()
    export = json.loads(budget.target(f"required/executions/{spec.execution}/export.json").read_text(encoding="utf-8"))
    if export["execution_id"] != spec.execution:
        raise Stop("EXECUTION_IDENTITY")
    derived = ByteGroup(DERIVED_LIMIT)
    db_path = budget.target("required/ledger.sqlite3")
    with sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise Stop("LEDGER_INTEGRITY")
        def notices() -> Iterable[dict[str, Any]]:
            previous = "GENESIS"
            for number, at, body, prior, digest in db.execute("SELECT n,at,body,previous,hash FROM events ORDER BY n"):
                if prior != previous or hashlib.sha256((at + body + prior).encode()).hexdigest() != digest:
                    raise Stop("LEDGER_EVENT_CHAIN")
                previous = digest
                event = json.loads(body)
                if event.get("execution_id") == spec.execution or event.get("kind") in ("DRIVER_FAILURE", "CLASSIFICATION_PROBE_FAILURE"):
                    yield {"n": number, "at": at, "body": event, "previous": prior, "hash": digest}
        budget.array("required/notices.json", notices(), derived)
        def checkpoints() -> Iterable[dict[str, Any]]:
            for identity, body, digest in db.execute("SELECT execution_id,body,hash FROM checkpoints WHERE execution_id=?", (spec.execution,)):
                if hashlib.sha256(body.encode()).hexdigest() != digest:
                    raise Stop("LEDGER_CHECKPOINT_HASH")
                yield {"execution_id": identity, "body": json.loads(body), "hash": digest}
        budget.array("required/ledger-checkpoints.json", checkpoints(), derived)
        slot = db.execute("SELECT sequence,case_id,arm,execution_id,state,deadline,attempt,error FROM slots WHERE execution_id=?", (spec.execution,)).fetchall()
        if len(slot) != 1 or slot[0][2] != "B3" or slot[0][6] != 1:
            raise Stop("LEDGER_SLOT_IDENTITY")
        budget.json("required/slot-row.json", slot, DERIVED_LIMIT, group=derived)
        budget.json("required/ledger-schema.json", db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall(), DERIVED_LIMIT, group=derived)
    proof["ledger_event_chain_verified"] = True
    proof["derived_files"] = {p.relative_to(budget.target("required")).as_posix(): file_hash(p)
                              for p in budget.target("required").rglob("*") if p.is_file()}
    budget.json("required/verification.json", proof, DERIVED_LIMIT, group=derived)
    make_bundle(budget)
    return {"status": "VERIFIED_REQUIRED_RECORDS_READY", "bundle_sha256": file_hash(budget.target("required-records.tar.gz")),
            "bundle_bytes": budget.target("required-records.tar.gz").stat().st_size,
            "original_failure_type": (export.get("failure") or {}).get("type"),
            "archive_sha256": spec.sha256}


def make_bundle(budget: Budget) -> None:
    with budget.open("required-records.tar.gz", BUNDLE_LIMIT) as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                for p in sorted(budget.target("required").rglob("*")):
                    if p.is_symlink():
                        raise Stop("BUNDLE_SYMLINK_REJECTED")
                    if p.is_file():
                        tar.add(p, arcname=p.relative_to(budget.root).as_posix(), recursive=False)


def worker(attempt_id: str, deadline: float) -> int:
    script = Path(__file__).resolve()
    budget = Budget(ROOT, extras=[script], deadline=deadline)
    result: dict[str, Any] = {"status": "STARTED", "started_at": utc(), "bytes_retrieved": 0,
                              "remaining_bytes": SPEC.size, "api_sends": {}}
    try:
        # Parent writes process.json and then creates start.signal; child writes nothing before it.
        while not budget.target("start.signal").exists():
            budget.tick()
            time.sleep(.01)
        attempt = json.loads(budget.target("attempt.json").read_text(encoding="utf-8"))
        process = json.loads(budget.target("process.json").read_text(encoding="utf-8"))
        if (attempt["attempt_id"] != attempt_id or process["pid"] != os.getpid()
                or process["parent_pid"] != os.getppid() or attempt["script_sha256"] != file_hash(script)):
            raise Stop("WORKER_BINDING_FAILED")
        import boto3
        from botocore.config import Config
        session = boto3.Session(region_name=REGION)
        config = Config(connect_timeout=5, read_timeout=10, retries={"total_max_attempts": 1, "mode": "standard"})
        def client(service: str, operation: str) -> Any:
            c = session.client(service, config=config)
            key = service + "." + operation
            def sending(**unused: Any) -> None:
                budget.tick()
                if result["api_sends"].get(key, 0) >= 1:
                    raise Stop("REMOTE_ATTEMPT_LIMIT_NO_RETRY")
                result["api_sends"][key] = 1
            c.meta.events.register("before-send." + service + "." + operation, sending)
            return c
        identity = client("sts", "GetCallerIdentity").get_caller_identity()
        if identity["Account"] != ACCOUNT:
            raise Stop("WRONG_PROJECT_STOP")
        result["account"], result["region"] = ACCOUNT, REGION
        ec2 = client("ec2", "DescribeInstances").describe_instances(InstanceIds=[HOST])
        state = ec2["Reservations"][0]["Instances"][0]["State"]["Name"]
        result["campaign_host_state"] = state
        if state != "stopped":
            raise Stop("CAMPAIGN_HOST_NOT_STOPPED_STOP")
        # Worst-case future footprint, before the sole GET. Every write is also checked.
        budget.check(charge(SPEC.size) + RAW_LIMIT + DERIVED_LIMIT + BUNDLE_LIMIT + 128 * 1024)
        response = client("s3", "GetObject").get_object(Bucket=SPEC.bucket, Key=SPEC.key, VersionId=SPEC.version)
        with response["Body"] as body:
            if response.get("VersionId") != SPEC.version or response.get("ContentLength") != SPEC.size:
                raise Stop("OBJECT_IDENTITY_OR_SIZE_MISMATCH")
            with budget.open("original145.partial", SPEC.size) as out, budget.open("download-progress.jsonl", 128 * 1024) as progress:
                last = 0
                for data in iter(lambda: body.read(65536), b""):
                    out.write(data)
                    result["bytes_retrieved"] += len(data)
                    result["remaining_bytes"] = SPEC.size - result["bytes_retrieved"]
                    if result["bytes_retrieved"] - last >= MIB:
                        progress.write((json.dumps({"at": utc(), "bytes": result["bytes_retrieved"]}) + "\n").encode())
                        last = result["bytes_retrieved"]
        partial = budget.target("original145.partial")
        if partial.stat().st_size != SPEC.size or file_hash(partial) != SPEC.sha256:
            raise Stop("COMPLETE_ARCHIVE_HASH_OR_LENGTH_FAILED")
        if budget.target("original145.tar.gz").exists():
            raise Stop("EXISTING_RECORD_NEVER_OVERWRITTEN")
        partial.rename(budget.target("original145.tar.gz"))  # Same inode; no second archive copy.
        result.update(extract_archive(budget))
    except Exception as exc:
        result.update(status="STOPPED", error_type=type(exc).__name__)
        if isinstance(exc, Stop):
            result["reason"] = str(exc)
        if hasattr(exc, "response"):
            code = exc.response.get("Error", {}).get("Code", "")
            result["aws_error_code"] = code[:80] if isinstance(code, str) and code.replace("_", "").isalnum() else "REDACTED"
        partial = budget.target("original145.partial")
        if partial.exists():
            result["bytes_retrieved"] = partial.stat().st_size
            result["remaining_bytes"] = SPEC.size - result["bytes_retrieved"]
    result["finished_at"] = utc()
    budget.json("worker-result.json", result, emergency=True)
    return 0 if result["status"] == "VERIFIED_REQUIRED_RECORDS_READY" else 1


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        return worker(sys.argv[2], float(sys.argv[3]))
    started = time.monotonic()
    deadline = started + 180
    script = Path(__file__).resolve()
    budget: Budget | None = None
    child: subprocess.Popen[bytes] | None = None
    owned_attempt = False
    try:
        budget = Budget(ROOT, extras=[script], deadline=deadline)
        refuse_existing_attempt(budget)
        if not sys.platform.startswith("linux"):
            raise Stop("CLOUD_RUN_REQUIRES_LINUX")
        regions = [os.environ[k] for k in ("AWS_REGION", "AWS_DEFAULT_REGION") if os.environ.get(k)]
        if not regions or any(r != REGION for r in regions):
            raise Stop("CLOUDSHELL_REGION_NOT_VERIFIED")
        # Import availability only; no credentials or AWS calls here.
        import boto3  # noqa: F401
        import botocore  # noqa: F401
        if shutil.disk_usage(ROOT).free < CAP:
            raise Stop("INSUFFICIENT_CLOUDSHELL_HEADROOM")
        budget.check(charge(SPEC.size) + RAW_LIMIT + DERIVED_LIMIT + BUNDLE_LIMIT + 256 * 1024)
        attempt_id = "d145v2-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        budget.json("attempt.json", {"attempt_id": attempt_id, "started_at": utc(), "script_sha256": file_hash(script),
                                    "original_script_sha256": ORIGINAL_SCRIPT_SHA256, "staging_cap_bytes": CAP,
                                    "failure_reserve_bytes": FAILURE_RESERVE, "initial_charged_bytes": budget.initial_usage,
                                    "process_deadline_seconds": 180, "sdk_total_attempts": 1,
                                    "api_budget": {"sts": 1, "ec2": 1, "s3_version_get": 1}})
        owned_attempt = True
        child = subprocess.Popen([sys.executable, "-B", str(script), "--worker", attempt_id, str(deadline)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        budget.json("process.json", {"pid": child.pid, "parent_pid": os.getpid(), "attempt_id": attempt_id})
        with budget.open("start.signal", 1) as f:
            f.write(b"1")
        logs = {"worker-stdout.log": bytearray(), "worker-stderr.log": bytearray()}
        log_failed = threading.Event()
        def drain(pipe: BinaryIO, name: str) -> None:
            while data := pipe.read(4096):
                remaining = LOG_LIMIT - len(logs[name])
                logs[name].extend(data[:remaining])
                if len(data) > remaining:
                    log_failed.set()
                    if child.poll() is None:
                        child.kill()
            pipe.close()
        threads = [threading.Thread(target=drain, args=(pipe, name), daemon=True)
                   for pipe, name in ((child.stdout, "worker-stdout.log"), (child.stderr, "worker-stderr.log"))]
        for thread in threads:
            thread.start()
        timed_out = False
        try:
            code = child.wait(timeout=max(.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            child.kill()
            code = child.wait(timeout=2)
        for thread in threads:
            thread.join(timeout=2)
        if any(thread.is_alive() for thread in threads):
            raise Stop("LOG_DRAIN_DID_NOT_FINISH")
        # The worker is now dead: parent alone commits bounded logs/final records.
        for name, data in logs.items():
            with budget.open(name, LOG_LIMIT, emergency=True) as f:
                f.write(data)
        summary = json.loads(budget.target("worker-result.json").read_text(encoding="utf-8")) if budget.target("worker-result.json").exists() else {"status": "STOPPED", "reason": "NO_FINAL_WORKER_RECORD"}
        if timed_out or log_failed.is_set() or code != 0:
            summary["status"] = "STOPPED"
            summary["parent_stop_reason"] = "PROCESS_DEADLINE" if timed_out else "LOG_BOUND" if log_failed.is_set() else "WORKER_EXIT"
        summary.update(process_exit=code, finished_at=utc())
        if "bytes_retrieved" not in summary:
            partial = budget.target("original145.partial")
            complete = budget.target("original145.tar.gz")
            summary["bytes_retrieved"] = partial.stat().st_size if partial.exists() else complete.stat().st_size if complete.exists() else 0
            summary["remaining_bytes"] = SPEC.size - summary["bytes_retrieved"]
        budget.json("process-result.json", summary, emergency=True)
        budget.deadline = None
        summary["charged_staging_bytes"] = budget.usage()
        summary["staging_cap_bytes"] = CAP
        summary["download_path"] = str(budget.target("required-records.tar.gz")) if summary["status"] == "VERIFIED_REQUIRED_RECORDS_READY" else None
        print(json.dumps(summary, indent=2))
        return 0 if summary["status"] == "VERIFIED_REQUIRED_RECORDS_READY" else 1
    except Exception as exc:
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=2)
        result = {"status": "STOPPED", "error_type": type(exc).__name__,
                  "reason": str(exc) if isinstance(exc, Stop) else "DIAGNOSTIC_SETUP_FAILURE", "at": utc()}
        if budget is not None and (owned_attempt or not budget.target("attempt.json").exists()) and not budget.target("parent-failure.json").exists():
            budget.json("parent-failure.json", result, emergency=True)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
