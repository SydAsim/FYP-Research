"""Arm-neutral semantic-proxy oracle. No controller verdict or repair row is truth."""

from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.speech_policy.phase4 import decisive_exposure, incompatible_exposure, semantic_start
from research.oracle.grade import _instant, _state_at
from research.scenario_dsl.models import stable_hash

Status = Literal["TRUE", "FALSE", "UNKNOWN", "NOT_APPLICABLE"]
VERSION = "readiness-observable-oracle-v2"


def predicates_match(
    facts: dict[str, Any], start: datetime, text: str | None, through: int | None
) -> bool:
    """Grade only completed semantic predicates, with the template's display zone."""
    if facts.get("status") != "CONFIRMED":
        return False
    if through is None or text is None:
        return (
            _instant(facts["starts_at"]) == start
            and facts.get("timezone") == str(start.tzinfo)
        )
    words = text.split()
    prefix = words[:through]
    actual = _instant(facts["starts_at"]).astimezone(start.tzinfo)
    return (
        (not any(w in ("AM", "PM") for w in prefix) or actual.time() == start.time())
        and (start.date().isoformat() not in prefix or actual.date() == start.date())
        and (through < len(words) or facts.get("timezone") == str(start.tzinfo))
    )


class RevisionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    scripted_at: datetime
    accepted_at: datetime
    requested_start: datetime
    requested_end: datetime
    timezone: str
    resource_key: str

    @field_validator("scripted_at", "accepted_at", "requested_start", "requested_end")
    @classmethod
    def offset(cls, value: datetime) -> datetime:
        return _instant(value)


def matches(facts: dict[str, Any], target: RevisionTarget) -> bool:
    return (
        facts.get("status") == "CONFIRMED"
        and facts.get("resource_key") == target.resource_key
        and _instant(facts["starts_at"]) == target.requested_start
        and _instant(facts["ends_at"]) == target.requested_end
        and facts.get("timezone") == target.timezone
    )


def support(
    commits: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    start: datetime | None,
    moment: datetime | None,
    resource_key: str,
    moved: bool = False,
    text: str | None = None,
    through: int | None = None,
) -> tuple[Status, Status]:
    if start is None or moment is None:
        return "UNKNOWN", "UNKNOWN"
    state = [s for s in _state_at(commits, moment) if s["resource_key"] == resource_key]
    truth: Status = (
        "TRUE"
        if (
            len(state) == 1
            and predicates_match(state[0], start, text, through)
        )
        else "FALSE"
    )
    if moved and not any(
        c.get("action") == "RESCHEDULE"
        and _instant(c["committed_at"]) <= moment
        and c.get("after_facts", {}).get("resource_key") == resource_key
        and predicates_match(c["after_facts"], start, text, through)
        for c in commits
    ):
        truth = "FALSE"
    available = [
        o
        for o in observations
        if o["source_type"] == "SIMULATOR_RESOURCE"
        and o["source_identifier"] == resource_key
        and _instant(o["available_at"]) <= moment
        and moment <= _instant(o["available_at"]) + timedelta(seconds=30)
    ]
    if not available:
        return truth, "UNKNOWN"
    latest = max(available, key=lambda o: _instant(o["available_at"]))
    raw = latest["raw"]
    body = raw.get("body")
    if raw.get("status") != 200 or not isinstance(body, dict) or not body.get("authoritative"):
        return truth, "UNKNOWN"
    appointments = [a for a in body.get("appointments", []) if a["status"] in ("CONFIRMED", "HELD")]
    entailed = (
        len(appointments) == 1
        and predicates_match(appointments[0], start, text, through)
        and appointments[0]["resource_key"] == resource_key
    )
    # Resource version relevance is independently checked against simulator history.
    relevant = (
        len(state) == 1
        and len(appointments) == 1
        and appointments[0]["version"] == state[0]["version"]
    )
    evidence: Status = "TRUE" if entailed and relevant else "FALSE"
    if moved:
        history = [
            o
            for o in observations
            if o["source_type"] == "SIMULATOR_OPERATION"
            and _instant(o["available_at"]) <= moment
            and moment <= _instant(o["available_at"]) + timedelta(seconds=30)
        ]
        witnessed = any(
            o.get("query", {}).get("action") == "RESCHEDULE"
            and o["raw"].get("status") == 200
            and o["raw"].get("body", {}).get("authoritative") is True
            and o["raw"]["body"].get("outcome") == "PRESENT"
            and o["raw"]["body"].get("facts", {}).get("resource_key") == resource_key
            and predicates_match(o["raw"]["body"]["facts"], start, text, through)
            for o in history
        )
        if evidence == "TRUE" and not witnessed:
            evidence = "UNKNOWN" if not history else "FALSE"
    return truth, evidence


