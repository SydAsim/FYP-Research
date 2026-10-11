"""Audio release, exposure, repair, and restart-safe facts in PostgreSQL."""

import base64
import hashlib
import io
import wave
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from apps.api_controller.main import app
from apps.durable_worker.phase2 import step
from research.provider_simulator.models import ProviderOperation, ScenarioConfig
from research.provider_simulator.store import create_scenario, inject_concurrent_change

client = TestClient(app, raise_server_exceptions=False)


def post(path: str, payload: dict[str, Any], expected: int) -> dict[str, Any]:
    response = client.post(path, json=payload)
    assert response.status_code == expected, response.text
    return dict(response.json())


def fixture() -> tuple[dict[str, Any], UUID]:
    scenario_id = create_scenario(ScenarioConfig())
    item = post("/internal/phase1/fixtures", {"command_id": str(uuid4())}, 201)
    item["scenario_id"] = str(scenario_id)
    revision(item, 1, 15)
    operation = post(
        "/internal/phase2/operations",
        {
            "command_id": str(uuid4()),
            "workflow_id": item["workflow_id"],
            "scenario_id": str(scenario_id),
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase4:{uuid4()}",
        },
        202,
    )
    assert step(operation_id=UUID(operation["operation_id"]))["action"] == "dispatch"
    assert step(operation_id=UUID(operation["operation_id"]))["action"] == "reconcile"
    return item, UUID(operation["operation_id"])


def revision(item: dict[str, Any], number: int, hour: int) -> dict[str, Any]:
    return post(
        f"/v1/workflows/{item['workflow_id']}/revisions",
        {
            "command_id": str(uuid4()),
            "expected_revision": number - 1,
            "change_class": "INITIAL" if number == 1 else "PARAMETER_CORRECTION",
            "desired_state": {
                "ticket_id": item["ticket_id"],
                "requested_start": f"2026-10-01T{hour:02d}:00:00+05:00",
                "requested_end": f"2026-10-01T{hour + 1:02d}:00:00+05:00",
                "timezone": "Asia/Karachi",
            },
            "candidate_source": {
                "utterance_id": item["utterance_ids"][number - 1],
                "model": "phase4-scripted-llm",
                "prompt_hash": f"p4:{number}",
                "transcript_version": 1,
            },
        },
        201,
    )


def wav_bytes() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(bytes(32000 * 2))
    return output.getvalue()


def audio_for(
    operation_id: UUID, revision_number: int, repair_obligation_id: str | None = None
) -> dict[str, Any]:
    receipt = post(
        "/internal/phase3/verifications",
        {
            "command_id": str(uuid4()),
            "operation_id": str(operation_id),
            "expected_intent_revision": revision_number,
            "claim_type": "RESCHEDULED_APPOINTMENT"
            if revision_number == 2
            else "CURRENT_APPOINTMENT",
        },
        201,
    )
    assert receipt["result"] == "SATISFIED"
    permit = post(
        "/internal/phase3/claims",
        {
            "command_id": str(uuid4()),
            "receipt_id": receipt["receipt_id"],
            "expected_intent_revision": revision_number,
        },
        201,
    )
    permit_id = permit["permit_id"]
    post(
        f"/internal/phase3/permits/{permit_id}/queue",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": revision_number,
        },
        200,
    )
    suffix = f"?repair_obligation_id={repair_obligation_id}" if repair_obligation_id else ""
    synthesis = client.get(f"/internal/phase4/permits/{permit_id}/synthesis-input{suffix}")
    assert synthesis.status_code == 200, synthesis.text
    data = wav_bytes()
    prepared = post(
        "/internal/phase4/audio-segments",
        {
            "command_id": str(uuid4()),
            "permit_id": permit_id,
            "expected_intent_revision": revision_number,
            "audio_base64": base64.b64encode(data).decode("ascii"),
            "audio_hash": hashlib.sha256(data).hexdigest(),
            "text_hash": synthesis.json()["text_hash"],
            "tts_model_id": "phase4-test-tone",
            "tts_config_hash": hashlib.sha256(b"phase4-test-tone").hexdigest(),
            "repair_obligation_id": repair_obligation_id,
        },
        201,
    )
    segment_id = prepared["segment_id"]
    post(
        f"/internal/phase4/audio-segments/{segment_id}/queue",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": revision_number,
        },
        200,
    )
    return {"permit_id": permit_id, "segment_id": segment_id, **prepared}


