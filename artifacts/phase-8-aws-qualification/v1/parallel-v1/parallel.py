"""Finite paired isolation qualification; no main input or application mutation."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SOURCE = Path("/opt/fyp-phase8-linux-v1")
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, "/opt/fyp-phase82-qualification")
from qualify import verify_export  # noqa: E402

from research.execution_linux_v1 import platform  # noqa: E402
from research.execution_setup.core import Ledger, digest, immutable, load, now  # noqa: E402
from research.execution_setup.resources import admission  # noqa: E402

ROOT = Path("/srv/fyp-p82/parallel-v1")
BACKUP = Path("/srv/fyp-p82-backup/parallel-v1")
ADDON = Path(__file__).parent


def command(args: list[str], timeout: int = 60) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    immutable(
        ROOT / "commands" / f"{time.time_ns()}.json",
        {
            "at": now(),
            "args": args,
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    result.check_returncode()
    return result.stdout.strip()


def main() -> None:
    if ROOT.exists():
        raise ValueError("ORIGINAL_DIRECTORY_EXISTS: do not replace or restart qualification")
    serial = load(Path("/srv/fyp-p82/qualification-success.json"))
    if serial["status"] != "PASS_NATIVE_COLLECTOR" or serial["main_started"]:
        raise ValueError("SERIAL_QUALIFICATION_REQUIRED")
    if float(Path("/proc/uptime").read_text().split()[0]) > 12600:
        raise ValueError("HOST_DEADLINE_ADMISSION_STOP")
    ROOT.mkdir(parents=True)
    BACKUP.mkdir(parents=True)
    sample = platform.host(ROOT, BACKUP)
    admission(sample, concurrent=2)
    seal = load(ADDON / "seal.json")
    for name, expected in seal["files"].items():
        if digest(ADDON / name) != expected:
            raise ValueError("ADDON_HASH_DRIFT")
    immutable(ROOT / "admission.json", {"at": now(), "resources": sample, "seal": seal})
    command(["docker", "pull", "ubuntu:24.04"], 120)
    image = json.loads(command(["docker", "image", "inspect", "ubuntu:24.04"]))[0]
    immutable(ROOT / "image.json", image)
    # Pin this qualification to the recorded resolved image, never a mutable tag.
    image_digest = image["RepoDigests"][0]
    barriers = ROOT / "barriers"
    barriers.mkdir()
    owner = "p82-par-v1-" + str(os.getpid())
    networks: dict[str, str] = {}
    lane_names: dict[str, str] = {}
    for lane in ("A", "B"):
        work, backup = ROOT / lane, BACKUP / lane
        work.mkdir()
        backup.mkdir()
        network, name = owner + "-net-" + lane, owner + "-lane-" + lane
        networks[lane], lane_names[lane] = network, name
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
        command(
            [
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
                "PYTHONDONTWRITEBYTECODE=1",
                "-e",
                "PYTHONUNBUFFERED=1",
                "-e",
                f"P8_VALIDATION_NETWORK={network}",
                "-e",
                "P8_DOCKER_DATA_PATH=/docker-data",
                "-v",
                "/usr:/usr:ro",
                "-v",
                "/var/run/docker.sock:/var/run/docker.sock",
                "-v",
                "/var/lib/docker:/docker-data:ro",
                "-v",
                f"{SOURCE}:{SOURCE}:ro",
                "-v",
                f"{ADDON}:{ADDON}:ro",
                "-v",
                "/opt/fyp-phase82-qualification:/opt/fyp-phase82-qualification:ro",
                "-v",
                f"{work}:/work",
                "-v",
                f"{backup}:/backup",
                "-v",
                f"{barriers}:/barriers:ro",
                image_digest,
                str(SOURCE / ".venv/bin/python"),
                str(ADDON / "lane.py"),
                lane,
            ]
        )
    until = time.monotonic() + 100
    while not all((ROOT / lane / "ready.json").exists() for lane in ("A", "B")):
        for lane, name in lane_names.items():
            if (ROOT / lane / "lane-failure.json").exists():
                raise ValueError(f"LANE_{lane}_PREPARATION_FAILURE")
            state = json.loads(command(["docker", "inspect", name]))[0]["State"]
            if not state["Running"]:
                raise ValueError(f"LANE_{lane}_EXITED_BEFORE_RELEASE")
        if time.monotonic() > until:
            raise TimeoutError("BOTH_RESOURCES_READY_TIMEOUT")
        time.sleep(2)
    resources = {lane: load(ROOT / lane / "ready.json")["resources"] for lane in ("A", "B")}
    if set(resources["A"]["containers"]) & set(resources["B"]["containers"]):
        raise ValueError("SHARED_CONTAINERS_REJECTED")
    before = {}
    for lane in ("A", "B"):
        cache = resources[lane]["containers"][2]
        before[lane] = command(["docker", "exec", cache, "redis-cli", "SET", "peer-sentinel", lane])
        for name in resources[lane]["containers"]:
            info = json.loads(command(["docker", "inspect", name]))[0]
            if info["HostConfig"]["PortBindings"]:
                raise ValueError("HOST_PORT_PUBLICATION_REJECTED")
            if set(info["NetworkSettings"]["Networks"]) != {networks[lane]}:
                raise ValueError("CROSS_LANE_NETWORK_REJECTED")
    immutable(
        barriers / "release.json", {"at": now(), "name": "BOTH_RESOURCES_READY", "before": before}
    )
    deadline = time.monotonic() + 800
    samples = []
    while True:
        sample = platform.host(ROOT, BACKUP)
        samples.append(sample)
        immutable(ROOT / "samples" / f"{len(samples):04d}.json", sample)
        states = {
            lane: json.loads(command(["docker", "inspect", name]))[0]["State"]
            for lane, name in lane_names.items()
        }
        if all(not state["Running"] for state in states.values()):
            break
        if time.monotonic() > deadline:
            raise TimeoutError("PARALLEL_FULL_WINDOW_TIMEOUT: original retained")
        # Do not stop an active observation at resource pressure: stop further admission.
        if sample["available_memory_bytes"] < 1024**3:
            immutable(ROOT / "resource-stop-notice.json", {"at": now(), "sample": sample})
            raise ValueError("PARALLEL_RESOURCE_STOP: collectors remain for full windows")
        time.sleep(5)
    evidence, traces = {}, {}
    for lane, name in lane_names.items():
        logs = command(["docker", "logs", name])
        (ROOT / f"lane-{lane}.log").write_text(logs)
        if states[lane]["ExitCode"] != 0:
            raise ValueError(f"LANE_{lane}_FAILED: retain original")
        root = ROOT / lane / "run"
        slot = Ledger(root).rows()[0]
        # Paths inside the immutable trace refer to /work. Resolve evidence on host;
        # grading still uses the original collector/export bytes and original deadline.
        evidence[lane] = verify_export(root, slot)
        traces[lane] = load(root / "executions" / slot["execution_id"] / "export.json")
    caches = {
        lane: command(
            [
                "docker",
                "exec",
                resources[lane]["containers"][2],
                "redis-cli",
                "GET",
                "peer-sentinel",
            ]
        )
        for lane in ("A", "B")
    }
    if caches != {"A": "A", "B": ""} or not traces["B"].get("redis_fault"):
        raise ValueError("CACHE_FAULT_OR_PEER_SENTINEL_ISOLATION_FAILED")
    events = {lane: traces[lane]["processes"] for lane in ("A", "B")}
    worker_starts = {
        lane: [e for e in events[lane] if e["event"] == "PROCESS_STARTED" and e["name"] == "worker"]
        for lane in ("A", "B")
    }
    if len(worker_starts["A"]) != 2 or len(worker_starts["B"]) != 1:
        raise ValueError("OWNED_RESTART_OR_PEER_LIFECYCLE_FAILED")
    workflows = {lane: traces[lane]["fixture_identity"]["workflow_id"] for lane in ("A", "B")}
    if workflows["A"] == workflows["B"]:
        raise ValueError("WORKFLOW_BINDING_COLLISION")
    for lane in ("A", "B"):
        serialized = json.dumps(traces[lane]["snapshot"])
        if str(workflows["B" if lane == "A" else "A"]) in serialized:
            raise ValueError("CROSS_WORKFLOW_COLLECTION_CONTAMINATION")
    immutable(
        ROOT / "success.json",
        {
            "at": now(),
            "status": "PASS_TWO_OBSERVED_RECIPES_ONLY",
            "evidence": evidence,
            "cache_sentinels": caches,
            "worker_starts": worker_starts,
            "workflows": workflows,
            "samples": len(samples),
            "main_started": False,
            "scope": "CALIBRATION_ONLY",
            "limitations": "No qualification of remaining recipes; no latency equivalence claim",
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        immutable(ROOT / "failure.json", {"at": now(), "detail": str(error), "main_started": False})
        raise
