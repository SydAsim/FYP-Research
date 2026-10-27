from __future__ import annotations
import hashlib,json,sys,socket,subprocess
from datetime import timedelta,datetime
from pathlib import Path

def main():
    source=Path('/opt/fyp-phase8-continuation-v11');r=source/'artifacts/phase-8-runner-amendment/v4-complete';sys.path.insert(0,str(r));sys.path.insert(1,str(source))
    from controls import read,write_new,hash_file,canonical,guard,utc,Journal
    from handover import ContinuationAuthority,CHECKS
    from closed616 import verify
    from runner import meter,verify_clock,unit_text
    from prelaunch_backup import verify_proof
    from storage import S3Cloud
    root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
    external=read(dep/'external-input.json')['external'];assert datetime.fromisoformat(external['expires_at'])>utc()
    a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True);verify(root,closed=True)
    assert not (root/'slots/0617').exists(),'NEXT_DRIVER_MUST_NOT_HAVE_STARTED'
    live=read(dep/'live-checks.json');assert live['status']=='PASS' and live['all616_local_archive_hashes_verified'] and live['all616_pinned_versions_head_verified']
    physical=read(dep/'root-resize-verified.json');plan=read(dep/'root-resize-plan.json');assert physical['status']=='PASS_ACTUAL_FILESYSTEM_EXPANSION'
    cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');verify_proof(root,'prelaunch',cloud)
    sample=meter(root);cloudbytes=cloud.inventory();at=utc()
    guard(a.policy,sample,at,cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    prep_growth=sample['backup_bytes']-live['resource_sample']['backup_bytes']
    # Bind COMPLETE's allowance to measured successful PRELAUNCH growth, with16MiB extra.
    complete_bound=prep_growth+16*1024**2
    assert prep_growth>0 and prep_growth+complete_bound<=live['prelaunch_complete_preparation_bound_bytes'],'MEASURED_BACKUP_STAGE_BOUND_EXCEEDED'
    backup_projection=sample['backup_bytes']+884*60*1024**2+1024**3+complete_bound
    cloud_projection=cloudbytes+884*60*1024**2+1024**3+100*1024**2
    required=(backup_projection-sample['backup_bytes'])+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3
    assert backup_projection<80*1024**3 and cloud_projection<80*1024**3,'FINAL_STORAGE_CAP_STOP'
    assert sample['system_free_bytes']>=required,'REMAINING_PHYSICAL_HEADROOM_STOP'
    finish=at+timedelta(hours=884*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24)
    extra=plan['total_extra_storage_reserve_usd']
    assert uncertain<a.policy.stop_at-timedelta(minutes=30) and a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra<74 and a.policy.committed_cost(a.policy.stop_at)+extra<75,'FINAL_TIME_OR_COST_STOP'
    for unit in ['fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v11-admission-cutoff.timer']:subprocess.run(['systemctl','is-active','--quiet',unit],check=True,timeout=10)
    for unit in ['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']:assert subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
    service,timer=unit_text(root,a.policy);assert Path('/etc/systemd/system/fyp-phase8-hardstop.timer').read_text()==timer
    assert hash_file(dep/'admission-cutoff.py')==physical['fence_script_sha256'] and hash_file(Path('/etc/systemd/system/fyp-v11-admission-cutoff.timer'))==physical['fence_timer_sha256']
    owner=Path('/var/lib/fyp-owner');assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
    for port in [16432,16433,19100,19101,19102,19110]:
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    verify_clock(root,a.policy)
    checks=dict.fromkeys(CHECKS,True)
    ready={'version':'phase85-continuation-v11','status':'PASS','at_utc':at.isoformat(),'run_id':a.policy.run_id,'instance_id':external['instance_id'],'policy_sha256':hashlib.sha256(canonical(a.policy.model_dump(mode='json'))).hexdigest(),'operational_limits_sha256':read(root/'run.json')['operational_limits_sha256'],'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),'checks':checks,'backed_up':616,'planned':884,'active':0,'next_sequence':617,'next_execution_id':'01a11705-11f2-7276-8d5f-0277ced1a5f5','evidence':{'source':hash_file(dep/'source-and-runtime-verified.json'),'live':hash_file(dep/'live-checks.json'),'metadata':hash_file(dep/'metadata-and-timers.json'),'root':hash_file(dep/'root-resize-verified.json'),'prelaunch':read(root/'prelaunch-backup-proof.json'),'external_guards_verified':external['guards']},'host':sample,'cloud_all_versions_bytes':cloudbytes,'cloud_full_projection_bytes':cloud_projection,'backup_full_projection_bytes':backup_projection,'required_physical_free_bytes':required,'measured_prelaunch_backup_growth_bytes':prep_growth,'complete_backup_stage_bound_bytes':complete_bound,'completion_utc':finish.isoformat(),'uncertainty_completion_utc':uncertain.isoformat(),'budget':{'uncertainty_usd':a.policy.committed_cost(uncertain)+extra,'full_deadline_usd':a.policy.committed_cost(a.policy.stop_at)+extra,'total_extra_root_reserve_usd':extra},'stop_at':a.policy.stop_at.isoformat(),'admission_fence':physical['admission_fence'],'driver_calls':0}
    write_new(root/'continuation-readiness.json',ready);Journal(root).event('V11_GENUINE_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),main_admitted=False)
    print(json.dumps({'status':'PASS','readiness_sha256':hash_file(root/'continuation-readiness.json'),'policy_sha256':ready['policy_sha256'],'instance_id':ready['instance_id'],'checks':checks,'main_admitted':False,'budget':ready['budget'],'backup_projection':backup_projection,'physical_free':sample['system_free_bytes'],'required_physical_free':required,'complete_backup_bound':complete_bound}))
if __name__=='__main__':main()
