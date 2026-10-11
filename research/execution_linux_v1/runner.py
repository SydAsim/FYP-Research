"""Versioned Linux terminal runner. Calibration only; no freeze or main launch API."""

import importlib.util
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from research.execution_linux_v1 import platform, runtime
from research.execution_linux_v1.portable import ensure_aliases
from research.execution_setup import cli, core, worker
from research.execution_setup.core import ROOT, atomic, immutable, load, now
from research.execution_setup.resources import admission

VERSION = "phase8-linux-setup-v1"
PREFIX = "cal-v4-linux-v1-"
PACKAGE = ROOT / "artifacts/phase-8-linux-setup/v1"
IMAGE_DIGESTS = {
    "postgres:16.9": (
        "postgres@sha256:ddfe3e8713e3ee5b8f286082cb12512488dfbf3f5a1ecb0b74a42e6055af0a5f"
    ),
    "redis:7.4.5-alpine": (
        "redis@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08"
    ),
}


def archive_class() -> Any:
    path = ROOT / "artifacts/phase-8-execution-setup/v2/runner.py"
    spec = importlib.util.spec_from_file_location("historical_storage_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing preserved storage adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ArchiveLedger


def ledger_for(root: Path) -> Any:
    """Dynamic historical storage boundary; overrides exist only in this process."""
    return vars(cli)["Ledger"](root)


def verify_package() -> None:
    manifest = load(ROOT / "linux-package-seal.json")
    if manifest["version"] != VERSION or manifest["main_started"] is not False:
        raise ValueError("INVALID_LINUX_PACKAGE")
    core.check_inventory(manifest["hashes"])
    ensure_aliases()


def initialize(root: Path, backup: Path) -> None:
    root, backup = root.resolve(), backup.resolve()
    if root == backup or root in backup.parents or backup in root.parents:
        raise ValueError("Backup must be outside the live output tree")
    if ROOT == root or ROOT in root.parents or ROOT == backup or ROOT in backup.parents:
        raise ValueError("Research evidence must be outside the sealed source tree")
    if root.exists() and any(root.iterdir()):
        raise ValueError("Use a new directory; unsuccessful attempts must not be replaced")
    verify_package()
    root.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)
    # Keep all historical sources/exports separately from the Linux adapter version.
    historical = load(PACKAGE / "preserved-before.json")
    core.check_inventory(historical)
    immutable(root / "historical-hashes-before.json", historical)
    bank = load(ROOT / "research/fixtures/phase8_design_v4/inputs.json")
    cases, slots = {}, []
    for number, (family, arm) in enumerate((("CLEAN", "B3"), ("buffered-stale", "P1")), 1):
        original = next(
            c
            for c in bank["calibration_inputs"]
            if (c["stratum"] == "CLEAN" if family == "CLEAN" else c["generator_family"] == family)
        )
        case = {**original, "case_id": f"{PREFIX}{number:04d}"}
        cases[case["case_id"]] = case
        slots.append((number, case["case_id"], arm, "PLANNED", 1, "ORIGINAL_PLANNED"))
    identity = uuid4().hex[:10]
    names = [f"p8-linux-v1-{identity}-{kind}" for kind in ("app", "truth", "cache")]
    # Bridge mode is for local Linux-in-Docker validation only; AWS uses loopback.
    network = os.environ.get("P8_VALIDATION_NETWORK")
    app_host = names[0] if network else "127.0.0.1:16432"
    truth_host = names[1] if network else "127.0.0.1:16433"
    resources = {
        "resource_id": identity,
        "containers": names,
        "database": f"postgresql://setup_app:setup_local_only@{app_host}/setup_app",
        "sim_database": f"postgresql://setup_truth:setup_local_only@{truth_host}/setup_truth",
        "services": [19100, 19101, 19102, 19110],
        "concurrency": 1,
        "validation_network": network,
        "image_digests": IMAGE_DIGESTS,
    }
    plan = {
        "version": VERSION,
        "classification": "CALIBRATION_ONLY_NOT_MAIN",
        "created_at": now(),
        "cases": cases,
        "order": [s[1:3] for s in slots],
        "window_seconds": 600,
        "poll_seconds": 5,
        "concurrency": 1,
        "purposes": ["LINUX_NORMAL_RETURN_FULL_WINDOW_RESUME", "LINUX_REFUSAL_FULL_WINDOW"],
        "main_started": False,
        "review_receipt": None,
        "freeze_hash": None,
    }
    ledger = ledger_for(root)
    for filename, value in (
        ("qualification-plan.json", plan),
        (
            "config.json",
            {
                "version": VERSION,
                "backup": str(backup),
                "main_started": False,
                "scope": "500 inputs across B3/P1/P2; 1500 main slots blocked",
            },
        ),
        ("resources.json", resources),
        ("source-seal.json", core.source_inventory()),
        ("linux-package-seal.json", load(ROOT / "linux-package-seal.json")),
    ):
        immutable(root / filename, value)
        ledger.seal(root / filename)
    ledger.seal(root / "historical-hashes-before.json")
    with ledger.connect() as conn:
        conn.executemany(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) VALUES (?,?,?,?,?,?)",
            slots,
        )
    sample = platform.host(root, backup)
    immutable(root / "initial-resources.json", sample)
    ledger.seal(root / "initial-resources.json")
    order = load(ROOT / "artifacts/phase-8-study-design/v4/execution-order.json")["rows"]
    template = [
        {
            "sequence": i * 3 + j + 1,
            "case_id": row["case_id"],
            "arm": arm,
            "status": "NOT_STARTED",
            "execution_id": None,
        }
        for i, row in enumerate(order)
        for j, arm in enumerate(row["arm_order"])
    ]
    immutable(
        root / "main-schedule-template.json",
        {
            "status": "GUARDED_NOT_ADMISSIBLE",
            "main_started": False,
            "slots": template,
        },
    )
    ledger.seal(root / "main-schedule-template.json")
    ledger.event("LINUX_INITIALIZED", version=VERSION, sample=sample, main_started=False)
    print(f"Initialized two CALIBRATION slots in {root}; all 1500 main slots blocked", flush=True)


