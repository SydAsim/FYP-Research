"""Fixed offline integration checks, including read-only retained PostgreSQL dump."""

import ast
import subprocess
from pathlib import Path

import pytest
from controls import Journal, hash_file, read, utc, write_new
from postflight import recover
from runner import HERE, REPO, initialize
from storage import ObjectProof, OfflineCloud, make_backup, reconcile_upload, upload, verify_local
from test_controls import calibration, sample
from test_storage import slot_archive
from test_transport import FakeStore


def test_integrated_backup_download_extract(tmp_path: Path) -> None:
    root, slot, archive = slot_archive(tmp_path)
    cloud = OfflineCloud(tmp_path / "remote")
    proof = upload(Journal(root), cloud, __import__("runner").authority_for(root).policy, archive)
    output = recover(proof, tmp_path / "p", FakeStore(archive.read_bytes()))
    assert (
        read(output / "slot/executions" / slot["execution_id"] / "export.json")["execution_id"]
        == slot["execution_id"]
    )
    assert read(tmp_path / "p/postflight-verified.json")["cleanup_authorized"] is False
    assert archive.exists()


def test_read_only_ambiguous_backup_reconciliation(tmp_path: Path) -> None:
    root, _, archive = slot_archive(tmp_path)

    class Interrupted(OfflineCloud):
        calls = 0

        def put(self, path: Path, key: str) -> ObjectProof:
            self.calls += 1
            super().put(path, key)
            raise TimeoutError("control-only lost response")

    cloud = Interrupted(tmp_path / "remote")
    with pytest.raises(TimeoutError):
        upload(Journal(root), cloud, __import__("runner").authority_for(root).policy, archive)
    proof = reconcile_upload(Journal(root), cloud, archive)
    cloud.verify(proof)
    assert cloud.calls == 1 and read(root / "pause.json")["reason"] == "BACKUP_FAILURE"
    assert (
        upload(Journal(root), cloud, __import__("runner").authority_for(root).policy, archive)
        == proof
    )
    assert cloud.calls == 1


def test_exact_main_saved_order_and_contract_units() -> None:
    bank = read(REPO / "research/fixtures/phase8_design_v4/inputs.json")
    order = read(REPO / "artifacts/phase-8-study-design/v4/execution-order.json")["rows"]
    schedule = read(REPO / "artifacts/phase-8-review-freeze/v1/schedule.json")["rows"]
    assert len(bank["main_inputs"]) == len(order) == 500
    assert len(schedule) == 1500
    assert [(s["case_id"], s["arm"]) for s in schedule] == [
        (p["case_id"], arm) for p in order for arm in p["arm_order"]
    ]
    assert all(s["attempt"] == 1 and s["execution_id"] is None for s in schedule)
    sql = (REPO / "database/001_initial_schema.sql").read_text()
    assert "max_attempts integer NOT NULL DEFAULT 8" in sql
    worker = (REPO / "apps/durable_worker/phase2.py").read_text()
    assert "attempt_count >= lease.max_attempts" in worker
    tree = ast.parse((REPO / "research/remedies/runner.py").read_text())
    assert any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "range"
        and len(n.args) == 1
        and isinstance(n.args[0], ast.Constant)
        and n.args[0].value == 30
        for n in ast.walk(tree)
    )
    design = (REPO / "research/study_v4/design.py").read_text()
    assert '"reconcile": 8' in design and '"drain_passes": 30' in design


def test_main_init_without_authorization_creates_no_ledger_or_resources(tmp_path: Path) -> None:
    root, cal = calibration(tmp_path / "control")
    main = cal.policy.model_copy(update={"scope": "CAMPAIGN", "run_id": "test-blocked-main"})
    destination = tmp_path / "blocked-main"
    with pytest.raises(ValueError, match="PACKAGE_SCOPE"):
        initialize(
            destination,
            cal.source,
            cal.manifest,
            main,
            cal.receipts,
            cal.key,
            cal.source / "schedule.json",
            tmp_path / "backup2",
        )
    assert not destination.exists()


@pytest.mark.skipif(
    __import__("sys").platform != "linux",
    reason="Linux process boundary exercised in separate local container",
)
def test_linux_terminal_and_process_identity(tmp_path: Path) -> None:
    from research.execution_linux_v1.platform import process_identity, runner_lock

    with runner_lock(tmp_path):
        with pytest.raises(RuntimeError, match="ALREADY_ACTIVE"), runner_lock(tmp_path):
            pass
    process = subprocess.Popen([__import__("sys").executable, "-c", "import time;time.sleep(30)"])
    try:
        assert process_identity(process.pid) is not None
    finally:
        process.terminate()
        process.wait(timeout=10)
    assert process_identity(process.pid) is None
    cli = subprocess.run(
        [__import__("sys").executable, str(HERE / "runner.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "install-watchdog" in cli.stdout and "reconcile-backup" in cli.stdout
    from runner import campaign_unit, watchdog_unit

    unit = campaign_unit(tmp_path)
    assert "KillMode=process" in unit and "Restart=no" in unit
    assert ".venv-transport/lib/python3.12/site-packages" in watchdog_unit(tmp_path)


@pytest.mark.skipif(
    __import__("sys").platform != "linux", reason="Owned service shutdown requires Linux pidfd"
)
def test_export_recovery_quiesces_real_owned_process_only(tmp_path: Path) -> None:
    import sys

    from runner import quiesce

    from research.execution_linux_v1.platform import boot_id, process_identity

    root, authority = calibration(tmp_path)
    slot = Journal(root).admit(authority, sample(), utc(), 0)
    assert slot
    folder = root / "slots/0001"
    execution = folder / "executions" / slot["execution_id"]
    process = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    other = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"])
    try:
        write_new(execution / "linux-boot.json", {"boot_id": boot_id()})
        write_new(
            execution / "services.json",
            {
                "records": {
                    "owned": {"pid": process.pid, "identity": process_identity(process.pid)},
                    "reused_pid": {
                        "pid": other.pid,
                        "identity": int(process_identity(other.pid) or 0) + 1,
                    },
                }
            },
        )
        quiesce(folder, slot["execution_id"])
        process.wait(timeout=10)
        assert other.poll() is None
    finally:
        for child in (process, other):
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=10)


def qualify_existing_postgres(output: Path) -> None:
    """Two real, already-isolated DBs; pg_dump only, no mutations/driver/cloud."""
    from research.execution_setup.core import Ledger

    folder = output / "slot"
    Ledger(folder)
    write_new(
        folder / "resources.json",
        {"containers": ["p8-linux-v1-1d9f386587-app", "p8-linux-v1-1d9f386587-truth"]},
    )
    for name in ("qualification-plan.json", "source-seal.json", "config.json"):
        write_new(folder / name, {"classification": "CALIBRATION_READ_ONLY_BACKUP_CHECK"})
    write_new(folder / "executions/control-only.json", {"main_executions": 0, "cloud_calls": 0})
    archive = make_backup(folder, output / "backup")
    verify_local(archive, hash_file(archive))
    write_new(
        output / "result.json",
        {
            "classification": "CALIBRATION_READ_ONLY_BACKUP_CHECK",
            "archive": str(archive),
            "sha256": hash_file(archive),
            "main_executions": 0,
            "cloud_calls": 0,
            "both_real_postgres_dumps": True,
            "retired_resources": False,
        },
    )


if __name__ == "__main__":
    qualify_existing_postgres(HERE / "local-postgres-qualification")
