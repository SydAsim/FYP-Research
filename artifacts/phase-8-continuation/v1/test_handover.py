"""Finite offline controls: no driver, AWS client or services are invoked."""

import hashlib
import hmac
import json
import os
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from controls import Policy, canonical, guard, read
from handover import (
    FIRST_HASH,
    HERE,
    PARENT_FREEZE,
    REPO,
    ContinuationAuthority,
    ContinuationPolicy,
    closed_boundary,
    original_policy,
    stage,
    verify_chain,
    verify_imported_first,
)


@pytest.fixture
def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = read(HERE / "saved-identities.json")["rows"]
    return result


@pytest.fixture
def saved() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = read(REPO / "artifacts/phase-8-review-freeze/v2/schedule.json")[
        "rows"
    ]
    return result


def test_exact_existing_boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    closed_boundary(rows, saved)
    assert len({r["case_id"] for r in rows}) == 500
    assert {arm: sum(r["arm"] == arm for r in rows) for arm in ("B3", "P1", "P2")} == {
        "B3": 500,
        "P1": 500,
        "P2": 500,
    }


@pytest.mark.parametrize("change", ["active", "reordered", "duplicate", "attempt", "missing"])
def test_unsafe_boundary_rejected(
    rows: list[dict[str, Any]],
    saved: list[dict[str, Any]],
    change: str,
) -> None:
    changed = deepcopy(rows)
    if change == "active":
        changed[1]["state"] = "RUNNING"
    elif change == "reordered":
        changed[1], changed[2] = changed[2], changed[1]
    elif change == "duplicate":
        changed[1]["execution_id"] = changed[0]["execution_id"]
    elif change == "attempt":
        changed[1]["attempt"] = 2
    else:
        changed.pop()
    with pytest.raises(ValueError):
        closed_boundary(changed, saved)


def test_no_policy_reset_and_conservative_handover_guard() -> None:
    raw = read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json")
    old = original_policy(raw)
    new = ContinuationPolicy.model_validate(raw)
    assert new.model_dump(mode="json") == old.model_dump(mode="json")
    assert new.stop_at == old.stop_at
    assert new.committed_cost(new.stop_at) == pytest.approx(old.committed_cost(old.stop_at) + 1.25)
    raw["host_started_at"] = "2026-10-08T00:00:00Z"
    with pytest.raises(ValueError, match="CLOCK_RESET"):
        original_policy(raw)


