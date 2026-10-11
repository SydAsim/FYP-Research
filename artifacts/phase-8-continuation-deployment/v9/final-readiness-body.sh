set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PY'
import hashlib,json,socket,subprocess,sys
from datetime import timedelta,datetime
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import CHECKS,ContinuationAuthority,original_policy,verify_imported_first
from runner import verify_clock
from prelaunch_backup import verify_proof
from closed_restart import boundary
from operational_limits import LIMITS_SHA256
from storage import S3Cloud
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation-v9/run');dep=root.parent/'deployment';owner=Path('/var/lib/fyp-owner')
external=read(dep/'external-reuse-gates-attempt3.json')
assert datetime.fromisoformat(external['expires_at'])>utc()
health=read(dep/'live-preparation-checks.json');source=read(dep/'current-source-integrity-attempt3.json');quiet=read(dep/'old-unit-quiescence-attempt3.json')
assert health['status']=='PASS' and health['closed_originals']==120 and health['driver_calls']==0
assert source['status']=='PASS' and quiet['status']=='PASS' and quiet['old_pause_preserved']
reuse=read(root/'reuse-preparation.json');assert reuse['status']=='PASS_PREPARATION_NOT_LAUNCH' and reuse['driver_calls']==0
assert read(Path('/var/lib/p8-continuation-v7/run/pause.json'))['reason']=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'
a=ContinuationAuthority(root,read(root/'run.json'));authority=a.verify(prelaunch=True)
j=Journal(root);j.verify();rows=j.rows();verify_imported_first(root)
boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
assert rows[120]['sequence']==121 and rows[120]['execution_id']=='01a11705-11f1-75f4-b64e-8f0a3679518b' and rows[120]['arm']=='P1' and rows[120]['attempt']==1
assert not (root/'slots').exists() and read(root/'pause.json')['reason']=='CONTINUATION_REVIEW_REQUIRED'
verify_clock(root,a.policy)
now=utc();finish=now+timedelta(hours=267.1562082777036+2+.5)
cost=a.policy.committed_cost(finish)
assert cost<60 and finish<a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');store=S3Store('fyp-research')
verify_proof(root,'prelaunch',cloud)
assert store.client.get_bucket_versioning(Bucket=a.policy.cloud_bucket).get('Status')=='Enabled'
cloud_bytes=cloud.inventory()
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
assert reserved==0
sample=host(root,root.parent/'backup')
guard(a.policy,sample,now,cloud_bytes+reserved,extra_bytes=a.policy.slot_capacity_reserve_bytes)
assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s:s.bind(('127.0.0.1',port))
subprocess.run(['systemctl','is-active','--quiet','fyp-p85-continuation-bootstrap-stop.timer'],check=True,timeout=10)
timers=subprocess.run(['systemctl','list-timers','--all','--no-pager'],check=True,text=True,capture_output=True,timeout=10).stdout
assert '2026-10-22 15:24:23' in timers
scheduler=external['evidence']['current_scheduler']
assert scheduler['State']=='ENABLED' and json.loads(scheduler['Target']['Input'])['InstanceIds']==[external['instance_id']]
stop=datetime.fromisoformat(scheduler['ScheduleExpression'].removeprefix('at(').removesuffix(')')+'+00:00')
assert now<stop and stop<=now+timedelta(hours=2)
actual=external['evidence']['host'];volume=external['evidence']['volume'];security=external['evidence']['security']
assert actual['State']['Name']=='running' and volume['Size']==160 and not security['SecurityGroups'][0]['IpPermissions']
credit=external['evidence']['feasibility']['plan'];assert credit['accountPlanType']=='FREE' and credit['accountPlanStatus']=='ACTIVE' and credit['accountPlanRemainingCredits']['amount']>=65
assert now<datetime.fromisoformat('2026-10-11T09:33:51.252814+00:00')
checks=dict.fromkeys(CHECKS,True)
ready={'version':'phase85-continuation-v9','status':'PASS','at_utc':now.isoformat(),'instance_id':actual['InstanceId'],'run_id':a.policy.run_id,'policy_sha256':hashlib.sha256(canonical(original_policy(read(root/'run.json')['policy']).model_dump(mode='json'))).hexdigest(),'operational_limits_sha256':LIMITS_SHA256,'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),'checks':checks,'evidence':{'actual_preparation':hash_file(root/'reuse-preparation.json'),'source_integrity':hash_file(dep/'current-source-integrity-attempt3.json'),'dependencies_and_all_82_original_backups':hash_file(dep/'live-preparation-checks.json'),'old_unit_ownership_and_quiescence':hash_file(dep/'old-unit-quiescence-attempt3.json'),'external_gates':hash_file(dep/'external-reuse-gates-attempt3.json'),'prelaunch_backup':read(root/'prelaunch-backup-proof.json'),'timer_output':timers,'authority':authority},'backed_up':120,'planned':1380,'active':0,'next_sequence':121,'next_execution_id':rows[120]['execution_id'],'main_driver_calls':0,'host':sample,'cloud_all_versions_bytes':cloud_bytes,'budget':{'total_usd':65,'guard_usd':60,'reviewed_remaining_hours':267.1562082777036,'projected_finish_utc':finish.isoformat(),'conservative_projected_usd':cost,'no_clock_reset':True},'original_deadline':a.policy.stop_at.isoformat()}
write_new(root/'continuation-readiness.json',ready)
j.event('V7_ACTUAL_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),instance=actual['InstanceId'],main_admitted=False)
print(json.dumps({'status':'PASS','instance_id':actual['InstanceId'],'readiness_sha256':hash_file(root/'continuation-readiness.json'),'checks':checks,'policy_sha256':ready['policy_sha256'],'operational_limits_sha256':LIMITS_SHA256,'conservative_projected_usd':cost,'main_admitted':False}))
PY
