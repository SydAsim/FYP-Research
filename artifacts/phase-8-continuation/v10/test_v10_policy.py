"""Focused operational/authority checks only; no scenarios or application services."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

SOURCE = Path(os.environ.get("V10_SOURCE", "E:/p8v10/source"))
HERE = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete"
sys.path[:0] = [str(HERE), str(SOURCE)]

from controls import Policy, canonical, clock_check, guard, read  # noqa: E402
from handover import original_policy, verify_chain  # noqa: E402
from operational_limits import LIMITS_SHA256, effective_policy, verified_limits  # noqa: E402
from runner import unit_text  # noqa: E402


def policy() -> Policy:
    return effective_policy(read(HERE / "original-launch-policy.json"))


def sample() -> dict[str, int]:
    return {
        "available_memory_bytes": 8 * 1024**3,
        "system_free_bytes": 160 * 1024**3,
        "output_free_bytes": 160 * 1024**3,
        "backup_free_bytes": 160 * 1024**3,
    }


def test_effective_limits_keep_original_clock_accounting_and_windows() -> None:
    amended = policy()
    original = original_policy(read(HERE / "original-launch-policy.json"))
    assert original.host_hours == 360 and original.budget_usd == 65
    assert amended.host_started_at == original.host_started_at
    assert amended.host_hours == 432 and amended.budget_usd == 75
    assert amended.admission_committed_usd == 70 and amended.observation_seconds == 600
    assert amended.stop_at == datetime.fromisoformat("2026-10-25T15:24:23.810674+00:00")
    assert amended.cloud_limit_bytes == amended.backup_archive_limit_bytes == 80 * 1024**3
    assert amended.committed_cost(amended.stop_at) == pytest.approx(72.22012602739726)


def test_exact_overlay_hash_and_retention() -> None:
    assert (
        hashlib.sha256((HERE / "operational-limit-proposal.json").read_bytes()).hexdigest()
        == LIMITS_SHA256
    )
    limits = verified_limits()
    assert limits.retention_decision_deadline == "2026-10-27T15:24:23.810674Z"


def test_unapproved_elapsed_limit_rejected() -> None:
    from pydantic import ValidationError

    body = policy().model_dump(mode="json")
    body["host_hours"] = 433
    with pytest.raises(ValidationError):
        Policy.model_validate(body)


def test_beyond_old_deadline_uses_amended_window() -> None:
    guard(policy(), sample(), datetime.fromisoformat("2026-10-23T00:00:00+00:00"), 0)


@pytest.mark.parametrize("reason", ["deadline", "cutoff", "cost", "cloud"])
def test_existing_failed_guard_paths_remain_fail_closed(reason: str) -> None:
    p = policy()
    at = p.host_started_at + timedelta(days=6)
    cloud = 0
    if reason == "deadline":
        at = p.stop_at
    elif reason == "cutoff":
        at = p.stop_at - timedelta(seconds=1800)
    elif reason == "cost":
        at = datetime.fromisoformat("2026-10-25T00:00:00+00:00")
    else:
        cloud = 80 * 1024**3
    with pytest.raises(ValueError):
        guard(p, sample(), at, cloud)


@pytest.mark.parametrize("bad", ["rollback", "boot"])
def test_clock_faults_remain_detected(bad: str) -> None:
    p = policy()
    at = p.host_started_at + timedelta(hours=150)
    anchor = {"boot_id": "cal-boot", "monotonic": 10.0, "wall": at.isoformat()}
    with pytest.raises(ValueError):
        clock_check(p, anchor, at, 20.0, "other" if bad == "boot" else "cal-boot")


def test_timer_bound_to_absolute_432_hour_limit() -> None:
    _, timer = unit_text(Path("/cal-v10/run"), policy())
    assert "OnCalendar=2026-10-25 15:24:23 UTC" in timer
    assert "OnBootSec=432h" in timer and "Persistent=true" in timer
    original = original_policy(read(HERE / "original-launch-policy.json"))
    assert "OnBootSec=360h" in unit_text(Path("/cal-old/run"), original)[1]


@pytest.mark.parametrize("wrong", [False, True])
def test_current_chain_binds_effective_policy_and_parent(tmp_path: Path, wrong: bool) -> None:
    p = policy()
    key = b"cal-v10-owner-not-a-real-key-00000"
    previous = "a" * 64
    chain_start = previous
    for kind in ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"):
        body: dict[str, Any] = {
            "kind": kind,
            "package_hash": "b" * 64,
            "operational_limits_sha256": LIMITS_SHA256,
            "predecessor_hash": previous,
            "policy_sha256": hashlib.sha256(canonical(p.model_dump(mode="json"))).hexdigest(),
            "identities_sha256": "c" * 64,
            "parent_freeze_sha256": (
                "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"
            ),
            "first_export_sha256": (
                "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b"
            ),
            "second_export_sha256": (
                "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42"
            ),
            "immediate_parent_freeze_sha256": (
                "92ef953de04518facf4c6dcc72d13572e1648ccad28001bad58ee435969a5162"
            ),
            "expires_at": p.stop_at.isoformat(),
            "signer": "cal-v10",
            "readiness_sha256": "d" * 64 if kind.endswith("LAUNCH") else None,
            "instance_id": "cal-host" if kind.endswith("LAUNCH") else None,
        }
        if wrong:
            body["policy_sha256"] = hashlib.sha256(
                canonical(
                    original_policy(read(HERE / "original-launch-policy.json")).model_dump(
                        mode="json"
                    )
                )
            ).hexdigest()
        raw = {**body, "signature": hmac.new(key, canonical(body), "sha256").hexdigest()}
        (tmp_path / (kind + ".json")).write_text(json.dumps(raw))
        previous = hashlib.sha256(canonical(raw)).hexdigest()
    at = datetime.fromisoformat("2026-10-23T00:00:00+00:00")
    if wrong:
        with pytest.raises(ValueError, match="INVALID_CONTINUATION_AUTHORIZATION"):
            verify_chain(tmp_path, key, "b" * 64, p, "c" * 64, chain_start, at)
    else:
        assert (
            verify_chain(tmp_path, key, "b" * 64, p, "c" * 64, chain_start, at).instance_id
            == "cal-host"
        )


def test_exact_pause_release_is_hash_bound() -> None:
    text = (HERE / "handover.py").read_text()
    assert 'hash_file(root / "pause.json") != hash_file(HERE / "closed-145/pause.json")' in text
    assert "retained-driver145-pause-v10.json" in text
