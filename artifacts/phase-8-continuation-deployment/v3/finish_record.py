"""Verify preserved local authority and record actual continuation evidence."""
import hashlib,json,sys
from pathlib import Path
from datetime import UTC,datetime
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path.insert(0,str(REPO/'artifacts/phase-8-runner-amendment/v3'))
from controls import canonical,hash_file,read,write_new

frozen=Path('\\\\?\\'+str((REPO/'artifacts/phase-8-continuation-freeze/v3').resolve()))
manifest=read(frozen/'freeze-manifest.json')
assert hash_file(frozen/'freeze-manifest.json')=='49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86'
assert all(hash_file(frozen/n)==v for n,v in manifest['files'].items())
candidate=REPO/'artifacts/phase-8-runner-amendment/v3';inventory=read(candidate/'candidate-inventory.json')
assert inventory['package_hash']=='2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736'
assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']
assert all(hash_file(REPO/n)==v for n,v in inventory['files'].items())
protected=read(candidate/'preservation-before.json')
assert all(hash_file(Path(n))==v for n,v in protected.items())
assert hash_file(candidate.parent/'v3-combined-review-candidate.tar.gz')=='0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf'
p=read(HERE/'progress-status1-result.json')['result'];assert p['Status']=='Success'
progress=json.loads(p['StandardOutputContent']);slot=progress['active'][0]
assert slot['sequence']==3 and slot['arm']=='P2' and slot['execution_id']=='01a11705-11f0-7a68-8c68-4da5c8126c84' and slot['attempt']==1
assert progress['counts']=={'BACKED_UP':2,'PLANNED':1497,'RUNNING':1} and progress['pause'] is None
assert 'ActiveState=active' in progress['units']['fyp-phase8-campaign.service']
assert 'ActiveState=active' in progress['units']['fyp-phase8-watchdog.service']
backup=json.loads(read(HERE/'activate-controls-lf-status3-result.json')['result']['StandardOutputContent'].splitlines()[0])
assert backup['status']=='PASS' and backup['watchdog_and_absolute_timer_verified']
write_new(HERE/'actual-continuation-start.json',{'status':'STARTED','observed_at_utc':progress['at_utc'],'admitted_at_utc':progress['last_admission']['at'],'run_id':progress['run_id'],'instance_id':progress['host_id'],'slot':slot,'counts':progress['counts'],'pause':None,'backup':backup['backup'],'deadline_utc':progress['absolute_stop_utc'],'units':progress['units']})
write_new(HERE/'final-verification.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'package_hash':inventory['package_hash'],'archive_sha256':hash_file(candidate.parent/'v3-combined-review-candidate.tar.gz'),'freeze_manifest_sha256':hash_file(frozen/'freeze-manifest.json'),'frozen_members_verified':len(manifest['files']),'accepted_source_members_verified':len(inventory['files']),'historical_files_preserved':len(protected),'main_continuation_started':True,'actual_sequence':3,'execution_id':slot['execution_id'],'source_application_changed':False,'operational_clock_reset':False,'campaign_completion_claimed':False})
files={p.name:hash_file(p) for p in HERE.iterdir() if p.is_file() and p.name!='operational-inventory.json'}
write_new(HERE/'operational-inventory.json',{'kind':'ACTUAL_DEPLOYMENT_EVIDENCE_INVENTORY_NOT_STUDY_AMENDMENT','files':files})
print(json.dumps(read(HERE/'final-verification.json')))
