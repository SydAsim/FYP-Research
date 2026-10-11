"""Launch cannot inherit a historical stage approval or broaden its scope."""

import pytest
from deploy import approve, price_rows


def test_approval_is_stage_specific() -> None:
    value = {"stage": "8.3", "limit_usd": "2.00", "planned_executions": 24,
             "max_powered_hours": 6, "main_authorized": False,
             "cleanup": "REMOVE_AFTER_TWO_VERIFIED_LOCAL_COPIES_AND_S3",
             "decision": "APPROVED_BY_USER", "user_message": "TEST_ONLY_NOT_AUTHORIZATION"}
    approve(value)
    for field, wrong in (("stage", "8.2"), ("main_authorized", True),
                         ("planned_executions", 1500), ("max_powered_hours", 7)):
        with pytest.raises(ValueError, match="NEW_HUMAN_STAGE_APPROVAL_REQUIRED"):
            approve({**value, field: wrong})
    with pytest.raises(ValueError, match="RETAIN_ACTUAL_USER_AUTHORIZATION"):
        approve({**value, "user_message": ""})


def test_absent_price_fails_closed() -> None:
    with pytest.raises(ValueError, match="UNAMBIGUOUS"):
        price_rows({"PriceList": []}, "Hrs")
