"""Prerecorded correction at P6-P9 speech scheduling/exposure boundaries."""

import base64
import hashlib
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from research.replay.livekit_token import dev_room_token
from research.replay.phase2_decisive import API, SIMULATOR, WORKER, call
from research.scenario_dsl.models import Barrier

VOICE = os.environ.get("PHASE4_VOICE_URL", "http://127.0.0.1:8001").rstrip("/")
FIXTURE = Path(__file__).parents[1] / "fixtures" / "audio" / "p8_correction.wav"


def _post(base: str, path: str, **fields: Any) -> dict[str, Any]:
    return call(base, "POST", path, fields)


def _drain(workflow_id: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for _ in range(20):
        history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
        active = False
        for operation in history["operations"]:
            result = _post(WORKER, "/internal/phase2/step", operation_id=operation["id"])
            steps.append(result)
            active = active or result["action"] != "idle"
        if not active:
            return steps
    raise AssertionError("Durable worker did not reach idle")


def _claim_audio(
    operation_id: str, revision: int, repair_id: str | None = None, *, stage: bool = False
) -> dict[str, Any]:
    receipt = _post(
        API,
        "/internal/phase3/verifications",
        command_id=str(uuid4()),
        operation_id=operation_id,
        expected_intent_revision=revision,
        claim_type="CURRENT_APPOINTMENT" if revision == 1 else "RESCHEDULED_APPOINTMENT",
    )
    assert receipt["result"] == "SATISFIED", receipt
    permit = _post(
        API,
        "/internal/phase3/claims",
        command_id=str(uuid4()),
        receipt_id=receipt["receipt_id"],
        expected_intent_revision=revision,
    )
    _post(
        API,
        f"/internal/phase3/permits/{permit['permit_id']}/queue",
        command_id=str(uuid4()),
        expected_intent_revision=revision,
    )
    scheduled = _post(
        VOICE,
        "/internal/phase6/claim/stage" if stage else "/internal/phase4/cascade/schedule",
        permit_id=permit["permit_id"],
        expected_intent_revision=revision,
        repair_obligation_id=repair_id,
    )
    assert scheduled["state"] == ("GENERATED" if stage else "PUBLISHED"), scheduled
    return {"receipt": receipt, "permit": permit, "scheduled": scheduled}


def _b3_audio(workflow_id: str, revision: int, *, stage: bool = False) -> dict[str, Any]:
    scheduled = _post(
        VOICE,
        "/internal/phase6/b3/stage" if stage else "/internal/phase6/b3/schedule",
        workflow_id=workflow_id,
        expected_intent_revision=revision,
    )
    assert scheduled["state"] == ("GENERATED" if stage else "PUBLISHED"), scheduled
    return {"receipt": None, "permit": None, "scheduled": scheduled}


def _play(
    call_id: str,
    segment_id: str,
    kind: str,
    *,
    evidence: list[dict[str, Any]] | None = None,
    **progress: int,
) -> dict[str, Any]:
    request = {
        "event_id": str(uuid4()),
        "segment_id": segment_id,
        "event_type": kind,
        "client_time": datetime.now(UTC).isoformat(),
        "played_ms": progress.get("played_ms", 0),
        "last_frame": progress.get("last_frame", 0),
        "last_word_index": progress.get("last_word_index", 0),
    }
    response = _post(
        API,
        f"/v1/calls/{call_id}/playback-events",
        **request,
    )
    if evidence is not None:
        evidence.append({"request": request, "response": response})
    return response


def run(
    *,
    research_arm: Literal["B3", "P1", "P2"] | None = None,
    on_p8_progress: Callable[[dict[str, Any]], None] | None = None,
    boundary: Barrier = Barrier.P8,
    on_barrier: Callable[[dict[str, Any]], None] | None = None,
    on_repair_open: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if boundary not in (Barrier.P6, Barrier.P7, Barrier.P8, Barrier.P9):
        raise ValueError("Speech replay supports only P6-P9")
    fixture_meta = json.loads(FIXTURE.with_suffix(".json").read_text(encoding="utf-8"))
    audio = FIXTURE.read_bytes()
    assert hashlib.sha256(audio).hexdigest() == fixture_meta["sha256"]
    scenario = _post(SIMULATOR, "/internal/scenarios")
    fixture = _post(
        API,
        "/internal/phase1/fixtures",
        command_id=str(uuid4()),
        research_arm=research_arm,
    )
    workflow_id, call_id = fixture["workflow_id"], fixture["call_id"]
    client_playback_evidence: list[dict[str, Any]] = []
    _post(
        API,
        f"/v1/workflows/{workflow_id}/revisions",
        command_id=str(uuid4()),
        expected_revision=0,
        change_class="INITIAL",
        desired_state={
            "ticket_id": fixture["ticket_id"],
            "requested_start": "2026-10-01T15:00:00+05:00",
            "requested_end": "2026-10-01T16:00:00+05:00",
            "timezone": "Asia/Karachi",
        },
        candidate_source={
            "utterance_id": fixture["utterance_ids"][0],
            "model": "phase4-initial-fixture",
            "prompt_hash": hashlib.sha256(b"phase4-initial-fixture-v1").hexdigest(),
            "transcript_version": 1,
        },
    )
    created = _post(
        API,
        "/internal/phase2/operations",
        command_id=str(uuid4()),
        workflow_id=workflow_id,
        scenario_id=scenario["scenario_id"],
        expected_intent_revision=1,
        expected_resource_version=0,
        idempotency_key=f"phase4-p8:{uuid4()}",
    )
    initial_steps = _drain(workflow_id)
    first = (
        _b3_audio(workflow_id, 1, stage=boundary is Barrier.P6)
        if research_arm == "B3"
        else _claim_audio(created["operation_id"], 1, stage=boundary is Barrier.P6)
    )
    stale_id = first["scheduled"]["segment_id"]
    stale_detail = call(API, "GET", f"/v1/audio-segments/{stale_id}")
    acknowledged: dict[str, Any] | None = None
    interrupted: dict[str, Any] | None = None
    if boundary in (Barrier.P6, Barrier.P7):
        expected_stage = "GENERATED" if boundary is Barrier.P6 else "PUBLISHED"
        assert stale_detail["state"] == expected_stage
        if on_barrier is not None:
            on_barrier({"event_id": stale_id, "event_type": expected_stage, "segment_id": stale_id})
    else:
        _play(call_id, stale_id, "STARTED", evidence=client_playback_evidence)
        if boundary is Barrier.P8:
            acknowledged = _play(
                call_id,
                stale_id,
                "PROGRESS",
                evidence=client_playback_evidence,
                played_ms=min(500, stale_detail["duration_ms"]),
                last_frame=min(8000, stale_detail["frame_count"]),
                last_word_index=min(2, len(stale_detail["word_timeline_json"])),
            )
            event = client_playback_evidence[-1]["request"]
            if on_p8_progress is not None:
                on_p8_progress(event)
            if on_barrier is not None:
                on_barrier(event)
            interrupted = _play(
                call_id,
                stale_id,
                "INTERRUPTED",
                evidence=client_playback_evidence,
                played_ms=min(500, stale_detail["duration_ms"]),
                last_frame=min(8000, stale_detail["frame_count"]),
                last_word_index=min(2, len(stale_detail["word_timeline_json"])),
            )
        else:
            acknowledged = _play(
                call_id,
                stale_id,
                "COMPLETED",
                evidence=client_playback_evidence,
                played_ms=stale_detail["duration_ms"],
                last_frame=stale_detail["frame_count"],
                last_word_index=len(stale_detail["word_timeline_json"]),
            )
            if on_barrier is not None:
                on_barrier(client_playback_evidence[-1]["request"])
    correction_scripted_at = datetime.now(UTC).isoformat()
    correction = _post(
        VOICE,
        "/internal/phase4/cascade/replay",
        call_id=call_id,
        workflow_id=workflow_id,
        turn_key=f"{boundary.value.lower()}:{uuid4()}",
        audio_base64=base64.b64encode(audio).decode("ascii"),
        transcript=fixture_meta["transcript"],
        desired_state={
            "ticket_id": fixture["ticket_id"],
            "requested_start": "2026-10-01T16:00:00+05:00",
            "requested_end": "2026-10-01T17:00:00+05:00",
            "timezone": "Asia/Karachi",
        },
        expected_revision=1,
        change_class="PARAMETER_CORRECTION",
        interrupted_segment_id=stale_id if boundary is Barrier.P8 else None,
    )
    assert correction["revision"] == 2, correction
    stopped = call(API, "GET", f"/v1/audio-segments/{stale_id}")
    expected_state = {
        Barrier.P6: "CANCELLED",
        Barrier.P7: "CANCELLED",
        Barrier.P8: "STOPPED",
        Barrier.P9: "COMPLETED",
    }
    assert stopped["state"] == expected_state[boundary], stopped
    history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
    required = [e for e in history["events"] if e["event_name"] == "RepairRequired"]
    repair_id: str | None = None
    repair_open: dict[str, Any] | None = None
    if research_arm in ("B3", "P1") or boundary in (Barrier.P6, Barrier.P7):
        assert not required, required
    else:
        assert len(required) == 1, required
        repair_id = required[0]["payload"]["repair_obligation_id"]
        repair_open = call(API, "GET", f"/v1/repairs/{repair_id}")
        assert repair_open["state"] == "OPEN"
        expected_frame = 8000 if boundary is Barrier.P8 else stale_detail["frame_count"]
        assert repair_open["played_span_json"]["last_frame"] == expected_frame
    if acknowledged is not None:
        assert acknowledged["repair_obligation_id"] is None
    cache_loss = on_repair_open(workflow_id) if on_repair_open else None
    correction_steps = _drain(workflow_id)
    history = call(API, "GET", f"/v1/workflows/{workflow_id}/history")
    operation2 = next(o for o in history["operations"] if o["intent_revision"] == 2)
    corrected = (
        _b3_audio(workflow_id, 2)
        if research_arm == "B3"
        else _claim_audio(operation2["id"], 2, repair_id)
    )
    corrected_id = corrected["scheduled"]["segment_id"]
    repair_authorized = call(API, "GET", f"/v1/repairs/{repair_id}") if repair_id else None
    if repair_authorized is not None:
        assert repair_authorized["state"] == "REPAIR_AUTHORIZED"
    _play(call_id, corrected_id, "STARTED", evidence=client_playback_evidence)
    livekit_sent = None
    if os.environ.get("PHASE4_LIVEKIT_SMOKE") == "true" and research_arm != "B3":
        livekit_sent = _post(
            VOICE,
            "/internal/phase4/livekit/publish",
            segment_id=corrected_id,
            expected_intent_revision=2,
            room_token=dev_room_token(f"phase4-{call_id}"),
        )
        assert livekit_sent["state"] == "SENT", livekit_sent
    detail = call(API, "GET", f"/v1/audio-segments/{corrected_id}")
    completed = _play(
        call_id,
        corrected_id,
        "COMPLETED",
        evidence=client_playback_evidence,
        played_ms=detail["duration_ms"],
        last_frame=detail["frame_count"],
        last_word_index=len(detail["word_timeline_json"]),
    )
    repair_played = call(API, "GET", f"/v1/repairs/{repair_id}") if repair_id else None
    if repair_played is not None:
        assert repair_played["state"] == "REPAIR_PLAYED", repair_played
    truth = call(SIMULATOR, "GET", f"/internal/scenarios/{scenario['scenario_id']}/truth")
    assert [entry["action"] for entry in truth["commits"]] == ["CREATE", "RESCHEDULE"]
    assert truth["commits"][-1]["after_facts"]["starts_at"] == "2026-10-01T11:00:00+00:00"
    result = {
        "scenario_id": scenario["scenario_id"],
        "boundary": boundary.value,
        "research_arm": research_arm,
        "workflow_id": workflow_id,
        "call_id": call_id,
        "prerecorded_audio_sha256": fixture_meta["sha256"],
        "correction_scripted_at": correction_scripted_at,
        "client_playback_evidence": client_playback_evidence,
        "initial_steps": initial_steps,
        "first_claim": first,
        "stale_segment": stopped,
        "acknowledged_partial_playback": acknowledged,
        "interrupted_playback": interrupted,
        "correction": correction,
        "repair_open": repair_open,
        "correction_steps": correction_steps,
        "corrected_claim": corrected,
        "corrected_segment": detail,
        "repair_authorized": repair_authorized,
        "corrected_playback": completed,
        "livekit_sent": livekit_sent,
        "repair_played": repair_played,
        "redis_repair_evidence": cache_loss,
        "normalized_timeline": history["events"],
        "simulator_truth_log": truth["commits"],
    }
    output = os.environ.get("PHASE4_REPLAY_OUTPUT")
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
