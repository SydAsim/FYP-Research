"""Pure three-valued appointment evidence and receipt applicability rules."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo


class Result(StrEnum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


class ClaimType(StrEnum):
    CURRENT_APPOINTMENT = "CURRENT_APPOINTMENT"
    RESCHEDULED_APPOINTMENT = "RESCHEDULED_APPOINTMENT"
    COMPENSATED_APPOINTMENT = "COMPENSATED_APPOINTMENT"
    HISTORICAL_EFFECT = "HISTORICAL_EFFECT"
    HANDOFF_CREATED = "HANDOFF_CREATED"


@dataclass(frozen=True)
class Evaluation:
    result: Result
    predicates: dict[str, Any]
    resource_version: str | None


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        raise ValueError("Evidence time must include an offset")
    return instant


def evaluate_appointment(
    desired: dict[str, Any], resource_key: str, observation: dict[str, Any] | None
) -> Evaluation:
    """Require exactly one confirmed desired appointment and no other active slot."""
    base = {
        "resource_key": resource_key,
        "requested_start": desired["requested_start"],
        "requested_end": desired["requested_end"],
        "timezone": desired["timezone"],
        "active_count": None,
        "forbidden_active_count": None,
    }
    if observation is None or observation.get("authoritative") is not True:
        return Evaluation(Result.UNKNOWN, base, None)
    appointments = observation.get("appointments")
    if not isinstance(appointments, list):
        return Evaluation(Result.UNKNOWN, base, None)
    active = [
        item
        for item in appointments
        if isinstance(item, dict) and item.get("status") in ("CONFIRMED", "HELD")
    ]
    if any(item.get("status") == "HELD" for item in active):
        return Evaluation(
            Result.UNKNOWN,
            {**base, "active_count": len(active), "forbidden_active_count": None},
            None,
        )
    matching = [
        item
        for item in active
        if item.get("status") == "CONFIRMED"
        and item.get("resource_key") == resource_key
        and isinstance(item.get("starts_at"), str)
        and isinstance(item.get("ends_at"), str)
        and _instant(item["starts_at"]) == _instant(desired["requested_start"])
        and _instant(item["ends_at"]) == _instant(desired["requested_end"])
        and item.get("timezone") == desired["timezone"]
    ]
    predicates = {
        **base,
        "active_count": len(active),
        "forbidden_active_count": len(active) - len(matching),
    }
    if len(active) != 1 or len(matching) != 1:
        return Evaluation(Result.VIOLATED, predicates, None)
    matched = matching[0]
    if not isinstance(matched.get("version"), int) or not isinstance(
        matched.get("appointment_id"), str
    ):
        return Evaluation(Result.UNKNOWN, predicates, None)
    predicates["appointment_id"] = matched["appointment_id"]
    predicates["observed_version"] = str(matched["version"])
    return Evaluation(Result.SATISFIED, predicates, str(matched["version"]))


def receipt_applicable(
    receipt: dict[str, Any],
    claim_type: ClaimType,
    current_revision: int,
    now: datetime,
    current_resource_version: str | None,
) -> bool:
    if receipt["result"] != Result.SATISFIED:
        return False
    if receipt["claim_type"] != claim_type or receipt["intent_revision"] != current_revision:
        return False
    if receipt["invalidated_at"] is not None:
        return False
    if now < receipt["valid_from"] or (
        receipt["valid_until"] is not None and now >= receipt["valid_until"]
    ):
        return False
    observed = receipt["observed_resource_version"]
    if observed is not None and observed != current_resource_version:
        return False
    return True


def validate_template_predicates(claim_type: ClaimType, predicates: dict[str, Any]) -> None:
    if claim_type is ClaimType.HANDOFF_CREATED:
        if set(predicates) != {"handoff_id", "handoff_state"}:
            raise ValueError("Handoff template needs only verified handoff fields")
        if predicates["handoff_state"] not in ("OPEN", "ACKNOWLEDGED"):
            raise ValueError("Handoff is not active")
        return
    if claim_type is ClaimType.HISTORICAL_EFFECT:
        if set(predicates) != {"historical_start", "source_revision", "appointment_id"}:
            raise ValueError("Historical template needs exact evidence fields")
        _instant(predicates["historical_start"])
        return
    required = {
        "resource_key",
        "requested_start",
        "requested_end",
        "timezone",
        "active_count",
        "forbidden_active_count",
        "appointment_id",
        "observed_version",
    }
    if set(predicates) != required:
        raise ValueError("Appointment template needs exact verified fields")
    if predicates["active_count"] != 1 or predicates["forbidden_active_count"] != 0:
        raise ValueError("Final-state predicates are not satisfied")
    zone = ZoneInfo(predicates["timezone"])
    start = _instant(predicates["requested_start"])
    if start.utcoffset() != start.astimezone(zone).utcoffset():
        raise ValueError("Claim time does not match IANA zone")
