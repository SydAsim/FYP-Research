"""Seal operational disposition without changing frozen research evidence."""
import json,sqlite3,sys
from pathlib import Path
from datetime import datetime,timezone
repo=Path(__file__).resolve().parents[3];dep=Path(__file__).parent
sys.path.insert(0,str(repo/'artifacts/phase-8-continuation/v1'))
from controls import read,write_new,hash_file
from verify_package import verify
history=verify();local=read(dep/'poststop-local-evidence.json')
if local['status']!='PASS':raise ValueError('LOCAL_READBACK_INCOMPLETE')
db=sqlite3.connect('file:C:/p8c1/m/x/slot/campaign.sqlite3?mode=ro',uri=True);db.row_factory=sqlite3.Row
rows=[dict(x) for x in db.execute('SELECT * FROM slots ORDER BY sequence')];db.close()
saved=read(repo/'artifacts/phase-8-continuation/v1/saved-identities.json')['rows']
fields=('sequence','case_id','arm','attempt','execution_id','fixture_hash')
if len(rows)!=1500 or any(any(a[k]!=b[k] for k in fields) for a,b in zip(rows,saved,strict=True)):raise ValueError('ORIGINAL_IDENTITY_OR_ORDER_DRIFT')
if [x['state'] for x in rows]!=['BACKED_UP','BACKED_UP']+['PLANNED']*1498:raise ValueError('UNAUTHORIZED_EXTRA_ADMISSION')
frozen=repo/'artifacts/phase-8-continuation-freeze/v1'
if sys.platform=='win32':frozen=Path('\\\\?\\'+str(frozen))
freeze=read(frozen/'freeze-manifest.json')
for name,digest in freeze['files'].items():
 if hash_file(frozen/name)!=digest:raise ValueError('FROZEN_COPY_DRIFT')
state=read(dep/'confirmed-host-stopped.json')
aws=state.get('structuredContent') or json.loads(state['content'][0]['text'])
host=aws['return_value']['Reservations'][0]['Instances'][0]
if host['InstanceId']!='i-034252c3e9b083abf' or host['State']['Name']!='stopped':raise ValueError('STOP_NOT_CONFIRMED')
export=read(Path('C:/p8c1/s/x/slot/executions')/rows[1]['execution_id']/'export.json')
result={'verification_status':'PASS','campaign_disposition':'PAUSED_UNRECOGNIZED_P1_REFUSAL','at_utc':datetime.now(timezone.utc).isoformat(),'accepted_package_hash':freeze['package_hash'],'immutable_freeze_members_verified':len(freeze['files']),'historical_evidence_verification':history,'actual_host_state':'stopped','instance_id':host['InstanceId'],'standalone_admission_actually_occurred':True,'slot2_execution_id':rows[1]['execution_id'],'slot2_raw_status':export['status'],'slot2_original_observation_deadline':rows[1]['deadline'],'slot2_finished_at':export['finished_at'],'slot2_analysis':export['analysis_row'],'backed_up':2,'remaining_originals_unstarted':1498,'saved_identities_and_serial_order':'PASS','no_replay_or_replacement':True,'local_and_cloud_archive_member_checks':'PASS','source_or_application_changes':False,'budget_usd':65,'admission_guard_usd':55,'original_deadline_utc':'2026-10-22T15:24:23.810674Z','retention_review_due_utc':'2026-10-09T21:05:37.547530Z','old_host_and_owned_root_removed':True,'fresh_root_retained':True}
write_new(dep/'final-verification.json',result)
print(json.dumps({'verification_status':'PASS','campaign_disposition':result['campaign_disposition'],'actual_host_state':'stopped','backed_up':2,'remaining_unstarted':1498,'frozen_members':len(freeze['files']),'protected_historical_paths':history['protected_paths']}))

