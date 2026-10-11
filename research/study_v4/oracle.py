"""V4 delivery endpoints on the unchanged revised observable instrument."""

from datetime import datetime, timedelta
from typing import Any

from research.oracle.grade import _instant
from research.scenario_dsl.models import stable_hash
from research.study.models import Acceptance, AnalysisRow, Evidence, Status, StudyCase
from research.study.oracle import combine, evaluate
from research.study_v4.analysis import RECOVERY_FAMILIES


def adapt_calibration(trace: dict[str, Any]) -> tuple[StudyCase, Evidence]:
    if trace["classification"] != "CALIBRATION_NOT_MAIN_CAMPAIGN":
        raise ValueError("Only separate calibration traces accepted")
    case = StudyCase.model_validate(trace["input"])
    if not case.case_id.startswith("cal-v4-"):
        raise ValueError("Main IDs forbidden")
    snapshot = trace["snapshot"]
    revisions = {r["revision"]: r for r in snapshot["history"]["revisions"]}
    anchors = []
    for target in trace["targets"]:
        actual = revisions[target["revision"]]["desired_state_json"]
        anchors.append(
            Acceptance(
                revision=target["revision"],
                scripted_at=target["scripted_at"],
                accepted_at=revisions[target["revision"]]["accepted_at"],
                actual_start=actual["requested_start"],
                actual_end=actual["requested_end"],
                actual_timezone=actual["timezone"],
            )
        )
    evidence = Evidence.model_validate(
        {
            "classification": "VALIDATION_ONLY",
            "case_id": case.case_id,
            "arm": trace["arm"],
            "attempt": 1,
            "execution_id": trace["execution_id"],
            "fixture_hash": case.fixture_hash,
            "started_at": trace["started_at"],
            "ended_at": trace["finished_at"],
            "status": {"FAILED": "INFRASTRUCTURE_FAILURE"}.get(trace["status"], trace["status"]),
            "resource_key": trace["targets"][0]["resource_key"],
            "acceptances": anchors,
            "truth": snapshot["truth"],
            "segments": snapshot["segments"],
            "playback": trace["client_playback"],
            "observations": snapshot["observations"],
            "truth_complete": True,
            "publication_journal_complete": True,
            "playback_journal_complete": True,
            "independent_truth_source": "SIMULATOR_APPEND_ONLY_ORACLE_EXPORT",
            "raw_trace_hash": trace["trace_hash"],
            "repair_obligations": snapshot["obligations"],
            "repair_journal_complete": True,
        }
    )
    return case, evidence


def delivery(
    case: StudyCase,
    evidence: Evidence,
    observable: dict[str, Any],
    values: dict[str, Status],
    *,
    challenge_at: datetime | None,
) -> dict[str, Status]:
    """External challenge denominator; arm labels and internal obligations cannot earn credit."""
    if case.generator_family not in RECOVERY_FAMILIES:
        return {
            "corrective_delivery_after_challenge": "NOT_APPLICABLE",
            "withdrawal_and_corrective_delivery": "NOT_APPLICABLE",
            "complete_corrective_communication": "NOT_APPLICABLE",
        }
    eligible = {
        str(c["segment_id"]) for c in observable.get("claims", []) if c["correct_final_update"]
    }
    completed = [
        _instant(p["request"]["client_time"])
        for p in evidence.playback
        if p.get("status") == 202
        and p["request"]["event_type"] == "COMPLETED"
        and str(p["request"]["segment_id"]) in eligible
    ]
    value: Status = "UNKNOWN"
    if challenge_at is not None:
        if any(challenge_at <= at <= evidence.ended_at for at in completed):
            value = values["correct_final_update"]
        elif (evidence.ended_at - challenge_at).total_seconds() >= 600:
            value = (
                "UNKNOWN"
                if (
                    values["correct_final_update"] == "UNKNOWN"
                    or not evidence.playback_journal_complete
                )
                else "FALSE"
            )
    withdrawal = values["explicit_retraction"]
    # No exposed incompatibility: withdrawal is structurally unnecessary, not a demonstrated repair.
    joint: Status = (
        "NOT_APPLICABLE" if withdrawal == "NOT_APPLICABLE" else combine([value, withdrawal])
    )
    return {
        "corrective_delivery_after_challenge": value,
        "withdrawal_and_corrective_delivery": joint,
        "complete_corrective_communication": combine(
            [value, "TRUE" if withdrawal == "NOT_APPLICABLE" else withdrawal]
        ),
    }


