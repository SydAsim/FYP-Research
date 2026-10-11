"""Phase 1 HTTP and PostgreSQL invariants; requires a migrated test database."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.errors import ExclusionViolation

from apps.api_controller.main import app

client = TestClient(app, raise_server_exceptions=False)
BASE = datetime.fromisoformat("2026-10-01T15:00:00+05:00")


def fixture() -> dict[str, Any]:
    response = client.post("/internal/phase1/fixtures", json={"command_id": str(uuid4())})
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def revision_body(
    data: dict[str, Any], expected: int, hour: int, appointment_id: str | None = None
) -> dict[str, Any]:
    start = BASE + timedelta(hours=hour - 15)
    desired = {
        "ticket_id": data["ticket_id"],
        "requested_start": start.isoformat(),
        "requested_end": (start + timedelta(minutes=30)).isoformat(),
        "timezone": "Asia/Karachi",
    }
    if appointment_id is not None:
        desired["appointment_id"] = appointment_id
    return {
        "command_id": str(uuid4()),
        "expected_revision": expected,
        "change_class": "INITIAL" if expected == 0 else "PARAMETER_CORRECTION",
        "desired_state": desired,
        "candidate_source": {
            "utterance_id": data["utterance_ids"][min(expected, 1)],
            "model": "synthetic-phase1",
            "prompt_hash": "sha256:synthetic-phase1",
            "transcript_version": 1,
        },
    }


def accept(data: dict[str, Any], body: dict[str, Any]) -> Any:
    return client.post(f"/v1/workflows/{data['workflow_id']}/revisions", json=body)


def prepare(
    data: dict[str, Any], revision: int, version: int, key: str | None = None
) -> tuple[dict[str, Any], Any]:
    body = {
        "command_id": str(uuid4()),
        "workflow_id": data["workflow_id"],
        "expected_intent_revision": revision,
        "expected_resource_version": version,
        "idempotency_key": key or f"local:{uuid4()}",
    }
    response = client.post("/v1/operations/appointments", json=body)
    return body, response


def commit(operation_id: str, command_id: str | None = None) -> Any:
    return client.post(
        f"/v1/operations/{operation_id}/commit-local",
        json={"command_id": command_id or str(uuid4())},
    )


def history(data: dict[str, Any]) -> dict[str, Any]:
    response = client.get(f"/v1/workflows/{data['workflow_id']}/history")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_three_pm_to_four_pm_http_audit_history() -> None:
    data = fixture()
    first = accept(data, revision_body(data, 0, 15))
    assert first.status_code == 201, first.text
    prepared1, op1 = prepare(data, 1, 0)
    assert op1.status_code == 202, op1.text
    done1 = commit(op1.json()["operation_id"])
    assert done1.status_code == 200, done1.text
    appointment_id = done1.json()["appointment_id"]
    assert done1.json()["appointment_version"] == 0

    second = accept(data, revision_body(data, 1, 16, appointment_id))
    assert second.status_code == 201, second.text
    prepared2, op2 = prepare(data, 2, 0)
    assert op2.status_code == 202, op2.text
    done2 = commit(op2.json()["operation_id"])
    assert done2.status_code == 200, done2.text
    assert done2.json()["appointment_id"] == appointment_id
    assert done2.json()["appointment_version"] == 1

    audit = history(data)
    assert audit["current_revision"] == 2
    assert [item["revision"] for item in audit["revisions"]] == [1, 2]
    assert [item["effect_type"] for item in audit["effects"]] == [
        "APPOINTMENT_CREATED",
        "APPOINTMENT_RESCHEDULED",
    ]
    assert len(audit["appointments"]) == 1
    assert audit["appointments"][0]["starts_at"].startswith("2026-10-01T11:00:00")
    assert audit["appointments"][0]["status"] == "CONFIRMED"
    assert audit["operations"][0]["applicability"] == "SUPERSEDED"
    assert audit["operations"][0]["effect_knowledge"] == "PRESENT"
    assert audit["operations"][1]["speech_eligibility"] == "BLOCKED"
    assert prepared1["idempotency_key"] != prepared2["idempotency_key"]
    assert [item["workflow_sequence"] for item in audit["events"]] == list(range(1, 8))
    dsn = os.environ.get(
        "DATABASE_SYNC_URL", "postgresql://voice_agent:voice_agent_local@127.0.0.1:5432/voice_agent"
    )
    with psycopg.connect(dsn) as conn:
        event_and_outbox = conn.execute(
            "SELECT count(*) FROM workflow_events e JOIN outbox o ON o.id=e.id "
            "WHERE e.workflow_id=%s",
            (data["workflow_id"],),
        ).fetchone()
    assert event_and_outbox == (7,)


def test_concurrent_revision_acceptance_one_revision_two() -> None:
    data = fixture()
    assert accept(data, revision_body(data, 0, 15)).status_code == 201
    barrier = Barrier(3)

    def attempt(hour: int) -> Any:
        barrier.wait()
        return accept(data, revision_body(data, 1, hour))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, 16), pool.submit(attempt, 17)]
        barrier.wait()
        responses = [future.result() for future in futures]
    assert sorted(response.status_code for response in responses) == [201, 409]
    assert history(data)["current_revision"] == 2


def test_stale_revision_problem_and_same_command_replay() -> None:
    data = fixture()
    body = revision_body(data, 0, 15)
    first = accept(data, body)
    replay = accept(data, body)
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    stale = accept(data, revision_body(data, 0, 16))
    assert stale.status_code == 409
    assert stale.headers["content-type"].startswith("application/problem+json")
    assert stale.json()["type"].endswith("/stale-intent-revision")
    assert stale.json()["trace_id"]
    assert len(history(data)["revisions"]) == 1


def test_fixture_command_replay_and_changed_request_conflict() -> None:
    body = {"command_id": str(uuid4())}
    first = client.post("/internal/phase1/fixtures", json=body)
    second = client.post("/internal/phase1/fixtures", json=body)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    changed = client.post(
        "/internal/phase1/fixtures",
        json={**body, "first_transcript": "Different synthetic request"},
    )
    assert changed.status_code == 409
    assert changed.json()["type"].endswith("/idempotency-conflict")


def test_revision_two_before_commit_blocks_obsolete_revision_one() -> None:
    data = fixture()
    assert accept(data, revision_body(data, 0, 15)).status_code == 201
    _, op = prepare(data, 1, 0)
    assert op.status_code == 202
    assert accept(data, revision_body(data, 1, 16)).status_code == 201
    blocked = commit(op.json()["operation_id"])
    assert blocked.status_code == 409
    assert blocked.json()["type"].endswith("/stale-intent-revision")
    audit = history(data)
    assert audit["appointments"] == []
    assert audit["operations"][0]["effect_knowledge"] == "ABSENT"
    assert audit["operations"][0]["applicability"] == "SUPERSEDED"


def test_prepare_key_conflict_and_commit_replay() -> None:
    data = fixture()
    assert accept(data, revision_body(data, 0, 15)).status_code == 201
    key = f"local:{uuid4()}"
    body, prepared = prepare(data, 1, 0, key)
    assert prepared.status_code == 202
    exact = client.post("/v1/operations/appointments", json=body)
    assert exact.status_code == 202
    assert exact.json() == prepared.json()
    altered = {**body, "command_id": str(uuid4()), "expected_resource_version": 1}
    conflict = client.post("/v1/operations/appointments", json=altered)
    assert conflict.status_code == 409
    assert conflict.json()["type"].endswith("/idempotency-conflict")
    op_id = prepared.json()["operation_id"]
    command_id = str(uuid4())
    first = commit(op_id, command_id)
    second = commit(op_id, command_id)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(history(data)["effects"]) == 1


def test_stale_resource_version_blocks_prepare() -> None:
    data = fixture()
    assert accept(data, revision_body(data, 0, 15)).status_code == 201
    _, response = prepare(data, 1, 1)
    assert response.status_code == 409
    assert response.json()["type"].endswith("/stale-resource-version")
    assert history(data)["operations"] == []


def test_database_exclusion_rejects_active_overlap() -> None:
    data = fixture()
    assert accept(data, revision_body(data, 0, 15)).status_code == 201
    _, op = prepare(data, 1, 0)
    assert op.status_code == 202
    assert commit(op.json()["operation_id"]).status_code == 200
    dsn = os.environ.get(
        "DATABASE_SYNC_URL", "postgresql://voice_agent:voice_agent_local@127.0.0.1:5432/voice_agent"
    )
    with pytest.raises(ExclusionViolation), psycopg.connect(dsn) as conn:
        conn.execute(
            "INSERT INTO appointments (ticket_id,resident_id,resource_key,starts_at,ends_at,"
            "timezone,requested_local_start,status,source_workflow_id,source_intent_revision) "
            "VALUES (%s,%s,%s,%s,%s,'Asia/Karachi','2026-10-01T15:15:00+05:00','CONFIRMED',%s,1)",
            (
                data["ticket_id"],
                data["resident_id"],
                data["resource_key"],
                BASE + timedelta(minutes=15),
                BASE + timedelta(minutes=45),
                data["workflow_id"],
            ),
        )
