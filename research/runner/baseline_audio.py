"""Isolated B0-B2 playout counterfactuals through the same provider and TTS ports.

Client acknowledgements are scripted transport evidence, never physical hearing.
No unpermitted segment is routed to a real call or the product audio publisher.
"""

import hashlib
import io
import json
import wave
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from apps.voice_worker.cascade import DeterministicToneTTS
from packages.provider_adapters.simulator import operation_status, resource_state, send_operation
from research.arms import Arm
from research.provider_simulator.store import truth_log
from research.replay.phase2_decisive import API, SIMULATOR, call
from research.run_store import baseline_events_for, record_baseline_event
from research.runner.baselines import _accept, _observation, _post, _request
from research.scenario_dsl.models import Barrier, ScenarioCase, stable_hash


def segment(case: ScenarioCase, *, final: bool) -> dict[str, Any]:
    start = case.final_start if final else case.initial_start
    lead = (
        "Your maintenance appointment has been moved to "
        if final
        else "Your maintenance appointment is confirmed for "
    )
    clock = f"{start.hour % 12 or 12}:{start.minute:02d} {'AM' if start.hour < 12 else 'PM'}"
    text = f"{lead}{clock} on {start.date().isoformat()} ({case.timezone})."
    audio = DeterministicToneTTS().synthesize(text)
    with wave.open(io.BytesIO(audio), "rb") as reader:
        frames, rate = reader.getnframes(), reader.getframerate()
    return {
        "segment_id": str(uuid4()),
        "segment_text": text,
        "text_hash": stable_hash(text),
        "content_hash": stable_hash(text),
        "audio_hash": hashlib.sha256(audio).hexdigest(),
        "duration_ms": frames * 1000 // rate,
        "frame_count": frames,
        "word_timeline_json": [{"word": word} for word in text.split()],
        "research_unpermitted": True,
    }


def run_baseline_audio(
    execution_id: UUID,
    case: ScenarioCase,
    arm: Arm,
    on_boundary: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    """Run baseline effects; the outer paired runner owns failure records and barriers."""
    if arm not in (Arm.B0, Arm.B1, Arm.B2):
        raise ValueError("Baseline audio requires B0, B1, or B2")
    ordinal = 0
    trace_id = str(uuid4())

    def observed(kind: str, raw: dict[str, Any], normalized: dict[str, Any]) -> None:
        nonlocal ordinal
        ordinal += 1
        record_baseline_event(execution_id, ordinal, kind, raw, normalized, trace_id)

    def write(payload: dict[str, Any]) -> dict[str, Any]:
        observed("REQUEST_SENT", payload, {"action": payload["action"], "sent": True})
        response = send_operation(payload)
        observed("PROVIDER_RESPONSE", response.raw, _observation(response))
        if response.status != 200 or not response.body:
            raise AssertionError("Fault-free baseline audio provider write failed")
        if arm is not Arm.B0:
            status = operation_status(UUID(payload["scenario_id"]), UUID(payload["operation_id"]))
            observed("STATUS_LOOKUP", status.raw, _observation(status))
            if not status.body or not status.body.get("authoritative"):
                raise AssertionError("Baseline status is not authoritative")
        return response.body

    scenario_id = UUID(_post(SIMULATOR, "/internal/scenarios", {})["scenario_id"])
    fixture = _post(API, "/internal/phase1/fixtures", {"command_id": str(uuid4())})
    _accept(fixture, case, 1)
    first_id = uuid4()
    response = write(
        _request(
            scenario_id,
            first_id,
            f"baseline-audio:{execution_id}:first",
            "CREATE",
            fixture["resource_key"],
            start=case.initial_start,
            timezone=case.timezone,
        )
    )
    facts = response["facts"]
    first = segment(case, final=False)
    client: list[dict[str, Any]] = []

    def client_event(detail: dict[str, Any], kind: str, *, partial: bool = False) -> dict[str, Any]:
        event = {
            "event_id": str(uuid4()),
            "segment_id": detail["segment_id"],
            "event_type": kind,
            "client_time": datetime.now(UTC).isoformat(),
            "played_ms": 0 if kind == "STARTED" else 500 if partial else detail["duration_ms"],
            "last_frame": 0 if kind == "STARTED" else 8000 if partial else detail["frame_count"],
            "last_word_index": 0
            if kind == "STARTED"
            else 2
            if partial
            else len(detail["word_timeline_json"]),
        }
        observed("CLIENT_PLAYBACK", event, event)
        client.append({"request": event, "response": {**event, "repair_obligation_id": None}})
        return event

    boundary = case.correction_barrier
    if boundary in (Barrier.P6, Barrier.P7):
        event = {
            "event_id": first["segment_id"],
            "event_type": "GENERATED" if boundary is Barrier.P6 else "PUBLISHED",
        }
        observed("AUDIO_BOUNDARY", {**event, **first}, event)
    else:
        client_event(first, "STARTED")
        event = client_event(
            first,
            "PROGRESS" if boundary is Barrier.P8 else "COMPLETED",
            partial=boundary is Barrier.P8,
        )
    on_boundary(event)
    if boundary is Barrier.P8:
        client_event(first, "INTERRUPTED", partial=True)
    corrected_at = datetime.now(UTC).isoformat()
    accepted = _accept(fixture, case, 2)
    final_id = uuid4()
    if arm is not Arm.B2:
        write(
            _request(
                scenario_id,
                final_id,
                f"baseline-audio:{execution_id}:cancel",
                "CANCEL",
                fixture["resource_key"],
                appointment_id=facts["appointment_id"],
                expected_version=int(facts["version"]),
                timezone=case.timezone,
            )
        )
        final_id = uuid4()
    write(
        _request(
            scenario_id,
            final_id,
            f"baseline-audio:{execution_id}:final",
            "RESCHEDULE" if arm is Arm.B2 else "CREATE",
            fixture["resource_key"],
            start=case.final_start,
            timezone=case.timezone,
            appointment_id=facts["appointment_id"] if arm is Arm.B2 else None,
            expected_version=int(facts["version"]) if arm is Arm.B2 else None,
        )
    )
    if arm is not Arm.B0:
        read = resource_state(scenario_id, final_id, fixture["resource_key"])
        observed("POSTCONDITION_READ", read.raw, _observation(read))
        if not read.body or not read.body.get("authoritative"):
            raise AssertionError("Baseline final state is not authoritative")
    corrected = segment(case, final=True)
    client_event(corrected, "STARTED")
    client_event(corrected, "COMPLETED")
    return {
        "scenario_id": str(scenario_id),
        "workflow_id": fixture["workflow_id"],
        "call_id": fixture["call_id"],
        "research_arm": arm.value,
        "boundary": boundary.value,
        "prerecorded_audio_sha256": case.audio_hash,
        "correction": {**accepted, "audio_hash": case.audio_hash},
        "correction_scripted_at": corrected_at,
        "client_playback_evidence": client,
        "first_claim": {"receipt": None, "permit": None, "scheduled": first},
        "corrected_claim": {"receipt": None, "permit": None, "scheduled": corrected},
        "stale_segment": first,
        "corrected_segment": corrected,
        "repair_open": None,
        "repair_authorized": None,
        "repair_played": None,
        "normalized_timeline": call(API, "GET", f"/v1/workflows/{fixture['workflow_id']}/history")[
            "events"
        ],
        "simulator_truth_log": json.loads(json.dumps(truth_log(scenario_id), default=str)),
        "baseline_events": baseline_events_for(execution_id),
        "exposure_scope": "scripted_client_acknowledgements_not_physical_hearing",
    }
