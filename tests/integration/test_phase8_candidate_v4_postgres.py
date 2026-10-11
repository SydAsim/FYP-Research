"""Separate v4 PostgreSQL regressions; no main slots or historical writes."""

from typing import Any
from uuid import uuid4

import pytest

from research.arms import Arm
from research.remedies.runner import now
from research.scenario_dsl.models import stable_hash
from research.study_v4.calibration import CalibrationTrial
from research.study_v4.design import ROOT, materialize
from research.study_v4.runtime import SIMULATOR, Runtime, prepare_databases


@pytest.fixture(scope="module")
def runtime() -> Any:
    prepare_databases()
    with Runtime(ROOT / "integration" / str(uuid4()) / "logs") as services:
        yield services


def retain(item: CalibrationTrial) -> None:
    item.row.update(snapshot=item.snapshot(), finished_at=now(), status="VALIDATION_ONLY")
    item.row["trace_hash"] = stable_hash(item.row)
    item.save()


@pytest.mark.parametrize("arm", [Arm.B3, Arm.P1, Arm.P2])
def test_delayed_duplicate_decisive_ack_is_safe(runtime: Runtime, arm: Arm) -> None:
    directory = ROOT / "integration" / str(uuid4())
    directory.mkdir(parents=True)
    item = CalibrationTrial(runtime, materialize(calibration=True)[37], arm, directory)
    operation = item.setup()
    segment = item.schedule(operation, 1)
    item.ack(segment, "STARTED")
    delayed = item.ack_body(segment, "PROGRESS", 8)
    item.revision(2, 16)
    response = item.ack(segment, "PROGRESS", body=delayed)
    assert response == item.ack(segment, "PROGRESS", body=delayed)
    snapshot = item.snapshot()
    assert len(snapshot["obligations"]) == (1 if arm is Arm.P2 else 0)
    assert item.detail(segment["id"])["last_word_index"] == 8
    retain(item)


@pytest.mark.parametrize("arm", [Arm.B3, Arm.P1, Arm.P2])
def test_stale_attempt_normal_path_and_independent_oracle(runtime: Runtime, arm: Arm) -> None:
    directory = ROOT / "integration" / str(uuid4())
    directory.mkdir(parents=True)
    item = CalibrationTrial(runtime, materialize(calibration=True)[30], arm, directory)
    item.run()
    assert item.row["unsafe_attempt"]["status"] == 409
    rejected = item.request(
        SIMULATOR, "GET", f"/internal/scenarios/{item.scenario}/truth", allow_failure=True
    )
    assert item.row["http"][-1]["status"] in (401, 403)
    assert rejected
    retain(item)
