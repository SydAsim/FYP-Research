"""Dedicated local PostgreSQL resources and independently owned service processes."""

import ctypes
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from threading import Event
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import psycopg

from research.execution_setup.core import ROOT, atomic, load, now
from research.execution_setup.resources import FileTime
from research.study_v4.runtime import Runtime as V4Runtime

MODULES = {
    "simulator": ("research.provider_simulator.main:app", 19110),
    "api": ("apps.api_controller.main:app", 19100),
    "voice": ("apps.voice_worker.main:app", 19101),
    "worker": ("apps.durable_worker.main:app", 19102),
}


def process_identity(pid: int, *, terminate: bool = False) -> int | None:
    """Creation timestamp protects resumed cleanup from PID reuse."""
    api = ctypes.windll.kernel32
    api.OpenProcess.restype = ctypes.c_void_p
    api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    api.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 4
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = api.OpenProcess(0x1000 | (1 if terminate else 0), 0, pid)
    if not handle:
        return None
    try:
        created, exited, kernel, user = (FileTime() for _ in range(4))
        if not api.GetProcessTimes(
            handle,
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            raise OSError("Process identity could not be checked")
        return created.value()
    finally:
        api.CloseHandle(handle)


def stop_owned(pid: int, identity: int) -> None:
    if process_identity(pid) != identity:
        return
    result = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=10)
    if result.returncode and process_identity(pid) == identity:
        raise RuntimeError(f"Could not stop owned service PID {pid}")


class Runtime(V4Runtime):
    def __init__(self, root: Path, execution: Path, *, attach: bool = False) -> None:
        self.root, self.directory = root, execution
        self.logs = execution / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.config = load(root / "resources.json")
        self.database = self.config["database"]
        self.sim_database = self.config["sim_database"]
        self.state_path = execution / "services.json"
        self.events: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        if attach:
            saved = load(self.state_path)
            self.token, self.events, self.records = (
                saved["token"],
                saved["events"],
                saved["records"],
            )
        else:
            self.token = secrets.token_hex(24)
        self.env = {
            **os.environ,
            "DATABASE_SYNC_URL": self.database,
            "DATABASE_URL": self.database.replace("postgresql://", "postgresql+asyncpg://"),
            "SIMULATOR_BASE_URL": "http://127.0.0.1:19110",
            "API_BASE_URL": "http://127.0.0.1:19100",
            "EXPERIMENT_MODE": "true",
            "REPAIR_DELIVERY_ENABLED": "false",
        }
        for key in (
            "SIMULATOR_DATABASE_URL",
            "ORACLE_READ_TOKEN",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
        ):
            self.env.pop(key, None)

    def save(self) -> None:
        atomic(
            self.state_path, {"token": self.token, "events": self.events, "records": self.records}
        )

    def start(self, name: str, *, recovery: bool = False, workflow: str | None = None) -> None:
        module, port = MODULES[name]
        env = dict(self.env)
        if name == "simulator":
            env.update(SIMULATOR_DATABASE_URL=self.sim_database, ORACLE_READ_TOKEN=self.token)
        if name == "worker" and recovery:
            env.update(REPAIR_DELIVERY_ENABLED="true", REPAIR_WORKFLOW_SCOPE=workflow or "")
        log = self.logs / f"{name}-{time.time_ns()}.log"
        with log.open("xb") as output:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    module,
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=output,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        self.processes[name] = process
        identity = process_identity(process.pid)
        if identity is None:
            raise RuntimeError("Service exited before identity checkpoint")
        self.records[name] = {"pid": process.pid, "identity": identity, "port": port}
        self.events.append(
            {
                "event": "PROCESS_STARTED",
                "at": now(),
                "name": name,
                "pid": process.pid,
                "recovery": recovery,
                "workflow_scope": workflow,
                "log": str(log),
            }
        )
        self.save()
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Service exited; inspect {log}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health/live", timeout=1):
                    return
            except (URLError, TimeoutError):
                Event().wait(0.1)
        raise TimeoutError(f"Service readiness failed: {name}")

    def start_all(self) -> None:
        for name in MODULES:
            self.start(name)

    def stop(self, name: str) -> None:
        record = self.records.pop(name, None)
        if record:
            stop_owned(record["pid"], record["identity"])
            process = self.processes.pop(name, None)
            if process:
                process.wait(timeout=10)
            self.events.append({"event": "PROCESS_STOPPED", "at": now(), "name": name, **record})
            self.save()

    def restart_worker(self, workflow: str) -> None:
        self.stop("worker")
        self.start("worker", recovery=True, workflow=workflow)

    def stop_all(self) -> None:
        for name in list(reversed(self.records)):
            self.stop(name)


def provision(root: Path) -> None:
    """Two new servers; existing application containers and volumes never reset."""
    config = load(root / "resources.json")
    for name, port, user, database in (
        (config["containers"][0], 16432, "setup_app", "setup_app"),
        (config["containers"][1], 16433, "setup_truth", "setup_truth"),
    ):
        inspected = subprocess.run(["docker", "inspect", name], capture_output=True, text=True)
        if inspected.returncode:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--pull=never",
                    "--name",
                    name,
                    "--label",
                    f"research.setup={config['resource_id']}",
                    "--memory",
                    "256m",
                    "--cpus",
                    "1",
                    "--log-opt",
                    "max-size=10m",
                    "--log-opt",
                    "max-file=3",
                    "-p",
                    f"127.0.0.1:{port}:5432",
                    "-e",
                    f"POSTGRES_USER={user}",
                    "-e",
                    "POSTGRES_PASSWORD=setup_local_only",
                    "-e",
                    f"POSTGRES_DB={database}",
                    "-v",
                    f"{name}-data:/var/lib/postgresql/data",
                    "postgres:16.9",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            atomic(
                root / f"provision-{name}.json",
                {
                    "at": now(),
                    "status": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
            result.check_returncode()
        else:
            resource = json.loads(inspected.stdout)[0]
            if resource["Config"]["Labels"].get("research.setup") != config["resource_id"]:
                raise ValueError("Dedicated resource ownership mismatch")
            subprocess.run(["docker", "start", name], check=True, capture_output=True, timeout=20)
    for dsn in (config["database"], config["sim_database"]):
        until = time.monotonic() + 40
        while True:
            try:
                with psycopg.connect(dsn, connect_timeout=2):
                    break
            except psycopg.OperationalError:
                if time.monotonic() >= until:
                    raise
                Event().wait(0.2)
    env = {
        **os.environ,
        "DATABASE_ADMIN_URL": config["database"].replace("postgresql://", "postgresql+psycopg://"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    log = root / f"existing-schema-install-{time.time_ns()}.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    result.check_returncode()
    cache = config["containers"][2]
    inspected = subprocess.run(["docker", "inspect", cache], capture_output=True, text=True)
    if inspected.returncode:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--pull=never",
                "--name",
                cache,
                "--label",
                f"research.setup={config['resource_id']}",
                "--memory",
                "64m",
                "--cpus",
                ".25",
                "--log-opt",
                "max-size=5m",
                "--log-opt",
                "max-file=2",
                "redis:7.4.5-alpine",
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
    else:
        resource = json.loads(inspected.stdout)[0]
        if resource["Config"]["Labels"].get("research.setup") != config["resource_id"]:
            raise ValueError("Dedicated cache ownership mismatch")
        subprocess.run(["docker", "start", cache], check=True, capture_output=True, timeout=20)
