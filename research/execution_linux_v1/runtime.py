"""Owned Linux service processes and dedicated simulator resources."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from threading import Event
from typing import Any

import psycopg

from research.execution_linux_v1.platform import boot_id, process_identity, stop_owned
from research.execution_setup import runtime as historical
from research.execution_setup.core import ROOT, immutable, load, now


class Runtime(historical.Runtime):
    def __init__(self, root: Path, execution: Path, *, attach: bool = False) -> None:
        super().__init__(root, execution, attach=attach)
        stamp = execution / "linux-boot.json"
        if attach:
            if load(stamp)["boot_id"] != boot_id():
                raise ValueError("HOST_REBOOT_UNQUALIFIED: preserve attempt; no automatic replay")
            for name, record in self.records.items():
                if process_identity(record["pid"]) != record["identity"]:
                    raise ValueError(f"SERVICE_LOST_UNQUALIFIED: {name}; no automatic replay")
        else:
            immutable(stamp, {"boot_id": boot_id(), "at": now()})
        # The protocol uses simulator/tone paths only. No AWS key is needed by services.
        for key in list(self.env):
            if key.startswith("AWS_") or key.endswith(("API_KEY", "API_SECRET")):
                self.env.pop(key)
        self.env["PYTHONPATH"] = str(ROOT)  # analysis overlays must not change application imports


def install_process_boundary() -> None:
    # Historical source stays byte-identical. Overrides live only in this research process.
    historical.process_identity = process_identity
    historical.stop_owned = stop_owned


def inspect_owned(name: str, owner: str) -> dict[str, Any] | None:
    result = subprocess.run(["docker", "inspect", name], capture_output=True, text=True, timeout=10)
    if result.returncode:
        # A broken daemon must not be mistaken for an absent named resource.
        subprocess.run(["docker", "info"], capture_output=True, check=True, timeout=10)
        absent = {
            f"{prefix}no such {kind}: {name}".casefold()
            for prefix in ("error: ", "error response from daemon: ")
            for kind in ("object", "container")
        }
        if result.stderr.strip().casefold() not in absent:
            raise RuntimeError(f"Docker inspection failed: {result.stderr}")
        return None
    value: dict[str, Any] = json.loads(result.stdout)[0]
    if value["Config"].get("Labels", {}).get("research.setup") != owner:
        raise ValueError("DEDICATED_RESOURCE_OWNERSHIP_MISMATCH")
    return value


def provision(root: Path) -> None:
    config = load(root / "resources.json")
    for tag, expected in config["image_digests"].items():
        result = subprocess.run(
            ["docker", "image", "inspect", tag],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if expected not in json.loads(result.stdout)[0].get("RepoDigests", []):
            raise ValueError(f"DATABASE_IMAGE_DRIFT: {tag}")
    owner, network = config["resource_id"], config.get("validation_network")
    if network:
        result = subprocess.run(
            ["docker", "network", "inspect", network],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if json.loads(result.stdout)[0].get("Labels", {}).get("research.linux.validation") != "v1":
            raise ValueError("VALIDATION_NETWORK_NOT_OWNED")
    for index, (user, port) in enumerate((("setup_app", 16432), ("setup_truth", 16433))):
        name = config["containers"][index]
        if inspect_owned(name, owner) is None:
            command = [
                "docker",
                "run",
                "-d",
                "--pull=never",
                "--name",
                name,
                "--label",
                f"research.setup={owner}",
                "--memory",
                "256m",
                "--cpus",
                "1",
                "--log-opt",
                "max-size=10m",
                "--log-opt",
                "max-file=3",
                "-e",
                f"POSTGRES_USER={user}",
                "-e",
                "POSTGRES_PASSWORD=setup_local_only",
                "-e",
                f"POSTGRES_DB={user}",
                "-v",
                f"{name}-data:/var/lib/postgresql/data",
            ]
            command += ["--network", network] if network else ["-p", f"127.0.0.1:{port}:5432"]
            command.append("postgres:16.9")
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            immutable(
                root / f"provision-{name}-{time.time_ns()}.json",
                {
                    "at": now(),
                    "status": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
            result.check_returncode()
        else:
            subprocess.run(["docker", "start", name], check=True, capture_output=True, timeout=20)
    for dsn in (config["database"], config["sim_database"]):
        deadline = time.monotonic() + 40
        while True:
            try:
                with psycopg.connect(dsn, connect_timeout=2):
                    break
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
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
    if inspect_owned(cache, owner) is None:
        command = [
            "docker",
            "run",
            "-d",
            "--pull=never",
            "--name",
            cache,
            "--label",
            f"research.setup={owner}",
            "--memory",
            "64m",
            "--cpus",
            ".25",
            "--log-opt",
            "max-size=5m",
            "--log-opt",
            "max-file=2",
        ]
        if network:
            command += ["--network", network]
        subprocess.run(
            command + ["redis:7.4.5-alpine"], check=True, capture_output=True, timeout=30
        )
    else:
        subprocess.run(["docker", "start", cache], check=True, capture_output=True, timeout=20)
