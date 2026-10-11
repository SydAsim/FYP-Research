"""Real Linux process/lock checks and protocol guard regressions; no main inputs."""

import json
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from research.execution_linux_v1.platform import (
    memory_sample,
    process_identity,
    runner_lock,
    stop_owned,
)
from research.execution_setup.core import Ledger


def sleeper() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", "import sys,signal;print('READY',flush=True);signal.pause()"],
        stdout=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )


def test_cgroup_memory_cannot_borrow_host_headroom(tmp_path: Path) -> None:
    proc, cgroup = tmp_path / "proc", tmp_path / "cgroup"
    proc.mkdir()
    cgroup.mkdir()
    (proc / "meminfo").write_text("MemTotal: 8000000 kB\nMemAvailable: 6000000 kB\n")
    (cgroup / "memory.max").write_text(str(2 * 1024**3))
    (cgroup / "memory.current").write_text(str(1024**3))
    sampled = memory_sample(proc, cgroup)
    assert sampled["total_memory_bytes"] == 2 * 1024**3
    assert sampled["available_memory_bytes"] == 1024**3


def test_lock_rejects_other_process_and_releases_after_exit(tmp_path: Path) -> None:
    code = (
        "from pathlib import Path; from research.execution_linux_v1.platform import runner_lock; "
        f"\nwith runner_lock(Path({str(tmp_path)!r})): print('ACQUIRED')"
    )
    with runner_lock(tmp_path):
        refused = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert refused.returncode != 0 and "RUNNER_ALREADY_ACTIVE" in refused.stderr
    accepted = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert accepted.returncode == 0 and "ACQUIRED" in accepted.stdout


def test_identity_mismatch_does_not_signal_process() -> None:
    child = sleeper()
    try:
        assert child.stdout and child.stdout.readline().strip() == "READY"
        identity = process_identity(child.pid)
        assert identity is not None
        stop_owned(child.pid, identity + 1)
        assert child.poll() is None
        stop_owned(child.pid, identity)
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_detached_child_survives_launching_terminal_process(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid.json"
    child_code = "import signal;signal.pause()"
    code = (
        "import subprocess,sys,json,pathlib; "
        f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}],start_new_session=True); "
        f"pathlib.Path({str(pid_file)!r}).write_text(json.dumps({{'pid':p.pid}}))"
    )
    parent = subprocess.run([sys.executable, "-c", code], timeout=5)
    assert parent.returncode == 0
    pid = json.loads(pid_file.read_text())["pid"]
    identity = process_identity(pid)
    assert identity is not None
    stop_owned(pid, identity)