def verify(root: Path) -> None:
    verify_package()
    ledger_for(root).full_verify()
    core.check_source(root)
    core.check_inventory(load(root / "historical-hashes-before.json"))
    slots = load(ROOT / "artifacts/phase-8-study-design/v4/main-slots.json")
    if len(slots) != 1500 or any(s["status"] != "NOT_STARTED" or s["execution_id"] for s in slots):
        raise ValueError("MAIN_GUARD_CHANGED")


def _terminate_parent(signum: int, frame: Any) -> None:
    raise KeyboardInterrupt


def run(root: Path, *, checkpoint_once: bool = False, pause_after: int | None = None) -> None:
    ledger = ledger_for(root)
    backup = Path(load(root / "config.json")["backup"])
    with platform.runner_lock(root):
        completed = 0
        while True:
            verify(root)
            active = [r for r in ledger.rows() if r["state"] in ("RUNNING", "CHECKPOINTED")]
            if (root / "pause.json").exists() and not active:
                print(f"PAUSED: {load(root / 'pause.json')}; no new admissions", flush=True)
                return
            if not active:
                sample = platform.host(root, backup)
                ledger.event("ADMISSION_RESOURCE_CHECK", sample=sample)
                admission(sample)
            slot = ledger.admit()
            if slot is None:
                print("DONE: finite calibration queue; main campaign unstarted", flush=True)
                ledger.backup(backup)
                return
            directory = root / "executions" / slot["execution_id"]
            directory.mkdir(parents=True, exist_ok=True)
            owner_path = directory / "linux-collector-owner.json"
            attached_pid = None
            attached_identity = None
            if active and owner_path.exists():
                owner = load(owner_path)
                if owner["boot_id"] != platform.boot_id():
                    raise ValueError("HOST_REBOOT_UNQUALIFIED")
                if platform.process_identity(owner["pid"]) == owner["identity"]:
                    attached_pid = owner["pid"]
                    attached_identity = owner["identity"]
            child: subprocess.Popen[bytes] | None = None
            if attached_pid is None:
                if not active:
                    runtime.provision(root)
                command = [
                    sys.executable,
                    "-m",
                    "research.execution_linux_v1.runner",
                    "worker",
                    "--root",
                    str(root),
                    "--execution",
                    slot["execution_id"],
                ]
                if not active:
                    command.append("--fresh")
                if checkpoint_once:
                    command.append("--checkpoint-once")
                log = directory / f"terminal-{uuid4()}.log"
                with log.open("xb") as output:
                    child = subprocess.Popen(
                        command, cwd=ROOT, stdout=output, stderr=output, start_new_session=True
                    )
                identity = platform.process_identity(child.pid)
                if identity is None:
                    raise RuntimeError("COLLECTOR_EXITED_BEFORE_CHECKPOINT")
                atomic(
                    owner_path,
                    {
                        "pid": child.pid,
                        "identity": identity,
                        "boot_id": platform.boot_id(),
                        "log": str(log),
                    },
                )
                attached_pid = child.pid
                attached_identity = identity
                ledger.event(
                    "LINUX_COLLECTOR_STARTED",
                    execution_id=slot["execution_id"],
                    pid=child.pid,
                    log=str(log),
                )
            else:
                ledger.event(
                    "LINUX_PARENT_REATTACHED", execution_id=slot["execution_id"], pid=attached_pid
                )
            print(
                f"RUN {slot['sequence']} {slot['case_id']} {slot['arm']} {slot['execution_id']}",
                flush=True,
            )
            try:
                while platform.process_identity(attached_pid) == attached_identity:
                    if child is not None:
                        try:
                            child.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            pass
                    else:
                        import time

                        time.sleep(30)
                    current = next(
                        r for r in ledger.rows() if r["execution_id"] == slot["execution_id"]
                    )
                    print(f"PROGRESS {current['state']} deadline={current['deadline']}", flush=True)
            except KeyboardInterrupt:
                atomic(root / "pause.json", {"reason": "USER_SAFE_STOP", "at": now()})
                ledger.event(
                    "SAFE_PARENT_SHUTDOWN",
                    execution_id=slot["execution_id"],
                    worker_pid=attached_pid,
                    detail="Detached collector continues",
                )
                print("SAFE STOP: collector continues. Keep host and Docker running.", flush=True)
                return
            if child is not None:
                child.wait(timeout=5)
            current = next(r for r in ledger.rows() if r["execution_id"] == slot["execution_id"])
            if current["state"] == "CHECKPOINTED" and (child is None or child.returncode == 75):
                ledger.backup(backup)
                print("CHECKPOINTED: resume SAME execution and original deadline", flush=True)
                return
            if current["state"] != "EXPORTED" or (child is not None and child.returncode != 0):
                ledger.event(
                    "FAILURE_NOTICE",
                    execution_id=slot["execution_id"],
                    exit=child.returncode if child else "UNKNOWN_DETACHED_EXIT",
                )
                atomic(root / "pause.json", {"reason": "WORKER_FAILURE", "at": now()})
                raise RuntimeError(
                    "Collector failed; original attempt retained; admissions stopped"
                )
            completed += 1
            ledger.backup(backup)
            if pause_after is not None and completed >= pause_after:
                atomic(root / "pause.json", {"reason": "PAUSE_BETWEEN_SLOTS", "at": now()})
                print("PAUSED between completed slots; saved order unchanged", flush=True)
                return


