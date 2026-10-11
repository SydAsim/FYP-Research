"""Finite control calibration. Tokens have CALIBRATION scope, never main approval."""

import hashlib
import hmac
import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from controls import (
    Authority,
    Journal,
    Policy,
    canonical,
    guard,
    hash_file,
    policy_commitment,
    read,
    utc,
    write_new,
)
from runner import initialize, unit_text, verify_run, watchdog_tick


def sample() -> dict[str, int]:
    return {
        "available_memory_bytes": 4 * 1024**3,
        "system_free_bytes": 100 * 1024**3,
        "output_free_bytes": 100 * 1024**3,
        "backup_free_bytes": 100 * 1024**3,
    }


def calibration(tmp: Path) -> tuple[Path, Authority]:
    tmp.mkdir(parents=True, exist_ok=True)
    source = tmp / "source"
    fixture = source / "research/fixtures/phase8_design_v4/inputs.json"
    original = Path(__file__).resolve().parents[3] / fixture.relative_to(source)
    bank = read(original)
    write_new(fixture, bank)
    case = bank["calibration_inputs"][0]
    from research.study.models import StudyCase

    rows = [
        {
            "sequence": i + 1,
            "case_id": case["case_id"],
            "arm": arm,
            "fixture_hash": StudyCase.model_validate(case).fixture_hash,
        }
        for i, arm in enumerate(case["arm_order"])
    ]
    schedule = source / "schedule.json"
    write_new(schedule, {"rows": rows, "classification": "CALIBRATION_ONLY"})
    files = {
        fixture.relative_to(source).as_posix(): hash_file(fixture),
        "schedule.json": hash_file(schedule),
    }
    manifest = source / "manifest.json"
    package_hash = hashlib.sha256(canonical(files)).hexdigest()
    write_new(
        manifest,
        {
            "kind": "REVIEW_INVENTORY",
            "scope": "CALIBRATION",
            "files": files,
            "package_hash": package_hash,
        },
    )
    key = tmp / "synthetic-owner-test-key"
    key.write_bytes(b"test-only-never-campaign-authority" * 2)
    policy = Policy(
        scope="CALIBRATION",
        run_id="cal-p84-controls-v2",
        host_started_at=utc() - timedelta(hours=1),
    )
    receipt_root = tmp / "synthetic-calibration-capabilities"
    prior = None
    for kind in ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH"):
        body: dict[str, Any] = {
            "kind": kind,
            "scope": "CALIBRATION",
            "package_hash": package_hash,
            "policy_hash": policy_commitment(policy, kind),
            "schedule_hash": hash_file(schedule),
            "predecessor_hash": prior,
            "expires_at": (policy.stop_at + timedelta(hours=24)).isoformat(),
            "signer": "SYNTHETIC_LOCAL_TEST_NOT_USER_ACCEPTANCE",
        }
        body["signature"] = hmac.new(key.read_bytes(), canonical(body), "sha256").hexdigest()
        write_new(receipt_root / (kind + ".json"), body)
        prior = hashlib.sha256(canonical(body)).hexdigest()
    root = tmp / "execution"
    initialize(root, source, manifest, policy, receipt_root, key, schedule, tmp / "backup")
    write_new(root / "cloud.json", {"offline_root": str(tmp / "offline-cloud")})
    return root, Authority(source, manifest, policy, hash_file(schedule), receipt_root, key)


