"""Verify historical preservation and retain actual admission evidence; no driver calls."""
import hashlib,json,sys
from datetime import UTC,datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
RUNTIME=Path('E:/p8v4/source/artifacts/phase-8-runner-amendment/v4-complete')
sys.path.insert(0,str(RUNTIME))
from controls import canonical,hash_file,read,write_new

def main() -> None:
    frozen=Path('\\\\?\\'+str((REPO/'artifacts/phase-8-continuation-freeze/v4').resolve()))
    manifest=read(frozen/'freeze-manifest.json')
    assert hash_file(frozen/'freeze-manifest.json')=='cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c'
    assert all(hash_file(frozen/n)==v for n,v in manifest['files'].items())
    candidate=REPO/'artifacts/phase-8-continuation/v4';inventory=read(candidate/'candidate-inventory.json')
    assert inventory['package_hash']=='a869745a6c1807e4f2427cc9597e5d85f41a2b4eb2aa4aa8abd4bdb8cc9b7306'
    assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']
    assert all(hash_file(Path('E:/p8v4/source')/n)==v for n,v in inventory['files'].items())
    assert hash_file(candidate/'v4-complete-continuation-review-candidate.tar.gz')=='7044595739003670be74669eea70c50b0c99ff9a537cf8fde4587405182cc1c9'
    sys.path.insert(0,str(candidate))
    from qualify import verify_preserved
    preservation=verify_preserved()
    response=read(HERE/'progress-status1-result.json')['result'];assert response['Status']=='Success'
    progress=json.loads(response['StandardOutputContent']);slot=progress['active'][0]
    assert slot['sequence']==39 and slot['arm']=='B3' and slot['execution_id']=='01a11705-11f0-73c0-af15-dd9f1d590b08' and slot['attempt']==1
    assert progress['counts']=={'BACKED_UP':38,'PLANNED':1461,'RUNNING':1} and progress['pause'] is None
    assert all('ActiveState=active' in progress['units'][n] for n in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer'))
    assert all('ActiveState=inactive' in progress['units'][n] for n in ('fyp-p85-continuation-preparation-stop.timer','fyp-p85-combined-preparation-absolute.timer'))
    backup_response=read(HERE/'activate-controls-lf-status3-result.json')['result'];assert backup_response['Status']=='Success' and backup_response['ResponseCode']==0
    backup=json.loads(backup_response['StandardOutputContent'].splitlines()[0]);assert backup['status']=='PASS' and backup['watchdog_and_absolute_timer_verified']
    write_new(HERE/'actual-continuation-start.json',{'status':'STARTED','observed_at_utc':progress['at_utc'],'admitted_at_utc':progress['last_admission']['at'],'run_id':progress['run_id'],'instance_id':progress['host_id'],'slot':slot,'counts':progress['counts'],'pause':None,'backup':backup['backup'],'deadline_utc':progress['absolute_stop_utc'],'units':progress['units'],'no_original_replay':True,'remaining_including_active':1462,'unstarted':1461})
    write_new(HERE/'final-verification.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'package_hash':inventory['package_hash'],'archive_sha256':hash_file(candidate/'v4-complete-continuation-review-candidate.tar.gz'),'freeze_manifest_sha256':hash_file(frozen/'freeze-manifest.json'),'frozen_members_verified':len(manifest['files']),'accepted_source_members_verified':len(inventory['files']),'preservation':preservation,'main_continuation_started':True,'actual_sequence':39,'execution_id':slot['execution_id'],'source_application_changed':False,'operational_clock_reset':False,'campaign_completion_claimed':False,'preparation_failures_retained':['initial pre-readiness final-backup helper invocation','CRLF activation wrapper rejected before work','two Windows CLI output encoding failures while reading successful activation'],'original_outcomes_replaced':0})
    print(json.dumps(read(HERE/'final-verification.json')))

if __name__=='__main__':main()
