"""Isolated local v2 application processes and databases; no production reset."""

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
from psycopg import sql

from research.remedies.runtime import Runtime as HistoricalRuntime

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/phase-8-study-design/v4"

API = "http://127.0.0.1:18100"
VOICE = "http://127.0.0.1:18101"
WORKER = "http://127.0.0.1:18102"
SIMULATOR = "http://127.0.0.1:18110"
DATABASE = "postgresql://voice_agent:voice_agent_local@127.0.0.1:15432/study_calibration_v4"
SIM_DATABASE = "postgresql://simulator:simulator_local@127.0.0.1:5433/study_calibration_v4_truth"


def prepare_databases() -> None:
    for dsn, name in (
        (
            "postgresql://voice_agent:voice_agent_local@127.0.0.1:15432/voice_agent",
            "study_calibration_v4",
        ),
        (
            "postgresql://simulator:simulator_local@127.0.0.1:5433/simulator_truth",
            "study_calibration_v4_truth",
        ),
    ):
        with psycopg.connect(dsn, autocommit=True) as conn:
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone():
                conn.execute(sql.SQL("CREATE DATABASE {} ").format(sql.Identifier(name)))
    env = {
        **os.environ,
        "DATABASE_ADMIN_URL": DATABASE.replace("postgresql://", "postgresql+psycopg://"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    (OUTPUT / "migration-upgrade.log").write_text(result.stdout + result.stderr, encoding="utf-8")


class Runtime(HistoricalRuntime):
    def __init__(self, log_directory: Path) -> None:
        self.logs = log_directory
        self.logs.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_hex(24)
        self.env = {
            **os.environ,
            "DATABASE_SYNC_URL": DATABASE,
            "DATABASE_URL": DATABASE.replace("postgresql://", "postgresql+asyncpg://"),
            "SIMULATOR_BASE_URL": SIMULATOR,
            "API_BASE_URL": API,
            "EXPERIMENT_MODE": "true",
            "REPAIR_DELIVERY_ENABLED": "false",
        }
        self.env.pop("SIMULATOR_DATABASE_URL", None)
        self.env.pop("ORACLE_READ_TOKEN", None)
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        self.events: list[dict[str, Any]] = []

    def start(self, name: str, *, recovery: bool = False, workflow: str | None = None) -> None:
        modules = {
            "api": ("apps.api_controller.main:app", 18100),
            "voice": ("apps.voice_worker.main:app", 18101),
            "worker": ("apps.durable_worker.main:app", 18102),
            "simulator": ("research.provider_simulator.main:app", 18110),
        }
        module, port = modules[name]
        env = dict(self.env)
        if name == "simulator":
            env.update(SIMULATOR_DATABASE_URL=SIM_DATABASE, ORACLE_READ_TOKEN=self.token)
        if name == "worker" and recovery:
            env["REPAIR_DELIVERY_ENABLED"] = "true"
            if workflow:
                env["REPAIR_WORKFLOW_SCOPE"] = workflow
        log = self.logs / f"{name}-{time.time_ns()}.log"
        with log.open("wb") as output:
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
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"{name} exited; inspect {log}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health/live", timeout=1):
                    break
            except (URLError, TimeoutError):
                Event().wait(0.1)  # readiness polling, never race placement
        else:
            raise TimeoutError(f"{name} did not become ready")
        self.events.append(
            {
                "event": "PROCESS_STARTED",
                "name": name,
                "pid": process.pid,
                "recovery": recovery,
                "workflow_scope": workflow,
                "log": str(log),
            }
        )

    def stop(self, name: str) -> None:
        process = self.processes.pop(name, None)
        if process:
            process.terminate()
            process.wait(timeout=10)
            self.events.append({"event": "PROCESS_STOPPED", "name": name, "pid": process.pid})

    def restart_worker(self, workflow: str) -> None:
        self.stop("worker")
        self.start("worker", recovery=True, workflow=workflow)

    def __enter__(self) -> "Runtime":
        try:
            for name in ("simulator", "api", "voice", "worker"):
                self.start(name)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *_: object) -> None:
        for name in list(reversed(self.processes)):
            self.stop(name)
