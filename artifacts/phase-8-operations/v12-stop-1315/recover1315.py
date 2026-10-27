"""External, same-source/same-boot credential recovery; never replays a slot."""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC,datetime,timedelta
from pathlib import Path

SOURCE=Path('/opt/fyp-phase8-continuation-v12')
ROOT=Path('/var/lib/p8-continuation-v9/run')
DEP=Path('/var/lib/p8-continuation-v12/recovery1315')
PAUSE='89bf7369aaa355e52c0bd3f59afb101d87701db33d85379b2b64549f24c4a95c'
BOOT='7b5b5cb0-f978-4e49-a75c-7d49bc40da82'
NEXT='01a11705-11f4-7875-b6f4-62729851bd64'
UNITS=('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')
ENV={'AWS_METADATA_SERVICE_TIMEOUT':'3','AWS_METADATA_SERVICE_NUM_ATTEMPTS':'3'}
DROPIN='[Service]\nEnvironment=AWS_METADATA_SERVICE_TIMEOUT=3 AWS_METADATA_SERVICE_NUM_ATTEMPTS=3\n'
PREP=1610612736
sys.path.insert(0,str(SOURCE/'artifacts/phase-8-runner-amendment/v4-complete'))
sys.path.insert(1,str(SOURCE))
from closed145 import snapshot
from controls import Journal,guard,read,hash_file,write_new
from runner import verify_run,verify_clock,verify_host_timer,meter,campaign_unit,watchdog_unit
from storage import S3Cloud,ObjectProof,final_backup,upload,verify_local
from prelaunch_backup import verify_proof
from postflight import recover

def cmd(args,seconds=20):
    return subprocess.run(args,capture_output=True,text=True,check=True,timeout=seconds).stdout

def record(name,value):
    write_new(DEP/name,value)
    print(json.dumps({'stage':name,**value},default=str),flush=True)

def closed():
    rows,notices=snapshot(ROOT/'campaign.sqlite3')
    assert len(rows)==1500 and all(x['state']=='BACKED_UP' for x in rows[:1315]),'RETAINED_BOUNDARY_DRIFT'
    assert all(x['state']=='PLANNED' and not any(x[k] for k in ('deadline','backup_hash','error')) for x in rows[1315:]),'PENDING_BOUNDARY_DRIFT'
    assert rows[1315]['execution_id']==NEXT and rows[1315]['sequence']==1316 and rows[1315]['arm']=='B3' and rows[1315]['attempt']==1,'NEXT_IDENTITY_DRIFT'
    assert not (ROOT/'slots/1316').exists(),'NEXT_SLOT_ALREADY_MATERIALIZED'
    assert hash_file(ROOT/'pause.json')==PAUSE,'UNREVIEWED_PAUSE'
    return rows

