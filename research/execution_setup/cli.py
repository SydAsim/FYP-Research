"""Normal-terminal orchestration. Intentionally no freeze or main-launch command."""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from research.execution_setup.core import (
    PREFIX,
    ROOT,
    VERSION,
    Ledger,
    atomic,
    check_inventory,
    check_source,
    immutable,
    load,
    now,
    preserve,
    runner_lock,
    source_inventory,
)
from research.execution_setup.resources import admission, host
from research.execution_setup.runtime import provision


def initialize(root: Path, backup: Path) -> None:
    if root.exists() and any(root.iterdir()):
        raise ValueError("Use a new directory; existing attempts must not be replaced")
    root.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)
    if root == backup or root in backup.parents or backup in root.parents:
        raise ValueError("Backup must be outside the live output tree")
    preserve(root)
    bank = load(ROOT / "research/fixtures/phase8_design_v4/inputs.json")
    cases: dict[str, Any] = {}
    selected = (("CLEAN", "B3"), ("buffered-stale", "P1"))
    slots = []
    for number, (family, arm) in enumerate(selected, 1):
        original = next(
            c
            for c in bank["calibration_inputs"]
            if (c["stratum"] == "CLEAN" if family == "CLEAN" else c["generator_family"] == family)
        )
        case = {**original, "case_id": f"{PREFIX}{number:04d}"}
        cases[case["case_id"]] = case
        slots.append((number, case["case_id"], arm, "PLANNED", 1, "ORIGINAL_PLANNED"))
    plan = {
        "version": VERSION,
        "classification": "CALIBRATION_ONLY_NOT_MAIN",
        "created_at": now(),
        "cases": cases,
        "order": [s[1:3] for s in slots],
        "window_seconds": 600,
        "poll_seconds": 5,
        "concurrency": 1,
        "purposes": [
            "NORMAL_RETURN_FULL_WINDOW_SAME_EXECUTION_RESUME",
            "REFUSAL_FULL_WINDOW_SAVED_ORDER_RESUME",
        ],
        "parallel_condition": "Only test two if available RAM >=4GiB and disk guards pass",
        "main_started": False,
        "review_receipt": None,
        "freeze_hash": None,
    }
    config = {
        "version": VERSION,
        "backup": str(backup),
        "main_started": False,
        "scope": "500 paired inputs, B3/P1/P2, 1500 slots; main admission disabled",
    }
    identity = uuid4().hex[:10]
    resources = {
        "resource_id": identity,
        "containers": [
            f"p8-setup-v1-{identity}-app",
            f"p8-setup-v1-{identity}-truth",
            f"p8-setup-v1-{identity}-cache",
        ],
        "database": "postgresql://setup_app:setup_local_only@127.0.0.1:16432/setup_app",
        "sim_database": "postgresql://setup_truth:setup_local_only@127.0.0.1:16433/setup_truth",
        "services": [19100, 19101, 19102, 19110],
        "concurrency": 1,
    }
    ledger = Ledger(root)
    for filename, value in (
        ("qualification-plan.json", plan),
        ("config.json", config),
        ("resources.json", resources),
        ("source-seal.json", source_inventory()),
    ):
        immutable(root / filename, value)
        ledger.seal(root / filename)
    ledger.seal(root / "historical-hashes-before.json")
    with ledger.connect() as conn:
        conn.executemany(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) VALUES (?,?,?,?,?,?)",
            slots,
        )
    sample = host(root, backup)
    immutable(root / "initial-resources.json", sample)
    ledger.seal(root / "initial-resources.json")
    ledger.event("SETUP_INITIALIZED", version=VERSION, sample=sample, main_started=False)
    order = load(ROOT / "artifacts/phase-8-study-design/v4/execution-order.json")["rows"]
    immutable(
        root / "main-schedule-template.json",
        {
            "status": "GUARDED_NOT_ADMISSIBLE",
            "main_started": False,
            "slots": [
                {
                    "sequence": i * 3 + j + 1,
                    "case_id": row["case_id"],
                    "arm": arm,
                    "status": "NOT_STARTED",
                    "execution_id": None,
                }
                for i, row in enumerate(order)
                for j, arm in enumerate(row["arm_order"])
            ],
        },
    )
    ledger.seal(root / "main-schedule-template.json")
    print(f"Initialized two calibration slots in {root}; main campaign blocked", flush=True)


def verify(root: Path) -> None:
    ledger = Ledger(root)
    ledger.verify()
    check_source(root)
    check_inventory(load(root / "historical-hashes-before.json"))
    slots = load(ROOT / "artifacts/phase-8-study-design/v4/main-slots.json")
    if len(slots) != 1500 or any(s["status"] != "NOT_STARTED" or s["execution_id"] for s in slots):
        raise ValueError("MAIN_GUARD_CHANGED")


