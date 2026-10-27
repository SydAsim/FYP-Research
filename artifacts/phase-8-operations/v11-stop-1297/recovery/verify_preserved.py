"""Reuse completed backups/readbacks; verify stopped-boundary facts without retry."""
from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('read_transport',ROOT/'artifacts/phase-8-results-share/v3/download.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE
body=r'''
import collections,json,subprocess,sys
from pathlib import Path
from datetime import timedelta
source=Path('/opt/fyp-phase8-continuation-v11');sys.path.insert(0,str(source/'artifacts/phase-8-runner-amendment/v4-complete'));sys.path.insert(1,str(source))
from controls import read,hash_file,utc
from closed145 import snapshot
from runner import meter
from handover import ContinuationAuthority
root=Path('/var/lib/p8-continuation-v9/run');out=Path('/var/lib/p8-continuation-v11/deployment/stop1297-1792750933234669142')
rows=read(out/'saved-rows.json');pause=read(out/'pause.json')
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':1297,'PLANNED':203} and not (root/'slots/1298').exists()
units=['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']
unit_state=subprocess.run(['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID'],capture_output=True,text=True,check=True,timeout=10).stdout
assert all(subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()=='0' for u in units)
master=read(out/'master-cloud-proof.json');diagnostic=read(out/'diagnostic-cloud-proof.json')
mr=root.parent/'backup/r1297m/postflight-verified.json';dr=root.parent/'backup/r1297d/postflight-verified.json'
assert read(mr)['object']==master and read(dr)['object']==diagnostic
assert snapshot(mr.parent/'x/slot/campaign.sqlite3')[0]==rows and read(mr.parent/'x/slot/pause.json')==pause
assert snapshot(dr.parent/'x/slot/consistent-master.sqlite3')[0]==rows
correction=read(out/'correction-checks.json');assert correction['status']=='PASS' and hash_file(Path(correction['config']))==correction['sha256']
resources=meter(root)
a=ContinuationAuthority(root,read(root/'run.json'));extra=read(Path('/var/lib/p8-continuation-v11/deployment/root-resize-plan.json'))['total_extra_storage_reserve_usd']
at=utc();completion=at+timedelta(hours=203*262.31642189586114/1355+2.5);uncertain=completion+timedelta(hours=24)
cloud_prior=56775776795
cloud_current=cloud_prior+master['bytes']+diagnostic['bytes']
cloud_projection=cloud_current+203*60*1024**2+1024**3
backup_projection=resources['backup_bytes']+203*60*1024**2+1024**3
forecast={'at':at.isoformat(),'completion':completion.isoformat(),'uncertainty_completion':uncertain.isoformat(),'minimum_stop_with_30minute_margin':(uncertain+timedelta(minutes=30)).isoformat(),'time_shortfall_hours':(uncertain+timedelta(minutes=30)-a.policy.stop_at).total_seconds()/3600,'admission_projection_usd':a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra,'full_deadline_usd':a.policy.committed_cost(a.policy.stop_at)+extra,'cloud_bytes_after_two_verified_puts':cloud_current,'cloud_projection_bytes':cloud_projection,'backup_projection_bytes':backup_projection,'storage_caps_pass':max(cloud_projection,backup_projection)<80*1024**3,'additional_preservation_bytes':resources['backup_bytes']-63094759928,'external_one_GiB_staging_target_pass':resources['backup_bytes']-63094759928<1024**3,'actual_billing':'NOT_QUERIED; conservative original elapsed-clock forecast unchanged'}
print(json.dumps({'status':'VERIFIED_PRESERVATION_WITH_RETAINED_OPERATIONAL_BOUND_FAILURE_NO_RESUME','at':at.isoformat(),'counts':{'BACKED_UP':1297,'PLANNED':203},'units_quiesced':True,'unit_state':unit_state,'pause':pause,'pause_sha256':hash_file(root/'pause.json'),'next':rows[1297],'master_backup':master,'master_readback_sha256':hash_file(mr),'diagnostic_backup':diagnostic,'diagnostic_readback_sha256':hash_file(dr),'correction':correction,'resources':resources,'forecast':forecast,'no_main_admission':True,'preservation_attempt_status':'FAILED_EXTERNAL_1GIB_COPY_TARGET_AFTER_SUCCESSFUL_BACKUPS_AND_READBACKS; no retry or replacement performed','host_stop_pending':True}))
'''
x=json.loads(m.run('verify-completed-preservation',"cd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1\n.venv/bin/python -B - <<'READ_ONLY'\n"+body+"\nREAD_ONLY\n",65))
m.save('verified-preservation-summary.json',x);print(json.dumps(x,indent=2))