def install() -> None:
    platform.require_linux()
    ensure_aliases()
    runtime.install_process_boundary()
    ledger_class = archive_class()
    core.PREFIX = PREFIX
    for module in (cli, worker):
        vars(module).update(
            PREFIX=PREFIX, Ledger=ledger_class, host=platform.host, runner_lock=platform.runner_lock
        )
    vars(cli).update(VERSION=VERSION, provision=runtime.provision)
    vars(worker)["Runtime"] = runtime.Runtime
    cli.initialize, cli.verify, cli.run = initialize, verify, run


def main() -> None:
    install()
    signal.signal(signal.SIGTERM, _terminate_parent)
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        verify_package()
        root = Path(sys.argv[sys.argv.index("--root") + 1])
        execution = sys.argv[sys.argv.index("--execution") + 1]
        ledger = ledger_for(root)
        slot = next(r for r in ledger.rows() if r["execution_id"] == execution)
        if not slot["case_id"].startswith(PREFIX):
            raise ValueError("MAIN_CAMPAIGN_GUARD")
        if "--fresh" in sys.argv:
            sys.argv.remove("--fresh")
        else:
            # SQL checkpoint is authoritative even if the convenience file was lost.
            recovered = ledger.recover_checkpoint(execution)
            atomic(root / "executions" / execution / "checkpoint.json", recovered)
        sys.argv.pop(1)
        worker.main()
        return
    cli.main()


def entrypoint() -> None:
    try:
        main()
    except Exception as error:
        if "--root" in sys.argv:
            failed_root = Path(sys.argv[sys.argv.index("--root") + 1])
            failed_ledger = core.Ledger(failed_root)
            failed_ledger.event("LINUX_PROTOCOL_STOP", detail=str(error), main_started=False)
            atomic(failed_root / "pause.json", {"reason": str(error), "at": now()})
        raise


if __name__ == "__main__":
    entrypoint()
