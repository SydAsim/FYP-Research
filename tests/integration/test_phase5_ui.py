"""Browser read models must honor durable commands and applicable evidence."""

from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from apps.api_controller.main import app

client = TestClient(app, raise_server_exceptions=False)


def fixture() -> dict[str, Any]:
    response = client.post("/internal/phase1/fixtures", json={"command_id": str(uuid4())})
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_call_start_is_idempotent_and_media_end_preserves_unresolved_business() -> None:
    resident_id = client.get("/v1/public/config").json()["synthetic_resident_id"]
    key = str(uuid4())
    request = {"consent": True, "resident_id": resident_id}
    first = client.post("/v1/calls", json=request, headers={"Idempotency-Key": key})
    replay = client.post("/v1/calls", json=request, headers={"Idempotency-Key": key})
    assert first.status_code == replay.status_code == 201
    call_id = first.json()["call_id"]
    assert replay.json()["call_id"] == call_id
    media = client.get(f"/v1/calls/{call_id}/media-token")
    assert media.status_code == 200
    assert media.json()["voice_agent_status"] == "UNAVAILABLE"
    changed = client.post(
        "/v1/calls",
        json={**request, "consent": False},
        headers={"Idempotency-Key": key},
    )
    assert changed.status_code == 422
    ending = client.post(f"/v1/calls/{call_id}/end", json={"command_id": str(uuid4())})
    assert ending.status_code == 200
    summary = client.get(f"/v1/calls/{call_id}/summary").json()
    assert summary["media_status"] == "ENDED"
    assert summary["business_resolution"] == "UNRESOLVED_RECOVERING"
    assert summary["receipt_id"] is None
    assert client.get(f"/v1/calls/{call_id}/media-token").status_code == 409


def test_summary_needs_current_revision_and_resource_bound_receipt() -> None:
    data = fixture()
    workflow_id = data["workflow_id"]
    first_revision = {
        "command_id": str(uuid4()),
        "expected_revision": 0,
        "change_class": "INITIAL",
        "desired_state": {
            "ticket_id": data["ticket_id"],
            "requested_start": "2026-11-02T15:00:00+05:00",
            "requested_end": "2026-11-02T16:00:00+05:00",
            "timezone": "Asia/Karachi",
        },
        "candidate_source": {
            "utterance_id": data["utterance_ids"][0],
            "model": "phase5-integration",
            "prompt_hash": "phase5-integration-v1",
            "transcript_version": 1,
        },
    }
    assert (
        client.post(f"/v1/workflows/{workflow_id}/revisions", json=first_revision).status_code
        == 201
    )
    prepared = client.post(
        "/v1/operations/appointments",
        json={
            "command_id": str(uuid4()),
            "workflow_id": workflow_id,
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase5:{uuid4()}",
        },
    )
    assert prepared.status_code == 202, prepared.text
    operation_id = prepared.json()["operation_id"]
    committed = client.post(
        f"/v1/operations/{operation_id}/commit-local",
        json={"command_id": str(uuid4())},
    )
    assert committed.status_code == 200
    appointment_id = committed.json()["appointment_id"]
    before = client.get(f"/v1/calls/{data['call_id']}/summary").json()
    assert before["business_resolution"] == "UNRESOLVED_RECOVERING"
    checked = client.post(
        "/internal/phase3/verifications",
        json={
            "command_id": str(uuid4()),
            "operation_id": operation_id,
            "expected_intent_revision": 1,
            "claim_type": "CURRENT_APPOINTMENT",
        },
    )
    assert checked.status_code == 201 and checked.json()["result"] == "SATISFIED"
    receipt_id = checked.json()["receipt_id"]
    verified = client.get(f"/v1/calls/{data['call_id']}/summary").json()
    assert verified["business_resolution"] == "RESOLVED_VERIFIED"
    assert verified["receipt_id"] == receipt_id
    appointment = client.get(f"/v1/appointments/{appointment_id}").json()["appointment"]
    assert appointment["current_receipt_id"] == receipt_id
    corrected = {
        **first_revision,
        "command_id": str(uuid4()),
        "expected_revision": 1,
        "change_class": "PARAMETER_CORRECTION",
        "desired_state": {
            **first_revision["desired_state"],
            "appointment_id": appointment_id,
            "requested_start": "2026-11-02T16:00:00+05:00",
            "requested_end": "2026-11-02T17:00:00+05:00",
        },
        "candidate_source": {
            **first_revision["candidate_source"],
            "utterance_id": data["utterance_ids"][1],
        },
    }
    assert client.post(f"/v1/workflows/{workflow_id}/revisions", json=corrected).status_code == 201
    after = client.get(f"/v1/calls/{data['call_id']}/summary").json()
    assert after["business_resolution"] != "RESOLVED_VERIFIED"
    assert after["receipt_id"] is None
    assert (
        client.get(f"/v1/appointments/{appointment_id}").json()["appointment"]["current_receipt_id"]
        is None
    )
    moved = client.post(
        "/v1/operations/appointments",
        json={
            "command_id": str(uuid4()),
            "workflow_id": workflow_id,
            "expected_intent_revision": 2,
            "expected_resource_version": appointment["version"],
            "idempotency_key": f"phase5-reschedule:{uuid4()}",
        },
    )
    assert moved.status_code == 202, moved.text
    move_id = moved.json()["operation_id"]
    committed_move = client.post(
        f"/v1/operations/{move_id}/commit-local", json={"command_id": str(uuid4())}
    )
    assert committed_move.status_code == 200, committed_move.text
    move_receipt = client.post(
        "/internal/phase3/verifications",
        json={
            "command_id": str(uuid4()),
            "operation_id": move_id,
            "expected_intent_revision": 2,
            "claim_type": "RESCHEDULED_APPOINTMENT",
        },
    )
    assert move_receipt.status_code == 201, move_receipt.text
    assert move_receipt.json()["result"] == "SATISFIED"
    assert move_receipt.json()["observed_resource_version"] == str(appointment["version"] + 1)
    claim = client.post(
        "/internal/phase3/claims",
        json={
            "command_id": str(uuid4()),
            "receipt_id": move_receipt.json()["receipt_id"],
            "expected_intent_revision": 2,
        },
    )
    assert claim.status_code == 201, claim.text
    permit_id = claim.json()["permit_id"]
    queued = client.post(
        f"/internal/phase3/permits/{permit_id}/queue",
        json={"command_id": str(uuid4()), "expected_intent_revision": 2},
    )
    assert queued.status_code == 200, queued.text
    published = client.post(
        f"/internal/phase3/permits/{permit_id}/publish",
        json={"command_id": str(uuid4()), "expected_intent_revision": 2},
    )
    assert published.status_code == 200, published.text
    assert "moved to" in published.json()["text"]
    final = client.get(f"/v1/calls/{data['call_id']}/summary").json()
    assert final["business_resolution"] == "RESOLVED_VERIFIED"
    assert final["receipt_id"] == move_receipt.json()["receipt_id"]


