"""Receipt, permit and release gates against migrated PostgreSQL and the provider."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from apps.api_controller.main import app
from apps.durable_worker.phase2 import step
from research.provider_simulator.models import ProviderOperation, ScenarioConfig, Visibility
from research.provider_simulator.store import create_scenario, inject_concurrent_change

client = TestClient(app, raise_server_exceptions=False)


def revision(fixture: dict[str, Any], number: int, hour: int) -> Any:
    response = client.post(
        f"/v1/workflows/{fixture['workflow_id']}/revisions",
        json={
            "command_id": str(uuid4()),
            "expected_revision": number - 1,
            "change_class": "INITIAL" if number == 1 else "PARAMETER_CORRECTION",
            "desired_state": {
                "ticket_id": fixture["ticket_id"],
                "requested_start": f"2026-10-01T{hour:02d}:00:00+05:00",
                "requested_end": f"2026-10-01T{hour + 1:02d}:00:00+05:00",
                "timezone": "Asia/Karachi",
            },
            "candidate_source": {
                "utterance_id": fixture["utterance_ids"][number - 1],
                "model": "phase3-test",
                "prompt_hash": f"phase3:{number}",
                "transcript_version": 1,
            },
        },
    )
    assert response.status_code == 201, response.text
    return response


def setup(config: ScenarioConfig | None = None) -> tuple[dict[str, Any], UUID, UUID]:
    scenario_id = create_scenario(config or ScenarioConfig())
    created = client.post("/internal/phase1/fixtures", json={"command_id": str(uuid4())})
    assert created.status_code == 201, created.text
    fixture = created.json()
    revision(fixture, 1, 15)
    prepared = client.post(
        "/internal/phase2/operations",
        json={
            "command_id": str(uuid4()),
            "workflow_id": fixture["workflow_id"],
            "scenario_id": str(scenario_id),
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase3:{uuid4()}",
        },
    )
    assert prepared.status_code == 202, prepared.text
    return fixture, scenario_id, UUID(prepared.json()["operation_id"])


def completed(config: ScenarioConfig | None = None) -> tuple[dict[str, Any], UUID, UUID]:
    fixture, scenario_id, operation_id = setup(config)
    assert step(operation_id=operation_id)["action"] == "dispatch"
    if config is None or config.resource_lookup:
        assert step(operation_id=operation_id)["action"] == "reconcile"
    return fixture, scenario_id, operation_id


def verify(
    operation_id: UUID, revision_number: int, claim_type: str = "CURRENT_APPOINTMENT"
) -> Any:
    return client.post(
        "/internal/phase3/verifications",
        json={
            "command_id": str(uuid4()),
            "operation_id": str(operation_id),
            "expected_intent_revision": revision_number,
            "claim_type": claim_type,
        },
    )


def drain(fixture: dict[str, Any]) -> None:
    for _ in range(12):
        history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
        active = False
        for operation in history["operations"]:
            active = step(operation_id=UUID(operation["id"]))["action"] != "idle" or active
        if not active:
            return
    raise AssertionError("Scoped worker did not reach idle")


def authorize(receipt_id: str, revision_number: int) -> Any:
    return client.post(
        "/internal/phase3/claims",
        json={
            "command_id": str(uuid4()),
            "receipt_id": receipt_id,
            "expected_intent_revision": revision_number,
        },
    )


def queue(permit_id: str, revision_number: int) -> Any:
    return client.post(
        f"/internal/phase3/permits/{permit_id}/queue",
        json={
            "command_id": str(uuid4()),
            "expected_intent_revision": revision_number,
        },
    )


def publish(permit_id: str, revision_number: int, command_id: str | None = None) -> Any:
    return client.post(
        f"/internal/phase3/permits/{permit_id}/publish",
        json={
            "command_id": command_id or str(uuid4()),
            "expected_intent_revision": revision_number,
        },
    )


def test_satisfied_receipt_single_use_publication_and_command_replay() -> None:
    _, _, operation_id = completed()
    checked = verify(operation_id, 1)
    assert checked.status_code == 201, checked.text
    assert checked.json()["result"] == "SATISFIED"
    receipt_id = checked.json()["receipt_id"]
    detail = client.get(f"/v1/receipts/{receipt_id}").json()
    assert len(detail["evidence_items"]) == 1
    assert detail["evidence_items"][0]["source_type"] == "SIMULATOR_RESOURCE"
    allowed = authorize(receipt_id, 1)
    assert allowed.status_code == 201, allowed.text
    permit_id = allowed.json()["permit_id"]
    assert queue(permit_id, 1).status_code == 200
    command_id = str(uuid4())
    first = publish(permit_id, 1, command_id)
    replay = publish(permit_id, 1, command_id)
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert "3:00 PM" in first.json()["text"]
    assert publish(permit_id, 1).status_code == 409
    model_text = client.post(
        "/internal/phase3/claims",
        json={
            "command_id": str(uuid4()),
            "receipt_id": receipt_id,
            "expected_intent_revision": 1,
            "model_text": "Everything succeeded.",
        },
    )
    assert model_text.status_code == 422


def test_tool_success_without_postcondition_evidence_is_unknown() -> None:
    config = ScenarioConfig(
        resource_lookup=False, status_lookup=True, visibility=Visibility.IMMEDIATE
    )
    fixture, _, operation_id = setup(config)
    dispatched = step(operation_id=operation_id)
    assert dispatched["provider_status"] == 200
    checked = verify(operation_id, 1)
    assert checked.status_code == 201
    assert checked.json()["result"] == "UNKNOWN"
    denied = authorize(checked.json()["receipt_id"], 1)
    assert denied.status_code == 409
    assert denied.json()["type"].endswith("/receipt-not-applicable")
    progress = client.get(f"/v1/workflows/{fixture['workflow_id']}/safe-language")
    assert progress.status_code == 200
    assert "cannot yet determine" in progress.json()["text"]
    # Finish the pending reconciliation job without treating the uncertain result as failure.
    drain(fixture)


def test_revision_invalidates_receipt_and_queued_permit_before_release() -> None:
    fixture, _, operation_id = completed()
    receipt_id = verify(operation_id, 1).json()["receipt_id"]
    permit_id = authorize(receipt_id, 1).json()["permit_id"]
    assert queue(permit_id, 1).status_code == 200
    revision(fixture, 2, 16)
    blocked = publish(permit_id, 1)
    assert blocked.status_code == 409
    detail = client.get(f"/v1/receipts/{receipt_id}").json()
    permit = client.get(f"/v1/permits/{permit_id}").json()
    assert detail["receipt"]["invalidated_at"] is not None
    assert permit["permit"]["state"] == "INVALIDATED"
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert not any(item["event_name"] == "ClaimPublished" for item in history["events"])
    assert verify(operation_id, 2).status_code == 409
    drain(fixture)


def test_publication_revision_race_uses_named_barrier(monkeypatch: Any) -> None:
    import apps.api_controller.phase3_claim_service as service

    fixture, _, operation_id = completed()
    permit_id = authorize(verify(operation_id, 1).json()["receipt_id"], 1).json()["permit_id"]
    assert queue(permit_id, 1).status_code == 200
    barrier = Barrier(2, timeout=10)
    original = service._external_observations

    def held(*args: Any, **kwargs: Any) -> Any:
        observations = original(*args, **kwargs)
        barrier.wait()
        barrier.wait()
        return observations

    monkeypatch.setattr(service, "_external_observations", held)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(publish, permit_id, 1)
        barrier.wait()
        revision(fixture, 2, 16)
        barrier.wait()
        result = pending.result()
    assert result.status_code == 409
    assert client.get(f"/v1/permits/{permit_id}").json()["permit"]["state"] == "INVALIDATED"
    drain(fixture)


def test_changed_provider_version_invalidates_queued_permit() -> None:
    fixture, scenario_id, operation_id = completed()
    receipt_id = verify(operation_id, 1).json()["receipt_id"]
    receipt = client.get(f"/v1/receipts/{receipt_id}").json()["receipt"]
    permit_id = authorize(receipt_id, 1).json()["permit_id"]
    assert queue(permit_id, 1).status_code == 200
    predicates = receipt["predicates_json"]
    inject_concurrent_change(
        ProviderOperation.model_validate(
            {
                "scenario_id": str(scenario_id),
                "operation_id": str(uuid4()),
                "idempotency_key": f"concurrent:{uuid4()}",
                "request_hash": "concurrent",
                "action": "RESCHEDULE",
                "resource_key": predicates["resource_key"],
                "appointment_id": predicates["appointment_id"],
                "requested_start": "2026-10-01T15:00:00+05:00",
                "requested_end": "2026-10-01T16:00:00+05:00",
                "timezone": "Asia/Karachi",
            }
        )
    )
    blocked = publish(permit_id, 1)
    assert blocked.status_code == 409
    assert blocked.json()["type"].endswith("/fresh-evidence-required")
    assert client.get(f"/v1/permits/{permit_id}").json()["permit"]["state"] == "INVALIDATED"
    assert client.get(f"/v1/receipts/{receipt_id}").json()["receipt"]["invalidated_at"]
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    assert not any(item["event_name"] == "ClaimPublished" for item in history["events"])


def test_historical_and_current_claims_have_different_evidence() -> None:
    fixture, _, first_operation = completed()
    revision(fixture, 2, 16)
    drain(fixture)
    history = client.get(f"/v1/workflows/{fixture['workflow_id']}/history").json()
    current_id = UUID(
        next(item["id"] for item in history["operations"] if item["intent_revision"] == 2)
    )
    historical = verify(first_operation, 2, "HISTORICAL_EFFECT")
    current = verify(current_id, 2, "CURRENT_APPOINTMENT")
    assert historical.status_code == current.status_code == 201
    assert historical.json()["result"] == current.json()["result"] == "SATISFIED"
    historical_facts = client.get(f"/v1/receipts/{historical.json()['receipt_id']}").json()
    current_facts = client.get(f"/v1/receipts/{current.json()['receipt_id']}").json()
    assert "historical_start" in historical_facts["receipt"]["predicates_json"]
    assert "active_count" in current_facts["receipt"]["predicates_json"]
    assert authorize(historical.json()["receipt_id"], 2).status_code == 201
    assert authorize(current.json()["receipt_id"], 2).status_code == 201
