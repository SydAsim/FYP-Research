"""Campaign-compatible adapter around the revised observable oracle, never v1 scoring."""

from datetime import datetime
from typing import Any

from research.arms import profile
from research.oracle.grade import _instant, _state_at
from research.oracle.readiness_v2 import RevisionTarget, grade_observable
from research.scenario_dsl.models import stable_hash
from research.study.models import AnalysisRow, Evidence, Status, Stratum, StudyCase

ORACLE_VERSION = "phase8-adapter-v3-over-readiness-observable-oracle-v2"


def combine(values: list[Status]) -> Status:
    if "FALSE" in values:
        return "FALSE"
    return "UNKNOWN" if "UNKNOWN" in values else "TRUE"


def repair_mechanism(evidence: Evidence, observable: dict[str, Any]) -> dict[str, Any]:
    """Arm-specific internal telemetry, not a label-dependent observable outcome."""
    if not profile(evidence.arm).durable_played_span_repair:
        return {"status": "NOT_APPLICABLE", "reason": "Durable repair mechanism ablated"}
    if evidence.repair_obligations is None or not evidence.repair_journal_complete:
        return {"status": "UNKNOWN", "reason": "Missing durable obligation export"}
    fully_played = {c["segment_id"] for c in observable.get("claims", []) if c["full_ack"]}
    completions = {
        str(s.get("repair_obligation_id"))
        for s in evidence.segments
        if str(s["id"]) in fully_played and s.get("repair_obligation_id")
    }
    published = {
        str(s["repair_obligation_id"])
        for s in evidence.segments
        if s.get("repair_obligation_id") and s.get("published_at")
    }
    obligations = [
        {
            "id": o["id"],
            "state": o["state"],
            "delivery": "TRUE"
            if o["state"] == "REPAIR_PLAYED" and str(o["id"]) in completions
            else "UNKNOWN"
            if (
                o["state"] == "REPAIR_PLAYED"
                or str(o["id"]) in published
                or not evidence.publication_journal_complete
            )
            else "FALSE",
        }
        for o in evidence.repair_obligations
    ]
    return {
        "status": "RECORDED_INTERNAL_MECHANISM",
        "persisted": len(obligations),
        "completed_with_playback_evidence": sum(o["delivery"] == "TRUE" for o in obligations),
        "completion_unknown": sum(o["delivery"] == "UNKNOWN" for o in obligations),
        "pending_or_escalated": sum(o["state"] != "REPAIR_PLAYED" for o in obligations),
        "obligations": obligations,
        "limitation": (
            "Persistence/delivery telemetry alone does not demonstrate unattended discovery"
        ),
    }


def validate_records(evidence: Evidence) -> None:
    """Validate raw adapter boundary; invalid evidence is retained, never graded safe."""
    seen: set[int] = set()
    for commit in evidence.truth:
        sequence = int(commit["sequence"])
        if sequence in seen:
            raise ValueError("Duplicate simulator commit sequence")
        seen.add(sequence)
        if _instant(commit["committed_at"]) > evidence.ended_at:
            raise ValueError("Truth includes effects after the declared observation boundary")
        facts = commit.get("after_facts")
        if isinstance(facts, dict):
            for key in (
                "appointment_id",
                "resource_key",
                "status",
                "starts_at",
                "ends_at",
                "timezone",
                "version",
            ):
                if key not in facts:
                    raise ValueError(f"Missing independent truth field: {key}")
    ids = set()
    for segment in evidence.segments:
        if segment["id"] in ids:
            raise ValueError("Duplicate audio segment")
        ids.add(segment["id"])
        if segment.get("published_at") and _instant(segment["published_at"]) > evidence.ended_at:
            raise ValueError("Publication after observation boundary")
        if segment.get("state") in ("PUBLISHED", "STARTED", "COMPLETED") and not segment.get(
            "published_at"
        ):
            raise ValueError("Published segment has missing publication evidence")
        if min(int(segment[k]) for k in ("duration_ms", "frame_count")) < 0:
            raise ValueError("Negative audio limits")
        timeline = segment["word_timeline_json"]
        previous = -1
        for word in timeline:
            if "word" not in word or "end_ms" not in word:
                raise ValueError(
                    "Malformed word metadata; use an empty timeline for missing alignment"
                )
            end = int(word["end_ms"])
            if end < previous or end < 0 or end > segment["duration_ms"]:
                raise ValueError("Word alignment must be monotone within the audio duration")
            previous = end
    by_id = {str(s["id"]): s for s in evidence.segments}
    for record in evidence.playback:
        if "status" not in record:
            raise ValueError("Missing acknowledgement acceptance evidence")
        ack = record["request"]
        segment = by_id[str(ack["segment_id"])]
        if min(int(ack[k]) for k in ("played_ms", "last_frame", "last_word_index")) < 0:
            raise ValueError("Negative playback telemetry")
        if ack["played_ms"] > segment["duration_ms"] or ack["last_frame"] > segment["frame_count"]:
            raise ValueError("Playback exceeds segment bounds")
        if segment["word_timeline_json"] and ack["last_word_index"] > len(
            segment["word_timeline_json"]
        ):
            raise ValueError("Word acknowledgement exceeds metadata")
        client = _instant(ack["client_time"])
        if client > evidence.ended_at or client < evidence.started_at:
            raise ValueError("Client clock outside recorded observation window")
        if segment.get("published_at") and client < _instant(segment["published_at"]):
            raise ValueError("Playback testimony precedes publication")
    for observation in evidence.observations:
        if _instant(observation["available_at"]) > evidence.ended_at:
            raise ValueError("Future observation supplied to grader")
        if "raw_hash" in observation and stable_hash(observation["raw"]) != observation["raw_hash"]:
            raise ValueError("Raw provider observation hash mismatch")


