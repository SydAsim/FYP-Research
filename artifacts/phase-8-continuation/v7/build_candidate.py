"""Inventory complete v7 candidate; preserve v6; no acceptance or AWS mutations."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import shutil
import sqlite3
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from prepare import BASE, HERE, PREFIX, SOURCE, canonical, digest


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, default=str)


def main() -> None:
    parent = json.loads((BASE/PREFIX/'candidate-inventory.json').read_text())
    assert parent['package_hash'] == '3807d690ad46abdd07da12710ea933e03e3d86fb4440f5933b186db74de76a34'
    assert hashlib.sha256(canonical(parent['files'])).hexdigest() == parent['package_hash']
    for name, sha in parent['files'].items():
        assert digest(BASE/name) == sha, name
    assert digest(HERE.parent/'v6/v6-complete-continuation-review-candidate.tar.gz') == '8e51871ad8e9b9baea8b36515f0fab2c63a6cb3d364c615b605c4af67af9a113'
    protected_archive = Path('E:/p8v5/blocked-20261009/evidence.tar.gz')
    assert digest(protected_archive) == '57fa8f85c017bee13fd1325f685b928d96ba129db1b6175a4962895791ba9392'
    frozen_parent = HERE.parents[1]/'phase-8-continuation-freeze/v5/freeze-manifest.json'
    assert digest(frozen_parent) == '95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26'
    runtime = SOURCE/PREFIX
    changed = {n for n, sha in parent['files'].items() if digest(SOURCE/n) != sha}
    assert changed == {PREFIX+'/'+n for n in ('controls.py','handover.py','closed_restart.py','runner.py')}, changed
    result = json.loads((HERE/'new-controls-result.json').read_text())
    assert result['status'] == 'PASS' and result['wall_seconds'] < 60
    for name, sha in result['files'].items():
        assert digest(runtime/name) == sha, name
    assert json.loads((HERE/'aws-stopped-readonly.json').read_text())['State'] == 'stopped'
    estimates = json.loads((HERE/'estimates.json').read_text())
    assert estimates['status'] == 'PROPOSED_FITS'
    # Read-only identity preservation, not a repeated handover execution/test.
    master = runtime/'closed-82/campaign.sqlite3'
    with sqlite3.connect(master.resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')
        rows = [dict(row) for row in db.execute('SELECT * FROM slots ORDER BY sequence')]
    assert len(rows) == 1500
    assert sum(r['state']=='BACKED_UP' for r in rows)==82
    assert sum(r['state']=='PLANNED' for r in rows)==1418
    assert rows[82]['sequence']==83 and rows[82]['arm']=='B3' and rows[82]['attempt']==1
    assert rows[82]['execution_id']=='01a11705-11f1-792b-ae1e-36bfc6773842'
    diff = []
    for name in sorted(changed | {PREFIX+'/'+n for n in ('operational_limits.py','staging_retention.py','test_operational_limits.py','operational-limit-proposal.json')}):
        before = (BASE/name).read_text().splitlines(keepends=True) if (BASE/name).exists() else []
        diff.extend(difflib.unified_diff(before,(SOURCE/name).read_text().splitlines(keepends=True),fromfile='qualified-v6/'+name,tofile='candidate-v7/'+name))
    (HERE/'runtime.diff').write_text(''.join(diff))
    assert all(digest(SOURCE/n)==sha for n,sha in parent['files'].items() if n.startswith(('apps/','packages/','research/','tests/','database/','contracts/','docs/')))
    reused = ('qualified-source-closure.json','final-verification.json','final-two-check-results.json','focused/results.json','remaining/qualification.json','stopped-boundary-preservation.json','unsuccessful-preparation-notices.json','retained-calibration-payloads.json')
    write(HERE/'reused-v6-evidence.json', {'qualified_package_hash':parent['package_hash'],
          'historical_files':{n:digest(HERE.parent/'v6'/n) for n in reused},
          'distinct_prior_controls':14,'repeated_completed_tests':0,'prior_full_suite_status':'TIMED_OUT_NOT_PASS',
          'new_only_controls':8,'new_only_result_sha256':digest(HERE/'new-controls-result.json')})
    write(HERE/'preservation-after.json',{'status':'PASS','v6_files':len(parent['files']),
          'v6_archive_sha256':digest(HERE.parent/'v6/v6-complete-continuation-review-candidate.tar.gz'),
          'frozen_v5_manifest_sha256':digest(frozen_parent),'stopped_boundary_sha256':digest(protected_archive),
          'identities':1500,'backed_up':82,'planned':1418,'next':rows[82],
          'application_fixture_analysis_window_changes':0})
    # Compile/inspect only; never run freeze/deployment helpers or research code.
    for path in [HERE/'freeze_accepted.py', *(runtime/n for n in ('operational_limits.py','staging_retention.py','controls.py','handover.py','closed_restart.py','runner.py'))]:
        ast.parse(path.read_text())
    for path in sorted(HERE.glob('*')):
        if not path.is_file() or path.suffix == '.gz' or path.name in ('candidate-package.json','candidate-inventory.json','final-verification.json'):
            continue
        target = SOURCE/'artifacts/phase-8-continuation/v7'/path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path,target)
    inventory_name = PREFIX+'/candidate-inventory.json'
    files = {p.relative_to(SOURCE).as_posix():digest(p) for p in sorted(SOURCE.rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
             and p.relative_to(SOURCE).as_posix()!=inventory_name}
    package_hash=hashlib.sha256(canonical(files)).hexdigest()
    inventory={'kind':'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE','version':'phase85-continuation-v7',
               'package_hash':package_hash,'files':files,'parent_package_hash':parent['package_hash'],
               'parent_freeze_sha256':digest(frozen_parent),'operational_limits_sha256':digest(runtime/'operational-limit-proposal.json'),
               'accepted':False,'frozen':False,'launch_authorized':False,'closed_originals':82,
               'planned_originals':1418,'next_sequence':83,'next_execution_id':rows[82]['execution_id']}
    (runtime/'candidate-inventory.json').write_text(json.dumps(inventory,indent=2))
    write(HERE/'candidate-inventory.json',inventory)
    archive=HERE/'v7-complete-continuation-review-candidate.tar.gz'
    with tarfile.open(archive,'x:gz') as outgoing:
        for name in sorted([*files,inventory_name]):
            outgoing.add(SOURCE/name,arcname=name,recursive=False)
    expected={**files,inventory_name:digest(runtime/'candidate-inventory.json')}
    seen=set()
    with tarfile.open(archive,'r|gz') as incoming:
        for member in incoming:
            assert member.isfile() and member.name in expected and member.name not in seen
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            stream=incoming.extractfile(member)
            assert stream is not None and hashlib.sha256(stream.read()).hexdigest()==expected[member.name],member.name
            seen.add(member.name)
    assert seen==expected.keys()
    assert all(digest(SOURCE/n)==sha for n,sha in files.items())
    package={k:v for k,v in inventory.items() if k!='files'}
    package.update(archive_sha256=digest(archive),archive_bytes=archive.stat().st_size,
                   archive_members=len(expected),inventory_sha256=digest(runtime/'candidate-inventory.json'),source=str(SOURCE))
    write(HERE/'candidate-package.json',package)
    write(HERE/'final-verification.json',{**package,'status':'PASS','scope':'LOCAL_REVIEW_PACKAGE_NOT_LIVE_READINESS',
          'at_utc':datetime.now(UTC).isoformat(),'new_checks':result,'existing_v6_tests_repeated':0,
          'v6_qualification_reused':14,'source_and_archive_closure':'PASS','preserved_boundary':'82/1418 PASS',
          'static_runtime_checks':'ruff/mypy PASS seven files','research_executions':0,'AWS_mutations':0,
          'application_fixture_oracle_analysis_windows_changes':0,'feasibility':estimates})
    print(json.dumps(package,indent=2))


if __name__=='__main__':
    main()
