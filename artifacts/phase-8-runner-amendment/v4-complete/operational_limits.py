"""Explicit, signed continuation-only operational policy; original study policy stays intact."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from controls import Policy, Strict, hash_file, read
from pydantic import Field

HERE = Path(__file__).resolve().parent
LIMITS_SHA256 = "68421df365be6cd8696c137e7b5f32c27634b87085315086ee3b1841c2841769"
BASE_V6_PACKAGE = "3807d690ad46abdd07da12710ea933e03e3d86fb4440f5933b186db74de76a34"


class OperationalLimits(Strict):
    kind: Literal["PROPOSED_OPERATIONAL_LIMIT_AMENDMENT_NOT_AUTHORIZATION"]
    version: Literal["phase85-continuation-v12"]
    qualified_v6_package_hash: Literal[
        "3807d690ad46abdd07da12710ea933e03e3d86fb4440f5933b186db74de76a34"
    ]
    run_id: Literal["p85-01a116f7-3b82-7a79-8653-3aee62dc99e9"]
    original_deadline: Literal["2026-10-22T15:24:23.810674Z"]
    amended_deadline: Literal["2026-10-26T12:00:00Z"]
    original_clock_anchor: Literal["2026-10-07T15:24:23.810674Z"]
    elapsed_host_limit_hours: float = Field(ge=452.5933859238889, le=452.5933859238889)
    retention_decision_deadline: Literal["2026-10-28T12:00:00Z"]
    admission_committed_usd: Literal[76]
    budget_usd: Literal[77]
    cloud_limit_bytes: Literal[85899345920]
    backup_archive_limit_bytes: Literal[85899345920]
    working_limit_bytes: Literal[53687091200]
    slot_reservation_bytes: Literal[1073741824]
    volume_gib: Literal[160]
    retention: str
    no_automatic_increases: Literal[True]
    original_policy_and_receipts_unchanged: Literal[True]


def verified_limits() -> OperationalLimits:
    path = HERE / "operational-limit-proposal.json"
    if hash_file(path) != LIMITS_SHA256:
        raise ValueError("OPERATIONAL_LIMIT_AMENDMENT_DRIFT")
    return OperationalLimits.model_validate(read(path))


class EffectiveContinuationPolicy(Policy):
    host_hours: Literal[360, 432] | float = 452.5933859238889
    budget_usd: Literal[65, 75, 77] = 77
    admission_committed_usd: Literal[55, 60, 70, 74, 76] = 76

    @property
    def backup_archive_limit_bytes(self) -> int:
        return verified_limits().backup_archive_limit_bytes

    def committed_cost(self, at: datetime) -> float:
        # Original elapsed clock, compute/disk/request reservations unchanged.
        # Base historic policy reserves 30GiB; explicitly reserve the full 80GiB.
        return super().committed_cost(at) + 50 * self.s3_usd_gib_month + 1.25


def effective_policy(original: dict[str, Any]) -> EffectiveContinuationPolicy:
    limits = verified_limits()
    return EffectiveContinuationPolicy.model_validate(
        {
            **original,
            "host_hours": limits.elapsed_host_limit_hours,
            "budget_usd": limits.budget_usd,
            "admission_committed_usd": limits.admission_committed_usd,
            "cloud_limit_bytes": limits.cloud_limit_bytes,
        }
    )
