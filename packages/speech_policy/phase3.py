"""Closed deterministic text templates; model strings are never parameters."""

from typing import Any

from packages.domain.phase3_verification import (
    ClaimType,
    _instant,
    validate_template_predicates,
)

POLICY_VERSION = "phase3-policy-v1"
TEMPLATE_VERSION = "phase3-template-v1"
PROGRESS = "I am still checking the appointment. It is not confirmed yet."
UNKNOWN = "I cannot yet determine whether the earlier request completed. I am continuing to check."


def _spoken_time(value: str) -> str:
    date = _instant(value)
    hour = date.hour % 12 or 12
    suffix = "AM" if date.hour < 12 else "PM"
    minute = f"{date.minute:02d}"
    return f"{hour}:{minute} {suffix} on {date.date().isoformat()}"


def render(claim_type: ClaimType, predicates: dict[str, Any]) -> str:
    validate_template_predicates(claim_type, predicates)
    if claim_type is ClaimType.CURRENT_APPOINTMENT:
        return (
            f"Your maintenance appointment is confirmed for "
            f"{_spoken_time(predicates['requested_start'])} "
            f"({predicates['timezone']})."
        )
    if claim_type is ClaimType.RESCHEDULED_APPOINTMENT:
        return (
            f"Your maintenance appointment has been moved to "
            f"{_spoken_time(predicates['requested_start'])} "
            f"({predicates['timezone']})."
        )
    if claim_type is ClaimType.COMPENSATED_APPOINTMENT:
        return (
            f"The earlier appointment was cancelled, and a new maintenance appointment "
            f"is confirmed for {_spoken_time(predicates['requested_start'])} "
            f"({predicates['timezone']})."
        )
    if claim_type is ClaimType.HISTORICAL_EFFECT:
        return (
            f"The earlier appointment at {_spoken_time(predicates['historical_start'])} "
            "was created before your correction."
        )
    if claim_type is ClaimType.HANDOFF_CREATED:
        return "I could not confirm the appointment. A human reviewer will follow up."
    raise ValueError("Unsupported claim type")
