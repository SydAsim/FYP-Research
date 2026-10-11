"""Real PostgreSQL late ACK isolation and crash/restart recovery regressions."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
import pytest

from research.remedies.plan import FIXTURES
from research.remedies.preserve import OUTPUT, ROOT
from research.remedies.runner import Trial
from research.remedies.runtime import API, DATABASE, Runtime


@pytest.fixture(scope="module")
def runtime() -> Any:
    with Runtime(OUTPUT / f"validation/test-services-{uuid4()}") as services:
        yield services


def trial(runtime: Runtime, arm: str, tmp_path: Path) -> tuple[Trial, dict[str, Any]]:
    item = Trial(runtime, FIXTURES[2], arm, tmp_path)
    op = item.setup()
    return item, item.schedule(op, 1)


@pytest.mark.parametrize("arm", ["B3", "P1", "P2"])
@pytest.mark.parametrize("kind", ["PROGRESS", "COMPLETED"])
def test_late_ack_capability_duplicate_and_reordering(
    runtime: Runtime, arm: str, kind: str, tmp_path: Path
) -> None:
    item, old = trial(runtime, arm, tmp_path)
    item.ack(old, "STARTED")
    request = item.ack_body(old, kind, 8 if kind == "PROGRESS" else len(old["word_timeline_json"]))
    item.revision(2, 16)
    first = item.ack(old, kind, body=request)
    assert first == item.ack(old, kind, body=request)
    lower = {**item.ack_body(old, "PROGRESS", 2), "client_time": request["client_time"]}
    item.ack(old, "PROGRESS", body=lower)
    snapshot = item.snapshot()
    assert len(snapshot["obligations"]) == (1 if arm == "P2" else 0)
    assert item.detail(old["id"])["last_word_index"] == request["last_word_index"]
    assert sum(e["event_name"] == "RepairRequired" for e in snapshot["history"]["events"]) == (
        1 if arm == "P2" else 0
    )
    assert all(p["status"] == 202 for p in item.row["client_playback"])


@pytest.mark.parametrize("arm", ["B3", "P1", "P2"])
def test_intro_before_correction_has_no_repair(runtime: Runtime, arm: str, tmp_path: Path) -> None:
    item, old = trial(runtime, arm, tmp_path)
    item.ack(old, "STARTED")
    item.ack(old, "PROGRESS", 2)
    item.revision(2, 16)
    assert not item.snapshot()["obligations"]


def test_compatible_target_does_not_create_retraction_obligation(
    runtime: Runtime, tmp_path: Path
) -> None:
    item, old = trial(runtime, "P2", tmp_path)
    item.full(old)
    item.revision(2, 15)
    assert not item.snapshot()["obligations"]


def pending(runtime: Runtime, tmp_path: Path) -> Trial:
    item, old = trial(runtime, "P2", tmp_path)
    item.full(old)
    item.revision(2, 16)
    item.drain()
    return item


@pytest.mark.parametrize(
    "boundary",
    [
        "before_discovery",
        "after_lease",
        "after_verification",
        "after_authorization",
        "after_generation",
        "after_queue",
        "after_publication",
    ],
)
def test_crash_boundaries_resume_without_duplicate_audio_or_false_completion(
    runtime: Runtime, boundary: str, tmp_path: Path
) -> None:
    item = pending(runtime, tmp_path)
    command = [
        sys.executable,
        "-m",
        "apps.durable_worker.repair",
        "--workflow",
        item.item["workflow_id"],
    ]
    crashed = subprocess.run(
        [*command, "--crash-at", boundary],
        cwd=ROOT,
        env=runtime.env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert crashed.returncode == 73
    # Named fault clock: owner process is proved dead; make its lease due. This
    # tests expiry selection without using wall-clock sleeps to place a race.
    with psycopg.connect(DATABASE) as conn:
        conn.execute(
            "UPDATE repair_obligations SET delivery_lease_until=now()-interval '1 second' "
            "WHERE workflow_id=%s",
            (item.item["workflow_id"],),
        )
    resumed = subprocess.run(
        command, cwd=ROOT, env=runtime.env, capture_output=True, text=True, timeout=40
    )
    assert resumed.returncode == 0, resumed.stderr
    result = json.loads(resumed.stdout)
    assert result["action"] in ("published", "awaiting_ack"), result
    snapshot = item.snapshot()
    repaired = [s for s in snapshot["segments"] if s["segment_class"] == "REPAIR"]
    assert len(repaired) == 1
    assert snapshot["obligations"][0]["state"] == "REPAIR_AUTHORIZED"
    item.full(repaired[0])
    assert item.snapshot()["obligations"][0]["state"] == "REPAIR_PLAYED"
    log = {
        "boundary": boundary,
        "crash_returncode": crashed.returncode,
        "resumed": result,
        "workflow_id": item.item["workflow_id"],
        "snapshot": item.snapshot(),
    }
    (OUTPUT / f"validation/crash-{boundary}-{uuid4()}.json").write_text(
        json.dumps(log, indent=2) + "\n", encoding="utf-8"
    )


def test_two_consumers_cannot_schedule_two_segments(runtime: Runtime, tmp_path: Path) -> None:
    item = pending(runtime, tmp_path)
    command = [
        sys.executable,
        "-m",
        "apps.durable_worker.repair",
        "--workflow",
        item.item["workflow_id"],
    ]

    def consume() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command, cwd=ROOT, env=runtime.env, capture_output=True, text=True, timeout=40
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: consume(), range(2)))
    assert all(r.returncode == 0 for r in results)
    assert len([s for s in item.snapshot()["segments"] if s["segment_class"] == "REPAIR"]) == 1


def test_deadline_escalates_unknown_completion_durably(runtime: Runtime, tmp_path: Path) -> None:
    item = pending(runtime, tmp_path)
    with psycopg.connect(DATABASE) as conn:
        conn.execute(
            "UPDATE repair_obligations SET deadline_at=%s WHERE workflow_id=%s",
            (datetime(2020, 1, 1, tzinfo=UTC), item.item["workflow_id"]),
        )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "apps.durable_worker.repair",
            "--workflow",
            item.item["workflow_id"],
        ],
        cwd=ROOT,
        env=runtime.env,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert json.loads(result.stdout)["action"] == "escalated"
    assert item.snapshot()["obligations"][0]["state"] == "ESCALATED"
    with psycopg.connect(DATABASE) as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM handoffs WHERE workflow_id=%s "
                "AND reason_code='REPAIR_DELIVERY_UNRESOLVED'",
                (item.item["workflow_id"],),
            ).fetchone()[0]
            == 1
        )


def test_oracle_truth_boundary_denies_controller_without_token(
    runtime: Runtime, tmp_path: Path
) -> None:
    item, _ = trial(runtime, "B3", tmp_path)
    from research.remedies.runtime import SIMULATOR

    response = item.request(
        SIMULATOR, "GET", f"/internal/scenarios/{item.scenario}/truth", allow_failure=True
    )
    assert item.row["http"][-1]["status"] == 403
    assert response["detail"] == "Oracle-only truth boundary"
    assert "ORACLE_READ_TOKEN" not in runtime.env
    assert "SIMULATOR_DATABASE_URL" not in runtime.env
    assert item.request(
        SIMULATOR, "GET", f"/internal/scenarios/{item.scenario}/truth", oracle=True
    )["commits"]


def test_changed_event_id_facts_rejected(runtime: Runtime, tmp_path: Path) -> None:
    item, old = trial(runtime, "P2", tmp_path)
    started = item.ack_body(old, "STARTED")
    item.ack(old, "STARTED", body=started)
    item.request(
        API,
        "POST",
        f"/v1/calls/{item.item['call_id']}/playback-events",
        {**started, "played_ms": 1},
        allow_failure=True,
    )
    assert item.row["http"][-1]["status"] == 409
