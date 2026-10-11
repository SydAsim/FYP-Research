"""Linux resource, lock and PID identity boundaries. No application transitions."""

import importlib
import os
import shutil
import signal
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from research.execution_setup.core import now


def require_linux() -> None:
    if sys.platform != "linux":
        raise RuntimeError("LINUX_ONLY: use the historical Windows runner on Windows")


def memory_sample(
    proc: Path = Path("/proc"), cgroup: Path = Path("/sys/fs/cgroup")
) -> dict[str, int]:
    memory = {}
    for line in (proc / "meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        memory[key] = int(value.strip().split()[0]) * 1024
    total, available = memory["MemTotal"], memory["MemAvailable"]
    # A container must not admit work using the host's larger RAM allowance.
    limit, current = cgroup / "memory.max", cgroup / "memory.current"
    if limit.exists() and current.exists() and limit.read_text().strip() != "max":
        total = min(total, int(limit.read_text()))
        available = min(available, max(0, int(limit.read_text()) - int(current.read_text())))
    return {
        "total_memory_bytes": total,
        "available_memory_bytes": available,
        "used_memory_bytes": total - available,
    }


def host(root: Path, backup: Path) -> dict[str, Any]:
    require_linux()
    docker_data = Path(os.environ.get("P8_DOCKER_DATA_PATH", "/var/lib/docker"))
    if not docker_data.is_dir():
        raise ValueError("Docker data path must exist; set P8_DOCKER_DATA_PATH explicitly")
    ticks = [int(v) for v in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
    return {
        "at": now(),
        **memory_sample(),
        "cpu_idle_ticks": ticks[3] + ticks[4],
        # guest/guest_nice already occur inside user/nice; do not double count.
        "cpu_total_ticks": sum(ticks[:8]),
        "output_free_bytes": shutil.disk_usage(root).free,
        "backup_free_bytes": shutil.disk_usage(backup).free,
        "system_free_bytes": min(shutil.disk_usage("/").free, shutil.disk_usage(docker_data).free),
        "docker_data_path": str(docker_data),
        "cpu_scope": "PROC_HOST_AGGREGATE_NOT_CONTAINER_ATTRIBUTION",
        "memory_scope": "PROC_MEMAVAILABLE_CAPPED_BY_CGROUP_V2_WHEN_LIMITED",
        "output_device": root.stat().st_dev,
        "backup_device": backup.stat().st_dev,
    }


@contextmanager
def runner_lock(root: Path) -> Iterator[None]:
    require_linux()
    fcntl = importlib.import_module("fcntl")  # OS boundary, also type checked on Windows

    with (root / "runner.lock").open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("RUNNER_ALREADY_ACTIVE") from error
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def process_identity(pid: int, *, terminate: bool = False) -> int | None:
    """Linux start ticks; exclude zombies. Boot ID is checked separately on attach."""
    require_linux()
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return None if fields[0] == "Z" else int(fields[19])
    except (FileNotFoundError, ProcessLookupError):
        return None


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def stop_owned(pid: int, identity: int) -> None:
    """Pin a process with pidfd before signalling; never kill a reused numeric PID."""
    require_linux()
    if process_identity(pid) != identity:
        return
    try:
        descriptor = int(vars(os)["pidfd_open"](pid))
    except ProcessLookupError:
        return
    try:
        if process_identity(pid) != identity:
            return
        vars(signal)["pidfd_send_signal"](descriptor, signal.SIGTERM)
        deadline = time.monotonic() + 5
        while process_identity(pid) == identity and time.monotonic() < deadline:
            time.sleep(0.02)  # OS lifecycle polling, never scenario fault placement.
        if process_identity(pid) == identity:
            vars(signal)["pidfd_send_signal"](descriptor, vars(signal)["SIGKILL"])
            deadline = time.monotonic() + 3
            while process_identity(pid) == identity and time.monotonic() < deadline:
                time.sleep(0.02)
        if process_identity(pid) == identity:
            raise RuntimeError(f"OWNED_PROCESS_STOP_FAILED: {pid}")
    finally:
        os.close(descriptor)
