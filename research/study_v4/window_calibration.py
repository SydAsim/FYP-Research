"""Separate 40/120/600-second probes, including real provider and PG journals."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from apps.durable_worker.phase2 import _provider_payload
from research.arms import Arm
from research.remedies.runner import now
from research.scenario_dsl.models import stable_hash
from research.study.package import write_json
from research.study_v4.calibration import CalibrationTrial
from research.study_v4.design import ROOT, materialize
from research.study_v4.runtime import DATABASE, SIMULATOR, Runtime, prepare_databases
from research.study_v4.window import observe


def main() -> None:
    directory = ROOT / "window-calibration" / str(uuid4())
    directory.mkdir(parents=True)
    write_json(
        directory / "plan.json",
        {
            "planned_at": now(),
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "budgets": [40, 120, 600],
            "main_started": False,
            "faults": [
                "CONSUMER_NOT_STARTED",
                "PROVIDER_BARRIER_NOT_RELEASED",
                "COMPLETION_ACK_WITHHELD",
            ],
            "limits": "Protocol only: no real disconnect, acoustic playback or human exposure",
        },
    )
    prepare_databases()
    with Runtime(directory / "logs") as runtime:
        case = materialize(calibration=True)[38]
        trial = CalibrationTrial(runtime, case, Arm.P2, directory)
        op = trial.setup()
        trial.full(trial.schedule(op, 1))
        trial.revision(2, 16)
        trial.drain()
        trial.barrier(
            "CONSUMER_NOT_STARTED", state="Durable repair persists; automatic consumer disabled"
        )
        barrier = CalibrationTrial(runtime, materialize(calibration=True)[42], Arm.B3, directory)
        before = barrier.initialize()
        with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
            operation = conn.execute("SELECT * FROM operations WHERE id=%s", (before,)).fetchone()
        assert operation is not None

        def provider_barrier() -> dict[str, Any]:
            payload = _provider_payload(operation)
            began = time.monotonic()
            try:
                with urlopen(
                    Request(
                        SIMULATOR + "/v1/operations",
                        method="POST",
                        data=json.dumps(payload).encode(),
                        headers={"Content-Type": "application/json"},
                    ),
                    timeout=130,
                ) as response:
                    status = response.status
            except HTTPError as error:
                status = error.code
            result = {
                "budget": "barrier",
                "seconds": 120,
                "elapsed_seconds": time.monotonic() - began,
                "status": status,
                "scope": "ACTUAL_SIMULATOR_UNRELEASED_BARRIER",
            }
            result["qualified"] = 120 <= result["elapsed_seconds"] < 125 and status == 500
            barrier.row.update(
                finished_at=now(),
                snapshot=barrier.snapshot(),
                status="EXPECTED_BARRIER_TIMEOUT",
                boundary_result=result,
            )
            barrier.row["trace_hash"] = stable_hash(barrier.row)
            barrier.save()
            write_json(directory / "barrier-boundary.json", result)
            return result

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(provider_barrier)
            recovery = observe(
                trial,
                40,
                "RECOVERY_WITH_CONSUMER_PAUSED",
                lambda s, cutoff: any(
                    v["intent_revision"] == 2
                    and v["published_at"]
                    and datetime.fromisoformat(v["published_at"]) <= cutoff
                    for v in s["segments"]
                ),
            )
            write_json(directory / "recovery-boundary.json", recovery)
            current = trial.recover(2)
            for segment in current:
                trial.ack(segment, "STARTED")
            trial.barrier("COMPLETION_ACK_WITHHELD", segments=[s["id"] for s in current])
            observed = observe(trial, case.observation_budget_seconds, "MISSING_COMPLETION_WINDOW")
            trial.row.update(finished_at=now(), snapshot=trial.snapshot(), status="COMPLETED")
            trial.row["trace_hash"] = stable_hash(trial.row)
            trial.save()
            write_json(
                directory / "results.json",
                {
                    "recovery": recovery["outcome"],
                    "recovery_seconds": recovery["elapsed_seconds"],
                    "barrier": future.result(),
                    "observation": observed["outcome"],
                    "observation_seconds": observed["elapsed_seconds"],
                    "missing_completion_remains_unknown": True,
                    "main_started": False,
                },
            )
    print(directory, flush=True)


if __name__ == "__main__":
    main()