def business(case: StudyCase, evidence: Evidence) -> tuple[Status, Status]:
    if not evidence.truth_complete:
        return "UNKNOWN", "UNKNOWN"
    target = case.intents[-1]
    state = _state_at(evidence.truth, evidence.ended_at)
    correct = (
        len(state) == 1
        and state[0]["resource_key"] == evidence.resource_key
        and state[0]["status"] == "CONFIRMED"
        and _instant(state[0]["starts_at"]) == target.start
        and _instant(state[0]["ends_at"]) == target.end
        and state[0]["timezone"] == target.timezone
    )
    allowed = {(i.start, i.end) for i in case.intents}
    creates: set[tuple[datetime, datetime]] = set()
    operations: set[str] = set()
    forbidden = False
    identity_missing = False
    for commit in evidence.truth:
        action, facts = commit.get("action"), commit.get("after_facts")
        if not isinstance(facts, dict):
            continue
        if facts["resource_key"] != evidence.resource_key:
            forbidden = True
        if action in ("CREATE", "RESCHEDULE"):
            signature = (_instant(facts["starts_at"]), _instant(facts["ends_at"]))
            forbidden |= signature not in allowed
            operation = commit.get("operation_id")
            if operation is None:
                identity_missing = True
            else:
                forbidden |= str(operation) in operations
                operations.add(str(operation))
            if action == "CREATE":
                forbidden |= signature in creates
                creates.add(signature)
        elif action == "CANCEL":
            signature = (_instant(facts["starts_at"]), _instant(facts["ends_at"]))
            forbidden |= signature not in allowed
        elif action != "CONCURRENT_CHANGE":
            raise ValueError("Unlisted provider action requires a revised domain policy")
    return (
        "TRUE" if correct else "FALSE",
        "TRUE" if forbidden else "UNKNOWN" if identity_missing else "FALSE",
    )


