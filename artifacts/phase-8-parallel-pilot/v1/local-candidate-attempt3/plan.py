"""Fixed calibration plan and admission arithmetic; never admits main inputs."""

from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from research.study.models import StudyCase

PREFIX = "cal-v4-linux-v1-p83-v1-"
ArmName = Literal["B3", "P1", "P2"]
ARMS: tuple[ArmName, ...] = ("B3", "P1", "P2")
FAMILIES = (
    "clean-Asia/Karachi-30",
    "hidden-True-IMMEDIATE-DROP_RESPONSE",
    "buffered-stale",
    "partial-time",
    "restart-before-repair",
    "redis-loss",
)


class Slot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot_id: str
    case: StudyCase
    arm: Literal["B3", "P1", "P2"]
    schedule: Literal["SERIAL_REFERENCE", "BOUNDED_PAIR_CANDIDATE"]
    block: int
    label: Literal["ORIGINAL_PLANNED", "PLANNED_SCHEDULE_REPEAT"]
    reference_slot: str | None = None

    @model_validator(mode="after")
    def guard(self) -> "Slot":
        if not self.case.case_id.startswith(PREFIX):
            raise ValueError("MAIN_INPUT_GUARD")
        if self.case.observation_budget_seconds != 600:
            raise ValueError("UNCHANGED_WINDOW_REQUIRED")
        if (self.label == "PLANNED_SCHEDULE_REPEAT") != (self.reference_slot is not None):
            raise ValueError("SCHEDULE_REPEAT_LINK_REQUIRED")
        return self


def build(prototypes: list[StudyCase]) -> list[Slot]:
    if any(not c.case_id.startswith("cal-v4-") for c in prototypes):
        raise ValueError("CALIBRATION_PROTOTYPES_ONLY")
    selected = {
        name: next(c for c in prototypes if c.generator_family == name) for name in FAMILIES
    }
    slots: list[Slot] = []
    for i, family in enumerate(FAMILIES):
        for arm in ARMS:
            case = selected[family].model_copy(
                update={
                    "case_id": f"{PREFIX}s{i + 1:02d}",
                    "cluster_id": f"p83-context-{i + 1:02d}",
                }
            )
            slots.append(
                Slot(
                    slot_id=f"serial-{i + 1:02d}-{arm}",
                    case=case,
                    arm=arm,
                    schedule="SERIAL_REFERENCE",
                    block=len(slots) + 1,
                    label="ORIGINAL_PLANNED",
                )
            )
    for j, arm in enumerate(ARMS):
        for i in (4, 5):
            case = selected[FAMILIES[i]].model_copy(
                update={
                    "case_id": f"{PREFIX}p{i + 1:02d}",
                    "cluster_id": f"p83-context-{i + 1:02d}",
                }
            )
            slots.append(
                Slot(
                    slot_id=f"pair-{j + 1:02d}-{arm}-{i + 1:02d}",
                    case=case,
                    arm=arm,
                    schedule="BOUNDED_PAIR_CANDIDATE",
                    block=19 + j,
                    label="PLANNED_SCHEDULE_REPEAT",
                    reference_slot=f"serial-{i + 1:02d}-{arm}",
                )
            )
    return slots


def eligible(first: dict[str, int], current: dict[str, int], remaining_seconds: float) -> bool:
    """Only admits a finite pair with a measured reference and full-window reserve."""
    return (
        first["minimum_available_memory_bytes"] >= 4 * 1024**3
        and first["peak_used_memory_bytes"] <= 3 * 1024**3
        and current["available_memory_bytes"] >= 4 * 1024**3
        and current["system_free_bytes"] >= 5 * 1024**3
        and min(current["output_free_bytes"], current["backup_free_bytes"]) >= 2 * 1024**3
        and remaining_seconds >= 1200
    )


def budget(compute: str, ipv4: str, disk: str) -> dict[str, str]:
    six_hours = (Decimal(compute) + Decimal(ipv4)) * 6 + Decimal(disk) * 40 * 6 / 730
    retention = Decimal(disk) * 40 * 48 / 730
    total = six_hours + retention + Decimal("0.50")
    return {
        "six_hour_host": str(six_hours),
        "two_day_disk": str(retention),
        "contingency": "0.50",
        "total": str(total),
        "ceiling": "2.00",
        "within_ceiling": str(total <= Decimal("2.00")),
    }


def validate_plan(path: Path) -> list[Slot]:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    if data["main_started"] is not False or data["classification"] != "CALIBRATION_ONLY":
        raise ValueError("MAIN_CAMPAIGN_GUARD")
    slots = [Slot.model_validate(s) for s in data["slots"]]
    if len(slots) != 24 or len({s.slot_id for s in slots}) != 24:
        raise ValueError("FIXED_SIZE_AND_UNIQUE_ORDER_REQUIRED")
    return slots
