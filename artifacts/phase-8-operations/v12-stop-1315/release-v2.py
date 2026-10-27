"""External-only correction: authenticate review in the durable admission chain."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,shutil,sqlite3,subprocess,sys,tarfile,time,traceback
from datetime import UTC,datetime
from pathlib import Path
from types import SimpleNamespace

BASE=Path('/var/lib/p8-continuation-v12/recovery1315')
spec=importlib.util.spec_from_file_location('retained_recovery',BASE/'recover1315.py')
assert spec and spec.loader
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from controls import Journal,Policy,read,write_new,hash_file
from storage import ObjectProof,verify_local
from runner import verify_run,verify_clock,verify_host_timer
from transport import Receipt,S3Store,download,extract
ROOT=m.ROOT
OUT=BASE/'release-v2'
BOUND=192*1024**2

def tree(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def save(name,v):
    write_new(OUT/name,v);print(json.dumps({'record':name,**v},default=str),flush=True)

def controls():
    start=time.monotonic();now=datetime.now(UTC)
    sample={'available_memory_bytes':4*1024**3,'system_free_bytes':100*1024**3,'output_free_bytes':100*1024**3,'backup_free_bytes':100*1024**3,'working_bytes':0,'backup_bytes':0}
    auth=SimpleNamespace(policy=Policy(scope='CALIBRATION',run_id='cal-v4-review-control',host_started_at=now),verify=lambda at:None)
    j=Journal(OUT/'offline-controls/rename-only')
    j.initialize([{'sequence':1,'case_id':'cal-v4-review-1315','arm':'B3','fixture_hash':'0'*64}],'CALIBRATION')
    identity=j.rows()[0]['execution_id'];j.pause('PROTOCOL_STOP');(j.root/'pause.json').rename(j.root/'retained-test-pause.json')
    try:j.admit(auth,sample,now,0)
    except ValueError as e:assert str(e)=='DURABLE_PAUSE_REQUIRES_REVIEW'
    else:raise AssertionError('MISSING_RESUME_EVENT_NOT_REJECTED')
    j.event('RESUME_SAVED_ORDER',review='offline-synthetic-review')
    admitted=j.admit(auth,sample,now,0);assert admitted['execution_id']==identity and admitted['state']=='RUNNING'
    j2=Journal(OUT/'offline-controls/pause-still-present')
    j2.initialize([{'sequence':1,'case_id':'cal-v4-review-1315-pause','arm':'P2','fixture_hash':'0'*64}],'CALIBRATION')
    j2.pause('PROTOCOL_STOP');j2.event('RESUME_SAVED_ORDER',review='offline-synthetic-review')
    try:j2.admit(auth,sample,now,0)
    except ValueError as e:assert str(e)=='PAUSED_ADMISSIONS'
    else:raise AssertionError('PAUSE_FILE_BYPASSED')
    assert time.monotonic()-start<30
    save('offline-controls.json',{'status':'PASS','checks':3,'seconds':time.monotonic()-start,'controls':['rename_only_rejected','review_event_preserves_saved_identity','existing_pause_still_blocks'],'research_drivers':0,'aws_calls':0,'retained_control_ledgers':True})

def main():
    OUT.mkdir(mode=0o700,exist_ok=False)
    try:
        controls()
        os.environ.update(m.ENV)
        auth=read(BASE/'authorization.json');assert datetime.now(UTC)<datetime.fromisoformat(auth['expires_at'])
        # This is only the positively diagnosed external release failure, not an arbitrary pause.
        assert read(ROOT/'pause.json')=={'reason':'PROTOCOL_STOP','at':'2026-10-23T19:35:07.147941+00:00'}
        pausehash=hash_file(ROOT/'pause.json')
        rows,notices=m.snapshot(ROOT/'campaign.sqlite3')
        failures=[x for x in notices if x.get('kind')=='PROTOCOL_STOP' and x.get('at','')>='2026-10-23T19:34:19']
        assert len(failures)==1 and failures[0]['type']=='ValueError' and failures[0]['detail']=='DURABLE_PAUSE_REQUIRES_REVIEW'
        assert rows==read(BASE/'boundary-before.json')['rows'] and not (ROOT/'slots/1316').exists()
        a=verify_run(ROOT);verify_clock(ROOT,a.policy)
        cloud=m.S3Cloud(a.policy.cloud_bucket,'exports/phase8/'+a.policy.run_id+'/')
        initial=m.capacity(a,cloud,preparation=BOUND)
        units=m.cmd(['systemctl','show',*m.UNITS,'--property=Id,MainPID,ActiveState,SubState,ExecStart,Result'])
        save('before-quiescence.json',{'units':units,'pause_sha256':pausehash,'forecast':initial})
        m.cmd(['systemctl','stop',*m.UNITS],seconds=60);m.inactive()
        for u,text in zip(m.UNITS,(m.campaign_unit(ROOT),m.watchdog_unit(ROOT))):
            assert Path('/etc/systemd/system',u).read_text()==text
            assert Path('/etc/systemd/system',u+'.d/75-fyp-imds-discovery.conf').read_text()==m.DROPIN
        assert m.snapshot(ROOT/'campaign.sqlite3')[0]==rows
        failed=OUT/'failed-attempt1';failed.mkdir()
        assert (ROOT/'campaign.sqlite3').stat().st_size<80*1024**2,'BOUNDED_LEDGER_COPY_STOP'
        with Journal(ROOT).connect() as db,sqlite3.connect(failed/'campaign.sqlite3') as target:db.backup(target)
        shutil.copyfile(ROOT/'pause.json',failed/'pause.json')
        shutil.copyfile(BASE/'recover1315.py',failed/'external-controller-attempt1.py')
        write_new(failed/'diagnosis.json',{'original_credential_pause_sha256':m.PAUSE,'current_pause_sha256':pausehash,'trigger':failures[0],'full_recovery_backup':read(BASE/'recovery-backup-verified.json'),'failed_release_ssm':'1ec66c9b-7c3a-4eb5-8636-ff976f24924a','frozen_source_unchanged':True,'boundary':{'BACKED_UP':1315,'PLANNED':185},'controller_v2_sha256':hash_file(Path(__file__))})
        manifest={p.name:hash_file(p) for p in failed.iterdir() if p.is_file()}
        write_new(failed/'manifest.json',{'files':manifest,'postgres_dumps':False,'kind':'EXTERNAL_RELEASE_FAILURE_DIAGNOSTIC'})
        archive=OUT/'failed-attempt1.tar.gz'
        with tarfile.open(archive,'x:gz') as tf:tf.add(failed,arcname='slot')
        verify_local(archive,hash_file(archive));assert tree(OUT)<BOUND
        expanded=sum(p.stat().st_size for p in failed.iterdir() if p.is_file())
        assert tree(OUT)+2*archive.stat().st_size+expanded+1024**2<BOUND,'BOUNDED_INDEPENDENT_READBACK_STOP'
        key=cloud.prefix+'recovery1315-failed-release/'+hash_file(archive)+'.tar.gz'
        proof=cloud.put(archive,key)
        # Independent version-specific readback, not the local archive; no continuation claim.
        received=download(S3Store('fyp-research'),Receipt.model_validate(proof.model_dump()),OUT/'t')
        verify_local(received,proof.sha256);extract(received,OUT/'x',proof.sha256)
        assert tree(OUT)<BOUND
        save('failed-attempt-preserved.json',{'status':'PASS_INDEPENDENT_READBACK','cloud':proof.model_dump(),'staging_bytes':tree(OUT),'bound_bytes':BOUND,'recovery_master_unchanged':read(BASE/'recovery-backup-verified.json')['cloud']['sha256']})
        for phase in ('prelaunch','complete'):m.verify_proof(ROOT,phase,cloud)
        recovery=read(BASE/'recovery-backup-verified.json')
        assert hash_file(Path(recovery['readback_record']))==recovery['readback_sha256']
        cloud.verify(ObjectProof.model_validate(recovery['cloud']))
        verify_clock(ROOT,a.policy);forecast=m.capacity(a,cloud)
        assert m.snapshot(ROOT/'campaign.sqlite3')[0]==rows and hash_file(ROOT/'pause.json')==pausehash
        for timer in ('fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v12-admission-cutoff.timer'):m.cmd(['systemctl','is-active','--quiet',timer])
        save('readiness.json',{'status':'PASS_REVIEWED_EXTERNAL_RELEASE_V2','at':datetime.now(UTC).isoformat(),'authorization_sha256':hash_file(BASE/'authorization.json'),'pause_sha256':pausehash,'forecast':forecast,'next_execution':m.NEXT,'failed_attempt_backup':proof.model_dump(),'frozen_source_unchanged':True})
        m.cmd(['systemctl','start','fyp-phase8-watchdog.service']);verify_host_timer(ROOT)
        assert m.snapshot(ROOT/'campaign.sqlite3')[0]==rows and hash_file(ROOT/'pause.json')==pausehash
        target=ROOT/'retained-protocol1315-release-attempt1-pause.json';assert not target.exists()
        # This is the same durable decision required by frozen handover.py and Journal.admit.
        # Until the exact pause is moved, even this decision cannot permit admission.
        Journal(ROOT).event('RESUME_SAVED_ORDER',human_authorization_sha256=hash_file(BASE/'authorization.json'),reviewed_pause_sha256=pausehash,readiness_sha256=hash_file(OUT/'readiness.json'),failed_attempt_evidence=proof.model_dump(),next_execution=m.NEXT,external_release_correction=True)
        (ROOT/'pause.json').rename(target);assert hash_file(target)==pausehash
        m.cmd(['systemctl','start','fyp-phase8-campaign.service'])
        save('started.json',{'status':'SERVICES_STARTED_ACTUAL_ADMISSION_PENDING_VERIFICATION','at':datetime.now(UTC).isoformat(),'units':m.cmd(['systemctl','show',*m.UNITS,'--property=Id,MainPID,ActiveState,SubState,Result']),'next_execution':m.NEXT})
    except BaseException as e:
        save('failure-'+str(time.time_ns())+'.json',{'type':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc()})
        Journal(ROOT).pause('CREDENTIAL_RECOVERY_V2_FAILED')
        subprocess.run(['systemctl','stop',*m.UNITS],timeout=60,check=False)
        subprocess.run(['shutdown','-h','+1','Bounded recovery failed; preserve root/evidence'],timeout=10,check=False)
        raise

if __name__=='__main__':main()
