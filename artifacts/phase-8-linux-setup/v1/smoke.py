"""Finite Linux/real-PostgreSQL boot check; issues zero business or main-input requests."""

import json
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

import psycopg

from research.execution_linux_v1 import platform, runner, runtime
from research.execution_setup.core import immutable, load, now
from research.execution_setup.resources import admission
from research.execution_setup.runtime import MODULES


def smoke(root: Path, backup: Path) -> None:
    runner.install()
    runner.initialize(root, backup)
    admission(platform.host(root, backup))
    runtime.provision(root)
    services = runtime.Runtime(root, root / "boot-only-services")
    try:
        services.start_all()
        readiness = {}
        for name, (_, port) in MODULES.items():
            with urlopen(f"http://127.0.0.1:{port}/health/live", timeout=2) as response:
                readiness[name] = response.status
        # A new process attaches to the same service checkpoint without restarting them.
        attach_code = (
            "import json,sys;from pathlib import Path; "
            "from research.execution_linux_v1.runtime import Runtime; "
            "print(json.dumps(Runtime(Path(sys.argv[1]),Path(sys.argv[2]),attach=True).records))"
        )
        attached = subprocess.run(
            [sys.executable, "-c", attach_code, str(root), str(services.directory)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert json.loads(attached.stdout) == services.records
        config = load(root / "resources.json")
        with psycopg.connect(config["database"]) as conn:
            counts = conn.execute(
                "SELECT (SELECT count(*) FROM workflows), "
                "(SELECT count(*) FROM executions), "
                "(SELECT version_num FROM alembic_version)"
            ).fetchone()
        assert counts is not None and counts[:2] == (0, 0)
        archive = runner.ledger_for(root).backup(backup)
        runner.verify(root)
        immutable(
            root / "boot-smoke-success.json",
            {
                "at": now(),
                "health": readiness,
                "workflows": counts[0],
                "executions": counts[1],
                "schema_head": counts[2],
                "backup": str(archive),
                "resource_sample": platform.host(root, backup),
                "services_same_pid_attach": True,
                "calibration_slots_admitted": 0,
                "main_executions": 0,
                "main_started": False,
            },
        )
    finally:
        services.stop_all()
        config = load(root / "resources.json")
        for name in config["containers"]:
            runtime.inspect_owned(name, config["resource_id"])
            subprocess.run(["docker", "stop", name], check=True, capture_output=True, timeout=30)
    print(json.dumps(load(root / "boot-smoke-success.json")), flush=True)


if __name__ == "__main__":
    root, backup = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    try:
        smoke(root, backup)
    except Exception as error:
        root.mkdir(parents=True, exist_ok=True)
        immutable(
            root / "boot-smoke-failure.json",
            {
                "at": now(),
                "error": str(error),
                "main_started": False,
            },
        )
        raise