def release(segment_id: str, revision_number: int) -> dict[str, Any]:
    return post(
        f"/internal/phase4/audio-segments/{segment_id}/release",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": revision_number,
        },
        200,
    )


def playback(
    call_id: str,
    segment_id: str,
    kind: str,
    played_ms: int = 0,
    last_frame: int = 0,
    last_word_index: int = 0,
    event_id: str | None = None,
) -> Any:
    return client.post(
        f"/v1/calls/{call_id}/playback-events",
        json={
            "event_id": event_id or str(uuid4()),
            "segment_id": segment_id,
            "event_type": kind,
            "client_time": datetime.now(UTC).isoformat(),
            "played_ms": played_ms,
            "last_frame": last_frame,
            "last_word_index": last_word_index,
        },
    )


def drain(item: dict[str, Any]) -> None:
    for _ in range(12):
        history = client.get(f"/v1/workflows/{item['workflow_id']}/history").json()
        active = False
        for operation in history["operations"]:
            active = step(operation_id=UUID(operation["id"]))["action"] != "idle" or active
        if not active:
            return
    raise AssertionError("Worker did not reach idle")


def test_queued_stale_audio_never_starts() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    revision(item, 2, 16)
    response = playback(item["call_id"], segment["segment_id"], "STARTED")
    assert response.status_code == 409
    detail = client.get(f"/v1/audio-segments/{segment['segment_id']}").json()
    assert detail["state"] == "CANCELLED"
    with_session = client.get(f"/v1/workflows/{item['workflow_id']}/history").json()
    assert not any(event["event_name"] == "RepairRequired" for event in with_session["events"])
    drain(item)


def test_played_stale_span_creates_exact_durable_repair() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    release(segment["segment_id"], 1)
    assert playback(item["call_id"], segment["segment_id"], "STARTED").status_code == 202
    progress = playback(item["call_id"], segment["segment_id"], "PROGRESS", 1500, 24000, 8)
    assert progress.status_code == 202, progress.text
    revision(item, 2, 16)
    detail = client.get(f"/v1/audio-segments/{segment['segment_id']}").json()
    assert detail["state"] == "STOPPED"
    assert client.get(f"/v1/audio-segments/{segment['segment_id']}/audio").status_code == 409
    history = client.get(f"/v1/workflows/{item['workflow_id']}/history").json()
    event = next(event for event in history["events"] if event["event_name"] == "RepairRequired")
    repair = client.get(f"/v1/repairs/{event['payload']['repair_obligation_id']}").json()
    assert repair["state"] == "OPEN"
    assert repair["played_span_json"]["last_frame"] == 24000
    assert repair["played_span_json"]["last_word_index"] == 8
    assert len(repair["played_span_json"]["words"]) == 8
    drain(item)


def test_late_ack_after_revision_creates_repair_and_corrected_playback_closes_it() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    release(segment["segment_id"], 1)
    assert playback(item["call_id"], segment["segment_id"], "STARTED").status_code == 202
    revision(item, 2, 16)
    late = playback(item["call_id"], segment["segment_id"], "PROGRESS", 1500, 24000, 8)
    assert late.status_code == 202, late.text
    obligation_id = late.json()["repair_obligation_id"]
    assert obligation_id
    drain(item)
    history = client.get(f"/v1/workflows/{item['workflow_id']}/history").json()
    revised_operation = UUID(
        next(row["id"] for row in history["operations"] if row["intent_revision"] == 2)
    )
    repair_audio = audio_for(revised_operation, 2, obligation_id)
    release(repair_audio["segment_id"], 2)
    assert playback(item["call_id"], repair_audio["segment_id"], "STARTED").status_code == 202
    pending = client.get(f"/v1/repairs/{obligation_id}").json()
    assert pending["state"] == "REPAIR_AUTHORIZED"
    completed = playback(
        item["call_id"],
        repair_audio["segment_id"],
        "COMPLETED",
        repair_audio["duration_ms"],
        repair_audio["frame_count"],
        repair_audio["word_count"],
    )
    assert completed.status_code == 202, completed.text
    assert client.get(f"/v1/repairs/{obligation_id}").json()["state"] == "REPAIR_PLAYED"


