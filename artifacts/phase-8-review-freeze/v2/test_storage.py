import json
from pathlib import Path
from typing import Any

import pytest
from controls import Journal, read, utc, write_new
from storage import OfflineCloud, complete_backup, make_backup, upload, verify_local
from test_controls import calibration, sample


def slot_archive(tmp: Path) -> tuple[Path, dict[str, Any], Path]:
    from research.execution_setup.core import Ledger

    root, authority = calibration(tmp)
    slot = Journal(root).admit(authority, sample(), utc(), 0)
    assert slot is not None
    slot_root = root / "slots/0001"
    ledger = Ledger(slot_root)
    for name in ("qualification-plan.json", "resources.json", "source-seal.json", "config.json"):
        write_new(slot_root / name, {"classification": "LOCAL_CONTROL_ONLY"})
    trace = slot_root / "executions" / slot["execution_id"] / "export.json"
    write_new(trace, {"classification": "LOCAL_CONTROL_ONLY", "execution_id": slot["execution_id"]})
    ledger.seal(trace)
    archive = make_backup(slot_root, tmp / "archives", dumps=False)
    Journal(root).update(slot["execution_id"], state="EXPORTED")
    return root, slot, archive


def test_per_slot_verified_backup_and_next_admission(tmp_path: Path) -> None:
    root, slot, archive = slot_archive(tmp_path)
    from runner import authority_for

    authority = authority_for(root)
    cloud = OfflineCloud(tmp_path / "remote-copy")
    proof = complete_backup(Journal(root), cloud, authority.policy, slot, archive)
    cloud.verify(proof)
    assert Journal(root).rows()[0]["state"] == "BACKED_UP"
    next_slot = Journal(root).admit(authority, sample(), utc(), cloud.inventory())
    assert next_slot and next_slot["sequence"] == 2
    assert archive.is_file() and (cloud.root / proof.version_id).is_file()


def test_backup_hash_failure_stops_next_slot_and_preserves_archive(tmp_path: Path) -> None:
    root, slot, archive = slot_archive(tmp_path)
    from runner import authority_for

    damaged = archive.read_bytes()[:-20]
    archive.write_bytes(damaged)
    with pytest.raises(ValueError, match="ARCHIVE_DRIFT"):
        complete_backup(
            Journal(root),
            OfflineCloud(tmp_path / "remote-copy"),
            authority_for(root).policy,
            slot,
            archive,
        )
    assert archive.read_bytes() == damaged
    assert Journal(root).rows()[0]["state"] == "EXPORTED"
    assert read(root / "pause.json")["reason"] == "BACKUP_FAILURE"
    with pytest.raises(ValueError, match="NO_AUTO_UNPAUSE"):
        Journal(root).resume()


def test_ambiguous_cloud_write_keeps_reservation_and_refuses_resend(tmp_path: Path) -> None:
    root, _, archive = slot_archive(tmp_path)
    from runner import authority_for

    class InterruptedCloud(OfflineCloud):
        calls = 0

        def put(self, path: Path, key: str) -> Any:
            self.calls += 1
            super().put(path, key)  # Effect occurred, response is ambiguous.
            raise TimeoutError("after cloud object persistence")

    cloud = InterruptedCloud(tmp_path / "remote-copy")
    with pytest.raises(TimeoutError):
        upload(Journal(root), cloud, authority_for(root).policy, archive)
    with pytest.raises(ValueError, match="AMBIGUOUS_UPLOAD"):
        upload(Journal(root), cloud, authority_for(root).policy, archive)
    assert cloud.calls == 1 and archive.exists()
    with Journal(root).connect() as db:
        assert db.execute("SELECT state FROM reservations").fetchone()[0] == "RESERVED"


def test_cloud_cap_reservation_before_put(tmp_path: Path) -> None:
    root, _, archive = slot_archive(tmp_path)
    from runner import authority_for

    class FullCloud(OfflineCloud):
        def inventory(self) -> int:
            return 30 * 1024**3

        def put(self, path: Path, key: str) -> Any:
            raise AssertionError("Capacity check must precede writes")

    with pytest.raises(ValueError, match="30GIB_RESERVATION"):
        upload(
            Journal(root), FullCloud(tmp_path / "remote-copy"), authority_for(root).policy, archive
        )
    with Journal(root).connect() as db:
        assert db.execute("SELECT count(*) FROM reservations").fetchone()[0] == 0


def test_backup_members_independently_verified(tmp_path: Path) -> None:
    _, _, archive = slot_archive(tmp_path)
    from controls import hash_file

    verify_local(archive, hash_file(archive))
    with pytest.raises(ValueError, match="LOCAL_ARCHIVE_DRIFT"):
        verify_local(archive, "0" * 64)


def test_database_backup_failure_retains_partial_attempt(tmp_path: Path, monkeypatch: Any) -> None:
    from research.execution_setup.core import Ledger

    root = tmp_path / "slot"
    Ledger(root)
    for name in ("qualification-plan.json", "source-seal.json", "config.json"):
        write_new(root / name, {})
    write_new(root / "resources.json", {"containers": ["isolated-app", "isolated-truth"]})
    from subprocess import CompletedProcess

    monkeypatch.setattr(
        "storage.subprocess.run",
        lambda *a, **k: CompletedProcess(
            args=a, returncode=1, stdout=b"", stderr=b"controlled local pg_dump failure"
        ),
    )
    with pytest.raises(ValueError, match="POSTGRES_DUMP_FAILED"):
        make_backup(root, tmp_path / "backup")
    failures = list((tmp_path / "backup").glob("*/setup_app-FAILURE.json"))
    assert len(failures) == 1 and json.loads(failures[0].read_text())["exit"] == 1


def test_final_master_backup_is_verified_without_overwriting_originals(tmp_path: Path) -> None:
    from storage import final_backup

    root, slot, archive = slot_archive(tmp_path)
    from runner import authority_for

    cloud = OfflineCloud(tmp_path / "remote-copy")
    complete_backup(Journal(root), cloud, authority_for(root).policy, slot, archive)
    final = final_backup(Journal(root), tmp_path / "final-copy")
    from controls import hash_file

    verify_local(final, hash_file(final))
    proof = upload(Journal(root), cloud, authority_for(root).policy, final)
    cloud.verify(proof)
    assert final.exists() and archive.exists()
    import tarfile

    with tarfile.open(final, "r:gz") as content:
        assert "slot/backups/" + slot["execution_id"] + ".json" in content.getnames()
