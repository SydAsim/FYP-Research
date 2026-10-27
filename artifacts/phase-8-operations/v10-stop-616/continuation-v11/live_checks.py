from __future__ import annotations
import hashlib,json,sys,socket,subprocess,time
from pathlib import Path
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

def main():
    source=Path('/opt/fyp-phase8-continuation-v11');r=source/'artifacts/phase-8-runner-amendment/v4-complete';sys.path.insert(0,str(r));sys.path.insert(1,str(source))
    from controls import read,write_new,hash_file,guard,utc
    from handover import ContinuationAuthority
    from closed616 import verify
    from closed145 import snapshot
    from runner import meter,unit_text
    from storage import S3Cloud,ObjectProof
    from research.execution_linux_v1.runner import IMAGE_DIGESTS
    root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
    a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True);verify(root,closed=True)
    assert read(dep/'source-and-runtime-verified.json')['status']=='PASS'
    for u in ['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']:
        assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
    assert not subprocess.run(['docker','ps','--format','{{.Names}}'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()
    for port in [16432,16433,19100,19101,19102,19110]:
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    for tag,digest in IMAGE_DIGESTS.items():
        image=json.loads(subprocess.run(['docker','image','inspect',tag],check=True,capture_output=True,text=True,timeout=15).stdout)[0]
        assert digest in image['RepoDigests'],'IMAGE_DIGEST_DRIFT'
    cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
    rows,_=snapshot(root/'campaign.sqlite3');proofs=[]
    for row in rows[:616]:
        receipt=root/'backups'/(row['execution_id']+'.json');assert hash_file(receipt)==row['backup_hash']
        p=read(receipt);assert p['execution_id']==row['execution_id'] and p['sha256']==p['cloud']['sha256'];proofs.append(p)
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks=[pool.submit(cloud.verify,ObjectProof.model_validate(p['cloud'])) for p in proofs]
        for n,p in enumerate(proofs,1):
            path=Path(p['local'])
            if not path.exists() and n<=38:path=Path('/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives')/(f'{n:04d}.tar.gz')
            assert hash_file(path)==p['sha256'],'ORIGINAL_ARCHIVE_DRIFT:'+str(n)
            checks[n-1].result()
            if n%100==0:print('VERIFIED original archives and pinned versions '+str(n)+'/616',flush=True)
    at=utc();sample=meter(root);cloudbytes=cloud.inventory()
    guard(a.policy,sample,at,cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    finish=at+timedelta(hours=884*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24)
    extra=read(dep/'external-input.json')['external']['cost']['extra_root_reserve']
    assert uncertain<a.policy.stop_at-timedelta(minutes=30) and a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra<74 and a.policy.committed_cost(a.policy.stop_at)+extra<75,'LIVE_TIME_COST_STOP'
    # Preserve the same60MiB future archive allowance, plus1GiB reservation.
    prep_bound=int(2.5*1024**3)
    cloudprojection=cloudbytes+884*60*1024**2+1024**3+100*1024**2
    backupprojection=sample['backup_bytes']+884*60*1024**2+1024**3+prep_bound
    assert cloudprojection<80*1024**3 and backupprojection<80*1024**3,'LIVE_FULL_STORAGE_PROJECTION_STOP'
    for unit in ['fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v11-admission-cutoff.timer']:
        subprocess.run(['systemctl','is-active','--quiet',unit],check=True,timeout=10)
    service,timer=unit_text(root,a.policy)
    assert Path('/etc/systemd/system/fyp-phase8-hardstop.timer').read_text()==timer
    body={'status':'PASS','at':at.isoformat(),'backed_up':616,'planned':884,'next':rows[616],'all616_local_archive_hashes_verified':True,'all616_pinned_versions_head_verified':True,'source_runtime_dependency_evidence_sha256':hash_file(dep/'source-and-runtime-verified.json'),'metadata_sha256':hash_file(dep/'metadata-and-timers.json'),'resource_sample':sample,'cloud_all_versions_bytes':cloudbytes,'cloud_full_projection_bytes':cloudprojection,'backup_full_projection_bytes':backupprojection,'prelaunch_complete_preparation_bound_bytes':prep_bound,'future_archive_allowance_bytes':60*1024**2,'remaining_window_budget_seconds':600,'completion_utc':finish.isoformat(),'uncertain_completion_utc':uncertain.isoformat(),'uncertainty_usd':a.policy.committed_cost(uncertain)+extra,'full_deadline_usd':a.policy.committed_cost(a.policy.stop_at)+extra,'stop_at':a.policy.stop_at.isoformat(),'driver_calls':0}
    write_new(dep/'live-checks.json',body);print(json.dumps(body))
if __name__=='__main__':main()
