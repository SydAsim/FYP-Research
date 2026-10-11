"""Corrected standalone barrier probe against already isolated calibration services."""

import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from apps.durable_worker.phase2 import _provider_payload
from research.arms import Arm
from research.provider_simulator.store import truth_log
from research.remedies.runner import now
from research.scenario_dsl.models import stable_hash
from research.study.package import write_json
from research.study_v4.calibration import CalibrationTrial
from research.study_v4.design import ROOT, materialize
from research.study_v4.runtime import DATABASE, SIM_DATABASE, SIMULATOR, Runtime


def main() -> None:
    directory = ROOT / "barrier-calibration" / str(uuid4())
    directory.mkdir(parents=True)
    write_json(
        directory / "plan.json",
        {
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "planned_at": now(),
            "budget": 120,
            "fault": "PROVIDER_BARRIER_NOT_RELEASED",
            "uses": "Already isolated v4 calibration simulator; new scenario and operation",
            "amendment": "Read full PG operation; history API intentionally summarizes operations",
            "main_started": False,
        },
    )
    trial = CalibrationTrial(
        Runtime(directory / "unused"), materialize(calibration=True)[42], Arm.B3, directory
    )
    operation_id = trial.initialize()
    with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
        operation = conn.execute("SELECT * FROM operations WHERE id=%s", (operation_id,)).fetchone()
    assert operation is not None
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
    elapsed = time.monotonic() - began
    previous = os.environ.get("SIMULATOR_DATABASE_URL")
    os.environ["SIMULATOR_DATABASE_URL"] = SIM_DATABASE
    try:
        from uuid import UUID

        truth = json.loads(json.dumps(truth_log(UUID(trial.scenario)), default=str))
    finally:
        if previous is None:
            os.environ.pop("SIMULATOR_DATABASE_URL", None)
        else:
            os.environ["SIMULATOR_DATABASE_URL"] = previous
    result = {
        "budget": "barrier",
        "seconds": 120,
        "elapsed_seconds": elapsed,
        "status": status,
        "truth": truth,
        "qualified": 120 <= elapsed < 125 and status == 500 and not truth,
        "scope": "Actual unreleased BEFORE_COMMIT barrier",
    }
    trial.row.update(finished_at=now(), boundary_result=result, status="EXPECTED_BARRIER_TIMEOUT")
    trial.row["trace_hash"] = stable_hash(trial.row)
    trial.save()
    write_json(directory / "results.json", result)
    print(directory, flush=True)


if __name__ == "__main__":
    main()
