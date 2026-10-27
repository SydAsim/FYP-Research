"""Fresh bracketed operational clock samples; never adjust research timestamps."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from controls import Policy, clock_check, utc

MAX_BRACKET_SECONDS = 0.05
METHOD = "monotonic-wall-monotonic-v1"


@dataclass(frozen=True)
class Sample:
    wall: datetime
    before: float
    after: float

    @property
    def midpoint(self) -> float:
        return self.before + (self.after - self.before) / 2

    def record(self) -> dict[str, Any]:
        return {
            "sampling_method": METHOD,
            "wall": self.wall.isoformat(),
            "monotonic": self.midpoint,
            "monotonic_before": self.before,
            "monotonic_after": self.after,
            "bracket_seconds": self.after - self.before,
            "uncertainty_seconds": (self.after - self.before) / 2,
        }


def sample(
    wall: Callable[[], datetime] = utc, mono: Callable[[], float] = time.monotonic
) -> Sample:
    before = mono()
    at = wall()
    return Sample(at, before, mono())


def quality(reading: Sample) -> None:
    if (
        not math.isfinite(reading.before)
        or not math.isfinite(reading.after)
        or reading.wall.tzinfo is None
    ):
        raise ValueError("CLOCK_SAMPLE_INVALID")
    if reading.after < reading.before:
        raise ValueError("MONOTONIC_CLOCK_DRIFT")
    if reading.after - reading.before > MAX_BRACKET_SECONDS:
        raise ValueError("CLOCK_SAMPLE_UNCERTAIN")


def anchor_record(reading: Sample, boot: str) -> dict[str, Any]:
    quality(reading)
    return {"boot_id": boot, **reading.record()}


def measurement(anchor: dict[str, Any], reading: Sample, boot: str) -> dict[str, Any]:
    wall_delta = (reading.wall - datetime.fromisoformat(anchor["wall"])).total_seconds()
    mono_delta = reading.midpoint - anchor["monotonic"]
    uncertainty = reading.record()["uncertainty_seconds"] + anchor.get("uncertainty_seconds", 0.0)
    return {
        "anchor": anchor,
        "sample": reading.record(),
        "actual_boot_id": boot,
        "wall_elapsed_seconds": wall_delta,
        "monotonic_elapsed_seconds": mono_delta,
        "wall_minus_monotonic_seconds": wall_delta - mono_delta,
        "combined_sampling_uncertainty_seconds": uncertainty,
        "difference_lower_seconds": wall_delta - mono_delta - uncertainty,
        "difference_upper_seconds": wall_delta - mono_delta + uncertainty,
        "rollback_threshold_seconds": 5,
        "comparison_rhs_seconds": mono_delta - 5,
        "point_comparison_rejects": wall_delta < mono_delta - 5,
    }


def check(policy: Policy, anchor: dict[str, Any], reading: Sample, boot: str) -> None:
    # Boot identity and counter direction remain fail-closed before other checks.
    if boot != anchor["boot_id"]:
        raise ValueError("HOST_REBOOT_UNQUALIFIED")
    quality(reading)
    if anchor.get("sampling_method") != METHOD:
        raise ValueError("BRACKETED_BOOT_ANCHOR_REQUIRED")
    anchored = Sample(
        datetime.fromisoformat(anchor["wall"]),
        anchor["monotonic_before"],
        anchor["monotonic_after"],
    )
    quality(anchored)
    if anchor_record(anchored, anchor["boot_id"]) != anchor:
        raise ValueError("CLOCK_ANCHOR_OPERAND_DRIFT")
    # The existing five-second check is called unchanged with fresh paired values.
    clock_check(policy, anchor, reading.wall, reading.midpoint, boot)