def revised_evaluate(
    case: StudyCase, evidence: Evidence, *, challenge_at: datetime | None
) -> tuple[dict[str, Any], AnalysisRow]:
    evidence = administrative_cap(case, evidence)
    result, row = evaluate(case, evidence)
    values = dict(row.values)
    values.update(delivery(case, evidence, result["observable"], values, challenge_at=challenge_at))
    final_request = next(
        (a.scripted_at for a in evidence.acceptances if a.revision == case.intents[-1].revision),
        None,
    )
    if final_request is None or (evidence.ended_at - final_request).total_seconds() < 600:
        for endpoint in ("unsupported_exposed_claim", "incompatible_stale_exposure"):
            if values[endpoint] == "FALSE":
                values[endpoint] = "UNKNOWN"
    result.update(
        version="phase8-observable-adapter-v4",
        values=values,
        challenge_at=challenge_at.isoformat() if challenge_at else None,
        delivery_evidence="SCRIPTED_TONE_ACK_PROTOCOL_ONLY",
    )
    result.pop("hash")
    result["hash"] = stable_hash(result)
    return result, row.model_copy(update={"values": values, "oracle_hash": result["hash"]})


def administrative_cap(case: StudyCase, evidence: Evidence) -> Evidence:
    """Retain raw trace; analyze only information available at the fixed external-request cap."""
    anchor = next(
        (a.scripted_at for a in evidence.acceptances if a.revision == case.intents[-1].revision),
        None,
    )
    if anchor is None:
        return evidence
    cap = min(evidence.ended_at, anchor + timedelta(seconds=case.observation_budget_seconds))
    playback = [
        p
        for p in evidence.playback
        if p.get("server_received_at")
        and _instant(p["server_received_at"]) <= cap
        and _instant(p["request"]["client_time"]) <= cap
    ]
    complete = evidence.playback_journal_complete and all(
        p.get("server_received_at") is not None for p in evidence.playback
    )
    milestones = {
        "generated_at": "GENERATED",
        "queued_at": "QUEUED",
        "published_at": "PUBLISHED",
        "started_at": "STARTED",
        "completed_at": "COMPLETED",
        "cancelled_at": "CANCELLED",
        "stopped_at": "INTERRUPTED",
    }
    segments = []
    for original in evidence.segments:
        if _instant(original["generated_at"]) > cap:
            continue
        segment = dict(original)
        prior = []
        for key, state in milestones.items():
            value = segment.get(key)
            if value and _instant(value) > cap:
                segment[key] = None
            elif value:
                prior.append((_instant(value), state))
        if prior:
            segment["state"] = max(prior)[1]
        segments.append(segment)
    return evidence.model_copy(
        update={
            "ended_at": cap,
            "playback": playback,
            "playback_journal_complete": complete,
            "segments": segments,
            "truth": [t for t in evidence.truth if _instant(t["committed_at"]) <= cap],
            "observations": [
                o for o in evidence.observations if _instant(o["available_at"]) <= cap
            ],
            "acceptances": [
                a.model_copy(
                    update={
                        "accepted_at": None,
                        "actual_start": None,
                        "actual_end": None,
                        "actual_timezone": None,
                    }
                )
                if a.accepted_at and a.accepted_at > cap
                else a
                for a in evidence.acceptances
            ],
            "repair_obligations": [
                o for o in evidence.repair_obligations if _instant(o["created_at"]) <= cap
            ]
            if evidence.repair_obligations is not None
            else None,
        }
    )
