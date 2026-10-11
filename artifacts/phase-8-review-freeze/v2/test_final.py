"""Finite extra checks for clock, missingness, durable seals and retirement ownership."""

from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from analyze import ENDPOINTS, unavailable
from controls import Journal, clock_check, guard, read, utc
from runner import prepare_slot, verify_binding
from test_controls import calibration, sample

from research.study.models import StudyCase


@pytest.mark.parametrize(
    "change,error", [("reboot", "HOST_REBOOT"), ("backward", "WALL_CLOCK"), ("360h", "HOST_360H")]
)
def test_clock_guard_never_resets_host_allowance(tmp_path: Path, change: str, error: str) -> None:
    _, authority = calibration(tmp_path)
    at = utc()
    anchor = {"boot_id": "calibration-boot", "monotonic": 100, "wall": at.isoformat()}
    with pytest.raises(ValueError, match=error):
        clock_check(
            authority.policy,
            anchor,
            at,
            100 + (360 * 3600 if change == "360h" else 60),
            "different-boot" if change == "reboot" else "calibration-boot",
        )
    clock_check(authority.policy, anchor, at + timedelta(seconds=60), 160, "calibration-boot")


@pytest.mark.parametrize("field", ["working_bytes", "backup_bytes"])
def test_capacity_reservation_stops_before_next_slot(tmp_path: Path, field: str) -> None:
    _, authority = calibration(tmp_path)
    current = sample()
    current[field] = 50 * 1024**3
    with pytest.raises(ValueError, match="RESERVATION_STOP"):
        guard(authority.policy, current, utc(), 0)


def test_sealed_resource_drift_prevents_worker(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    slot = Journal(root).admit(authority, sample(), utc(), 0)
    assert slot
    folder = prepare_slot(root, slot)
    from research.execution_setup.core import Ledger

    verify_binding(folder, Ledger(folder).rows()[0])
    (folder / "resources.json").write_text('{"database":"wrong"}')
    with pytest.raises(ValueError):
        verify_binding(folder, Ledger(folder).rows()[0])


def test_failure_pause_cannot_be_hidden_by_operator_pause(tmp_path: Path) -> None:
    root, _ = calibration(tmp_path)
    journal = Journal(root)
    journal.pause("BETWEEN_SLOTS")
    journal.pause("SOURCE_DRIFT")
    journal.pause("BETWEEN_SLOTS")
    assert read(root / "pause.json")["reason"] == "SOURCE_DRIFT"
    with pytest.raises(ValueError, match="NO_AUTO_UNPAUSE"):
        journal.resume()


def test_missing_original_is_explicit_unknown_without_timed_censor(tmp_path: Path) -> None:
    root, _ = calibration(tmp_path)
    slot = Journal(root).rows()[0]
    case = StudyCase.model_validate(read(root / "run.json")["cases"][slot["case_id"]])
    row = unavailable(case, slot, "CALIBRATION", "ORIGINAL_INTERRUPTED")
    assert set(row.values) == set(ENDPOINTS)
    assert set(row.values.values()) == {"UNKNOWN"}
    assert row.duration_seconds is row.event_observed is None
    assert row.execution_id == slot["execution_id"] and row.attempt == 1


def test_watchdog_main_shutdown_command_boundary_without_real_shutdown(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import runner

    root, authority = calibration(tmp_path)
    # Scope-only control object, no signed main receipt or main admission.
    policy = authority.policy.model_copy(update={"scope": "CAMPAIGN"})
    monkeypatch.setattr(
        runner, "authority_for", lambda _: __import__("types").SimpleNamespace(policy=policy)
    )
    monkeypatch.setattr(runner, "verify_clock", lambda *a: None)
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", lambda args, **kw: calls.append(args))
    assert not runner.watchdog_tick(root, policy.stop_at, sample(), 0, stop_host=True)
    assert calls == [["/sbin/shutdown", "-h", "now"]]
    assert read(root / "pause.json")["reason"] == "HOST_360H_LIMIT"


@pytest.mark.parametrize("tamper", [False, True])
def test_retirement_requires_verified_dumps_and_exact_owned_volumes(
    tmp_path: Path, monkeypatch: Any, tamper: bool
) -> None:
    import json
    from subprocess import CompletedProcess

    import runner
    import storage
    from controls import hash_file, write_new
    from test_storage import slot_archive

    root, slot, _ = slot_archive(tmp_path)
    folder = root / "slots/0001"
    names = ["cal-retire-app", "cal-retire-truth", "cal-retire-cache"]
    (folder / "resources.json").write_text(
        json.dumps({"resource_id": "cal-retire", "containers": names})
    )
    calls = []

    def command(args: list[str], **kw: Any) -> Any:
        calls.append(args)
        if "pg_dump" in args:
            return CompletedProcess(args, 0, stdout=b"-- control-only SQL backup\n", stderr=b"")
        return CompletedProcess(
            args, 0, stdout="" if kw.get("text") else b"", stderr="" if kw.get("text") else b""
        )

    monkeypatch.setattr(storage.subprocess, "run", command)
    archive = storage.make_backup(folder, tmp_path / "retirement-backup", dumps=True)
    storage.complete_backup(
        Journal(root), runner.cloud_for(root), runner.authority_for(root).policy, slot, archive
    )
    inspected = set(names)

    def inspect(name: str, owner: str) -> Any:
        if name not in inspected:
            return None
        return {"Mounts": [{"Destination": "/var/lib/postgresql/data", "Name": name + "-data"}]}

    monkeypatch.setattr("research.execution_linux_v1.runtime.inspect_owned", inspect)
    if tamper:
        intent = folder / "retirement-intent.json"
        write_new(
            intent,
            {
                "execution_id": slot["execution_id"],
                "backup_hash": hash_file(root / "backups" / (slot["execution_id"] + ".json")),
                "containers": names,
                "volumes": ["unrelated-project-data", names[1] + "-data"],
            },
        )
        Journal(root).event("RETIREMENT_INTENT", hash=hash_file(intent))
        calls.clear()
        with pytest.raises(ValueError, match="RETIREMENT_BINDING_DRIFT"):
            runner.retire(root, slot)
        assert not calls and not (folder / "retired.json").exists()
    else:
        runner.retire(root, slot)
        deleted = [args[-1] for args in calls if args[:3] == ["docker", "volume", "rm"]]
        assert deleted == [name + "-data" for name in names[:2]]
        assert read(folder / "retired.json")["raw_evidence_local_and_cloud_retained"] is True
        assert archive.exists()


def test_ledger_state_tamper_and_deleted_pause_are_rejected(tmp_path: Path) -> None:
    root, authority = calibration(tmp_path)
    journal = Journal(root)
    slot = journal.admit(authority, sample(), utc(), 0)
    assert slot
    with journal.connect() as db:
        db.execute("UPDATE slots SET state='BACKED_UP' WHERE sequence=1")
    with pytest.raises(ValueError, match="TRANSITION_DRIFT"):
        journal.verify()