def test_missing_continuation_authorization(tmp_path: Path) -> None:
    policy = Policy.model_validate(read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"))
    with pytest.raises(FileNotFoundError):
        verify_chain(
            tmp_path,
            b"synthetic-calibration-only-key!!xx",
            "a" * 64,
            policy,
            "b" * 64,
            "c" * 64,
            policy.host_started_at,
        )


def synthetic_chain(
    folder: Path,
    policy: Policy,
    package: str = "a" * 64,
    identities: str = "b" * 64,
    predecessor: str = "c" * 64,
    readiness: str = "d" * 64,
    instance: str = "i-test-only",
) -> bytes:
    key = b"synthetic-calibration-only-key!!xx"
    previous = predecessor
    for kind in ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"):
        body = {
            "kind": kind,
            "package_hash": package,
            "predecessor_hash": previous,
            "policy_sha256": hashlib.sha256(canonical(policy.model_dump(mode="json"))).hexdigest(),
            "identities_sha256": identities,
            "parent_freeze_sha256": PARENT_FREEZE,
            "first_export_sha256": FIRST_HASH,
            "expires_at": policy.stop_at.isoformat(),
            "signer": "SYNTHETIC_CONTROL_TEST_NOT_HUMAN_ACCEPTANCE",
            "readiness_sha256": readiness if kind == "CONTINUATION_LAUNCH" else None,
            "instance_id": instance if kind == "CONTINUATION_LAUNCH" else None,
        }
        signed = {**body, "signature": hmac.new(key, canonical(body), "sha256").hexdigest()}
        (folder / f"{kind}.json").write_text(json.dumps(signed))
        previous = hashlib.sha256(canonical(signed)).hexdigest()
    return key


def test_synthetic_receipt_chain_validates_only_exact_binding(tmp_path: Path) -> None:
    policy = Policy.model_validate(read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"))
    key = synthetic_chain(tmp_path, policy)
    result = verify_chain(
        tmp_path, key, "a" * 64, policy, "b" * 64, "c" * 64, policy.host_started_at
    )
    assert result.kind == "CONTINUATION_LAUNCH"
    with pytest.raises(ValueError, match="AUTHORIZATION"):
        verify_chain(tmp_path, key, "e" * 64, policy, "b" * 64, "c" * 64, policy.host_started_at)
    with pytest.raises(ValueError, match="AUTHORIZATION"):
        verify_chain(tmp_path, key, "a" * 64, policy, "e" * 64, "c" * 64, policy.host_started_at)
    with pytest.raises(ValueError, match="AUTHORIZATION"):
        verify_chain(
            tmp_path,
            key,
            "a" * 64,
            policy,
            "b" * 64,
            "c" * 64,
            policy.stop_at + timedelta(seconds=1),
        )


def test_actual_readonly_import_preserves_first_and_all_identities(tmp_path: Path) -> None:
    retained = Path(os.environ.get("P85_RETAINED_SNAPSHOT", "C:/fyp-p85/stopped-attempt1"))
    root = tmp_path / "import-calibration-control"
    result = stage(retained / "master/x/slot", retained / "slot1/x/slot", root)
    verify_imported_first(root)
    assert result["driver_calls"] == 0
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    assert not (root / "host-clock.json").exists()
    assert not (root / "slots").exists()
    with pytest.raises(ValueError, match="RETAIN_ATTEMPTS"):
        stage(retained / "master/x/slot", retained / "slot1/x/slot", root)
    copied = (
        root / "historical/first-slot/executions" / result["first_execution_id"] / "export.json"
    )
    copied.write_text("tampered")
    with pytest.raises(ValueError, match="HISTORY_DRIFT"):
        verify_imported_first(root)


def test_timing_sidecar_never_replaces_original_grade() -> None:
    side = read(REPO / "artifacts/phase-8-runner-amendment/v1/first-original-sidecar.json")
    assert side["raw_status"] == "FAILED"
    assert side["original_grade"]["values"] == side["proposed_grade"]["values"]
    assert side["original_analysis_row"]["duration_seconds"] == 600
    assert side["proposed_analysis_row"]["duration_seconds"] == 600
    assert side["original_analysis_row"]["censor_reason"] == "INFRASTRUCTURE_FAILURE"
    assert side["proposed_analysis_row"]["censor_reason"] == "NO_SUPPORTED_COMPLETION"
    assert not side["proposed_analysis_row"]["event_observed"]


def test_no_new_main_identity_initialization(tmp_path: Path) -> None:
    import runner

    policy = original_policy(read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"))
    root = tmp_path / "never-create-main"
    with pytest.raises(ValueError, match="NO_NEW_IDENTITIES"):
        runner.initialize(
            root,
            REPO,
            tmp_path / "missing",
            policy,
            tmp_path,
            tmp_path,
            tmp_path,
            tmp_path / "backup",
        )
    assert not root.exists()


def test_main_authority_refuses_source_drift_before_any_old_capability(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    data = source / "pinned.txt"
    data.write_text("original")
    files = {"pinned.txt": hashlib.sha256(data.read_bytes()).hexdigest()}
    manifest = {
        "kind": "CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE",
        "files": files,
        "package_hash": hashlib.sha256(canonical(files)).hexdigest(),
    }
    (source / "candidate.json").write_text(json.dumps(manifest))
    config = {
        "source": str(source),
        "manifest": str(source / "missing-parent.json"),
        "policy": read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"),
        "schedule_hash": "a" * 64,
        "receipts": str(tmp_path / "no-receipts"),
        "key": str(tmp_path / "no-key"),
        "continuation": {"manifest": "candidate.json", "receipts": str(tmp_path)},
    }
    data.write_text("changed")
    with pytest.raises(ValueError, match="CONTINUATION_SOURCE_DRIFT"):
        ContinuationAuthority(tmp_path, config).verify()


@pytest.mark.parametrize("stop", ["deadline", "cost", "ram", "disk", "cloud"])
def test_existing_guards_still_stop_with_handover_reserve(stop: str) -> None:
    policy = ContinuationPolicy.model_validate(
        read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json")
    )
    sample = {
        "available_memory_bytes": 3 * 1024**3,
        "system_free_bytes": 100 * 1024**3,
        "output_free_bytes": 100 * 1024**3,
        "backup_free_bytes": 100 * 1024**3,
    }
    at = policy.host_started_at
    cloud_bytes = 0
    if stop == "deadline":
        at = policy.stop_at
    elif stop == "cost":
        at += timedelta(hours=330)
    elif stop == "ram":
        sample["available_memory_bytes"] = 0
    elif stop == "disk":
        sample["output_free_bytes"] = 0
    else:
        cloud_bytes = policy.cloud_limit_bytes
    with pytest.raises(ValueError):
        guard(policy, sample, at, cloud_bytes)


def test_signature_corruption_rejected(tmp_path: Path) -> None:
    policy = original_policy(read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"))
    key = synthetic_chain(tmp_path, policy)
    receipt = tmp_path / "CONTINUATION_LAUNCH.json"
    changed = read(receipt)
    changed["signature"] = "0" * 64
    receipt.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="AUTHORIZATION"):
        verify_chain(tmp_path, key, "a" * 64, policy, "b" * 64, "c" * 64, policy.host_started_at)


def test_review_freeze_can_prepare_but_cannot_admit_without_launch(tmp_path: Path) -> None:
    policy = original_policy(read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json"))
    key = synthetic_chain(tmp_path, policy)
    (tmp_path / "CONTINUATION_LAUNCH.json").rename(tmp_path / "retained-synthetic-launch.json")
    frozen = verify_chain(
        tmp_path, key, "a" * 64, policy, "b" * 64, "c" * 64, policy.host_started_at, prelaunch=True
    )
    assert frozen.kind == "CONTINUATION_FREEZE"
    with pytest.raises(FileNotFoundError):
        verify_chain(tmp_path, key, "a" * 64, policy, "b" * 64, "c" * 64, policy.host_started_at)


def test_first_original_joins_analysis_as_retained_sidecar_not_missing() -> None:
    from analyze import imported_first_row

    row, provenance = imported_first_row(HERE / "import-preview")
    assert row.values["correction_success"] == "TRUE"
    assert row.values["correct_final_update"] == "FALSE"
    assert row.duration_seconds == 600 and row.event_observed is False
    assert row.censor_reason == "NO_SUPPORTED_COMPLETION"
    assert provenance["raw_status"] == "FAILED"
    assert provenance["original_analysis_row"]["censor_reason"] == "INFRASTRUCTURE_FAILURE"
    assert provenance["replacement_or_driver_replay"] is False


def test_backup_contains_handover_authority_but_never_private_key(tmp_path: Path) -> None:
    from storage import copy_continuation_metadata

    source, destination = tmp_path / "source", tmp_path / "backup"
    source.mkdir()
    destination.mkdir()
    original, continuation = tmp_path / "original-receipts", tmp_path / "new-receipts"
    original.mkdir()
    continuation.mkdir()
    for folder, names in (
        (original, ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH")),
        (continuation, ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH")),
    ):
        for name in names:
            (folder / f"{name}.json").write_text('{"scope":"SYNTHETIC_CONTROL_ONLY"}')
        (folder / "owner.key").write_text("never-archive-this-secret-marker")
    for name in (
        "handover.json",
        "saved-identities.json",
        "host-clock.json",
        "continuation-readiness.json",
    ):
        (source / name).write_text("{}")
    (source / "run.json").write_text(
        json.dumps(
            {
                "receipts": str(original),
                "continuation": {"receipts": str(continuation)},
            }
        )
    )
    copy_continuation_metadata(source, destination)
    copied = [p for p in destination.rglob("*") if p.is_file()]
    assert len(copied) == 10
    assert not any("never-archive-this-secret-marker" in p.read_text() for p in copied)
