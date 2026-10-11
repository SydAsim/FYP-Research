"""Finite serial-first research schedule. No Codex callback or main admission."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SOURCE = Path("/opt/fyp-phase8-linux-v1")
V2 = Path("/opt/fyp-phase82-qualification-v2")
V31 = Path("/opt/fyp-phase82-qualification-v3.1")
ADDON = Path(__file__).parent
sys.path[:0] = [str(SOURCE), str(V2), str(ADDON)]
from checks import validate_isolation  # noqa: E402
from plan import Slot, eligible, validate_plan  # noqa: E402
from qualify import verify_export  # noqa: E402

from research.execution_linux_v1 import platform, runtime  # noqa: E402
from research.execution_setup.core import (  # noqa: E402
    Ledger,
    check_inventory,
    immutable,
    load,
    now,
)
from research.execution_setup.resources import cpu_fraction  # noqa: E402

ROOT = Path("/srv/fyp-p83-v1")
BACKUP = Path("/srv/fyp-p83-backup-v1")


def command(arguments: list[str], timeout: int = 60) -> str:
    path = ROOT / "commands" / f"{time.time_ns()}.json"
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        immutable(path, {"at": now(), "arguments": arguments, "status": "UNKNOWN_TIMEOUT"})
        raise
    immutable(
        path,
        {
            "at": now(),
            "arguments": arguments,
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    result.check_returncode()
    return result.stdout.strip()


def remaining() -> float:
    return (
        datetime.fromisoformat(os.environ["P83_HOST_STOP_AT"]) - datetime.fromisoformat(now())
    ).total_seconds()


def inspect_container(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(command(["docker", "inspect", name]))[0]
    return value  # Docker JSON boundary


def verify_seals() -> None:
    for directory in (V2, V31, ADDON):
        check_inventory(load(directory / "seal.json")["files"], directory)


def execute_block(slots: list[Slot], block_name: str, references: dict[str, str]) -> dict[str, Any]:
    if len(slots) not in (1, 2) or remaining() < 1200:
        raise ValueError("FINITE_BLOCK_OR_ABSOLUTE_DEADLINE_GUARD")
    verify_seals()
    folder = ROOT / "blocks" / block_name
    folder.mkdir(parents=True, exist_ok=False)
    barriers = folder / "barriers"
    barriers.mkdir()
    owner = f"p83-{block_name}"
    lanes: dict[str, dict[str, Any]] = {}
    for index, slot in enumerate(slots):
        lane = chr(65 + index)
        work, backup = folder / lane, BACKUP / block_name / lane
        work.mkdir()
        backup.mkdir(parents=True)
        network, name = owner + "-net-" + lane, owner + "-lane-" + lane
        command(
            [
                "docker",
                "network",
                "create",
                "--label",
                "research.linux.validation=v1",
                "--label",
                f"research.owner={owner}",
                network,
            ]
        )
        arguments = [
            "docker",
            "run",
            "-d",
            "--pull=never",
            "--name",
            name,
            "--label",
            f"research.owner={owner}",
            "--network",
            network,
            "--user",
            f"{vars(os)['getuid']()}:{vars(os)['getgid']()}",
            "--group-add",
            str(Path("/var/run/docker.sock").stat().st_gid),
            "--memory",
            "2g",
            "--cpus",
            "1",
            "--log-opt",
            "max-size=10m",
            "--log-opt",
            "max-file=2",
            "--workdir",
            str(SOURCE),
            "-e",
            "HOME=/work",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            f"P83_SLOT_ID={slot.slot_id}",
            "-e",
            f"P8_VALIDATION_NETWORK={network}",
            "-e",
            "P8_DOCKER_DATA_PATH=/work",
            "-v",
            "/usr:/usr:ro",
            "-v",
            "/var/run/docker.sock:/var/run/docker.sock",
            "-v",
            f"{SOURCE}:{SOURCE}:ro",
            "-v",
            f"{V2}:{V2}:ro",
            "-v",
            f"{V31}:{V31}:ro",
            "-v",
            f"{ADDON}:{ADDON}:ro",
            "-v",
            f"{work}:/work",
            "-v",
            f"{backup}:/backup",
            "-v",
            f"{barriers}:/barriers:ro",
        ]
        if slot.reference_slot:
            arguments += ["-e", f"P83_REFERENCE_EXECUTION={references[slot.reference_slot]}"]
        arguments += [
            os.environ["P83_LANE_IMAGE"],
            str(SOURCE / ".venv/bin/python"),
            str(ADDON / "lane.py"),
        ]
        command(arguments)
        lanes[lane] = {"name": name, "network": network, "work": work, "slot": slot}
    until = time.monotonic() + 160
    while not all((v["work"] / "ready.json").is_file() for v in lanes.values()):
        for value in lanes.values():
            if (value["work"] / "lane-failure.json").exists():
                raise ValueError("LANE_PREPARATION_FAILURE_RETAIN_ORIGINAL")
            if not inspect_container(value["name"])["State"]["Running"]:
                raise ValueError("LANE_EXITED_BEFORE_NAMED_RELEASE")
        if time.monotonic() >= until:
            raise TimeoutError("RESOURCES_READY_TIMEOUT")
        time.sleep(2)
    resources = {k: load(v["work"] / "ready.json")["resources"] for k, v in lanes.items()}
    all_names = [n for r in resources.values() for n in r["containers"]]
    if len(set(all_names)) != len(all_names):
        raise ValueError("RESOURCE_COLLISION")
    for lane, value in lanes.items():
        for name in resources[lane]["containers"]:
            info = inspect_container(name)
            if info["HostConfig"]["PortBindings"] or set(info["NetworkSettings"]["Networks"]) != {
                value["network"]
            }:
                raise ValueError("HOST_PORT_OR_CROSS_NETWORK_BINDING")
        command(
            [
                "docker",
                "exec",
                resources[lane]["containers"][2],
                "redis-cli",
                "SET",
                "peer-sentinel",
                lane,
            ]
        )
    immutable(
        barriers / "release.json",
        {
            "at": now(),
            "name": "BOTH_RESOURCES_READY" if len(slots) == 2 else "SINGLE_RESOURCE_READY",
            "slots": [s.slot_id for s in slots],
        },
    )
    samples: list[dict[str, Any]] = []
    deadline = time.monotonic() + 900
    pressure_recorded = False
    while True:
        sample = platform.host(ROOT, BACKUP)
        samples.append(sample)
        immutable(folder / "samples" / f"{len(samples):04d}.json", sample)
        states = {k: inspect_container(v["name"])["State"] for k, v in lanes.items()}
        if all(not state["Running"] for state in states.values()):
            break
        health = {}
        for lane, value in lanes.items():
            if not states[lane]["Running"]:
                continue
            # No credentials/Oracle token are returned by the lane probe.
            args = [
                "docker",
                "exec",
                value["name"],
                str(SOURCE / ".venv/bin/python"),
                str(ADDON / "monitor.py"),
            ]
            try:
                health[lane] = json.loads(command(args))
            except subprocess.CalledProcessError:
                # A completed container can exit between inspect and exec. Retain
                # the failed probe; accept only an actual EXPORTED ledger record.
                final = Ledger(value["work"] / "run").rows()[0]
                if final["state"] != "EXPORTED":
                    raise
                health[lane] = {"probe_exit_race": "EXPORTED", "required": False}
        immutable(folder / "worker-health" / f"{len(samples):04d}.json", health)
        lost = any(h.get("required") and not h.get("worker_alive") for h in health.values())
        if lost and not (ROOT / "admission-stop-worker-loss.json").exists():
            immutable(ROOT / "admission-stop-worker-loss.json", {"at": now(), "health": health})
            # Preserve already admitted observations; stop further admissions.
        if sample["available_memory_bytes"] < 1024**3 and not pressure_recorded:
            immutable(ROOT / "admission-stop-resource.json", {"at": now(), "sample": sample})
            pressure_recorded = True  # keep collecting the already admitted full windows
        if time.monotonic() > deadline:
            raise TimeoutError("FULL_WINDOW_INFRASTRUCTURE_TIMEOUT_RETAIN_EVIDENCE")
        time.sleep(5)
    evidence: dict[str, Any] = {}
    traces: dict[str, Any] = {}
    workers: dict[str, list[dict[str, Any]]] = {}
    workflows: dict[str, str] = {}
    caches = {}
    for lane, value in lanes.items():
        (folder / f"lane-{lane}.log").write_text(
            command(["docker", "logs", value["name"]]), encoding="utf-8"
        )
        if states[lane]["ExitCode"] != 0:
            raise ValueError("LANE_FAILED_RETAIN_FULL_ATTEMPT")
        root = value["work"] / "run"
        ledger_slot = Ledger(root).rows()[0]
        evidence[lane] = verify_export(root, ledger_slot)
        traces[lane] = load(root / "executions" / ledger_slot["execution_id"] / "export.json")
        workflows[lane] = traces[lane]["fixture_identity"]["workflow_id"]
        workers[lane] = [
            e
            for e in traces[lane]["processes"]
            if e["event"] == "PROCESS_STARTED" and e["name"] == "worker"
        ]
        caches[lane] = command(
            [
                "docker",
                "exec",
                resources[lane]["containers"][2],
                "redis-cli",
                "GET",
                "peer-sentinel",
            ]
        )
    validate_isolation(
        traces, {k: v["slot"].case.generator_family for k, v in lanes.items()}, caches
    )
    used = [int(s["used_memory_bytes"]) for s in samples]
    available = [int(s["available_memory_bytes"]) for s in samples]
    cpu = [cpu_fraction(a, b) for a, b in zip(samples, samples[1:], strict=False)]
    result = {
        "at": now(),
        "classification": "CALIBRATION_ONLY",
        "main_started": False,
        "slots": [s.slot_id for s in slots],
        "evidence": evidence,
        "workers": workers,
        "workflows": workflows,
        "cache_sentinels": caches,
        "peak_used_memory_bytes": max(used),
        "minimum_available_memory_bytes": min(available),
        "maximum_cpu_fraction": max((c for c in cpu if c is not None), default=None),
        "source_integrity": "COMBINED_V3_1_PLUS_P83",
        "pressure_recorded": pressure_recorded,
    }
    immutable(folder / "result.json", result)
    # All admitted windows/exports completed before stopping only owned resources.
    for lane in lanes:
        for name in resources[lane]["containers"]:
            runtime.inspect_owned(name, resources[lane]["resource_id"])
            command(["docker", "stop", name])
    return result


def main() -> None:
    if ROOT.exists() or BACKUP.exists():
        raise ValueError("FINITE_PILOT_DIRECTORY_EXISTS_NO_REPLAY")
    ROOT.mkdir()
    BACKUP.mkdir()
    slots = validate_plan(ADDON / "slots.json")
    immutable(ROOT / "planned-slots.json", [s.model_dump(mode="json") for s in slots])
    references: dict[str, str] = {}
    first: dict[str, Any] | None = None
    results = []
    for slot in slots[:18]:
        if list(ROOT.glob("admission-stop-*.json")):
            raise ValueError("RESOURCE_STOP_NEW_ADMISSIONS")
        print(f"SERIAL {slot.slot_id}; main campaign blocked", flush=True)
        result = execute_block([slot], slot.slot_id, references)
        results.append(result)
        references[slot.slot_id] = result["evidence"]["A"]["execution_id"]
        if first is None:
            first = result
            immutable(ROOT / "first-execution-measurement.json", result)
    assert first is not None
    for block in (19, 20, 21):
        pair = [s for s in slots if s.block == block]
        sample = platform.host(ROOT, BACKUP)
        parallel = eligible(first, sample, remaining())
        immutable(
            ROOT / f"schedule-block-{block}.json",
            {
                "at": now(),
                "decision": "BOUNDED_PARALLEL" if parallel else "SERIAL_FALLBACK",
                "sample": sample,
                "remaining_seconds": remaining(),
            },
        )
        if list(ROOT.glob("admission-stop-*.json")):
            raise ValueError("RESOURCE_STOP_NEW_ADMISSIONS")
        if parallel:
            results.append(execute_block(pair, f"pair-{block}", references))
        else:
            for slot in pair:
                results.append(execute_block([slot], slot.slot_id, references))
    immutable(
        ROOT / "pilot-complete.json",
        {
            "at": now(),
            "planned_executions": 24,
            "main_started": False,
            "results": results,
            "scope": "OBSERVED_RECIPES_ONLY_NO_WINNER_INFERENCE",
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        ROOT.mkdir(parents=True, exist_ok=True)
        immutable(
            ROOT / f"pilot-stop-{time.time_ns()}.json",
            {
                "at": now(),
                "detail": str(error),
                "new_admissions_stopped": True,
                "main_started": False,
            },
        )
        raise
