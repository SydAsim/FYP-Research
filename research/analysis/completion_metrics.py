"""Secondary endpoint and causal timestamp evidence; no Phase 7 inference."""

import json
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from research.oracle.grade import PlaybackAck, _state_at
from research.run_store import connection
from research.scenario_dsl.models import stable_hash


def timeline_snapshot(workflow_id: str) -> dict[str, Any]:
    with connection() as conn:
        events = conn.execute(
            "SELECT id,event_name,workflow_sequence,intent_revision,operation_id,occurred_at,"
            "trace_id,payload FROM workflow_events WHERE workflow_id=%s ORDER BY workflow_sequence",
            (UUID(workflow_id),),
        ).fetchall()
        receipts = conn.execute(
            "SELECT to_jsonb(t) AS facts FROM verification_receipts t WHERE workflow_id=%s",
            (UUID(workflow_id),),
        ).fetchall()
        permits = conn.execute(
            "SELECT to_jsonb(t) AS facts FROM claim_permits t WHERE workflow_id=%s",
            (UUID(workflow_id),),
        ).fetchall()
    return cast(
        dict[str, Any],
        json.loads(
            json.dumps(
                {
                    "workflow_id": workflow_id,
                    "events": events,
                    "receipts": [r["facts"] for r in receipts],
                    "permits": [r["facts"] for r in permits],
                },
                default=str,
            )
        ),
    )


def secondary_metrics(
    execution: dict[str, Any],
    timeline: dict[str, Any],
    version: str = "phase6-secondary-metrics-v2",
) -> dict[str, Any]:
    trace = execution.get("trace", execution)
    truth = trace.get("simulator_truth_log", execution.get("simulator_truth", []))
    acks = execution.get("playback_acks")
    if acks is None:
        acks = [execution["playback_ack"]] if execution.get("playback_ack") else []
    played = [PlaybackAck.model_validate(row) for row in acks if row["played_ms"] > 0]
    correction_text = trace.get("correction_scripted_at")
    correction = datetime.fromisoformat(correction_text) if correction_text else None
    stale = sum(
        ack.intent_revision < 2 and correction is not None and ack.played_at >= correction
        for ack in played
    )
    cancellations = [ack for ack in played if "CANCEL" in ack.claim_type]
    false_cancellations = sum(
        any(_state_at(truth, moment) for moment in (ack.released_at, ack.played_at))
        for ack in cancellations
    )
    events = timeline["events"]

    def event_time(name: str, revision: int | None = None) -> str | None:
        return next(
            (
                e["occurred_at"]
                for e in events
                if e["event_name"] == name
                and (revision is None or e["intent_revision"] == revision)
            ),
            None,
        )

    def duration(start: str | None, end: str | None, reason: str) -> dict[str, Any]:
        if start is None or end is None:
            return {"duration_ms": None, "status": "NOT_OBSERVED", "reason": reason}
        delta = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() * 1000
        if delta < 0:
            return {
                "duration_ms": None,
                "status": "NOT_COMPARABLE",
                "reason": "event preceded anchor; no negative latency "
                "or synchronized-hearing inference",
            }
        return {"duration_ms": round(delta, 3), "status": "OBSERVED", "reason": None}

    revision = 2 if correction else 1
    accepted = event_time("IntentRevisionAccepted", revision)
    useful = next(
        (ack.played_at.isoformat() for ack in played if ack.intent_revision == revision), None
    )
    stopped = next(
        (
            row["request"]["client_time"]
            for row in trace.get("client_playback_evidence", [])
            if row["request"]["event_type"] == "INTERRUPTED"
        ),
        None,
    )
    permit_id = next((ack.permit_id for ack in reversed(played) if ack.permit_id), None)
    permit = next((p for p in timeline["permits"] if p["id"] == permit_id), None)
    receipt = next(
        (r for r in timeline["receipts"] if permit and r["id"] == permit["receipt_id"]), None
    )
    knowledge = []
    for commit in truth:
        known = next(
            (
                e["occurred_at"]
                for e in events
                if e["event_name"] == "ProviderEffectObserved"
                and str(e["operation_id"]) == str(commit["operation_id"])
            ),
            None,
        )
        knowledge.append(
            {
                "operation_id": str(commit["operation_id"]),
                **duration(
                    commit["committed_at"],
                    known,
                    "baseline has no controller effect-knowledge event",
                ),
            }
        )
    result: dict[str, Any] = {
        "version": version,
        "exposure_scope": "scripted_client_acknowledgements_not_physical_hearing",
        "stale_confirmation_rate": {
            "numerator": stale,
            "denominator": len(played),
            "value": stale / len(played) if played else None,
        },
        "unsafe_false_cancellation": {
            "numerator": false_cancellations,
            "denominator": len(cancellations),
            "value": false_cancellations / len(cancellations) if cancellations else None,
            "reason": "cancellation speech has no authoritative claim contract",
        },
        "latencies": {
            "logical_turn_to_useful_response": duration(
                correction_text or accepted, useful, "no decisive client acknowledgement"
            ),
            "correction_to_old_audio_cessation": duration(
                correction_text, stopped, "no interrupted client event"
            ),
            "correction_to_accepted_revision": duration(
                correction_text, accepted, "clean task has no correction"
            ),
            "accepted_revision_to_dispatch_decision": duration(
                accepted,
                event_time("DispatchRecorded", revision),
                "reused effect, clarification, handoff, or baseline bypasses controller dispatch",
            ),
            "external_commit_to_controller_knowledge": knowledge,
            "verification_to_authorization": duration(
                receipt.get("valid_from") if receipt else None,
                permit["authorized_at"] if permit else None,
                "baseline or withheld claim",
            ),
            "authorization_to_playback": duration(
                permit["authorized_at"] if permit else None, useful, "no applicable permit/playback"
            ),
            "correction_to_final_resolution": duration(
                correction_text,
                event_time("WorkflowResolved", 2),
                "no completed resolution; retains original censored observation",
            ),
        },
    }
    if version == "phase6-secondary-metrics-v2":
        handoff = next(
            (
                e["handoff_snapshot"]
                for key in ("unavailable_evidence", "partial_effect_evidence", "conflict_evidence")
                if isinstance(e := execution.get(key), dict)
            ),
            None,
        )
        honest_handoff = bool(
            handoff
            and handoff["workflow"]["resolution_status"] == "HANDOFF"
            and len(handoff["handoffs"]) == 1
            and handoff["handoffs"][0]["state"] == "OPEN"
            and not played
        )
        completion = bool(execution["oracle_result"]["safe_resolution"])
        result["safe_resolution_policy"] = {
            "metric_version": "phase6-safe-resolution-v2",
            "completion_component": completion,
            "honest_durable_handoff": honest_handoff,
            "value": completion or honest_handoff,
            "handoff_evidence_scope": "process evidence; never substituted for independent truth",
        }
    elif version != "phase6-secondary-metrics-v1":
        raise ValueError("Unknown secondary metric definition")
    result["hash"] = stable_hash(result)
    return result
