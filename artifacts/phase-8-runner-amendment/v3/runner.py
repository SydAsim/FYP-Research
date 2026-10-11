"""Standalone serial campaign controller. No AWS provision/freeze/sign commands."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))

from controls import (  # noqa: E402
    Authority,
    Journal,
    Policy,
    clock_check,
    guard,
    hash_file,
    read,
    utc,
    write_new,
)
from handover import (  # noqa: E402
    FIRST,
    ContinuationAuthority,
    record_provenance,
    verify_imported_first,
)
from storage import (  # noqa: E402
    Cloud,
    OfflineCloud,
    S3Cloud,
    complete_backup,
    final_backup,
    make_backup,
    reconcile_upload,
    upload,
    verify_local,
)


def authority_for(root: Path) -> Authority:
    config = read(root / "run.json")
    if config["policy"]["scope"] != "CALIBRATION":
        return ContinuationAuthority(root, config)
    return Authority(
        Path(config["source"]),
        Path(config["manifest"]),
        Policy.model_validate(config["policy"]),
        config["schedule_hash"],
        Path(config["receipts"]),
        Path(config["key"]),
    )


def verify_binding(slot_root: Path, slot: dict[str, Any]) -> None:
    root = slot_root.parent.parent
    authority = verify_run(root)
    from research.execution_setup.core import Ledger

    Ledger(slot_root).verify()
    config = read(slot_root / "config.json")
    bound = next(
        r for r in read(root / "bindings.json") if r["execution_id"] == slot["execution_id"]
    )
    case = read(slot_root / "qualification-plan.json")["cases"][slot["case_id"]]
    from research.study.models import StudyCase

    if (
        bound["case_id"] != slot["case_id"]
        or bound["arm"] != slot["arm"]
        or slot["attempt"] != 1
        or config["execution_id"] != slot["execution_id"]
        or StudyCase.model_validate(case).fixture_hash != bound["fixture_hash"]
        or config["classification"]
        != ("CAMPAIGN" if authority.policy.scope == "CAMPAIGN" else "CALIBRATION_NOT_MAIN_CAMPAIGN")
    ):
        raise ValueError("IMMUTABLE_SLOT_BINDING_DRIFT")
    if (authority.policy.scope == "CAMPAIGN") != slot["case_id"].startswith("p8v4-"):
        raise ValueError("CALIBRATION_MAIN_SEPARATION")


def initialize(
    root: Path,
    source: Path,
    manifest: Path,
    policy: Policy,
    receipts: Path,
    key: Path,
    schedule: Path,
    backup: Path,
) -> None:
    if policy.scope != "CALIBRATION":
        raise ValueError("PREFLIGHT_REVIEW_REQUIRED_MAIN_BLOCKED")
    authority = Authority(source, manifest, policy, hash_file(schedule), receipts, key)
    authority.verify()  # No ledger creation or resource operation before all approvals.
    if policy.host_started_at > utc():
        raise ValueError("FUTURE_HOST_CLOCK_NOT_ALLOWED")
    if root.exists() or root == backup or root in backup.parents or backup in root.parents:
        raise ValueError("FRESH_SEPARATE_EVIDENCE_ROOTS_REQUIRED")
    rows = read(schedule)["rows"]
    source_bank = read(HERE / "calibration-inputs.json")
    cases = {c["case_id"]: c for c in source_bank["calibration_inputs"]}
    if "admission_sentinel" in source_bank:
        sentinel = source_bank["admission_sentinel"]
        cases[sentinel["case_id"]] = sentinel
    from research.study.models import StudyCase

    if any(
        StudyCase.model_validate(cases[r["case_id"]]).fixture_hash != r["fixture_hash"]
        for r in rows
    ):
        raise ValueError("FIXTURE_BINDING_DRIFT")
    root.mkdir(parents=True)
    backup.mkdir(parents=True, exist_ok=True)
    write_new(
        root / "run.json",
        {
            "source": str(source),
            "manifest": str(manifest),
            "policy": policy.model_dump(mode="json"),
            "receipts": str(receipts),
            "key": str(key),
            "schedule_hash": hash_file(schedule),
            "backup": str(backup),
            "cases": {r["case_id"]: cases[r["case_id"]] for r in rows},
        },
    )
    journal = Journal(root)
    journal.initialize(rows, policy.scope)
    # Execution IDs are reserved only now, after accepted freeze + separate launch.
    bindings = [
        {
            k: row[k]
            for k in ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
        }
        for row in journal.rows()
    ]
    write_new(root / "bindings.json", bindings)
    write_new(
        root / "binding-seal.json",
        {"run": hash_file(root / "run.json"), "bindings": hash_file(root / "bindings.json")},
    )
    journal.event(
        "BINDINGS_SEALED",
        run=hash_file(root / "run.json"),
        bindings=hash_file(root / "bindings.json"),
    )
    if sys.platform == "linux":
        from research.execution_linux_v1.platform import boot_id

        write_new(
            root / "host-clock.json",
            {"boot_id": boot_id(), "monotonic": time.monotonic(), "wall": utc().isoformat()},
        )
        journal.event("HOST_CLOCK_SEALED", hash=hash_file(root / "host-clock.json"))


def verify_run(root: Path, *, readonly: bool = False) -> Authority:
    authority = authority_for(root)
    authority.verify(authority.policy.host_started_at if readonly else None)
    journal = Journal(root)
    journal.verify()
    seal = read(root / "binding-seal.json")
    with journal.connect() as db:
        seals = [
            read_event
            for event in db.execute("SELECT body FROM notices")
            if (read_event := json.loads(event[0])).get("kind") == "BINDINGS_SEALED"
        ]
    if (
        not seals
        or seals[-1]["run"] != seal["run"]
        or seals[-1]["bindings"] != seal["bindings"]
        or hash_file(root / "run.json") != seal["run"]
        or hash_file(root / "bindings.json") != seal["bindings"]
    ):
        raise ValueError("RUN_BINDING_SOURCE_DRIFT")
    bindings = read(root / "bindings.json")
    actual = [{k: row[k] for k in bindings[0]} for row in journal.rows()]
    if actual != bindings:
        raise ValueError("LEDGER_SLOT_BINDING_DRIFT")
    if sys.platform == "linux" and not readonly:
        verify_clock(root, authority.policy, utc())
    return authority


def verify_clock(root: Path, policy: Policy, at: datetime) -> None:
    from research.execution_linux_v1.platform import boot_id

    clock = root / "host-clock.json"
    with Journal(root).connect() as db:
        hashes = [
            json.loads(r[0])["hash"]
            for r in db.execute("SELECT body FROM notices")
            if json.loads(r[0]).get("kind") == "HOST_CLOCK_SEALED"
        ]
    if hash_file(clock) not in hashes:
        raise ValueError("HOST_CLOCK_SEAL_DRIFT")
    clock_check(policy, read(clock), at, time.monotonic(), boot_id())


def cloud_for(root: Path, *, readonly: bool = False) -> Cloud:
    authority = authority_for(root)
    authority.verify(authority.policy.host_started_at if readonly else None)
    config = read(root / "cloud.json")
    prefix = f"exports/phase8/{authority.policy.run_id}/"
    if authority.policy.scope == "CALIBRATION":
        return OfflineCloud(Path(config["offline_root"]), prefix)
    if (
        "offline_root" in config
        or set(config) != {"bucket", "prefix"}
        or config["prefix"] != prefix
        or config["bucket"] != authority.policy.cloud_bucket
    ):
        raise ValueError("MAIN_REQUIRES_DEDICATED_VERSIONED_CLOUD")
    return S3Cloud(config["bucket"], prefix)


def prepare_slot(root: Path, slot: dict[str, Any]) -> Path:
    from research.execution_linux_v1.runner import IMAGE_DIGESTS
    from research.execution_setup.core import Ledger, source_inventory

    authority = verify_run(root)
    folder = root / "slots" / f"{slot['sequence']:04d}"
    if folder.exists():
        raise ValueError("EXISTING_SLOT_NO_FRESH_DRIVER_REPLAY")
    folder.mkdir(parents=True)
    identity = "p84-" + slot["execution_id"]
    containers = [identity + "-" + kind for kind in ("app", "truth", "cache")]
    resources = {
        "resource_id": identity,
        "containers": containers,
        "database": "postgresql://setup_app:setup_local_only@127.0.0.1:16432/setup_app",
        "sim_database": "postgresql://setup_truth:setup_local_only@127.0.0.1:16433/setup_truth",
        "services": [19100, 19101, 19102, 19110],
        "validation_network": None,
        "image_digests": IMAGE_DIGESTS,
        "concurrency": 1,
    }
    # Local test container: no published host ports, all databases are fresh.
    network = os.environ.get("P85_CALIBRATION_NETWORK")
    if network:
        if authority.policy.scope != "CALIBRATION":
            raise ValueError("CALIBRATION_NETWORK_ONLY")
        resources["validation_network"] = network
        resources["database"] = (
            f"postgresql://setup_app:setup_local_only@{containers[0]}:5432/setup_app"
        )
        resources["sim_database"] = (
            f"postgresql://setup_truth:setup_local_only@{containers[1]}:5432/setup_truth"
        )
    case = read(root / "run.json")["cases"][slot["case_id"]]
    backup = Path(read(root / "run.json")["backup"]) / f"{slot['sequence']:04d}"
    backup.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(folder)
    for name, value in (
        ("resources.json", resources),
        ("source-seal.json", source_inventory()),
        ("qualification-plan.json", {"cases": {slot["case_id"]: case}}),
    ):
        write_new(folder / name, value)
        ledger.seal(folder / name)
    write_new(
        folder / "config.json",
        {
            "backup": str(backup),
            "execution_id": slot["execution_id"],
            "driver_admitted": False,
            "classification": "CAMPAIGN"
            if authority.policy.scope == "CAMPAIGN"
            else "CALIBRATION_NOT_MAIN_CAMPAIGN",
        },
    )
    with ledger.connect() as db:
        db.execute(
            "INSERT INTO slots(sequence,case_id,arm,attempt,execution_id,state,label) "
            "VALUES(?,?,?,?,?,'RUNNING','ORIGINAL_PLANNED')",
            (slot["sequence"], slot["case_id"], slot["arm"], 1, slot["execution_id"]),
        )
    ledger.event("SLOT_BOUND", **slot)
    return folder


def meter(root: Path) -> dict[str, Any]:
    from research.execution_linux_v1.platform import host
    from research.execution_setup.resources import tree_bytes

    backup = Path(read(root / "run.json")["backup"])
    result = host(root, backup)
    result.update(working_bytes=tree_bytes(root), backup_bytes=tree_bytes(backup))
    return result


def run_slot(root: Path, slot: dict[str, Any], *, checkpoint_once: bool = False) -> bool:
    from research.execution_linux_v1 import platform, runtime
    from research.execution_setup.core import Ledger

    journal = Journal(root)
    folder = root / "slots" / f"{slot['sequence']:04d}"
    fresh = not folder.exists()
    if fresh:
        folder = prepare_slot(root, slot)
        # Each slot has fresh owned databases; no global FLUSHDB or shared worker.
        runtime.provision(folder)
    ledger = Ledger(folder)
    export = folder / "executions" / slot["execution_id"] / "export.json"
    if export.exists():
        ledger.verify()
        return True  # crash after export/before master transition: never rerun driver
    owner_path = folder / "collector-owner.json"
    owner = read(owner_path) if owner_path.exists() else None
    if owner and owner["boot_id"] != platform.boot_id():
        raise ValueError("HOST_REBOOT_UNQUALIFIED")
    pid: int | None = int(owner["pid"]) if owner else None
    attached = bool(
        owner and pid is not None and platform.process_identity(pid) == owner["identity"]
    )
    child: subprocess.Popen[bytes] | None = None
    if not attached:
        # Once provision/collector launch was attempted, missing checkpoint is
        # uncertain. Never infer it is safe to replay a driver from missing files.
        if not fresh:
            ledger.recover_checkpoint(slot["execution_id"])
        args = [
            sys.executable,
            str(HERE / "collector.py"),
            "--root",
            str(folder),
            "--execution",
            slot["execution_id"],
        ]
        if checkpoint_once:
            args.append("--checkpoint-once")
        log = folder / f"collector-{time.time_ns()}.log"
        with log.open("xb") as output:
            child = subprocess.Popen(
                args, cwd=REPO, stdout=output, stderr=output, start_new_session=True
            )
        pid = child.pid
        owner = {
            "pid": pid,
            "identity": platform.process_identity(pid),
            "boot_id": platform.boot_id(),
            "log": str(log),
        }
        write_new(folder / f"collector-start-{time.time_ns()}.json", owner)
        from research.execution_setup.core import atomic

        atomic(owner_path, owner)
    assert owner is not None and pid is not None
    while platform.process_identity(pid) == owner["identity"]:
        Event().wait(5)
        if child:
            child.poll()
        local = ledger.rows()[0]
        if local["deadline"]:
            journal.update(slot["execution_id"], deadline=local["deadline"])
        print(
            f"COLLECT slot {slot['sequence']} {slot['arm']} deadline={local['deadline']}",
            flush=True,
        )
    if child:
        child.wait(timeout=5)
    local = ledger.rows()[0]
    if local["deadline"]:
        journal.update(slot["execution_id"], deadline=local["deadline"])
    if local["state"] == "CHECKPOINTED":
        return False
    if local["state"] != "EXPORTED":
        raise ValueError("COLLECTOR_FAILURE_RETAIN_ORIGINAL")
    if (folder / "pause.json").exists():
        journal.pause(read(folder / "pause.json")["reason"])
    return True


def retire(root: Path, slot: dict[str, Any]) -> None:
    from research.execution_linux_v1.runtime import inspect_owned

    proof_path = root / "backups" / f"{slot['execution_id']}.json"
    proof = read(proof_path)
    verify_local(Path(proof["local"]), proof["sha256"])
    from storage import ObjectProof

    cloud_for(root).verify(ObjectProof.model_validate(proof["cloud"]))
    folder = root / "slots" / f"{slot['sequence']:04d}"
    config = read(folder / "resources.json")
    # Retire only exact isolated resources after full logical dumps and independent
    # cloud/local copies. Retaining 1500 WAL-preallocated volumes would exceed disk.
    intent_path = folder / "retirement-intent.json"
    if not intent_path.exists():
        volumes = []
        for name in config["containers"][:2]:
            info = inspect_owned(name, config["resource_id"])
            if info is None:
                raise ValueError("MISSING_DB_BEFORE_RETIREMENT_INTENT")
            mounts = [m for m in info["Mounts"] if m["Destination"] == "/var/lib/postgresql/data"]
            if len(mounts) != 1 or mounts[0]["Name"] != name + "-data":
                raise ValueError("OWNED_VOLUME_BINDING_REQUIRED")
            volumes.append(mounts[0]["Name"])
        write_new(
            intent_path,
            {
                "execution_id": slot["execution_id"],
                "volumes": volumes,
                "containers": config["containers"],
                "backup_hash": hash_file(proof_path),
            },
        )
        Journal(root).event("RETIREMENT_INTENT", hash=hash_file(intent_path))
    intent = read(intent_path)
    with Journal(root).connect() as db:
        recorded = [
            json.loads(r[0])["hash"]
            for r in db.execute("SELECT body FROM notices")
            if json.loads(r[0]).get("kind") == "RETIREMENT_INTENT"
        ]
    if (
        intent["backup_hash"] != hash_file(proof_path)
        or intent["containers"] != config["containers"]
        or intent["execution_id"] != slot["execution_id"]
        or intent["volumes"] != [name + "-data" for name in config["containers"][:2]]
        or hash_file(intent_path) not in recorded
    ):
        raise ValueError("RETIREMENT_BINDING_DRIFT")
    import tarfile

    with tarfile.open(proof["local"], "r:gz") as archive:
        manifest_handle = archive.extractfile("slot/manifest.json")
        assert manifest_handle is not None
        manifest = json.load(manifest_handle)
        if not manifest["postgres_dumps"] or any(
            name not in manifest["files"] for name in ("setup_app.sql.gz", "setup_truth.sql.gz")
        ):
            raise ValueError("BOTH_DATABASE_DUMPS_REQUIRED_BEFORE_RETIREMENT")
    for name in config["containers"]:
        if inspect_owned(name, config["resource_id"]):
            result = subprocess.run(["docker", "stop", name], capture_output=True, timeout=30)
            write_new(
                folder / f"retire-{name}-{time.time_ns()}.json",
                {"exit": result.returncode, "stderr": result.stderr.decode(errors="replace")},
            )
            result.check_returncode()
            subprocess.run(["docker", "rm", name], check=True, capture_output=True, timeout=30)
    for volume in intent["volumes"]:
        users = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"volume={volume}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        if users.stdout.strip():
            raise ValueError("VOLUME_STILL_IN_USE_RETAIN")
        inspected = subprocess.run(
            ["docker", "volume", "inspect", volume], capture_output=True, text=True, timeout=10
        )
        if inspected.returncode == 0:
            subprocess.run(
                ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=20
            )
        elif f"no such volume: {volume}" not in inspected.stderr.casefold():
            raise ValueError("VOLUME_RETIREMENT_UNKNOWN_RECONCILE")
    write_new(
        folder / "retired.json",
        {
            "execution_id": slot["execution_id"],
            "backup_hash": hash_file(proof_path),
            "volumes_retained": False,
            "raw_evidence_local_and_cloud_retained": True,
        },
    )


def quiesce(folder: Path, execution_id: str) -> None:
    """Crash-after-export recovery: stop surviving owned services before PG dumps."""
    from research.execution_linux_v1.platform import boot_id, stop_owned

    execution = folder / "executions" / execution_id
    if read(execution / "linux-boot.json")["boot_id"] != boot_id():
        raise ValueError("HOST_REBOOT_UNQUALIFIED")
    records = read(execution / "services.json")["records"]
    for record in records.values():
        stop_owned(record["pid"], record["identity"])
    Journal(folder.parent.parent).event(
        "SERVICES_QUIESCED_BEFORE_BACKUP", execution_id=execution_id
    )


def run(root: Path, *, pause_after: int | None = None, checkpoint_once: bool = False) -> None:
    from research.execution_linux_v1.platform import runner_lock

    authority = verify_run(root)
    if checkpoint_once and authority.policy.scope == "CAMPAIGN":
        raise ValueError("QUALIFICATION_CHECKPOINT_CALIBRATION_ONLY")
    journal = Journal(root)
    cloud = cloud_for(root)
    with runner_lock(root):
        completed = 0
        while True:
            authority = verify_run(root)
            # Recover crash after backup commit but before releasing the prior ports.
            for closed in journal.rows():
                if (
                    closed["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")
                    and (root / "handover.json").exists()
                ):
                    # Closed evidence imported; old host resources were not restored here.
                    # This does not assert that old volumes were deleted or retired.
                    verify_imported_first(root)
                    continue
                if (
                    closed["state"] == "BACKED_UP"
                    and not (root / "slots" / f"{closed['sequence']:04d}" / "retired.json").exists()
                ):
                    retire(root, closed)
            slot = journal.admit(authority, meter(root), utc(), cloud.inventory())
            if slot is None:
                pending = root / "pending-final-backup.json"
                if not pending.exists():
                    archive = final_backup(journal, Path(read(root / "run.json")["backup"]))
                    write_new(pending, {"archive": str(archive), "sha256": hash_file(archive)})
                archive = Path(read(pending)["archive"])
                verify_local(archive, read(pending)["sha256"])
                proof = upload(journal, cloud, authority.policy, archive)
                if not (root / "completion.json").exists():
                    write_new(
                        root / "completion.json",
                        {
                            "originals": len(journal.rows()),
                            "all_backed_up": True,
                            "cloud": proof.model_dump(),
                            "at": utc().isoformat(),
                        },
                    )
                    journal.event("QUEUE_COMPLETE_FINAL_BACKUP_VERIFIED", proof=proof.model_dump())
                print("DONE: exact saved original queue; originals never replaced", flush=True)
                if authority.policy.scope == "CAMPAIGN":
                    subprocess.run(["/sbin/shutdown", "-h", "now"], check=True, timeout=15)
                return
            if slot["state"] == "RUNNING":
                if not run_slot(root, slot, checkpoint_once=checkpoint_once):
                    print("CHECKPOINTED same execution; original deadline retained", flush=True)
                    return
                if authority.policy.scope == "CAMPAIGN":
                    record_provenance(
                        root, root / "slots" / f"{slot['sequence']:04d}", slot["execution_id"]
                    )
                journal.update(slot["execution_id"], state="EXPORTED")
            folder = root / "slots" / f"{slot['sequence']:04d}"
            quiesce(folder, slot["execution_id"])
            backup_folder = Path(read(root / "run.json")["backup"]) / f"{slot['sequence']:04d}"
            pending = folder / "pending-backup.json"
            if pending.exists():
                archive = Path(read(pending)["archive"])
                verify_local(archive, read(pending)["sha256"])
            else:
                archive = make_backup(folder, backup_folder)
                write_new(pending, {"archive": str(archive), "sha256": hash_file(archive)})
            complete_backup(journal, cloud, authority.policy, slot, archive)
            retire(root, slot)
            completed += 1
            print(f"VERIFIED BACKUP {slot['sequence']} / {len(journal.rows())}", flush=True)
            if pause_after and completed >= pause_after:
                journal.pause("BETWEEN_SLOTS")
                return


def watchdog_tick(
    root: Path, at: datetime, sample: dict[str, Any], cloud_bytes: int, *, stop_host: bool = False
) -> bool:
    journal = Journal(root)
    policy = authority_for(root).policy
    hard = at >= policy.stop_at
    if sys.platform == "linux":
        try:
            verify_clock(root, policy, at)
        except ValueError as error:
            hard = hard or str(error) == "HOST_360H_LIMIT"
            journal.pause(str(error))
    if hard:
        journal.pause("HOST_360H_LIMIT")
        journal.event("HARD_HOST_STOP_REQUIRED", at=at.isoformat(), retained=True)
        if stop_host:
            if policy.scope != "CAMPAIGN":
                raise ValueError("CALIBRATION_NEVER_STOPS_HOST")
            subprocess.run(["/sbin/shutdown", "-h", "now"], check=True, timeout=15)
        return False
    try:
        verify_run(root)
        guard(policy, sample, at, cloud_bytes)
    except Exception as error:
        journal.pause(type(error).__name__ + ":" + str(error))
        journal.event("WATCHDOG_STOP_ADMISSIONS", detail=str(error))
    return True  # Active collector continues through its original window.


def unit_text(root: Path, policy: Policy) -> tuple[str, str]:
    deadline = policy.stop_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    service = (
        "[Unit]\nDescription=FYP absolute compute stop; retain evidence disk\n"
        "[Service]\nType=oneshot\nExecStart=/sbin/shutdown -h now\n"
    )
    timer = (
        "[Unit]\nDescription=FYP 360-hour absolute host limit\n[Timer]\n"
        f"OnCalendar={deadline}\nOnBootSec=360h\nPersistent=true\nAccuracySec=1s\n"
        "Unit=fyp-phase8-hardstop.service\n[Install]\nWantedBy=timers.target\n"
    )
    return service, timer


def install_watchdog(root: Path) -> None:
    authority = verify_run(root)
    if authority.policy.scope != "CAMPAIGN":
        raise ValueError("HOST_TIMER_MAIN_AUTHORIZATION_REQUIRED")
    service, timer = unit_text(root, authority.policy)
    for name, content in (
        ("fyp-phase8-hardstop.service", service),
        ("fyp-phase8-hardstop.timer", timer),
        ("fyp-phase8-watchdog.service", watchdog_unit(root)),
        ("fyp-phase8-campaign.service", campaign_unit(root)),
    ):
        path = Path("/etc/systemd/system") / name
        with path.open("x") as output:
            output.write(content)
    subprocess.run(["systemctl", "daemon-reload"], check=True, timeout=20)
    subprocess.run(
        ["systemctl", "enable", "--now", "fyp-phase8-hardstop.timer"], check=True, timeout=20
    )
    subprocess.run(
        ["systemctl", "enable", "--now", "fyp-phase8-watchdog.service"], check=True, timeout=20
    )
    journal = Journal(root)
    journal.event("ABSOLUTE_HOST_TIMER_INSTALLED", deadline=authority.policy.stop_at.isoformat())


def watchdog_unit(root: Path) -> str:
    import re

    if any(
        not re.fullmatch(r"/[A-Za-z0-9_/.-]+", str(path))
        for path in (root, Path(sys.executable), HERE)
    ):
        raise ValueError("SAFE_LINUX_SERVICE_ROOT_REQUIRED")
    return (
        "[Unit]\nDescription=FYP admission watchdog\nAfter=network-online.target\n"
        "[Service]\nType=simple\nRestart=on-failure\nRestartSec=5s\n"
        + pythonpath_environment()
        + f"ExecStart={sys.executable} {HERE / 'runner.py'} watchdog --root {root}\n"
        "[Install]\nWantedBy=multi-user.target\n"
    )


def campaign_unit(root: Path) -> str:
    # Validate all unit paths via the same boundary.
    watchdog_unit(root)
    return (
        "[Unit]\nDescription=FYP exact serial original queue\nAfter=docker.service\n"
        "Requires=fyp-phase8-hardstop.timer fyp-phase8-watchdog.service\n"
        "[Service]\nType=simple\nRestart=no\nKillMode=process\nKillSignal=SIGINT\nTimeoutStopSec=30s\n"
        f"WorkingDirectory={REPO}\n"
        + pythonpath_environment()
        + f"ExecStart={sys.executable} {HERE / 'runner.py'} run --root {root}\n"
    )


def pythonpath_environment() -> str:
    analysis = REPO / ".venv-analysis/lib/python3.12/site-packages"
    transport = REPO / ".venv-transport/lib/python3.12/site-packages"
    return f"Environment=PYTHONPATH={REPO}:{analysis}:{transport}\n"


def verify_host_timer(root: Path) -> None:
    policy = verify_run(root).policy
    service, timer = unit_text(root, policy)
    for name, expected in (
        ("fyp-phase8-hardstop.service", service),
        ("fyp-phase8-hardstop.timer", timer),
        ("fyp-phase8-watchdog.service", watchdog_unit(root)),
    ):
        if (Path("/etc/systemd/system") / name).read_text() != expected:
            raise ValueError("INDEPENDENT_HOST_CONTROL_DRIFT")
    for name in ("fyp-phase8-hardstop.timer", "fyp-phase8-watchdog.service"):
        result = subprocess.run(
            ["systemctl", "is-active", name], capture_output=True, text=True, timeout=10
        )
        if result.returncode or result.stdout.strip() != "active":
            raise ValueError("INDEPENDENT_HOST_CONTROLS_REQUIRED")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=[
            "init",
            "run",
            "resume",
            "pause",
            "clear-pause",
            "status",
            "verify",
            "worker",
            "watchdog",
            "install-watchdog",
            "reconcile-backup",
        ],
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=HERE / "review-inventory.json")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--receipts", type=Path)
    parser.add_argument("--key", type=Path)
    parser.add_argument("--schedule", type=Path, default=HERE / "schedule.json")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--pause-after", type=int)
    parser.add_argument("--checkpoint-once", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    # Refuse an existing campaign root before the error handler can write a notice.
    if (root / "run.json").exists():
        authority_for(root)
    try:
        if args.action == "init":
            if not all((args.policy, args.receipts, args.key, args.backup)):
                parser.error("init requires policy, receipts, owner key and backup")
            initialize(
                root,
                args.source.resolve(),
                args.manifest.resolve(),
                Policy.model_validate(read(args.policy)),
                args.receipts.resolve(),
                args.key.resolve(),
                args.schedule.resolve(),
                args.backup.resolve(),
            )
        elif args.action == "status":
            print(Journal(root).rows())
        elif args.action == "pause":
            Journal(root).pause("BETWEEN_SLOTS")
        elif args.action == "clear-pause":
            verify_run(root)
            Journal(root).resume()
            print("Ordinary pause cleared; saved queue retained; no execution admitted")
        elif args.action == "verify":
            verify_run(root)
            print("PASS: exact bindings, source and accepted freeze plus launch chain")
        elif args.action == "install-watchdog":
            install_watchdog(root)
        elif args.action == "reconcile-backup":
            verify_run(root, readonly=True)
            for row in Journal(root).rows():
                pending = root / "slots" / f"{row['sequence']:04d}" / "pending-backup.json"
                if row["state"] == "EXPORTED" and pending.exists():
                    archive = Path(read(pending)["archive"])
                    verify_local(archive, read(pending)["sha256"])
                    reconcile_upload(Journal(root), cloud_for(root, readonly=True), archive)
                    print("Read-only backup reconciliation succeeded; failure pause retained")
            final = root / "pending-final-backup.json"
            if final.exists():
                archive = Path(read(final)["archive"])
                verify_local(archive, read(final)["sha256"])
                reconcile_upload(Journal(root), cloud_for(root, readonly=True), archive)
                print("Read-only final backup reconciliation succeeded; failure pause retained")
        elif args.action == "watchdog":
            cloud = cloud_for(root)
            while watchdog_tick(root, utc(), meter(root), cloud.inventory(), stop_host=True):
                Event().wait(5)
        elif args.action in ("run", "resume"):
            if args.action == "resume" and (root / "pause.json").exists():
                verify_run(root)
                Journal(root).resume()
            if authority_for(root).policy.scope == "CAMPAIGN":
                # Main cannot start without a confirmed independent host timer.
                verify_host_timer(root)
            run(root, pause_after=args.pause_after, checkpoint_once=args.checkpoint_once)
        else:
            parser.error("Use collector.py for the signed slot worker boundary")
    except KeyboardInterrupt:
        Journal(root).pause("BETWEEN_SLOTS")
        print("Parent stopped; detached collector continues. Keep host running.", flush=True)
    except Exception as error:
        if root.exists():
            Journal(root).event("PROTOCOL_STOP", type=type(error).__name__, detail=str(error))
            Journal(root).pause("PROTOCOL_STOP")
        print(f"STOP: {error}; retain all originals, no new admission", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