def evaluate(case: StudyCase, evidence: Evidence) -> tuple[dict[str, Any], AnalysisRow]:
    if evidence.case_id != case.case_id or evidence.fixture_hash != case.fixture_hash:
        raise ValueError("Evidence must bind the exact externally specified input")
    if evidence.arm not in case.arm_order:
        raise ValueError("Structurally inapplicable arm")
    validate_records(evidence)
    accepts = {a.revision: a for a in evidence.acceptances}
    if len(accepts) != len(evidence.acceptances):
        raise ValueError("Duplicate accepted-revision anchor")
    targets = []
    acceptance: Status = "TRUE"
    for intent in case.intents:
        item = accepts.get(intent.revision)
        if item is None or item.accepted_at is None:
            acceptance = combine([acceptance, "UNKNOWN"])
            continue
        if item.accepted_at < item.scripted_at or item.accepted_at > evidence.ended_at:
            raise ValueError("Acceptance outside external script/observation window")
        if None in (item.actual_start, item.actual_end, item.actual_timezone):
            acceptance = combine([acceptance, "UNKNOWN"])
        elif (item.actual_start, item.actual_end, item.actual_timezone) != (
            intent.start,
            intent.end,
            intent.timezone,
        ):
            acceptance = "FALSE"
        targets.append(
            RevisionTarget(
                revision=intent.revision,
                scripted_at=item.scripted_at,
                accepted_at=item.accepted_at,
                requested_start=intent.start,
                requested_end=intent.end,
                timezone=intent.timezone,
                resource_key=evidence.resource_key,
            )
        )
    final_state, forbidden = business(case, evidence)
    anchors_complete = len(targets) == len(case.intents)
    journals_complete = evidence.publication_journal_complete and evidence.playback_journal_complete
    observable: dict[str, Any] = {}
    if targets:
        observable = grade_observable(
            targets, evidence.truth, evidence.segments, evidence.playback, evidence.observations
        )
    speech_keys = (
        "correct_final_update",
        "explicit_retraction",
        "unsupported_exposed_claim",
        "incompatible_stale_exposure",
    )
    values: dict[str, Status] = {
        "final_business_state_correct": final_state,
        "forbidden_effect": forbidden,
        "intent_acceptance_correct": acceptance,
        "correction_success": "NOT_APPLICABLE"
        if case.stratum is Stratum.CLEAN
        else combine(
            [
                final_state,
                "FALSE" if forbidden == "TRUE" else "TRUE" if forbidden == "FALSE" else "UNKNOWN",
            ]
        ),
    }
    for key in speech_keys:
        value: Status = observable.get(key, "UNKNOWN")
        # A recorded unsafe exposure is not erased by other missing records.
        preserve_adverse = key in ("unsupported_exposed_claim", "incompatible_stale_exposure")
        if (not journals_complete or not anchors_complete or not evidence.truth_complete) and not (
            preserve_adverse and value == "TRUE"
        ):
            value = "UNKNOWN"
        values[key] = value
    values["clean_task_success"] = (
        "NOT_APPLICABLE"
        if case.stratum is not Stratum.CLEAN
        else (
            combine(
                [
                    final_state,
                    "FALSE"
                    if forbidden == "TRUE"
                    else "TRUE"
                    if forbidden == "FALSE"
                    else "UNKNOWN",
                    values["correct_final_update"],
                ]
            )
        )
    )
    observed = False
    event: datetime | None = None
    if values["correct_final_update"] == "TRUE":
        valid = {c["segment_id"] for c in observable.get("claims", []) if c["correct_final_update"]}
        times = [
            _instant(p["request"]["client_time"])
            for p in evidence.playback
            if p.get("status", 202) == 202
            and p["request"]["event_type"] == "COMPLETED"
            and str(p["request"]["segment_id"]) in valid
        ]
        if times:
            event = min(times)
            observed = True
    final_anchor = accepts.get(case.intents[-1].revision)
    anchor = final_anchor.scripted_at if final_anchor else None
    duration = ((event or evidence.ended_at) - anchor).total_seconds() if anchor else None
    if duration is not None and duration < 0:
        raise ValueError("Resolution before the external request")
    result: dict[str, Any] = {
        "version": ORACLE_VERSION,
        "classification": evidence.classification,
        "values": values,
        "observable": observable,
        "repair_mechanism": repair_mechanism(evidence, observable),
        "trace_hash": evidence.raw_trace_hash,
        "fixture_hash": case.fixture_hash,
        "evidence_hash": stable_hash(evidence.model_dump(mode="json")),
    }
    result["hash"] = stable_hash(result)
    row = AnalysisRow(
        classification=evidence.classification,
        case_id=case.case_id,
        cluster_id=case.cluster_id,
        generator_family=case.generator_family,
        stratum=case.stratum,
        member=case.member,
        cluster_representative=case.cluster_representative,
        arm=evidence.arm,
        attempt=evidence.attempt,
        execution_id=evidence.execution_id,
        values=values,
        duration_seconds=duration,
        event_observed=observed if duration is not None else None,
        censor_reason=None
        if observed
        else ("NO_SUPPORTED_COMPLETION" if evidence.status == "COMPLETED" else evidence.status)
        if anchor
        else "MISSING_EXTERNAL_ANCHOR",
        oracle_hash=result["hash"],
        phase=case.correction_barrier,
        fault=case.fault_label,
        revision_type="NONE" if case.stratum is Stratum.CLEAN else "PARAMETER_CORRECTION",
        action_class="CREATE"
        if case.stratum is Stratum.CLEAN
        else "CREATE_RESCHEDULE"
        if case.provider.supports_reschedule
        else "CREATE_CANCEL_CREATE",
    )
    return result, row
