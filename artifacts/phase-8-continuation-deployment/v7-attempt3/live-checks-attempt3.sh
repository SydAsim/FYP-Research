set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'INTEGRITY'
import hashlib,hmac,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,canonical,utc
import boto3
assert boto3.__version__=='1.43.108'
dep=Path('/var/lib/p8-continuation-v7/deployment')
assert hash_file(dep/'package.tar.gz')=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
assert inv['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
assert hashlib.sha256(canonical(inv['files'])).hexdigest()==inv['package_hash']
for name,digest in inv['files'].items():
    if hash_file(Path.cwd()/name)!=digest:raise ValueError('V7_SOURCE_MEMBER_DRIFT:'+name)
owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
public=dep/'authority.tar.gz.extract'
manifest=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
assert hash_file(public/'freeze-manifest.json')=='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46'
assert hmac.compare_digest(att['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
    name=kind+'.json';raw=read(owner/'continuation-v7-receipts'/name)
    assert hash_file(owner/'continuation-v7-receipts'/name)==hash_file(public/name)
    assert hmac.compare_digest(raw['signature'],hmac.new(key,canonical({k:v for k,v in raw.items() if k!='signature'}),'sha256').hexdigest())
assert read(dep/'old-unit-quiescence-attempt3.json')['status']=='PASS'
write_new(dep/'current-source-integrity-attempt3.json',{'status':'PASS','at_utc':utc().isoformat(),'source_files':len(inv['files']),'package_hash':inv['package_hash'],'archive_sha256':hash_file(dep/'package.tar.gz'),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'completed_transfer_reused':True,'dependency_install':False,'driver_calls':0})
INTEGRITY
cat >/var/lib/p8-continuation-v7/deployment/host_checks-attempt3.py <<'CHECKS'
"""Live read-only deployment gates; no scenario, SQL restore or admission."""
from __future__ import annotations
import base64
import csv
import hashlib
import hmac
import importlib.metadata
import json
import socket
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SOURCE=Path('/opt/fyp-phase8-continuation-v7')
RUNTIME=SOURCE/'artifacts/phase-8-runner-amendment/v4-complete'
sys.path.insert(0,str(RUNTIME))
from controls import canonical,guard,hash_file,read,utc,write_new
from closed_restart import boundary
from handover import ro_rows
from operational_limits import effective_policy
from storage import ObjectProof,S3Cloud,verify_local
from transport import Receipt,S3Store
from research.execution_linux_v1.runner import IMAGE_DIGESTS
from research.execution_linux_v1.platform import host

def main():
    dep=Path('/var/lib/p8-continuation-v7/deployment');old=Path('/var/lib/p8-combined-v4/run')
    source_ready=read(dep/'source-ready.json');assert source_ready['status']=='PASS'
    # Original v4 source, stopped boundary and old failure pause remain intact.
    parent=read(RUNTIME/'parent-v4-inventory.json')
    for name,digest in parent['files'].items():
        if hash_file(Path('/opt/fyp-phase8-combined-v4')/name)!=digest:raise ValueError('OLD_FROZEN_SOURCE_DRIFT: '+name)
    rows=ro_rows(old);pinned=read(RUNTIME/'closed-82/ledger-read-only.json')['rows'];boundary(rows,pinned)
    if read(old/'pause.json')['reason']!='PROTOCOL_STOP':raise ValueError('OLD_PAUSE_DRIFT')
    for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
        if subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()!='0':raise ValueError('OLD_OPERATIONAL_UNIT_RUNNING')
    for port in (16432,16433,19100,19101,19102,19110):
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    owner=Path('/var/lib/fyp-owner')
    if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS')
    dependencies={};lock=tomllib.loads((SOURCE/'uv.lock').read_text());locked={}
    for package in lock['package']:locked.setdefault(package['name'].lower().replace('_','-'),set()).add(package['version'])
    baseline=read(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json'))
    for label,env_name in (('application','.venv'),('analysis','.venv-analysis'),('transport','.venv-transport')):
        packages={};count=0;site=SOURCE/env_name/'lib/python3.12/site-packages'
        for dist in importlib.metadata.distributions(path=[str(site)]):
            name=dist.metadata['Name'].lower().replace('_','-');packages[name]=dist.version
            if label=='application' and name not in ('pip','setuptools','wheel') and dist.version not in locked.get(name,set()):raise ValueError('LOCK_VERSION_DRIFT: '+name)
            for line in csv.reader((dist.read_text('RECORD') or '').splitlines()):
                if not line or not line[1]:continue
                algorithm,digest=line[1].split('=',1);target=Path(dist.locate_file(line[0]))
                if algorithm!='sha256' or not target.is_file():raise ValueError('DEPENDENCY_RECORD_MISSING')
                if base64.urlsafe_b64encode(hashlib.sha256(target.read_bytes()).digest()).decode().rstrip('=')!=digest:raise ValueError('DEPENDENCY_RECORD_DRIFT: '+name)
                count+=1
        if packages!=baseline['dependency_environments'][label]['packages']:raise ValueError('INSTALLED_ENVIRONMENT_CHANGED: '+label)
        dependencies[label]={'packages':packages,'record_hashed_files':count,'installed_versions_sha256':hashlib.sha256(canonical(packages)).hexdigest()}
    if sys.version!=baseline['python'] or sys.version_info[:3]!=(3,12,13):raise ValueError('PINNED_PYTHON_BUILD_DRIFT')
    for tag,digest in IMAGE_DIGESTS.items():
        image=json.loads(subprocess.run(['docker','image','inspect',tag],check=True,capture_output=True,text=True,timeout=15).stdout)[0]
        if digest not in image['RepoDigests']:raise ValueError('IMAGE_DRIFT')
    running=subprocess.run(['docker','ps','--format','{{json .}}'],check=True,capture_output=True,text=True,timeout=15).stdout
    if running.strip():raise ValueError('UNEXPECTED_RUNNING_CONTAINER_BEFORE_CLOSED_HANDOVER')
    policy=effective_policy(read(RUNTIME/'original-launch-policy.json'))
    cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/');store=S3Store('fyp-research')
    proofs=[]
    for row in rows[:82]:
        receipt=read(old/'backups'/(row['execution_id']+'.json'))
        if hash_file(old/'backups'/(row['execution_id']+'.json'))!=row['backup_hash']:raise ValueError('BACKUP_RECEIPT_DRIFT')
        local=Path(receipt['local'])
        if not local.exists() and row['sequence']<=38:
            local=Path('/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives')/(str(row['sequence']).zfill(4)+'.tar.gz')
        verify_local(local,receipt['sha256'])
        proofs.append(ObjectProof.model_validate(receipt['cloud']))
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(store.head,Receipt.model_validate(p.model_dump())) for p in proofs]
        for f in futures:f.result()
    sample=host(old,Path('/var/lib/p8-combined-v4/backup'));sample.update(working_bytes=0,backup_bytes=0)
    cloud_bytes=cloud.inventory();guard(policy,sample,utc(),cloud_bytes,extra_bytes=policy.slot_capacity_reserve_bytes)
    timers=subprocess.run(['systemctl','list-timers','fyp-p85-continuation-bootstrap-stop.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout
    if '2026-10-22 15:24:23' not in timers:raise ValueError('ORIGINAL_ABSOLUTE_TIMER_DRIFT')
    write_new(dep/'live-preparation-checks.json', {'status':'PASS','at_utc':utc().isoformat(),'package_hash':source_ready['package_hash'],'source':source_ready,'old_v4_source_members':len(parent['files']),'closed_originals':82,'planned':1418,'active':0,'next_execution_id':rows[82]['execution_id'],'next_sequence':83,'next_arm':'B3','next_attempt':1,'dependency_environments':dependencies,'python':sys.version,'python_binary_sha256':hash_file(Path(sys.executable).resolve()),'image_digests':IMAGE_DIGESTS,'original_backups':[p.model_dump() for p in proofs],'local_archive_hashes_and_manifest_members':'PASS_ALL_82','S3_pinned_versions':'PASS_ALL_82','host':sample,'cloud_all_versions_bytes':cloud_bytes,'original_timer':timers,'new_application_stacks':0,'driver_calls':0})
    print(json.dumps({'status':'PASS','readiness_input_sha256':hash_file(dep/'live-preparation-checks.json'),'originals_verified':82,'planned':1418,'available_memory_bytes':sample['available_memory_bytes'],'disk_free_bytes':sample['system_free_bytes'],'cloud_bytes':cloud_bytes,'driver_calls':0}))

if __name__=='__main__':
    main()

CHECKS
timeout --signal=TERM --kill-after=5s 600s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/host_checks-attempt3.py
