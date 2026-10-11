"""Retain qualification notices and verify the stopped historical boundary."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

from prepare_candidate import HERE, PARENT, PREFIX, digest

log = json.loads((HERE / 'attempt2/run.json').read_text())
assert log['exit'] == 124
(HERE / 'attempt2/qualification.json').write_text(json.dumps({'status': 'FAIL_TIMEOUT_RETAINED', 'test_limit_seconds': 300, 'completed_controls': 5, 'interrupted_control': 'test_corrupt_required_history_rejected', 'source_archive_retained': True, 'copy_timeout_seconds': 30, 'stop_request_timeout_seconds': 15, 'original_container_retained': 'p85-v6-metadata-attempt2', 'research_executions': 0}, indent=2))
archive = Path('E:/p8v5/blocked-20261009/evidence.tar.gz')
assert digest(archive) == '57fa8f85c017bee13fd1325f685b928d96ba129db1b6175a4962895791ba9392'
snapshot = Path('E:/p8v5/blocked-20261009/campaign.sqlite3')
with sqlite3.connect(snapshot.resolve().as_uri()+'?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    db.execute('BEGIN')
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    rows = [dict(r) for r in db.execute('SELECT * FROM slots ORDER BY sequence')]
    prior = 'GENESIS'
    count = 0
    for row in db.execute('SELECT * FROM notices ORDER BY n'):
        assert row['previous'] == prior and hashlib.sha256((row['body']+prior).encode()).hexdigest() == row['hash']
        prior = row['hash']; count += 1
pinned = json.loads((PARENT/PREFIX/'closed-82/ledger-read-only.json').read_text())['rows']
assert rows == pinned
(HERE/'stopped-boundary-preservation.json').write_text(json.dumps({'status': 'PASS', 'identical_all_1500_rows': True, 'BACKED_UP':82, 'PLANNED':1418, 'next': rows[82], 'notices_verified':count, 'latest_stopped_snapshot_sha256':digest(snapshot), 'supplemental_596_member_evidence_archive_sha256':digest(archive), 'historical_verification_reference':'artifacts/phase-8-continuation-deployment/v5/blocked-evidence-readback.json'}, indent=2))
args=['aws','ec2','describe-instances','--instance-ids','i-057344e5372faf62f','--profile','fyp-research','--region','ap-southeast-2','--output','json','--no-cli-pager']
result=subprocess.run(args,capture_output=True,text=True,timeout=60)
record={'exit':result.returncode,'args':args,'stdout':result.stdout,'stderr':result.stderr}
(HERE/'aws-stopped-final.json').write_text(json.dumps(record,indent=2))
result.check_returncode()
host=json.loads(result.stdout)['Reservations'][0]['Instances'][0]
assert host['State']['Name']=='stopped'
for name in ('p85-v6-metadata-attempt1','p85-v6-metadata-attempt2','p85-v6-remaining-controls','p85-v6-final-metadata-guards'):
    result=subprocess.run(['docker','inspect',name,'--format','{{json .State}}'],capture_output=True,text=True,timeout=30)
    (HERE/(name+'-retained-state.json')).write_text(json.dumps({'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}))
    result.check_returncode()
    assert json.loads(result.stdout)['Running'] is False
print('PASS: unchanged stopped boundary/evidence; AWS stopped; local control containers exited and retained')