def grade_observable(
    targets: list[RevisionTarget],
    commits: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    playback: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Only external script, truth, ordinary observations and client testimony enter.

    Labels, receipt verdicts, permit IDs and obligation state are not read. ACKs are
    logical semantic proxies; no physical hearing or accurate acoustic alignment.
    """
    if not targets:
        raise ValueError("External accepted-revision schedule is required")
    targets = sorted(targets, key=lambda t: t.accepted_at)
    final = targets[-1]
    latest = max([final.accepted_at, *(_instant(c["committed_at"]) for c in commits)])
    active = _state_at(commits, latest)
    business = len(active) == 1 and matches(active[0], final)
    claims: list[dict[str, Any]] = []
    exposed: list[tuple[datetime, datetime]] = []
    completed_updates: list[tuple[datetime, bool]] = []
    unknown_playback = False
    for segment in segments:
        text = segment["segment_text"]
        moved = "has been moved to" in text
        claimed = semantic_start(text)
        events = [
            p
            for p in playback
            if p["request"]["segment_id"] == str(segment["id"]) and p.get("status", 202) == 202
        ]
        events.sort(key=lambda p: _instant(p["request"]["client_time"]))
        publication = _instant(segment["published_at"]) if segment.get("published_at") else None
        released_truth, released_evidence = support(
            commits, observations, claimed, publication, final.resource_key, moved
        )
        measured = [
            (
                p["request"],
                decisive_exposure({
                    **segment,
                    "last_played_ms": p["request"]["played_ms"],
                    "last_frame": p["request"]["last_frame"],
                    "last_word_index": p["request"]["last_word_index"],
                }),
            )
            for p in events
        ]
        exposures = [request for request, known in measured if known is True]
        ambiguous_exposure = any(known is None for _, known in measured)
        started = any(p["request"]["event_type"] == "STARTED" for p in events)
        terminal = any(p["request"]["event_type"] in ("COMPLETED", "INTERRUPTED") for p in events)
        playback_status: Status = (
            "TRUE" if exposures else "FALSE" if terminal and not ambiguous_exposure else "UNKNOWN"
        )
        if segment.get("published_at") and (not terminal or ambiguous_exposure):
            unknown_playback = True
        stale: Status = (
            "FALSE" if terminal and not exposures and not ambiguous_exposure else "UNKNOWN"
        )
        played_truth: Status = "UNKNOWN"
        played_evidence: Status = "UNKNOWN"
        if exposures:
            checks = []
            stale_flags = []
            for ack in exposures:
                at = _instant(ack["client_time"])
                checks.append(
                    support(
                        commits, observations, claimed, at, final.resource_key, moved,
                        text, ack["last_word_index"],
                    )
                )
                current = next((t for t in reversed(targets) if t.accepted_at <= at), None)
                proxy = {
                    **segment,
                    "last_word_index": ack["last_word_index"],
                    "last_played_ms": ack["played_ms"],
                    "last_frame": ack["last_frame"],
                }
                stale_flags.append(
                    current is not None
                    and incompatible_exposure(proxy, current.model_dump(mode="json")) is True
                )
                if (
                    claimed is not None
                    and incompatible_exposure(proxy, final.model_dump(mode="json")) is True
                ):
                    exposed.append((at, claimed))
            played_truth = aggregate([c[0] for c in checks])
            played_evidence = aggregate([c[1] for c in checks])
            stale = "TRUE" if any(stale_flags) else "FALSE"
        full = any(
            p["request"]["event_type"] == "COMPLETED"
            and p["request"]["played_ms"] == segment["duration_ms"]
            and p["request"]["last_frame"] == segment["frame_count"]
            and p["request"]["last_word_index"] == len(segment["word_timeline_json"])
            for p in events
        )
        valid_update = (
            started
            and full
            and claimed == final.requested_start
            and released_truth == released_evidence == played_truth == played_evidence == "TRUE"
            and stale == "FALSE"
            and any(
                p["request"]["event_type"] == "COMPLETED"
                and _instant(p["request"]["client_time"]) >= final.accepted_at
                for p in events
            )
        )
        if (
            claimed == final.requested_start
            and full
            and "UNKNOWN" in (released_truth, released_evidence, played_truth, played_evidence)
            and "FALSE" not in (released_truth, released_evidence, played_truth, played_evidence)
        ):
            unknown_playback = True
        if valid_update:
            end = max(
                _instant(p["request"]["client_time"])
                for p in events
                if p["request"]["event_type"] == "COMPLETED"
            )
            completed_updates.append(
                (end, text.startswith("Correction: my earlier confirmation was outdated. "))
            )
        claims.append(
            {
                "segment_id": str(segment["id"]),
                "truth_at_publication": released_truth,
                "evidence_at_publication": released_evidence,
                "decisive_exposure": playback_status,
                "truth_at_playback": played_truth,
                "evidence_at_playback": played_evidence,
                "incompatible_stale_exposure": stale,
                "full_ack": full,
                "correct_final_update": valid_update,
            }
        )
    outdated = [(at, value) for at, value in exposed if value != final.requested_start]
    retraction: Status = "NOT_APPLICABLE"
    if outdated:
        last = max(at for at, _ in outdated)
        retraction = (
            "TRUE"
            if any(at >= last and explicit for at, explicit in completed_updates)
            else "UNKNOWN"
            if unknown_playback
            else "FALSE"
        )
    result = {
        "oracle_version": VERSION,
        "final_business_state_correct": business,
        "correct_final_update": (
            "TRUE" if completed_updates else "UNKNOWN" if unknown_playback else "FALSE"
        ),
        "explicit_retraction": retraction,
        "incompatible_stale_exposure": event_status(
            [c["incompatible_stale_exposure"] for c in claims]
        ),
        "unsupported_exposed_claim": "TRUE"
        if any(
            c["decisive_exposure"] == "TRUE"
            and (
                c["truth_at_playback"] == "FALSE"
                or c["evidence_at_playback"] == "FALSE"
                or c["truth_at_publication"] == "FALSE"
                or c["evidence_at_publication"] == "FALSE"
            )
            for c in claims
        )
        else "UNKNOWN"
        if any(
            c["decisive_exposure"] == "UNKNOWN"
            or (
                c["decisive_exposure"] == "TRUE"
                and "UNKNOWN"
                in (
                    c["truth_at_publication"],
                    c["evidence_at_publication"],
                    c["truth_at_playback"],
                    c["evidence_at_playback"],
                )
            )
            for c in claims
        )
        else "FALSE",
        "unknown_claim_support": any(
            c["decisive_exposure"] == "TRUE"
            and "UNKNOWN"
            in (
                c["truth_at_publication"],
                c["evidence_at_publication"],
                c["truth_at_playback"],
                c["evidence_at_playback"],
            )
            for c in claims
        ),
        "playback_evidence_unknown": unknown_playback,
        "claims": claims,
        "active_final_truth": active,
        "voice_evidence": "SCRIPTED_TONE_SEMANTIC_PROXY",
    }
    result["result_hash"] = stable_hash(result)
    return result


def aggregate(values: list[Status]) -> Status:
    if "FALSE" in values:
        return "FALSE"
    return "UNKNOWN" if not values or "UNKNOWN" in values else "TRUE"


def event_status(values: list[Status]) -> Status:
    if "TRUE" in values:
        return "TRUE"
    return "UNKNOWN" if "UNKNOWN" in values else "FALSE"


def repair_telemetry(obligations: list[dict[str, Any]]) -> dict[str, Any]:
    """Internal mechanism endpoint, deliberately excluded from observable grading."""
    return {
        "persisted": len(obligations),
        "completed": sum(o["state"] == "REPAIR_PLAYED" for o in obligations),
        "pending": sum(o["state"] in ("OPEN", "REPAIR_AUTHORIZED") for o in obligations),
        "escalated": sum(o["state"] == "ESCALATED" for o in obligations),
    }