def test_backchannel_resume_rechecks_evidence_and_media_end_preserves_jobs() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    release(segment["segment_id"], 1)
    assert playback(item["call_id"], segment["segment_id"], "STARTED").status_code == 202
    assert (
        playback(item["call_id"], segment["segment_id"], "INTERRUPTED", 500, 8000, 2).status_code
        == 202
    )
    resumed = post(
        f"/internal/phase4/audio-segments/{segment['segment_id']}/resume",
        {
            "command_id": str(uuid4()),
            "expected_intent_revision": 1,
        },
        200,
    )
    assert resumed["resume_frame"] == 8000
    end = post(f"/v1/calls/{item['call_id']}/end", {"command_id": str(uuid4())}, 200)
    assert end["media_status"] == "ENDED"
    # Media closure is separate from durable reconciliation and workflow resolution.
    assert client.get(f"/v1/workflows/{item['workflow_id']}/history").status_code == 200


def test_backchannel_resume_rejects_changed_provider_version() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    release(segment["segment_id"], 1)
    assert playback(item["call_id"], segment["segment_id"], "STARTED").status_code == 202
    assert (
        playback(item["call_id"], segment["segment_id"], "INTERRUPTED", 500, 8000, 2).status_code
        == 202
    )
    detail = client.get(f"/v1/permits/{segment['permit_id']}").json()
    predicates = detail["claim"]["semantic_predicates_json"]
    inject_concurrent_change(
        ProviderOperation.model_validate(
            {
                "scenario_id": item["scenario_id"],
                "operation_id": str(uuid4()),
                "idempotency_key": f"phase4-concurrent:{uuid4()}",
                "request_hash": "phase4-concurrent",
                "action": "RESCHEDULE",
                "resource_key": predicates["resource_key"],
                "appointment_id": predicates["appointment_id"],
                "requested_start": "2026-10-01T15:00:00+05:00",
                "requested_end": "2026-10-01T16:00:00+05:00",
                "timezone": "Asia/Karachi",
            }
        )
    )
    blocked = client.post(
        f"/internal/phase4/audio-segments/{segment['segment_id']}/resume",
        json={"command_id": str(uuid4()), "expected_intent_revision": 1},
    )
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["type"].endswith("/fresh-evidence-required")
    assert client.get(f"/v1/audio-segments/{segment['segment_id']}").json()["state"] == "STOPPED"


def test_media_end_does_not_cancel_pending_external_operation() -> None:
    scenario_id = create_scenario(ScenarioConfig())
    item = post("/internal/phase1/fixtures", {"command_id": str(uuid4())}, 201)
    revision(item, 1, 15)
    prepared = post(
        "/internal/phase2/operations",
        {
            "command_id": str(uuid4()),
            "workflow_id": item["workflow_id"],
            "scenario_id": str(scenario_id),
            "expected_intent_revision": 1,
            "expected_resource_version": 0,
            "idempotency_key": f"phase4-disconnect:{uuid4()}",
        },
        202,
    )
    post(f"/v1/calls/{item['call_id']}/end", {"command_id": str(uuid4())}, 200)
    assert step(operation_id=UUID(prepared["operation_id"]))["action"] == "dispatch"
    assert step(operation_id=UUID(prepared["operation_id"]))["action"] == "reconcile"
    operation = client.get(f"/v1/operations/{prepared['operation_id']}").json()["operation"]
    assert operation["effect_knowledge"] == "PRESENT"
    history = client.get(f"/v1/workflows/{item['workflow_id']}/history").json()
    assert history["current_revision"] == 1


def test_playback_event_id_retries_exactly_and_rejects_changed_facts() -> None:
    item, operation_id = fixture()
    segment = audio_for(operation_id, 1)
    release(segment["segment_id"], 1)
    event = {
        "event_id": str(uuid4()),
        "segment_id": segment["segment_id"],
        "event_type": "STARTED",
        "client_time": datetime.now(UTC).isoformat(),
        "played_ms": 0,
        "last_frame": 0,
        "last_word_index": 0,
    }
    path = f"/v1/calls/{item['call_id']}/playback-events"
    first = client.post(path, json=event)
    retry = client.post(path, json=event)
    assert first.status_code == retry.status_code == 202
    assert first.json() == retry.json()
    changed = client.post(path, json={**event, "played_ms": 1})
    assert changed.status_code == 409
    assert changed.json()["type"].endswith("/event-id-conflict")
