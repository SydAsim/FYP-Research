"""Separate operational-limit candidate; retain all v6 evidence and frozen parents."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/p8v7/source')
BASE = Path('E:/p8v6/source')
PREFIX = 'artifacts/phase-8-runner-amendment/v4-complete'


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()


def main() -> None:
    inventory = json.loads((BASE/PREFIX/'candidate-inventory.json').read_text())
    assert inventory['package_hash'] == '3807d690ad46abdd07da12710ea933e03e3d86fb4440f5933b186db74de76a34'
    assert hashlib.sha256(canonical(inventory['files'])).hexdigest() == inventory['package_hash']
    assert json.loads((HERE.parent/'v6/final-verification.json').read_text())['status']=='PASS'
    for name, sha in inventory['files'].items():
        assert digest(BASE/name)==sha, name
    archive=HERE.parent/'v6/v6-complete-continuation-review-candidate.tar.gz'
    assert digest(archive)=='8e51871ad8e9b9baea8b36515f0fab2c63a6cb3d364c615b605c4af67af9a113'
    SOURCE.mkdir(parents=True,exist_ok=False)
    for name in [*inventory['files'],PREFIX+'/candidate-inventory.json']:
        target=SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BASE/name,target)
    limits={
        'kind':'PROPOSED_OPERATIONAL_LIMIT_AMENDMENT_NOT_AUTHORIZATION','version':'phase85-continuation-v7',
        'qualified_v6_package_hash':inventory['package_hash'],
        'run_id':'p85-01a116f7-3b82-7a79-8653-3aee62dc99e9','original_deadline':'2026-10-22T15:24:23.810674Z',
        'admission_committed_usd':60,'budget_usd':65,'cloud_limit_bytes':60*1024**3,
        'backup_archive_limit_bytes':60*1024**3,'working_limit_bytes':50*1024**3,
        'slot_reservation_bytes':1024**3,'volume_gib':160,
        'retention':'Only future v7 redundant attempt staging may be removed after local immutable archive/member and pinned S3 verification, BACKED_UP commit and owned-path verification. All 82 originals, raw execution traces, grades, archives, receipts and S3 versions are retained.',
        'no_automatic_increases':True,'original_policy_and_receipts_unchanged':True,
    }
    (SOURCE/PREFIX/'operational-limit-proposal.json').write_text(json.dumps(limits,indent=2)+'\n')
    (HERE/'operational-limit-proposal.json').write_text(json.dumps(limits,indent=2)+'\n')
    plan={'at_utc':datetime.now(UTC).isoformat(),'scope':'Two operational decisions only; no repeated v6 tests, pilot, study executions or observation windows',
          'files':{'controls.py':'Use signed effective cost/archive thresholds; historical defaults unchanged','handover.py':'Verify original authority separately, then signed limit amendment; preserve originals','closed_restart.py':'v7 paths and dedicated new backup directory','runner.py':'After verified BACKED_UP/retirement, remove only redundant new staging','staging_retention.py':'Fail closed on unverified/unsafe paths; never delete sole evidence','proposal and review package':'Exact limits, costs, inventory and combined-decision procedure'},
          'new_only_controls':8,'maximum_control_wall_seconds':60,'maximum_attempts':1,
          'coverage':['55/30 historical policy unchanged','60/60 signed effective policy','cost and archive thresholds enforced','valid redundancy deletion retains archive','missing archive rejection','hash corruption rejection','outside-directory rejection','historical-original exclusion'],
          'stop':'Any failed new control blocks candidate; no broad reruns',
          'application_fixture_oracle_analysis_windows_changes':0,'acceptance_freeze_launch_recorded':False}
    (HERE/'qualification-plan.json').write_text(json.dumps(plan,indent=2))
    print(json.dumps({'v6_source_verified':len(inventory['files']),'limits_sha256':digest(SOURCE/PREFIX/'operational-limit-proposal.json')}))


if __name__=='__main__':
    main()
