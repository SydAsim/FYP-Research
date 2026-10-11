"""Phase 2 durability tests against PostgreSQL and the isolated simulator service."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api_controller.main import app
from apps.api_controller.phase1_service import _connection
from apps.durable_worker.phase2 import WorkerCrash, step
from research.provider_simulator.models import FaultKind, FaultRule, ScenarioConfig, Visibility
from research.provider_simulator.store import create_scenario, truth_log

client = TestClient(app, raise_server_exceptions=False)
BASE = datetime.fromisoformat("2026-10-01T15:00:00+05:00")


def setup(config: ScenarioConfig | None = None) -> tuple[dict[str, str], UUID, UUID]:
    scenario_id = create_scenario(config or ScenarioConfig())
    response = client.post("/internal/phase1/fixtures", json={"command_id": str(uuid4())})
    assert response.status_code == 201, response.text
    fixture = response.json()
    accept(fixture, 1, 15)
    body = {
        "command_id": str(uuid4()),
        "workflow_id": fixture["workflow_id"],
        "scenario_id": str(scenario_id),
        "expected_intent_revision": 1,
        "expected_resource_version": 0,
        "idempotency_key": f"test:{uuid4()}",
    }
    prepared = client.post("/internal/phase2/operations", json=body)
    assert prepared.status_code == 202, prepared.text
    return fixture, scenario_id, UUID(prepared.json()["operation_id"])


def accept(fixture: dict[str, str], revision: int, hour: int) -> None:
    start = BASE + timedelta(hours=hour - 15)
    response = client.post(
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        json={
            "command_id": str(uuid4()),
            "expected_revision": revision - 1,
            "change_class": "INITIAL" if revision == 1 else "PARAMETER_CORRECTION",
            "desired_state": {
                "ticket_id": fixture["ticket_id"],
                "requested_start": start.isoformat(),
                "requested_end": (start + timedelta(hours=1)).isoformat(),
                "timezone": "Asia/Karachi",
            },
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][revision - 1],
                "model": "phase2-integration",
                "prompt_hash": f"fixture:{revision}",
                "transcript_version": 1,
            },
        },
    )
    assert response.status_code == 201, response.text


def expire_lease() -> None:
    # Deterministic crash recovery: move the database lease, never sleep on a timer.
    with _connection() as conn:
        conn.execute(
            "UPDATE reconciliation_jobs SET lease_until=now()-interval '1 second' "
            "WHERE state='LEASED'"
        )


def drain(workflow_id: str) -> list[dict[str, object]]:
    outcomes: list[dict[str, object]] = []
    for _ in range(15):
        history = client.get(f"/v1/workflows/{workflow_id}/history").json()
        active = False
        for operation in history["operations"]:
            result = step(operation_id=UUID(operation["id"]))
            outcomes.append(result)
            active = active or result["action"] != "idle"
        if not active:
            return outcomes
    raise AssertionError("Worker did not reach idle within the bounded recovery budget")


def test_prepare_external_command_replay_duplicate_key_and_stale_revision() -> None:
    fixture, scenario_id, operation_id = setup()
    with _connection() as conn:
        key = conn.execute(
            "SELECT idempotency_key FROM operations WHERE id=%s", (operation_id,)
        ).fetchone()["idempotency_key"]
    body = {
        "command_id": str(uuid4()),
        "workflow_id": fixture["workflow_id"],
        "scenario_id": str(scenario_id),
        "expected_intent_revision": 1,
        "expected_resource_version": 0,
        "idempotency_key": key,
    }
    first = client.post("/internal/phase2/operations", json=body)
    replay = client.post("/internal/phase2/operations", json=body)
    duplicate = client.post(
        "/internal/phase2/operations", json={**body, "command_id": str(uuid4())}
    )
    assert first.status_code == replay.status_code == duplicate.status_code == 202
    assert first.json() == replay.json() == duplicate.json()
    assert first.json()["operation_id"] == str(operation_id)
    changed = client.post(
        "/internal/phase2/operations",
        json={
            **body,
            "command_id": str(uuid4()),
            "expected_resource_version": 1,
        },
    )
    assert changed.status_code == 409
    assert changed.json()["type"].endswith("/idempotency-conflict")
    accept(fixture, 2, 16)
    stale = client.post(
        "/internal/phase2/operations",
        json={
            **body,
            "command_id": str(uuid4()),
            "idempotency_key": f"stale:{uuid4()}",
        },
    )
    assert stale.status_code == 409
    assert stale.json()["type"].endswith("/stale-intent-revision")


@pytest.mark.parametrize(
    "boundary",
    [
        "AFTER_LEASE",
        "AFTER_DISPATCH_RECORDED",
        "AFTER_SEND_MARKER",
        "AFTER_PROVIDER_CALL",
        "AFTER_OUTCOME_RECORDED",
        "BEFORE_LOOKUP",
        "AFTER_LOOKUP",
        "AFTER_RECONCILIATION_RECORDED",
    ],
)
def test_crash_at_every_durable_boundary_preserves_single_effect(boundary: str) -> None:
    fixture, scenario_id, operation_id = setup()
    if boundary in ("BEFORE_LOOKUP", "AFTER_LOOKUP", "AFTER_RECONCILIATION_RECORDED"):
        assert step(operation_id=operation_id)["action"] == "dispatch"
    with pytest.raises(WorkerCrash, match=boundary):
        step(operation_id=operation_id, crash_at=boundary)
    expire_lease()
    drain(fixture["workflow_id"])
    commits = truth_log(scenario_id)
    assert len(commits) == 1, commits
    assert commits[0]["operation_id"] == operation_id
    detail = client.get(f"/v1/operations/{operation_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["operation"]["effect_knowledge"] == "PRESENT"
    assert len([item for item in detail.json()["attempts"] if item["attempt_type"] == "WRITE"]) <= 2
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert history["current_revision"] == 1


def test_unavailable_provider_handoffs_unknown_without_retry() -> None:
    config = ScenarioConfig(
        idempotency=False,
        status_lookup=False,
        resource_lookup=False,
        visibility=Visibility.UNAVAILABLE,
        faults=[
            FaultRule(
                request_index=1, stage="AFTER_COMMIT_BEFORE_RESPONSE", kind=FaultKind.DROP_RESPONSE
            )
        ],
    )
    fixture, scenario_id, operation_id = setup(config)
    assert step(operation_id=operation_id)["effect_knowledge"] == "UNKNOWN"
    outcomes = drain(fixture["workflow_id"])
    assert len([item for item in outcomes if item["action"] == "reconcile"]) == 8
    detail = client.get(f"/v1/operations/{operation_id}").json()
    assert detail["operation"]["effect_knowledge"] == "UNKNOWN"
    assert any(job["state"] == "HANDOFF" for job in detail["jobs"])
    assert len(truth_log(scenario_id)) == 1
    assert len([item for item in detail["attempts"] if item["attempt_type"] == "WRITE"]) == 1
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert not any(event["event_name"] == "OperationFailed" for event in history["events"])


@pytest.mark.parametrize(
    "stage,kind,expected_writes",
    [
        ("BEFORE_COMMIT", FaultKind.RETURN_5XX, 2),
        ("AFTER_COMMIT_BEFORE_RESPONSE", FaultKind.RETURN_5XX, 1),
        ("BEFORE_COMMIT", FaultKind.DUPLICATE, 1),
    ],
)
def test_fault_recovery_uses_truth_and_never_duplicates(
    stage: str, kind: FaultKind, expected_writes: int
) -> None:
    config = ScenarioConfig(faults=[FaultRule(request_index=1, stage=stage, kind=kind)])
    fixture, scenario_id, operation_id = setup(config)
    assert step(operation_id=operation_id)["action"] == "dispatch"
    drain(fixture["workflow_id"])
    detail = client.get(f"/v1/operations/{operation_id}").json()
    writes = [item for item in detail["attempts"] if item["attempt_type"] == "WRITE"]
    assert len(writes) == expected_writes
    assert detail["operation"]["effect_knowledge"] == "PRESENT"
    assert len(truth_log(scenario_id)) == 1


def test_partial_provider_effect_remains_partial_and_handoffs() -> None:
    config = ScenarioConfig(
        faults=[
            FaultRule(
                request_index=1,
                stage="BEFORE_COMMIT",
                kind=FaultKind.PARTIAL_EFFECT,
            )
        ]
    )
    fixture, scenario_id, operation_id = setup(config)
    assert step(operation_id=operation_id)["effect_knowledge"] == "UNKNOWN"
    drain(fixture["workflow_id"])
    detail = client.get(f"/v1/operations/{operation_id}").json()
    assert detail["operation"]["effect_knowledge"] == "PARTIAL"
    assert any(job["state"] == "HANDOFF" for job in detail["jobs"])
    assert truth_log(scenario_id)[0]["result_code"] == "PARTIAL"
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert not any(event["event_name"] == "WorkflowResolved" for event in history["events"])


def test_no_atomic_reschedule_creates_linked_compensation() -> None:
    fixture, scenario_id, first_operation = setup(ScenarioConfig(supports_reschedule=False))
    assert step(operation_id=first_operation)["action"] == "dispatch"
    accept(fixture, 2, 16)
    drain(fixture["workflow_id"])
    commits = truth_log(scenario_id)
    assert [row["action"] for row in commits] == ["CREATE", "CANCEL", "CREATE"]
    assert commits[0]["operation_id"] == first_operation
    assert commits[-1]["after_facts"]["starts_at"] == "2026-10-01T11:00:00+00:00"
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert history["current_revision"] == 2
    assert history["operations"][-1]["effect_knowledge"] == "PRESENT"
    with _connection() as conn:
        links = conn.execute(
            "SELECT action_type,parent_operation_id,supersedes_operation_id FROM operations "
            "WHERE workflow_id=%s AND intent_revision=2 ORDER BY created_at,id",
            (fixture["workflow_id"],),
        ).fetchall()
    assert {row["action_type"] for row in links} == {"COMPENSATE_CANCEL", "CREATE_APPOINTMENT"}
    assert all(
        row["parent_operation_id"] is not None and row["supersedes_operation_id"] is not None
        for row in links
    )


@pytest.mark.parametrize(
    "boundary", ["BEFORE_LOOKUP", "AFTER_LOOKUP", "AFTER_RECONCILIATION_RECORDED"]
)
def test_provider_conflict_handoff_crash_recovery_preserves_known_absence(boundary: str) -> None:
    config = ScenarioConfig(
        faults=[
            FaultRule(request_index=2, stage="BEFORE_COMMIT", kind=FaultKind.CONFLICTING_CHANGE)
        ]
    )
    fixture, scenario_id, first_id = setup(config)
    step(operation_id=first_id)
    step(operation_id=first_id)
    accept(fixture, 2, 16)
    step(operation_id=first_id)
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    current_id = UUID(
        next(item["id"] for item in history["operations"] if item["intent_revision"] == 2)
    )
    assert step(operation_id=current_id)["provider_status"] == 409
    with pytest.raises(WorkerCrash, match=boundary):
        step(operation_id=current_id, crash_at=boundary)
    with _connection() as conn:
        conn.execute(
            "UPDATE reconciliation_jobs SET lease_until=now()-interval '1 second' "
            "WHERE operation_id=%s AND state='LEASED'",
            (current_id,),
        )
    step(operation_id=current_id)
    assert step(operation_id=current_id)["action"] == "idle"
    detail = client.get(f"/v1/operations/{current_id}").json()
    assert detail["operation"]["effect_knowledge"] == "ABSENT"
    assert not detail["operation"]["reconciliation_required"]
    assert len([item for item in detail["attempts"] if item["attempt_type"] == "WRITE"]) == 1
    assert [item["action"] for item in truth_log(scenario_id)] == ["CREATE", "CONCURRENT_CHANGE"]
    with _connection() as conn:
        handoffs = conn.execute(
            "SELECT known_facts,unknown_facts FROM handoffs WHERE workflow_id=%s",
            (fixture["workflow_id"],),
        ).fetchall()
    assert len(handoffs) == 1
    assert handoffs[0]["known_facts"]["effect_outcome"] == "ABSENT"
    assert handoffs[0]["unknown_facts"] == {"final_intent_resolution": "UNRESOLVED"}


def accept_change(fixture: dict[str, str], revision: int, change_class: str, hour: int) -> None:
    start = BASE + timedelta(hours=hour - 15)
    response = client.post(
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        json={
            "command_id": str(uuid4()),
            "expected_revision": revision - 1,
            "change_class": change_class,
            "desired_state": {
                "ticket_id": fixture["ticket_id"],
                "requested_start": start.isoformat(),
                "requested_end": (start + timedelta(hours=1)).isoformat(),
                "timezone": "Asia/Karachi",
            },
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][0],
                "model": "phase6-crash-fixture",
                "prompt_hash": f"revision:{revision}",
                "transcript_version": 1,
            },
        },
    )
    assert response.status_code == 201, response.text


@pytest.mark.parametrize("change_class", ["RETRACTION", "ADDITIVE_COMPATIBLE"])
@pytest.mark.parametrize(
    "boundary", ["BEFORE_LOOKUP", "AFTER_LOOKUP", "AFTER_RECONCILIATION_RECORDED"]
)
def test_revision_transition_recovers_before_and_after_durable_record(
    change_class: str, boundary: str
) -> None:
    fixture, scenario_id, operation_id = setup()
    step(operation_id=operation_id)
    accept_change(fixture, 2, change_class, 15)
    with pytest.raises(WorkerCrash, match=boundary):
        step(operation_id=operation_id, crash_at=boundary)
    with _connection() as conn:
        conn.execute(
            "UPDATE reconciliation_jobs SET lease_until=now()-interval '1 second' "
            "WHERE operation_id=%s AND state='LEASED'",
            (operation_id,),
        )
    for _ in range(8):
        history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
        for operation in history["operations"]:
            step(operation_id=UUID(operation["id"]))
    actions = [row["action"] for row in truth_log(scenario_id)]
    assert actions == (["CREATE", "CANCEL"] if change_class == "RETRACTION" else ["CREATE"])
    with _connection() as conn:
        row = conn.execute(
            "SELECT resolution_status FROM workflows WHERE id=%s", (fixture["workflow_id"],)
        ).fetchone()
        assert row["resolution_status"] == "RESOLVED"
        assert conn.execute(
            "SELECT count(*) AS total FROM operations WHERE workflow_id=%s",
            (fixture["workflow_id"],),
        ).fetchone()["total"] == (2 if change_class == "RETRACTION" else 1)


def test_reused_effect_requires_fresh_receipt_and_is_invalidated_by_later_change() -> None:
    fixture, scenario_id, operation_id = setup()
    step(operation_id=operation_id)
    step(operation_id=operation_id)
    old = client.post(
        "/internal/phase3/verifications",
        json={
            "command_id": str(uuid4()),
            "operation_id": str(operation_id),
            "expected_intent_revision": 1,
            "claim_type": "CURRENT_APPOINTMENT",
        },
    ).json()
    assert old["result"] == "SATISFIED"
    accept_change(fixture, 2, "ADDITIVE_COMPATIBLE", 15)
    step(operation_id=operation_id)
    deny = client.post(
        "/internal/phase3/claims",
        json={
            "command_id": str(uuid4()),
            "receipt_id": old["receipt_id"],
            "expected_intent_revision": 2,
        },
    )
    assert deny.status_code == 409
    fresh = client.post(
        "/internal/phase3/verifications",
        json={
            "command_id": str(uuid4()),
            "operation_id": str(operation_id),
            "expected_intent_revision": 2,
            "claim_type": "CURRENT_APPOINTMENT",
        },
    )
    assert fresh.status_code == 201, fresh.text
    assert fresh.json()["result"] == "SATISFIED"
    assert fresh.json()["receipt_id"] != old["receipt_id"]
    accept_change(fixture, 3, "PARAMETER_CORRECTION", 17)
    with _connection() as conn:
        row = conn.execute(
            "SELECT applicability,reconciliation_required FROM operations WHERE id=%s",
            (operation_id,),
        ).fetchone()
    assert row == {"applicability": "SUPERSEDED", "reconciliation_required": True}
    for _ in range(8):
        history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
        for operation in history["operations"]:
            step(operation_id=UUID(operation["id"]))
    assert [row["action"] for row in truth_log(scenario_id)] == ["CREATE", "RESCHEDULE"]
    assert truth_log(scenario_id)[-1]["after_facts"]["starts_at"] == "2026-10-01T12:00:00+00:00"


def test_historical_success_cannot_reuse_a_changed_current_resource() -> None:
    from packages.provider_adapters.simulator import send_operation
    from research.runner.baselines import _request

    fixture, scenario_id, operation_id = setup()
    step(operation_id=operation_id)
    step(operation_id=operation_id)
    first = truth_log(scenario_id)[0]["after_facts"]
    concurrent = send_operation(
        _request(
            scenario_id,
            uuid4(),
            f"concurrent-reuse:{uuid4()}",
            "RESCHEDULE",
            fixture["resource_key"],
            start=BASE + timedelta(hours=2),
            timezone="Asia/Karachi",
            appointment_id=first["appointment_id"],
            expected_version=int(first["version"]),
        )
    )
    assert concurrent.status == 200
    accept_change(fixture, 2, "ADDITIVE_COMPATIBLE", 15)
    step(operation_id=operation_id)
    with _connection() as conn:
        workflow = conn.execute(
            "SELECT resolution_status FROM workflows WHERE id=%s", (fixture["workflow_id"],)
        ).fetchone()
        handoff = conn.execute(
            "SELECT reason_code,known_facts FROM handoffs WHERE workflow_id=%s",
            (fixture["workflow_id"],),
        ).fetchone()
    assert workflow["resolution_status"] == "HANDOFF"
    assert handoff["reason_code"] == "REUSE_RESOURCE_NOT_CURRENT"
    assert handoff["known_facts"]["effect_outcome"] == "PRESENT"
    assert [row["action"] for row in truth_log(scenario_id)] == ["CREATE", "RESCHEDULE"]
