cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import hashlib,json,socket,subprocess,sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import CHECKS,ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from runner import verify_clock
from storage import ObjectProof,S3Cloud
from transport import Receipt,S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation/run');dep=Path('/var/lib/p8-continuation/deployment');owner=Path('/var/lib/fyp-owner')
external=read(dep/'external-readiness-evidence.json')
def aws_record(name):
 return json.loads(external[name]['result']['content'][0]['text'])
if aws_record('old-root-cleanup-delete.json')['status']!='success':raise ValueError('AUTHORIZED_OLD_ROOT_CLEANUP_NOT_VERIFIED')
if aws_record('old-host-cleanup-termination.json')['return_value']['termination']['TerminatingInstances'][0]['PreviousState']['Name']!='stopped':raise ValueError('ORIGINAL_HOST_NOT_STOPPED_BEFORE_CLEANUP')
credit=aws_record('preadmission-credits.json')['return_value']
if credit['accountPlanType']!='FREE' or credit['accountPlanStatus']!='ACTIVE' or credit['accountPlanRemainingCredits']['amount']<65:raise ValueError('PLAN_OR_CREDIT_GATE')
if read(dep/'host-health-readiness.json')['status']!='PASS':raise ValueError('ACTUAL_HOST_HEALTH_NOT_VERIFIED')
imported=read(dep/'import-and-backup-readiness.json')
if imported['status']!='PASS':raise ValueError('IMPORT_NOT_VERIFIED')
authority=ContinuationAuthority(root,read(root/'run.json'));freeze=authority.verify(prelaunch=True)
verify_imported_first(root);journal=Journal(root);journal.verify()
closed_boundary(journal.rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_clock(root,authority.policy,utc())
if (root/'slots').exists() or read(root/'pause.json')['reason']!='CONTINUATION_REVIEW_REQUIRED':raise ValueError('PREMATURE_MAIN_OR_PAUSE_DRIFT')
policy=authority.policy;now=utc();finish=now+timedelta(hours=314)
cost=policy.committed_cost(finish+timedelta(minutes=30))
if finish>=policy.stop_at-timedelta(seconds=policy.admission_cutoff_seconds) or cost>=55:raise ValueError('CONSERVATIVE_REMAINING_PLAN_DOES_NOT_FIT')
backup=Path('/var/lib/p8-continuation/backup');cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/');store=S3Store('fyp-research')
cloud_bytes=cloud.inventory()
with journal.connect() as db:outstanding=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
sample=host(root,backup);sample.update(working_bytes=0,backup_bytes=0)
guard(policy,sample,now,cloud_bytes+outstanding,extra_bytes=policy.slot_capacity_reserve_bytes)
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS')
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
if store.client.get_bucket_versioning(Bucket=policy.cloud_bucket).get('Status')!='Enabled':raise ValueError('VERSIONING_GATE')
for proof in imported['original_backups']+[imported['prelaunch_backup'],imported['permission_probe']]:
 store.head(Receipt.model_validate(proof))
verify_members(root.parent/'prelaunch-readback/x/slot')
for timer in ('fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer'):
 subprocess.run(['systemctl','is-active','--quiet',timer],check=True,timeout=10)
timers=subprocess.run(['systemctl','list-timers','fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout
if '2026-10-22 15:24:23' not in timers:raise ValueError('ABSOLUTE_DEADLINE_TIMER')
ready={
 'version':'phase85-continuation-v1','status':'PASS','at_utc':now.isoformat(),
 'instance_id':'i-034252c3e9b083abf','run_id':policy.run_id,
 'policy_sha256':hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest(),
 'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),
 'checks':dict.fromkeys(CHECKS,True),
 'evidence':{'import_and_backups':hash_file(dep/'import-and-backup-readiness.json'),'hashes_and_empty_services':hash_file(dep/'host-health-readiness.json'),'external_API_records':hash_file(dep/'external-readiness-evidence.json'),'prelaunch_backup':imported['prelaunch_backup'],'permission_probe':imported['permission_probe'],'timers':timers,'source_and_freeze_chain':freeze},
 'original_host_disposition':'Verified STOPPED before authorized termination; original root deleted after independent evidence verification; never restarted',
 'budget':{'unchanged_total_usd':65,'unchanged_guard_usd':55,'reserve_inside_limits_usd':1.25,'conservative_13_day_plus_setup_cost_usd':cost,'projected_finish_utc':finish.isoformat()},
 'host':sample,'cloud_bytes_all_versions':cloud_bytes,'outstanding_bytes':outstanding,
 'original_deadline_utc':policy.stop_at.isoformat(),'operational_clock_reset':False,
 'first_raw_status':'FAILED','first_backed_up':1,'remaining_planned':1499,'main_driver_calls':0,
 'historical_readiness_failures_retained':True,
}
write_new(root/'continuation-readiness.json',ready)
journal.event('CONTINUATION_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),instance=ready['instance_id'],main_admitted=False)
print(json.dumps({'status':'PASS','readiness_sha256':hash_file(root/'continuation-readiness.json'),'instance_id':ready['instance_id'],'policy_sha256':ready['policy_sha256'],'handover_sha256':ready['handover_sha256'],'boot_anchor_sha256':ready['boot_anchor_sha256'],'checks':ready['checks'],'prelaunch_backup':imported['prelaunch_backup'],'conservative_cost_usd':cost,'main_admitted':False}))
PY
