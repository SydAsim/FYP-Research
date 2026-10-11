"""Explicit research-arm mechanism switches; no implicit inheritance at runtime."""

from dataclasses import dataclass
from enum import StrEnum


class Arm(StrEnum):
    B0 = "B0"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    P1 = "P1"
    P2 = "P2"


@dataclass(frozen=True)
class ArmProfile:
    arm: Arm
    durable_idempotency: bool
    reconcile_before_retry: bool
    revision_invalidation: bool
    transaction_staging: bool
    compensation: bool
    playback_tracking: bool
    claim_permits: bool
    product_state_invariants: bool
    durable_played_span_repair: bool


PROFILES: dict[Arm, ArmProfile] = {
    Arm.B0: ArmProfile(Arm.B0, False, False, False, False, False, False, False, False, False),
    Arm.B1: ArmProfile(Arm.B1, True, True, False, False, False, False, False, False, False),
    Arm.B2: ArmProfile(Arm.B2, True, True, True, True, True, False, False, False, False),
    Arm.B3: ArmProfile(Arm.B3, True, True, True, True, True, True, False, False, False),
    Arm.P1: ArmProfile(Arm.P1, True, True, True, True, True, True, True, True, False),
    Arm.P2: ArmProfile(Arm.P2, True, True, True, True, True, True, True, True, True),
}


def profile(arm: Arm) -> ArmProfile:
    return PROFILES[arm]