def test_note_and_draft_commands_are_durable_and_conflict_on_changed_request() -> None:
    data = fixture()
    note = {
        "command_id": str(uuid4()),
        "resident_id": data["resident_id"],
        "category": "ACCESS_INSTRUCTION",
        "note_text": "Call before entering the synthetic unit",
        "expected_resident_version": 0,
    }
    first = client.post("/v1/notes", json=note)
    replay = client.post("/v1/notes", json=note)
    assert first.status_code == replay.status_code == 201
    assert first.json()["note_id"] == replay.json()["note_id"]
    changed = client.post("/v1/notes", json={**note, "note_text": "Use side door"})
    assert changed.status_code == 409
    stale = client.post("/v1/notes", json={**note, "command_id": str(uuid4())})
    assert stale.status_code == 409
    prohibited = client.post(
        "/v1/notes",
        json={**note, "command_id": str(uuid4()), "note_text": "allergy information"},
    )
    assert prohibited.status_code == 422
    draft = {
        "command_id": str(uuid4()),
        "name": f"Phase 5 draft {uuid4()}",
        "fixture_version": "synthetic-maintenance-v1",
        "final_intent": "Maintenance appointment at corrected time",
        "correction_phase": "P8",
        "provider_behavior": "HIDDEN_COMMIT",
        "fault_family": "RESPONSE_LOSS",
        "arms": ["B3", "P1"],
        "seeds": [1, 2],
        "oracle_required": True,
        "model_profile": "strict-cascade",
    }
    created = client.post("/v1/evaluation/runs", json=draft)
    retry = client.post("/v1/evaluation/runs", json=draft)
    assert created.status_code == retry.status_code == 201
    assert created.json()["run_id"] == retry.json()["run_id"]
    changed_draft = client.post("/v1/evaluation/runs", json={**draft, "correction_phase": "P7"})
    assert changed_draft.status_code == 409
    run = client.get(f"/v1/evaluation/runs/{created.json()['run_id']}").json()
    assert run["run"]["status"] == "DRAFT"
    assert run["executions"] == []
