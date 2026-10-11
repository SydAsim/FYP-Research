"""Complete review archive and exact preservation closure; no freeze/deployment."""
from __future__ import annotations
import ast
import difflib
import hashlib
import json
import shutil
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from prepare import BASE, HERE, MASTER, PREFIX, SOURCE, canonical, digest, write

def main() -> None:
    parent=json.loads((BASE/PREFIX/'candidate-inventory.json').read_text())
    assert hashlib.sha256(canonical(parent['files'])).hexdigest()==parent['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
    frozen=HERE.parents[1]/'phase-8-continuation-freeze/v7'
    if sys.platform=='win32':
        frozen=Path('\\\\?\\'+str(frozen.resolve()))
    assert digest(frozen/'freeze-manifest.json')=='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46'
    freeze=json.loads((frozen/'freeze-manifest.json').read_text())
    for name,sha in freeze['files'].items():
        assert digest(frozen/name)==sha,'FROZEN_PARENT_DRIFT '+name
    assert digest(HERE.parent/'v7/v7-complete-continuation-review-candidate.tar.gz')=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
    for name,sha in parent['files'].items():
        assert digest(BASE/name)==sha,'PARENT_SOURCE_DRIFT '+name
    changed={name for name,sha in parent['files'].items() if digest(SOURCE/name)!=sha}
    assert changed=={PREFIX+'/'+n for n in ('runner.py','handover.py','closed_restart.py','reuse_prepare.py')},changed
    for name,sha in parent['files'].items():
        if name.startswith(('apps/','packages/','research/','tests/','database/','contracts/','docs/')):
            assert digest(SOURCE/name)==sha,'PROTECTED_SCOPE_DRIFT '+name
    summary=json.loads((HERE/'qualification-summary.json').read_text())
    assert summary['status']=='PASS_DISTINCT_REQUIRED_CONTROLS' and summary['distinct_checks_completed']==18
    for name,sha in summary['tested_runtime_files'].items():
        assert digest(SOURCE/PREFIX/name)==sha,'TESTED_SOURCE_DRIFT '+name
    preservation=json.loads((HERE/'preservation-before.json').read_text())
    for name,sha in preservation['master_files'].items():
        assert digest(MASTER/name)==sha,'HISTORICAL_EVIDENCE_DRIFT '+name
    # Root and source runtime helpers must remain compileable but are not executed.
    for path in (SOURCE/PREFIX).glob('*.py'):ast.parse(path.read_text())
    changes=sorted(changed|{PREFIX+'/clock_sampling.py',PREFIX+'/test_clock_continuation_v8.py'})
    diff=[]
    for name in changes:
        before=(BASE/name).read_text().splitlines(keepends=True) if (BASE/name).is_file() else []
        diff.extend(difflib.unified_diff(before,(SOURCE/name).read_text().splitlines(keepends=True),fromfile='frozen-v7/'+name,tofile='candidate-v8/'+name))
    (HERE/'runtime.diff').write_text(''.join(diff))
    refs={
       'parent_v7_freeze':{'sha256':digest(frozen/'freeze-manifest.json'),'package':parent['package_hash'],'archive':'c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'},
       'originals_120_preservation':{'path':'artifacts/phase-8-operations/v7-stop-120-20261010/preservation-proof.json','sha256':digest(HERE.parents[1]/'phase-8-operations/v7-stop-120-20261010/preservation-proof.json')},
       'diagnosis':{'path':'artifacts/phase-8-operations/clock-diagnosis-120-v1/report.md','sha256':digest(HERE.parents[1]/'phase-8-operations/clock-diagnosis-120-v1/report.md')},
    }
    write(HERE/'parent-and-evidence-provenance.json',refs)
    write(HERE/'preservation-after.json',{'status':'PASS','parent_source_files':len(parent['files']),'frozen_parent_files':len(freeze['files']),'master_files':len(preservation['master_files']),'exact_boundary':preservation['counts'],'next':preservation['next'],'all_historical_content_hashes_unchanged':True,'controls_py_unchanged':digest(SOURCE/PREFIX/'controls.py')==digest(BASE/PREFIX/'controls.py'),'application_fixture_oracle_analysis_window_changes':0,'raw_failed_statuses_grades_timestamps_sidecars_preserved':True,'AWS_mutations':0})
    destination=SOURCE/'artifacts/phase-8-continuation/v8'
    destination.mkdir(parents=True,exist_ok=False)
    for path in sorted(HERE.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.gz','.pyc') and path.name not in ('candidate-package.json','candidate-inventory.json','final-verification.json'):
            target=destination/path.relative_to(HERE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    # Add the actual verified calibration backup objects, not only prose proofs.
    proofroot=destination/'qualification-evidence';proofroot.mkdir()
    for name,record in (('prelaunch.tar.gz','prelaunch-roundtrip.json'),('complete.tar.gz','complete-roundtrip.json')):
        original=Path('E:/p8v8/closure-remaining-evidence')/name
        proof=json.loads((HERE/record).read_text())
        assert digest(original)==proof['sha256'] and original.stat().st_size==proof['bytes']
        shutil.copyfile(original,proofroot/name)
    shutil.copyfile(frozen/'freeze-manifest.json',destination/'parent-v7-freeze-manifest.json')
    shutil.copyfile(BASE/PREFIX/'candidate-inventory.json',destination/'parent-v7-inventory.json')
    dependency=SOURCE/'linux-package-seal.json'
    inventory_name=PREFIX+'/candidate-inventory.json'
    files={p.relative_to(SOURCE).as_posix():digest(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.relative_to(SOURCE).as_posix()!=inventory_name}
    package_hash=hashlib.sha256(canonical(files)).hexdigest()
    sections={
      'runtime':{n:h for n,h in files.items() if n.startswith(PREFIX+'/') and n.endswith('.py')},
      'application':{n:h for n,h in files.items() if n.startswith(('apps/','packages/','database/','contracts/'))},
      'research_fixture_oracle_analysis':{n:h for n,h in files.items() if n.startswith('research/') or ('phase-8-review-freeze/v2/' in n)},
      'dependencies':{n:files[n] for n in ('uv.lock','pnpm-lock.yaml','Dockerfile.python','pyproject.toml','linux-package-seal.json')},
      'closed_boundary':{n:h for n,h in files.items() if n.startswith(PREFIX+'/closed-120')},
    }
    write(destination/'component-inventories.json',sections)
    # This inventories itself through the package's outer file map, without a cycle.
    files['artifacts/phase-8-continuation/v8/component-inventories.json']=digest(destination/'component-inventories.json')
    package_hash=hashlib.sha256(canonical(files)).hexdigest()
    inventory={'kind':'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE','version':'phase85-continuation-v8','package_hash':package_hash,'files':files,'parent_package_hash':parent['package_hash'],'parent_freeze_sha256':digest(frozen/'freeze-manifest.json'),'original_parent_freeze_sha256':freeze['parent_freeze_sha256'],'operational_limits_sha256':'60d8dbb2b7f3f6a83bd442ac491316e9a9e17d45a039e4b59d9400821d377791','accepted':False,'frozen':False,'launch_authorized':False,'closed_originals':120,'planned_originals':1380,'next_sequence':121,'next_arm':'P1','next_attempt':1,'next_execution_id':preservation['next']['execution_id'],'original_deadline':'2026-10-22T15:24:23.810674Z','deployment_ready':False,'deployment_blocker':'60 GiB capacity projection FAIL','dependency_seal_sha256':digest(dependency)}
    write(SOURCE/inventory_name,inventory);write(HERE/'candidate-inventory.json',inventory)
    archive=HERE/'v8-complete-continuation-review-candidate.tar.gz'
    with tarfile.open(archive,'x:gz') as out:
        for name in sorted([*files,inventory_name]):out.add(SOURCE/name,arcname=name,recursive=False)
    expected={**files,inventory_name:digest(SOURCE/inventory_name)};seen=set()
    with tarfile.open(archive,'r|gz') as incoming:
        for member in incoming:
            assert member.isfile() and member.name in expected and member.name not in seen
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            stream=incoming.extractfile(member);assert stream
            assert hashlib.file_digest(stream,'sha256').hexdigest()==expected[member.name],member.name
            seen.add(member.name)
    assert seen==expected.keys()
    assert all(digest(SOURCE/n)==h for n,h in files.items())
    package={k:v for k,v in inventory.items() if k!='files'}
    package.update(archive_sha256=digest(archive),archive_bytes=archive.stat().st_size,archive_members=len(expected),inventory_sha256=digest(SOURCE/inventory_name),source=str(SOURCE))
    write(HERE/'candidate-package.json',package)
    estimate=json.loads((HERE/'estimates.json').read_text())
    assert estimate['status']=='BLOCKED_DO_NOT_DEPLOY'
    write(HERE/'final-verification.json',{**package,'status':'PASS','scope':'CODE_EVIDENCE_AND_ARCHIVE_VERIFIED_NOT_DEPLOYMENT_READINESS','at_utc':datetime.now(UTC).isoformat(),'qualification':summary,'source_and_archive_member_closure':'PASS','historical_evidence_preservation':'PASS','feasibility':estimate,'overall_deployment_readiness':'BLOCKED_CAPACITY','acceptance_freeze_deployment_launch_recorded':False,'research_executions':0,'AWS_mutations':0})
    print(json.dumps(package,indent=2))

if __name__=='__main__':main()
