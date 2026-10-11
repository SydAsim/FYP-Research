#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import hashlib,json,socket,subprocess,sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import CHECKS,ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from runner import verify_clock
from storage import ObjectProof,S3Cloud
from transport import Receipt,S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined/run');dep=root.parent/'deployment';owner=Path('/var/lib/fyp-owner')
external=read(dep/'external-readiness-evidence.json')
credit=external['credits']['result']
if credit['accountPlanType']!='FREE' or credit['accountPlanStatus']!='ACTIVE' or credit['accountPlanRemainingCredits']['amount']<65:raise ValueError('PLAN_CREDIT_GATE')
cleanup=external['old_cleanup']
if cleanup['status']!='PASS' or cleanup['old_host']!='i-034252c3e9b083abf' or cleanup['old_root']!='vol-0f667d76019af7a47':raise ValueError('AUTHORIZED_OLD_CLEANUP_GATE')
old=external['old_stopped_before_cleanup']['result']['Reservations'][0]['Instances'][0]
if old['State']['Name']!='stopped':raise ValueError('OLD_HOST_NOT_STOPPED_BEFORE_CLEANUP')
actual=external['new_host']['result']['Reservations'][0]['Instances'][0]
volume=external['new_root']['result']['Volumes'][0]
if actual['InstanceId']!='i-002b63326e1566005' or actual['State']['Name']!='running' or actual['InstanceType']!='m7i-flex.large' or volume['Size']!=160 or volume['VolumeType']!='gp3' or not volume['Encrypted']:raise ValueError('NEW_HOST_OR_ROOT_DRIFT')
if actual['BlockDeviceMappings'][0]['Ebs']['DeleteOnTermination'] or actual['MetadataOptions']['HttpTokens']!='required':raise ValueError('EVIDENCE_DISK_OR_IMDS_DRIFT')
if external['security']['result']['SecurityGroups'][0]['IpPermissions']:raise ValueError('INBOUND_ACCESS_GATE')
health=read(dep/'host-health-readiness.json');imported=read(dep/'import-and-backup-readiness.json')
if health['status']!='PASS' or imported['status']!='PASS' or health['scientific_driver_calls']!=0 or imported['driver_calls']!=0:raise ValueError('HOST_HEALTH_OR_IMPORT_GATE')
a=ContinuationAuthority(root,read(root/'run.json'));freeze=a.verify(prelaunch=True)
verify_imported_first(root);j=Journal(root);j.verify();rows=j.rows()
closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_clock(root,a.policy,utc())
if (root/'slots').exists() or read(root/'pause.json')['reason']!='CONTINUATION_REVIEW_REQUIRED':raise ValueError('PREMATURE_MAIN_OR_PAUSE_DRIFT')
if rows[2]['execution_id']!='01a11705-11f0-7a68-8c68-4da5c8126c84':raise ValueError('NEXT_P2_DRIFT')
now=utc();finish=now+timedelta(hours=290);cost=a.policy.committed_cost(finish+timedelta(minutes=30))
if finish>=a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds) or cost>=55:raise ValueError('UNCHANGED_REMAINING_PLAN_DOES_NOT_FIT')
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');store=S3Store('fyp-research')
cloud_bytes=cloud.inventory()
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
sample=host(root,root.parent/'backup');sample.update(working_bytes=0,backup_bytes=0)
guard(a.policy,sample,now,cloud_bytes+reserved,extra_bytes=a.policy.slot_capacity_reserve_bytes)
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS_GATE')
for p in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',p))
if store.client.get_bucket_versioning(Bucket=a.policy.cloud_bucket).get('Status')!='Enabled':raise ValueError('VERSIONING_GATE')
for proof in imported['original_backups']+[imported['prelaunch_backup'],imported['permission_probe']]:store.head(Receipt.model_validate(proof))
verify_members(root.parent/'prelaunch-readback/x/slot');verify_imported_first(root.parent/'prelaunch-readback/x/slot')
for timer in ('fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer','fyp-p85-combined-preparation-absolute.timer'):
 subprocess.run(['systemctl','is-active','--quiet',timer],check=True,timeout=10)
timers=subprocess.run(['systemctl','list-timers','fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-combined-preparation-absolute.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout
if '2026-10-22 15:24:23' not in timers or '2026-10-08 09:05:38' not in timers:raise ValueError('ABSOLUTE_TIMER_DRIFT')
checks=dict.fromkeys(CHECKS,True)
ready={'version':'phase85-combined-amendment-v3','status':'PASS','at_utc':now.isoformat(),'instance_id':actual['InstanceId'],'run_id':a.policy.run_id,
 'policy_sha256':hashlib.sha256(canonical(a.policy.model_dump(mode='json'))).hexdigest(),'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),
 'checks':checks,'evidence':{'import_and_backup':hash_file(dep/'import-and-backup-readiness.json'),'source_dependencies_empty_stack':hash_file(dep/'host-health-readiness.json'),'external_readiness':hash_file(dep/'external-readiness-evidence.json'),'prelaunch_backup':imported['prelaunch_backup'],'timer_trigger_output':timers,'source_authority_chain':freeze},
 'originals_raw_status':['FAILED','FAILED'],'backed_up':2,'planned':1498,'next_execution_id':rows[2]['execution_id'],'main_driver_calls':0,
 'budget':{'total_usd':65,'guard_usd':55,'reserve_usd':1.25,'projected_finish_utc':finish.isoformat(),'cost_with_original_elapsed_clock_usd':cost,'includes_previous_spending':True,'twelve_days_not_guaranteed':True},
 'host':sample,'cloud_all_versions_bytes':cloud_bytes,'unresolved_reservations_bytes':reserved,'original_deadline':a.policy.stop_at.isoformat(),'operational_clock_reset':False,'historical_readiness_failures_retained':True}
write_new(root/'continuation-readiness.json',ready);j.event('V3_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),instance=actual['InstanceId'],main_admitted=False)
print(json.dumps({'status':'PASS','readiness_sha256':hash_file(root/'continuation-readiness.json'),'instance_id':actual['InstanceId'],'policy_sha256':ready['policy_sha256'],'handover_sha256':ready['handover_sha256'],'boot_anchor_sha256':ready['boot_anchor_sha256'],'checks':checks,'prelaunch_backup':imported['prelaunch_backup'],'conservative_cost_usd':cost,'main_admitted':False}))
PY