def run(root: Path, *, checkpoint_once: bool = False, pause_after: int | None = None) -> None:
    ledger = Ledger(root)
    backup = Path(load(root / "config.json")["backup"])
    with runner_lock(root):
        completed = 0
        while True:
            verify(root)
            active = [r for r in ledger.rows() if r["state"] in ("RUNNING", "CHECKPOINTED")]
            if (root / "pause.json").exists() and not active:
                print(f"PAUSED: {load(root / 'pause.json')}; no new admissions", flush=True)
                return
            if not active:
                sample = host(root, backup)
                ledger.event("ADMISSION_RESOURCE_CHECK", sample=sample)
                admission(sample)
            slot = ledger.admit()
            if slot is None:
                print(
                    "DONE: all planned calibration attempts retained; main campaign unstarted",
                    flush=True,
                )
                ledger.backup(backup)
                return
            if not active:
                provision(root)
            command = [
                sys.executable,
                "-m",
                "research.execution_setup.worker",
                "--root",
                str(root),
                "--execution",
                slot["execution_id"],
            ]
            if checkpoint_once:
                command.append("--checkpoint-once")
            log = root / "executions" / slot["execution_id"] / f"terminal-{uuid4()}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("xb") as output:
                worker = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    stdout=output,
                    stderr=output,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            ledger.event(
                "STANDALONE_WORKER_STARTED",
                execution_id=slot["execution_id"],
                pid=worker.pid,
                log=str(log),
            )
            print(
                f"RUN {slot['sequence']} {slot['case_id']} {slot['arm']} {slot['execution_id']}",
                flush=True,
            )
            try:
                while worker.poll() is None:
                    try:
                        worker.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        current = next(
                            r for r in ledger.rows() if r["execution_id"] == slot["execution_id"]
                        )
                        print(
                            f"PROGRESS {current['state']} deadline={current['deadline']} log={log}",
                            flush=True,
                        )
            except KeyboardInterrupt:
                atomic(root / "pause.json", {"reason": "USER_SAFE_STOP", "at": now()})
                ledger.event(
                    "SAFE_PARENT_SHUTDOWN",
                    execution_id=slot["execution_id"],
                    worker_pid=worker.pid,
                    detail="Child keeps collecting; no new admissions",
                )
                print(
                    "Safe stop: active collector continues. "
                    "Keep Docker running and the computer awake.",
                    flush=True,
                )
                return
            if worker.returncode == 75:
                ledger.backup(backup)
                print(
                    "CHECKPOINTED: rerun 'run' to attach to the same execution and deadline",
                    flush=True,
                )
                return
            if worker.returncode:
                ledger.event(
                    "FAILURE_NOTICE", execution_id=slot["execution_id"], exit=worker.returncode
                )
                atomic(
                    root / "pause.json", {"reason": "WORKER_FAILURE", "at": now(), "log": str(log)}
                )
                ledger.backup(backup)
                raise RuntimeError(f"STOPPED: worker failed; preserve {log}")
            completed += 1
            ledger.backup(backup)
            if pause_after is not None and completed >= pause_after:
                atomic(root / "pause.json", {"reason": "PAUSE_BETWEEN_SLOTS", "at": now()})
                print("PAUSED between completed slots; saved order unchanged", flush=True)
                return


def diagnostic(root: Path, execution: str) -> None:
    ledger = Ledger(root)
    original = next(r for r in ledger.rows() if r["execution_id"] == execution)
    if original["state"] != "EXPORTED":
        raise ValueError("Collect/export original before adding a diagnostic rerun")
    with ledger.connect() as conn:
        sequence = conn.execute("SELECT max(sequence)+1 FROM slots").fetchone()[0]
        attempt = conn.execute(
            "SELECT max(attempt)+1 FROM slots WHERE case_id=? AND arm=?",
            (original["case_id"], original["arm"]),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label,original_id) "
            "VALUES (?,?,?,'PLANNED',?,'DIAGNOSTIC_RERUN',?)",
            (sequence, original["case_id"], original["arm"], attempt, execution),
        )
    ledger.event("DIAGNOSTIC_ADDED", original_id=execution, sequence=sequence, attempt=attempt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=["init", "run", "resume", "status", "verify", "backup", "pause", "diagnostic"],
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--checkpoint-once", action="store_true")
    parser.add_argument("--pause-after", type=int)
    parser.add_argument("--original")
    args = parser.parse_args()
    if args.action == "init":
        if args.backup is None:
            parser.error("init needs --backup")
        initialize(args.root, args.backup)
        return
    ledger = Ledger(args.root)
    try:
        if args.action in ("run", "resume"):
            if args.action == "resume" and (args.root / "pause.json").exists():
                pause = load(args.root / "pause.json")
                if pause["reason"] not in ("PAUSE_BETWEEN_SLOTS", "USER_SAFE_STOP"):
                    raise ValueError(
                        "Defect/resource failure needs review; automatic unpause forbidden"
                    )
                (args.root / "pause.json").unlink()
                ledger.event("USER_RESUMED_SAVED_ORDER")
            run(args.root, checkpoint_once=args.checkpoint_once, pause_after=args.pause_after)
        elif args.action == "pause":
            atomic(args.root / "pause.json", {"reason": "USER_SAFE_STOP", "at": now()})
            ledger.event("SAFE_STOP_REQUESTED")
        elif args.action == "diagnostic":
            if args.original is None:
                parser.error("diagnostic needs --original")
            diagnostic(args.root, args.original)
        elif args.action == "backup":
            print(ledger.backup(Path(load(args.root / "config.json")["backup"])))
        elif args.action == "verify":
            verify(args.root)
            print("PASS: historical/source/export hashes; all 1500 main slots NOT_STARTED")
        else:
            for row in ledger.rows():
                print(row)
            if (args.root / "pause.json").exists():
                print("NOTICE:", load(args.root / "pause.json"))
    except Exception as error:
        ledger.event("ADMISSION_STOP", detail=str(error))
        atomic(args.root / "pause.json", {"reason": str(error), "at": now()})
        print(f"FAILURE: {error}. New admissions stopped; all evidence retained.", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