def test_new_linux_main_guard_and_fixed_deadline(tmp_path: Path) -> None:
    # Run installation in a separate process: never mutate the Windows regression suite.
    code = """
from pathlib import Path
from research.execution_linux_v1.runner import install, PREFIX
from research.execution_setup.core import Ledger
install()
ledger=Ledger(Path(__import__('sys').argv[1]))
with ledger.connect() as c:
 c.execute("INSERT INTO slots(sequence,case_id,arm,state,attempt,label) "
           "VALUES (1,?,'P2','PLANNED',1,'ORIGINAL_PLANNED')",(PREFIX+'0001',))
slot=ledger.admit()
ledger.update(slot['execution_id'], deadline='2030-01-01T00:10:00+00:00',state='CHECKPOINTED')
assert ledger.admit()['execution_id']==slot['execution_id']
try: ledger.update(slot['execution_id'],deadline='2030-01-01T00:20:00+00:00')
except ValueError: pass
else: raise AssertionError('deadline reset allowed')
with ledger.connect() as c:
 c.execute("UPDATE slots SET state='PLANNED',case_id='p8v4-0001',execution_id=NULL")
try: ledger.admit()
except ValueError as e: assert 'MAIN_CAMPAIGN_GUARD' in str(e)
else: raise AssertionError('main admitted')
print('PASS MAIN GUARD AND SAME DEADLINE')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_failed_boot_attempt_not_overwritten(tmp_path: Path) -> None:
    from research.execution_setup.core import immutable

    path = tmp_path / "failure.json"
    immutable(path, {"failure": "original"})
    with pytest.raises(FileExistsError):
        immutable(path, {"success": True})


def test_owned_resource_refusal(monkeypatch: Any) -> None:
    from research.execution_linux_v1.runtime import inspect_owned

    def inspect(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            [], 0, json.dumps([{"Config": {"Labels": {"research.setup": "different-owner"}}}]), ""
        )

    monkeypatch.setattr(subprocess, "run", inspect)
    with pytest.raises(ValueError, match="OWNERSHIP_MISMATCH"):
        inspect_owned("existing-application", "new-research-owner")


@pytest.mark.parametrize("prefix", ["Error: No such object: ", "error: no such object: "])
def test_missing_owned_container_message_compatibility(monkeypatch: Any, prefix: str) -> None:
    from research.execution_linux_v1.runtime import inspect_owned

    def inspect(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command == ["docker", "info"]:
            return subprocess.CompletedProcess(command, 0, "daemon available", "")
        return subprocess.CompletedProcess(command, 1, "[]", prefix + "dedicated-new\n")

    monkeypatch.setattr(subprocess, "run", inspect)
    assert inspect_owned("dedicated-new", "owner") is None


@pytest.mark.parametrize("message", ["permission denied", "error: no such object: different-name"])
def test_inspection_error_is_not_resource_absence(monkeypatch: Any, message: str) -> None:
    from research.execution_linux_v1.runtime import inspect_owned

    def inspect(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command == ["docker", "info"]:
            return subprocess.CompletedProcess(command, 0, "daemon available", "")
        return subprocess.CompletedProcess(command, 1, "[]", message)

    monkeypatch.setattr(subprocess, "run", inspect)
    with pytest.raises(RuntimeError, match="Docker inspection failed"):
        inspect_owned("dedicated-new", "owner")


def test_lost_checkpoint_cannot_replay_driver(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path)
    with pytest.raises(ValueError, match="do not reissue driver"):
        ledger.recover_checkpoint("missing")


def test_signal_handler_requests_safe_parent_stop() -> None:
    from research.execution_linux_v1.runner import _terminate_parent

    with pytest.raises(KeyboardInterrupt):
        _terminate_parent(signal.SIGTERM, None)


def test_lock_released_by_process_crash(tmp_path: Path) -> None:
    code = (
        "import signal;from pathlib import Path;"
        "from research.execution_linux_v1.platform import runner_lock;"
        f"\nwith runner_lock(Path({str(tmp_path)!r})): print('LOCKED',flush=True);signal.pause()"
    )
    holder = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout and holder.stdout.readline().strip() == "LOCKED"
        holder.kill()
        holder.wait(timeout=5)
        with runner_lock(tmp_path):
            pass
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait()


def test_service_attach_rejects_lost_pid_and_host_reboot(tmp_path: Path, monkeypatch: Any) -> None:
    from research.execution_linux_v1.runtime import Runtime
    from research.execution_setup.core import immutable

    root, execution = tmp_path / "root", tmp_path / "services"
    root.mkdir()
    immutable(root / "resources.json", {"database": "local-test", "sim_database": "local-truth"})
    original = Runtime(root, execution)
    original.records = {"worker": {"pid": 999999999, "identity": 1, "port": 19102}}
    original.save()
    with pytest.raises(ValueError, match="SERVICE_LOST_UNQUALIFIED"):
        Runtime(root, execution, attach=True)
    import research.execution_linux_v1.runtime as module

    monkeypatch.setattr(module, "boot_id", lambda: "different-boot")
    with pytest.raises(ValueError, match="HOST_REBOOT_UNQUALIFIED"):
        Runtime(root, execution, attach=True)


def test_application_environment_excludes_aws_and_analysis_overlay(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from research.execution_linux_v1.runtime import Runtime
    from research.execution_setup.core import ROOT, immutable

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-test-value")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-value")
    monkeypatch.setenv("PYTHONPATH", "/different-analysis/site-packages")
    immutable(
        tmp_path / "resources.json", {"database": "local-test", "sim_database": "local-truth"}
    )
    service = Runtime(tmp_path, tmp_path / "services")
    assert "AWS_ACCESS_KEY_ID" not in service.env and "GEMINI_API_KEY" not in service.env
    assert service.env["PYTHONPATH"] == str(ROOT)
