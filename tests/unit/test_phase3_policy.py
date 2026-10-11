"""Pure evidence, semantics, and template safety checks."""

from datetime import UTC, datetime, timedelta

import pytest

from packages.domain.phase3_verification import (
    ClaimType,
    Result,
    evaluate_appointment,
    receipt_applicable,
)
from packages.speech_policy.phase3 import PROGRESS, UNKNOWN, render

DESIRED = {
    "requested_start": "2026-10-01T16:00:00+05:00",
    "requested_end": "2026-10-01T17:00:00+05:00",
    "timezone": "Asia/Karachi",
}
KEY = "property:synthetic:maintenance"
FACT = {
    "appointment_id": "6c4901ea-1826-4c3a-a7e6-33dc9ba8276a",
    "resource_key": KEY,
    "starts_at": "2026-10-01T11:00:00+00:00",
    "ends_at": "2026-10-01T12:00:00+00:00",
    "timezone": "Asia/Karachi",
    "status": "CONFIRMED",
    "version": 4,
}


def test_three_valued_result_and_forbidden_active_effect() -> None:
    assert evaluate_appointment(DESIRED, KEY, None).result is Result.UNKNOWN
    assert (
        evaluate_appointment(
            DESIRED,
            KEY,
            {
                "authoritative": True,
                "appointments": [],
            },
        ).result
        is Result.VIOLATED
    )
    good = evaluate_appointment(
        DESIRED,
        KEY,
        {
            "authoritative": True,
            "appointments": [FACT],
        },
    )
    assert good.result is Result.SATISFIED
    assert good.resource_version == "4"
    wrong = evaluate_appointment(
        DESIRED,
        KEY,
        {
            "authoritative": True,
            "appointments": [
                FACT,
                {**FACT, "appointment_id": "other", "starts_at": "2026-10-01T10:00:00+00:00"},
            ],
        },
    )
    assert wrong.result is Result.VIOLATED
    held = evaluate_appointment(
        DESIRED,
        KEY,
        {
            "authoritative": True,
            "appointments": [{**FACT, "status": "HELD"}],
        },
    )
    assert held.result is Result.UNKNOWN


def test_receipt_revision_result_freshness_and_version_binding() -> None:
    now = datetime.now(UTC)
    receipt = {
        "result": "SATISFIED",
        "claim_type": "CURRENT_APPOINTMENT",
        "intent_revision": 1,
        "invalidated_at": None,
        "valid_from": now - timedelta(seconds=1),
        "valid_until": now + timedelta(seconds=1),
        "observed_resource_version": "4",
    }
    assert receipt_applicable(receipt, ClaimType.CURRENT_APPOINTMENT, 1, now, "4")
    assert not receipt_applicable(receipt, ClaimType.CURRENT_APPOINTMENT, 2, now, "4")
    assert not receipt_applicable(receipt, ClaimType.HISTORICAL_EFFECT, 1, now, "4")
    assert not receipt_applicable(receipt, ClaimType.CURRENT_APPOINTMENT, 1, now, "5")
    assert not receipt_applicable(
        receipt, ClaimType.CURRENT_APPOINTMENT, 1, now + timedelta(seconds=2), "4"
    )
    assert not receipt_applicable(
        {**receipt, "invalidated_at": now}, ClaimType.CURRENT_APPOINTMENT, 1, now, "4"
    )
    assert not receipt_applicable(
        {**receipt, "result": "UNKNOWN"}, ClaimType.CURRENT_APPOINTMENT, 1, now, "4"
    )


def test_closed_templates_reject_unverified_variables() -> None:
    predicates = evaluate_appointment(
        DESIRED,
        KEY,
        {
            "authoritative": True,
            "appointments": [FACT],
        },
    ).predicates
    assert "4:00 PM" in render(ClaimType.CURRENT_APPOINTMENT, predicates)
    assert PROGRESS == "I am still checking the appointment. It is not confirmed yet."
    assert "cannot yet determine" in UNKNOWN
    with pytest.raises(ValueError, match="exact verified fields"):
        render(
            ClaimType.CURRENT_APPOINTMENT,
            {**predicates, "model_text": "Everything definitely succeeded."},
        )
    with pytest.raises(ValueError, match="not satisfied"):
        render(ClaimType.CURRENT_APPOINTMENT, {**predicates, "forbidden_active_count": 1})