def test_valid_calibration_admission_identity_and_deadline(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    journal = Journal(root)
    original = journal.rows()
    assert all(row["state"] == "PLANNED" for row in original)
    slot = journal.admit(authority, sample(), utc(), 0)
    assert slot is not None
    assert slot["execution_id"] == original[0]["execution_id"] and slot["attempt"] == 1
    deadline = (utc() + timedelta(seconds=600)).isoformat()
    journal.update(slot["execution_id"], deadline=deadline)
    recovered = journal.admit(authority, sample(), utc(), 0)
    assert recovered and recovered["execution_id"] == slot["execution_id"]
    assert recovered["deadline"] == deadline
    with pytest.raises(ValueError, match="DEADLINE_IMMUTABLE"):
        journal.update(slot["execution_id"], deadline=utc().isoformat())


@pytest.mark.parametrize("kind", ["REVIEW_ACCEPTED", "FREEZE", "LAUNCH"])
def test_missing_authorization_stops_admission(tmp_path: Path, kind: str) -> None:
    root, authority = calibration(tmp_path)
    (authority.receipts / (kind + ".json")).unlink()
    with pytest.raises(FileNotFoundError):
        Journal(root).admit(authority, sample(), utc(), 0)
    assert all(r["state"] == "PLANNED" for r in Journal(root).rows())


def test_signature_chain_and_scope_rejection(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    path = authority.receipts / "LAUNCH.json"
    receipt = read(path)
    receipt["scope"] = "CAMPAIGN"
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="AUTHORIZATION"):
        Journal(root).admit(authority, sample(), utc(), 0)
    with pytest.raises(ValueError, match="CALIBRATION_MAIN"):
        Journal(tmp_path / "wrong-ledger").initialize(
            [{"sequence": 1, "case_id": "p8v4-0001", "arm": "B3", "fixture_hash": "x"}],
            "CALIBRATION",
        )


def test_source_and_binding_drift_stop(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    with Journal(root).connect() as db:
        db.execute("UPDATE slots SET arm='B0' WHERE sequence=1")
    with pytest.raises(ValueError, match="SLOT_BINDING_DRIFT"):
        verify_run(root)
    (authority.source / "schedule.json").write_text("source drift")
    with pytest.raises(ValueError, match="SOURCE_DRIFT"):
        Journal(root).admit(authority, sample(), utc(), 0)


@pytest.mark.parametrize(
    "hours,error", [(360, "HOST_360H"), (359.6, "ADMISSION_CUTOFF"), (340, "COMMITTED_COST")]
)
def test_time_and_budget_stops(tmp_path: Path, hours: float, error: str) -> None:
    _, authority = calibration(tmp_path)
    with pytest.raises(ValueError, match=error):
        guard(
            authority.policy, sample(), authority.policy.host_started_at + timedelta(hours=hours), 0
        )


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("available_memory_bytes", 2 * 1024**3 - 1, "RAM_STOP"),
        ("output_free_bytes", 20 * 1024**3 - 1, "DISK_STOP"),
        ("backup_free_bytes", 20 * 1024**3 - 1, "DISK_STOP"),
    ],
)
def test_resource_stops(tmp_path: Path, field: str, value: int, error: str) -> None:
    _, authority = calibration(tmp_path)
    current = sample()
    current[field] = value
    with pytest.raises(ValueError, match=error):
        guard(authority.policy, current, utc(), 0)


def test_cloud_and_active_thresholds(tmp_path: Path) -> None:
    _, authority = calibration(tmp_path)
    with pytest.raises(ValueError, match="CLOUD_30GIB"):
        guard(authority.policy, sample(), utc(), 30 * 1024**3)
    current = sample()
    current["available_memory_bytes"] = 1024**3 - 1
    with pytest.raises(ValueError, match="RAM_STOP"):
        guard(authority.policy, current, utc(), 0, active=True)
    current = sample()
    current["system_free_bytes"] = 10 * 1024**3 - 1
    with pytest.raises(ValueError, match="DISK_STOP"):
        guard(authority.policy, current, utc(), 0, active=True)


def test_pause_resume_and_prior_backup_gate(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    journal = Journal(root)
    slot = journal.admit(authority, sample(), utc(), 0)
    assert slot is not None
    journal.update(slot["execution_id"], state="EXPORTED")
    assert journal.admit(authority, sample(), utc(), 0)["sequence"] == 1
    journal.update(slot["execution_id"], state="BACKED_UP", backup_hash="offline-test-proof")
    journal.pause("BETWEEN_SLOTS")
    with pytest.raises(ValueError, match="PAUSED"):
        journal.admit(authority, sample(), utc(), 0)
    journal.resume()
    next_slot = journal.admit(authority, sample(), utc(), 0)
    assert next_slot and next_slot["execution_id"] == journal.rows()[1]["execution_id"]
    journal.pause("BACKUP_FAILURE")
    with pytest.raises(ValueError, match="NO_AUTO_UNPAUSE"):
        journal.resume()


def test_watchdog_stops_admission_but_keeps_active_window(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    at = authority.policy.stop_at - timedelta(minutes=20)
    assert watchdog_tick(root, at, sample(), 0)
    assert (root / "pause.json").exists()
    assert not watchdog_tick(root, authority.policy.stop_at, sample(), 0)
    assert all(r["state"] == "PLANNED" for r in Journal(root).rows())
    service, timer = unit_text(root, authority.policy)
    assert "shutdown -h now" in service and "Persistent=true" in timer
    assert authority.policy.stop_at.strftime("%Y-%m-%d %H:%M:%S UTC") in timer
