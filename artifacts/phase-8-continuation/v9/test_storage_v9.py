from __future__ import annotations
import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
import pytest

ROOT=Path('/source')
RUNTIME=ROOT/'artifacts/phase-8-runner-amendment/v4-complete'
sys.path.insert(0,str(RUNTIME))
import operational_limits as limits
from controls import Policy, guard, clock_check

GIB=1024**3
ORIGINAL=json.loads((RUNTIME/'original-launch-policy.json').read_text())
AT=datetime(2026,10,10,13,tzinfo=UTC)

def policy():
    return limits.effective_policy(ORIGINAL)

def sample():
    return dict(available_memory_bytes=8*GIB,system_free_bytes=130*GIB,
                output_free_bytes=130*GIB,backup_free_bytes=130*GIB,
                working_bytes=0,backup_bytes=0)

def test_effective_caps_preserve_historical_policy():
    assert policy().cloud_limit_bytes==policy().backup_archive_limit_bytes==80*GIB
    assert Policy.model_validate(ORIGINAL).cloud_limit_bytes==30*GIB
    assert policy().admission_committed_usd==60 and policy().budget_usd==65
    assert policy().stop_at.isoformat()=='2026-10-22T15:24:23.810674+00:00'

def test_full_month_cost_reserve():
    expected=Policy.model_validate(ORIGINAL).committed_cost(AT)+50*.025+1.25
    assert policy().committed_cost(AT)==pytest.approx(expected)

def test_cloud_boundary_includes_reservation():
    guard(policy(),sample(),AT,79*GIB-1,extra_bytes=GIB)
    with pytest.raises(ValueError,match='CLOUD_30GIB_LIMIT'):
        guard(policy(),sample(),AT,79*GIB,extra_bytes=GIB)

def test_local_boundary_includes_reservation():
    s=sample();s['backup_bytes']=79*GIB
    guard(policy(),s,AT,0)
    s['backup_bytes']+=1
    with pytest.raises(ValueError,match='BACKUP_RESERVATION_STOP'):
        guard(policy(),s,AT,0)

def test_larger_cap_rejected():
    with pytest.raises(ValueError):
        limits.OperationalLimits.model_validate({**limits.verified_limits().model_dump(),
                                                'cloud_limit_bytes':81*GIB})
    with pytest.raises(ValueError):
        Policy.model_validate({**ORIGINAL,'cloud_limit_bytes':81*GIB})

def test_tampered_overlay_rejected(tmp_path,monkeypatch):
    data=(RUNTIME/'operational-limit-proposal.json').read_text()
    (tmp_path/'operational-limit-proposal.json').write_text(data+' ')
    monkeypatch.setattr(limits,'HERE',tmp_path)
    with pytest.raises(ValueError,match='OPERATIONAL_LIMIT_AMENDMENT_DRIFT'):
        limits.verified_limits()

def test_clock_tolerance_unchanged():
    anchor=dict(wall=AT.isoformat(),monotonic=100,boot_id='same')
    clock_check(policy(),anchor,AT+timedelta(seconds=5),110,'same')
    with pytest.raises(ValueError,match='WALL_CLOCK_BACKWARD'):
        clock_check(policy(),anchor,AT+timedelta(seconds=4.999999),110,'same')

def test_qualified_clock_refusal_backup_code_unchanged():
    inv=json.loads((ROOT/'artifacts/phase-8-continuation/v8/qualification-summary.json').read_text())
    for name in ('clock_sampling.py','runner.py','reuse_prepare.py'):
        assert hashlib.sha256((RUNTIME/name).read_bytes()).hexdigest()==inv['tested_runtime_files'][name]
    expected=json.loads((ROOT/'artifacts/phase-8-continuation/v8/parent-v7-inventory.json').read_text())['files']
    prefix='artifacts/phase-8-runner-amendment/v4-complete/'
    for name in ('response_contracts.py','storage.py','prelaunch_backup.py','inventory_retry.py'):
        # Only files present in the qualified closure are selected.
        if prefix+name in expected:
            assert hashlib.sha256((RUNTIME/name).read_bytes()).hexdigest()==expected[prefix+name]