def capacity(a,cloud,*,preparation=0):
    now=datetime.now(UTC);s=meter(ROOT);total=cloud.inventory()
    guard(a.policy,s,now,total,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    future=185*68*1024**2
    completion=now+timedelta(hours=185*262.31642189586114/1355+2.5)
    uncertainty=completion+timedelta(hours=24,minutes=30)
    extra=.6551338996026301
    required=future+1024**3+(50*1024**3-s['working_bytes'])+20*1024**3+1024**3+preparation
    forecast={'at':now.isoformat(),'completion':completion.isoformat(),'uncertainty_including_margin':uncertainty.isoformat(),'uncertainty_cost':a.policy.committed_cost(uncertainty)+extra,'full_deadline_cost':a.policy.committed_cost(a.policy.stop_at)+extra,'cloud_bytes':total,'cloud_projection_bytes':total+future+1024**3+300*1024**2,'local_projection_bytes':s['backup_bytes']+future+1024**3+preparation,'required_free_bytes':required,'resource_sample':s,'stop_at':a.policy.stop_at.isoformat(),'additional_preparation_bound':preparation,'remaining':185,'future_archive_bytes':68*1024**2,'actual_billing':'NOT_QUERIED; unchanged conservative elapsed-clock forecast'}
    assert uncertainty<a.policy.stop_at and forecast['uncertainty_cost']<76 and forecast['full_deadline_cost']<77,'TIME_COST_FEASIBILITY_STOP'
    assert max(forecast['cloud_projection_bytes'],forecast['local_projection_bytes'])<80*1024**3 and s['system_free_bytes']>=required,'FULL_CAPACITY_FEASIBILITY_STOP'
    return forecast

def inactive():
    assert all(cmd(['systemctl','show',u,'--property=MainPID','--value']).strip()=='0' for u in UNITS),'OWNED_UNIT_NOT_QUIESCED'

def prepare():
    auth=read(DEP/'authorization.json')
    assert datetime.now(UTC)<datetime.fromisoformat(auth['expires_at']),'PREPARATION_AUTHORITY_EXPIRED'
    assert auth['next_execution']==NEXT and auth['source_package']=='cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d'
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'UNQUALIFIED_BOOT'
    assert hash_file(Path(sys.executable).resolve())=='021044895e95be79dc2f110367607e684119afbc8ce75f6f0eec94844e0acec7','RUNTIME_DRIFT'
    assert read(DEP/'qualification.json')['total']==5 and read(DEP/'qualification.json')['status']=='PASS'
    os.environ.update(ENV)
    rows=closed();a=verify_run(ROOT);verify_clock(ROOT,a.policy);verify_host_timer(ROOT)
    assert hash_file(Path('/etc/needrestart/conf.d/99-fyp-phase8-defer-restarts.conf'))=='a2fa11ad5a52dce6d32ce8731bf1bc8bea6eee6d76872a55e02bb01cda4cbe73'
    config=read(ROOT/'cloud.json');cloud=S3Cloud(config['bucket'],config['prefix'])
    start=capacity(a,cloud,preparation=PREP)
    record('initial-feasibility.json',{'status':'PASS',**start})
    expected=(campaign_unit(ROOT),watchdog_unit(ROOT))
    state=cmd(['systemctl','show',*UNITS,'--property=Id,MainPID,ActiveState,SubState,ExecStart,Result'])
    assert all(Path('/etc/systemd/system',u).read_text()==text for u,text in zip(UNITS,expected)),'OWNED_UNIT_SOURCE_DRIFT'
    record('owned-unit-before-quiescence.json',{'state':state,'base_units_unchanged':True,'pause_sha256':PAUSE})
    cmd(['systemctl','stop',*UNITS],seconds=60);inactive();assert closed()==rows
    history=ROOT/'restart-history/credential-recovery1315'
    history.mkdir(mode=0o700,exist_ok=False)
    write_new(history/'authorization.json',auth)
    write_new(history/'qualification.json',read(DEP/'qualification.json'))
    write_new(history/'external-controller.json',{'sha256':hash_file(Path(__file__)),'frozen_source_unchanged':True,'credential_discovery_environment':ENV,'shared_s3_request_retry_settings_unchanged':True,'historical_imds_transport_cause':'NOT_ESTABLISHED','current_inventory_complete':True})
    shutil.copyfile(ROOT/'pause.json',history/'original-pause.json')
    write_new(DEP/'boundary-before.json',{'rows':rows,'saved_identities_sha256':hash_file(ROOT/'saved-identities.json'),'bindings_sha256':hash_file(ROOT/'bindings.json'),'pause_sha256':PAUSE})
    proofs=[]
    for row in rows[:1315]:
        p=ROOT/'backups'/(row['execution_id']+'.json')
        assert hash_file(p)==row['backup_hash'],'RECEIPT_HASH_DRIFT'
        v=read(p);assert v['execution_id']==row['execution_id'] and v['sha256']==v['cloud']['sha256'],'RECEIPT_IDENTITY_DRIFT'
        if row['sequence']>1297:proofs.append((row,v))
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks=[pool.submit(cloud.verify,ObjectProof.model_validate(v['cloud'])) for _,v in proofs]
        for (row,v),task in zip(proofs,tasks):
            assert hash_file(Path(v['local']))==v['sha256'],'RECENT_ORIGINAL_ARCHIVE_DRIFT'
            task.result()
    verify_local(Path(proofs[-1][1]['local']),proofs[-1][1]['sha256'])
    for phase in ('prelaunch','complete'):verify_proof(ROOT,phase,cloud)
    assert not cmd(['docker','ps','--format','{{.Names}}']).strip(),'UNEXPECTED_LIVE_STACK'
    for u in UNITS:
        d=Path('/etc/systemd/system',u+'.d');d.mkdir(exist_ok=True)
        p=d/'75-fyp-imds-discovery.conf'
        with p.open('x',encoding='utf-8') as f:f.write(DROPIN);f.flush();os.fsync(f.fileno())
    cmd(['systemctl','daemon-reload'])
    for u in UNITS:
        effective=cmd(['systemctl','show',u,'--property=Environment','--value'])
        assert all(k+'='+v in effective.split() for k,v in ENV.items()),'CREDENTIAL_ENVIRONMENT_NOT_EFFECTIVE'
        assert Path('/etc/systemd/system',u).read_text()==expected[UNITS.index(u)]
    checks={'status':'CHECKS_PASSED_RECOVERY_BACKUP_PENDING','at':datetime.now(UTC).isoformat(),'backed_up':1315,'planned':185,'next_execution':NEXT,'original_pause_sha256':PAUSE,'boot_id':BOOT,'source_authority_verified':True,'runtime_verified':True,'old_prelaunch_complete_proofs_verified':True,'all1315_receipt_hashes_verified':True,'new18_archives_and_pinned_versions_verified':True,'original1297_qualification_reused':True,'credential_environment':ENV,'study_unchanged':True,'original_raw_outcomes_unchanged':True,'forecast':start}
    write_new(history/'checks-before-backup.json',checks)
    record('prepared.json',checks)
    Journal(ROOT).event('HUMAN_AUTHORIZED_CREDENTIAL_RECOVERY_PREPARED',authorization_sha256=hash_file(history/'authorization.json'),backed_up=1315,planned=185,next_execution=NEXT,code_unchanged=True)

def backup():
    inactive();rows=closed();auth=read(DEP/'authorization.json');assert datetime.now(UTC)<datetime.fromisoformat(auth['expires_at'])
    os.environ.update(ENV);a=verify_run(ROOT)
    config=read(ROOT/'cloud.json');cloud=S3Cloud(config['bucket'],config['prefix'])
    before=read(DEP/'initial-feasibility.json')['resource_sample']['backup_bytes']
    capacity(a,cloud,preparation=PREP)
    archive=final_backup(Journal(ROOT),ROOT.parent/'backup',prelaunch=False)
    assert meter(ROOT)['backup_bytes']-before<=PREP,'RECOVERY_BACKUP_BOUND_STOP'
    proof=upload(Journal(ROOT),cloud,a.policy,archive)
    record('uploaded-recovery-master.json',{'cloud':proof.model_dump(),'local':str(archive),'status':'PINNED_VERSION_VERIFIED_READBACK_PENDING'})
    out=ROOT.parent/'backup'/'recovery1315-readback'
    recover(proof,out)
    assert meter(ROOT)['backup_bytes']-before<=PREP,'RECOVERY_READBACK_BOUND_STOP'
    assert closed()==rows and rows==read(DEP/'boundary-before.json')['rows']
    record('recovery-backup-verified.json',{'status':'PASS_INDEPENDENT_PINNED_READBACK','archive':str(archive),'cloud':proof.model_dump(),'readback_record':str(out/'postflight-verified.json'),'readback_sha256':hash_file(out/'postflight-verified.json'),'local_growth_bytes':meter(ROOT)['backup_bytes']-before,'maximum_growth_bytes':PREP,'backed_up':1315,'planned':185})
    Journal(ROOT).event('CREDENTIAL_RECOVERY_MASTER_BACKUP_VERIFIED',cloud=proof.model_dump(),readback_sha256=hash_file(out/'postflight-verified.json'),no_replay=True)

def release():
    inactive();rows=closed();auth=read(DEP/'authorization.json');assert datetime.now(UTC)<datetime.fromisoformat(auth['expires_at'])
    assert rows==read(DEP/'boundary-before.json')['rows'],'BOUNDARY_REPLACEMENT'
    os.environ.update(ENV);a=verify_run(ROOT);config=read(ROOT/'cloud.json');cloud=S3Cloud(config['bucket'],config['prefix'])
    for phase in ('prelaunch','complete'):verify_proof(ROOT,phase,cloud)
    proof=read(DEP/'recovery-backup-verified.json');assert proof['status']=='PASS_INDEPENDENT_PINNED_READBACK'
    verify_local(Path(proof['archive']),proof['cloud']['sha256']);cloud.verify(ObjectProof.model_validate(proof['cloud']))
    assert hash_file(Path(proof['readback_record']))==proof['readback_sha256'],'RECOVERY_READBACK_DRIFT'
    forecast=capacity(a,cloud);verify_clock(ROOT,a.policy)
    for name in ('fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v12-admission-cutoff.timer'):cmd(['systemctl','is-active','--quiet',name])
    for u,text in zip(UNITS,(campaign_unit(ROOT),watchdog_unit(ROOT))):
        assert Path('/etc/systemd/system',u).read_text()==text
        assert Path('/etc/systemd/system',u+'.d/75-fyp-imds-discovery.conf').read_text()==DROPIN
    record('actual-recovery-readiness.json',{'status':'PASS_ALL_GATES_BEFORE_AUTHORIZED_RELEASE','at':datetime.now(UTC).isoformat(),'forecast':forecast,'backup_sha256':proof['cloud']['sha256'],'authorization_sha256':hash_file(DEP/'authorization.json'),'backed_up':1315,'planned':185,'next_execution':NEXT,'new_freeze':False,'same_frozen_source':True})
    cmd(['systemctl','start','fyp-phase8-watchdog.service'])
    verify_host_timer(ROOT)
    assert closed()==rows
    # Human-reviewed failure recovery only. Ordinary CLI resume still refuses this pause.
    Journal(ROOT).event('HUMAN_REVIEWED_CREDENTIAL_RECOVERY_RELEASE',authorization_sha256=hash_file(DEP/'authorization.json'),readiness_sha256=hash_file(DEP/'actual-recovery-readiness.json'),preserved_pause_sha256=PAUSE,next_execution=NEXT)
    target=ROOT/'retained-protocol1315-pause.json'
    assert not target.exists() and hash_file(ROOT/'pause.json')==PAUSE
    (ROOT/'pause.json').rename(target)
    assert hash_file(target)==PAUSE
    record('released.json',{'status':'AUTHORIZED_PAUSE_PRESERVED_SERVICES_NOT_YET_ADMITTED','at':datetime.now(UTC).isoformat(),'retained_pause':str(target),'pause_sha256':PAUSE,'next_execution':NEXT})
    cmd(['systemctl','start','fyp-phase8-campaign.service'])
    record('service-started.json',{'status':'STANDALONE_SERVICES_STARTED_VERIFY_ACTUAL_ADMISSION_SEPARATELY','at':datetime.now(UTC).isoformat(),'state':cmd(['systemctl','show',*UNITS,'--property=Id,MainPID,ActiveState,SubState,Result']),'stop_at':'2026-10-26T12:00:00Z'})

def main():
    try:{'prepare':prepare,'backup':backup,'release':release}[sys.argv[1]]()
    except BaseException as error:
        # Keep the original pause or create a durable new one. A failed recovery cannot admit.
        import traceback
        record('failure-'+str(time.time_ns())+'.json',{'type':type(error).__name__,'detail':str(error),'traceback':traceback.format_exc(),'failed_action':sys.argv[1]})
        Journal(ROOT).pause('CREDENTIAL_RECOVERY_FAILED')
        subprocess.run(['systemctl','stop',*UNITS],timeout=60,check=False)
        subprocess.run(['shutdown','-h','+1','Authorized bounded credential-recovery failed; retain evidence/root'],timeout=10,check=False)
        raise

if __name__=='__main__':main()
