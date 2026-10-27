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

SOURCE=Path('/opt/fyp-phase8-continuation-v10')
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
    dep=Path('/var/lib/p8-continuation-v10/deployment');old=Path('/var/lib/p8-continuation-v9/run')
    source_ready=read(dep/'source-ready.json');assert source_ready['status']=='PASS'
    assert source_ready['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
    from closed145 import verify_retained_root
    checked=verify_retained_root(old);rows=ro_rows(old)
    assert checked['backed_up']==145 and checked['planned']==1355
    provenance_path=old/'restart-history/export-layout-v1/provenance.json'
    assert hash_file(provenance_path)=='e575ee7413017464fa86c0f7e8806aabbbd3a9f07d58250c15bde2cbb49f48fd','RETAINED_LAYOUT_PROVENANCE_DRIFT'
    provenance=read(provenance_path);assert len(provenance['records'])==145
    for row,record in zip(rows[:145],provenance['records'],strict=True):
        assert record['identity']['sequence']==row['sequence'] and record['identity']['execution_id']==row['execution_id']
        target=old/'exports'/f"{row['sequence']:04d}"/'export.json'
        assert hash_file(target)==record['export_sha256'] and target.stat().st_size==record['export_bytes'],'MATERIALIZED_ORIGINAL_BYTES_DRIFT'
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
    for row in rows[:145]:
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
    sample=host(old,Path('/var/lib/p8-continuation-v9/backup'));sample.update(working_bytes=sum(p.stat().st_size for p in old.rglob('*') if p.is_file()),backup_bytes=sum(p.stat().st_size for p in old.parent.joinpath('backup').rglob('*.tar.gz')))
    if sample['system_free_bytes'] < 145670462448:raise ValueError('CAMPAIGN_PROJECTED_DISK_HEADROOM_STOP')
    cloud_bytes=cloud.inventory();guard(policy,sample,utc(),cloud_bytes,extra_bytes=policy.slot_capacity_reserve_bytes)
    timers=subprocess.run(['systemctl','list-timers','fyp-p85-continuation-bootstrap-stop.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout
    if '2026-10-22 15:24:23' not in timers:raise ValueError('ORIGINAL_ABSOLUTE_TIMER_DRIFT')
    write_new(dep/'live-preparation-checks.json', {'status':'PASS','at_utc':utc().isoformat(),'package_hash':source_ready['package_hash'],'source':source_ready,'closed_originals':145,'planned':1355,'active':0,'next_execution_id':rows[145]['execution_id'],'next_sequence':146,'next_arm':'P2','next_attempt':1,'dependency_environments':dependencies,'python':sys.version,'python_binary_sha256':hash_file(Path(sys.executable).resolve()),'image_digests':IMAGE_DIGESTS,'original_backups':[p.model_dump() for p in proofs],'local_archive_hashes_and_manifest_members':'PASS_ALL_145','S3_pinned_versions':'PASS_ALL_145','host':sample,'cloud_all_versions_bytes':cloud_bytes,'original_timer':timers,'new_application_stacks':0,'driver_calls':0})
    print(json.dumps({'status':'PASS','readiness_input_sha256':hash_file(dep/'live-preparation-checks.json'),'originals_verified':145,'planned':1355,'available_memory_bytes':sample['available_memory_bytes'],'disk_free_bytes':sample['system_free_bytes'],'cloud_bytes':cloud_bytes,'driver_calls':0}))

if __name__=='__main__':
    main()
