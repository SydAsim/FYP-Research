"""Decide a reconciled revision transition without storage or provider imports."""

from datetime import datetime
from typing import Any, Literal


def revision_transition(
    change_class: str, desired: dict[str, Any], observed: dict[str, Any], supports_reschedule: bool
) -> Literal["REUSE", "CANCEL", "RESCHEDULE", "COMPENSATE"]:
    if change_class == "RETRACTION":
        return "CANCEL"
    if change_class == "ADDITIVE_COMPATIBLE" and all(
        (
            datetime.fromisoformat(desired[key]) == datetime.fromisoformat(observed[provider_key])
            if key != "timezone"
            else desired.get(key) == observed.get(provider_key)
        )
        for key, provider_key in (
            ("requested_start", "starts_at"),
            ("requested_end", "ends_at"),
            ("timezone", "timezone"),
        )
    ):
        return "REUSE"
    return "RESCHEDULE" if supports_reschedule else "COMPENSATE"
