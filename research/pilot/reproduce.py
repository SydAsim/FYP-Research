"""Boot an isolated clean Docker project from the verified frozen source archive."""

import argparse
import json
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from research.pilot.freeze import ROOT, verify_freeze
from research.pilot.runner import write
from research.scenario_dsl.models import stable_hash


def reproduce_environment(freeze_path: Path) -> dict[str, Any]:
    verify_freeze(freeze_path)
    frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    pilot = json.loads((freeze_path.parent / frozen["pilot_path"]).read_text(encoding="utf-8"))
    index = next(
        i
        for i, item in enumerate(pilot["plan"]["cases"])
        if item["kind"] == "provider"
        and item["case"]["correction_barrier"] == "P3"
        and item["case"]["visibility"] == "IMMEDIATE"
        and item["case"]["revision_type"] == "PARAMETER_CORRECTION"
        and item["case"]["workflow_shape"] == "ONE_TICKET_ONE_APPOINTMENT"
    )
    original = json.loads(
        (freeze_path.parent / pilot["entries"][index]["path"]).read_text(encoding="utf-8")
    )
    project = f"phase7-clean-{uuid4().hex[:12]}"
    directory = (freeze_path.parent / project).resolve()
    source = directory / "source"
    evidence = directory / "evidence"
    source.mkdir(parents=True)
    evidence.mkdir()
    with zipfile.ZipFile(freeze_path.parent / frozen["source_archive"]["path"]) as archive:
        for member in archive.namelist():
            if not (source / member).resolve().is_relative_to(source):
                raise ValueError("Frozen archive member escapes source workspace")
        archive.extractall(source)
    environment = {
        **os.environ,
        "PHASE7_PYTHON_IMAGE": frozen["container_digests"]["api-controller"],
        "PHASE7_SOURCE_DIR": str(source),
        "PHASE7_EVIDENCE_DIR": str(evidence),
    }
    command = [
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        str(source / "deployment/phase7-clean.compose.yaml"),
    ]

    def execute(args: list[str], *, payload: str | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            command + args,
            cwd=ROOT,
            env=environment,
            input=payload,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=240,
        )
        (directory / f"command-{len(list(directory.glob('command-*.log'))) + 1}.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        result.check_returncode()
        return result

    try:
        print(f"Booting clean isolated project {project}", flush=True)
        execute(["up", "-d", "--wait"])
        config = execute(["ps", "--format", "json"])
        digests = {}
        for line in config.stdout.splitlines():
            row = json.loads(line)
            labels = dict(label.split("=", 1) for label in row["Labels"].split(",") if "=" in label)
            digests[row["Service"]] = labels["com.docker.compose.image"]
        request = {
            "bundle": original,
            "source_inventory": frozen["source_inventory"],
            "container_digests": digests,
        }
        write(directory / "request.json", request, immutable=True)
        execute(
            ["--profile", "replay", "run", "--rm", "-T", "--no-deps", "runner"],
            payload=json.dumps(request),
        )
        result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
        result.update(
            project=project,
            freeze_hash=frozen["hash"],
            evidence_path=str(evidence),
            isolation="Fresh Compose network and two empty PostgreSQL volumes; no host ports",
        )
        result.pop("hash")
        result["hash"] = stable_hash(result)
        write(directory / "reproduction-gate.json", result, immutable=True)
        return {
            "gate_path": str(directory / "reproduction-gate.json"),
            "gate_hash": result["hash"],
            "metric_rows_match": result["metric_rows_match"],
            "verified_executions": result["verified"]["verified_executions"],
        }
    except Exception as exc:
        write(
            directory / "failure.json",
            {"trace_id": str(uuid4()), "error": str(exc), "exception_type": type(exc).__name__},
        )
        raise
    finally:
        # Exact newly allocated project only; preserve host source and raw replay evidence.
        execute(["down", "--volumes"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reproduce a selected frozen pilot in clean Docker services"
    )
    parser.add_argument("freeze", type=Path)
    args = parser.parse_args()
    print(json.dumps(reproduce_environment(args.freeze.resolve()), indent=2))
