"""Host and dedicated database measurements, without extra dependencies."""

import ctypes
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import psycopg

from research.execution_setup.core import now

GIB = 1024**3


class Memory(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong)
        for name in (
            "total",
            "available",
            "total_page",
            "available_page",
            "total_virtual",
            "available_virtual",
            "extended",
        )
    ]


class FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

    def value(self) -> int:
        return int(self.low + (self.high << 32))


def host(root: Path, backup: Path) -> dict[str, Any]:
    if os.name != "nt":
        raise RuntimeError("This qualified resource probe currently targets Windows")
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("GlobalMemoryStatusEx failed")
    idle, kernel, user = FileTime(), FileTime(), FileTime()
    if not ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    ):
        raise OSError("GetSystemTimes failed")
    return {
        "at": now(),
        "total_memory_bytes": memory.total,
        "available_memory_bytes": memory.available,
        "used_memory_bytes": memory.total - memory.available,
        "cpu_idle_ticks": idle.value(),
        "cpu_total_ticks": kernel.value() + user.value(),
        "output_free_bytes": shutil.disk_usage(root).free,
        "backup_free_bytes": shutil.disk_usage(backup).free,
        "system_free_bytes": shutil.disk_usage("C:/").free,
    }


def cpu_fraction(before: dict[str, Any], after: dict[str, Any]) -> float | None:
    total = after["cpu_total_ticks"] - before["cpu_total_ticks"]
    return 1 - (after["cpu_idle_ticks"] - before["cpu_idle_ticks"]) / total if total > 0 else None


def admission(sample: dict[str, Any], *, concurrent: int = 1, campaign: bool = False) -> None:
    memory = (1.5 if concurrent == 1 else 4) * GIB
    if sample["available_memory_bytes"] < memory:
        raise RuntimeError("RESOURCE_STOP: insufficient available RAM for admission")
    if sample["system_free_bytes"] < (25 if campaign else 5) * GIB:
        raise RuntimeError("RESOURCE_STOP: Docker/system disk reserve is insufficient")
    if (
        min(sample["output_free_bytes"], sample["backup_free_bytes"])
        < (25 if campaign else 2) * GIB
    ):
        raise RuntimeError("RESOURCE_STOP: output/backup disk reserve is insufficient")


def database(dsn: str) -> dict[str, Any]:
    with psycopg.connect(dsn, connect_timeout=3) as conn:
        row = conn.execute(
            "SELECT pg_database_size(current_database()), "
            "COALESCE((SELECT sum(size) FROM pg_ls_waldir()),0), pg_current_wal_lsn()::text"
        ).fetchone()
        assert row is not None
        return {"database_bytes": row[0], "wal_directory_bytes": int(row[1]), "wal_lsn": row[2]}


def tree_bytes(path: Path, suffix: str | None = None) -> int:
    return sum(
        p.stat().st_size
        for p in path.rglob("*")
        if p.is_file() and (suffix is None or p.suffix == suffix)
    )


def docker_stats(names: list[str]) -> list[str]:
    result = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}", *names],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    return result.stdout.splitlines()
