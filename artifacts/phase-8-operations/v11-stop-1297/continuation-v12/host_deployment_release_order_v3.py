"""Reviewed external retained-host actions. No driver calls except final service start."""
from __future__ import annotations

import base64,csv,hashlib,hmac,importlib.metadata,json,os,shutil,socket,subprocess,sys,tarfile,time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC,datetime,timedelta
from pathlib import Path

OLD=Path('/opt/fyp-phase8-continuation-v11')
SOURCE=Path('/opt/fyp-phase8-continuation-v12')
ROOT=Path('/var/lib/p8-continuation-v9/run')
DEP=Path('/var/lib/p8-continuation-v12/deployment')
R='artifacts/phase-8-runner-amendment/v4-complete/'
UNITS=('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')
PAUSE='7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8'
NEXT='01a11705-11f4-7c05-9897-af35348a8028'
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()

def read(p):return json.loads(Path(p).read_bytes())
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(name,value):
    with (DEP/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,default=str);f.flush();os.fsync(f.fileno())
def cmd(args,seconds=20):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=seconds).stdout
def inactive():
    assert all(cmd(['systemctl','show',u,'--property=MainPID','--value']).strip()=='0' for u in UNITS),'OWNED_UNITS_MUST_BE_QUIESCED'
def modules():
    sys.path.insert(0,str(SOURCE/R));sys.path.insert(1,str(SOURCE))
def payload():return read(DEP/'external-input-release-order-v3.json')
def closed_rows():
    from closed145 import snapshot
    rows,notices=snapshot(ROOT/'campaign.sqlite3')
    assert len(rows)==1500 and all(r['state']=='BACKED_UP' for r in rows[:1297]) and all(r['state']=='PLANNED' and not any(r[k] for k in ('deadline','backup_hash','error')) for r in rows[1297:])
    assert rows[1297]['execution_id']==NEXT and rows[1297]['arm']=='B3' and rows[1297]['attempt']==1
    assert not (ROOT/'slots/1298').exists() and digest(ROOT/'pause.json')==PAUSE
    return rows,notices
def forecast(policy,sample,cloudbytes,*,prep=0):
    at=datetime.now(UTC);finish=at+timedelta(hours=203*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24)
    extra=payload()['external']['cost']['extra_root_reserve']
    cloud_projection=cloudbytes+203*68*1024**2+1024**3+300*1024**2
    local_projection=sample['backup_bytes']+203*68*1024**2+1024**3+prep
    physical=203*68*1024**2+1024**3+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3+prep
    v={'at':at.isoformat(),'completion':finish.isoformat(),'uncertainty_completion':uncertain.isoformat(),'uncertainty_plus_margin_usd':policy.committed_cost(uncertain+timedelta(minutes=30))+extra,'full_deadline_usd':policy.committed_cost(policy.stop_at)+extra,'extra_root_reserve_usd':extra,'cloud_all_versions_bytes':cloudbytes,'cloud_projection_bytes':cloud_projection,'local_projection_bytes':local_projection,'required_free_bytes':physical,'future_archive_allowance_bytes':71303168,'preparation_bound_bytes':prep,'stop_at':policy.stop_at.isoformat()}
    assert uncertain<policy.stop_at-timedelta(minutes=30) and v['uncertainty_plus_margin_usd']<76 and v['full_deadline_usd']<77,'TIME_COST_FEASIBILITY_STOP'
    assert max(cloud_projection,local_projection)<80*1024**3 and sample['system_free_bytes']>=physical,'FULL_CAPACITY_FEASIBILITY_STOP'
    return v

def prepare():
    p=payload();assert datetime.fromisoformat(p['external']['expires_at'])>datetime.now(UTC)
    sys.path.insert(0,str(OLD/R));sys.path.insert(1,str(OLD))
    from closed145 import snapshot
    from handover import ContinuationAuthority
    before=cmd(['systemctl','show',*UNITS,'--property=Id,MainPID,ActiveState,SubState,ExecStart,Result'])
    record('owned-unit-state-before-quiescence.json',{'state':before})
    for u in UNITS:
        text=Path('/etc/systemd/system',u).read_text()
        assert str(OLD)+'/' in text and '--root '+str(ROOT) in text,'OWNED_UNIT_SOURCE_DRIFT'
    cmd(['systemctl','stop',*UNITS]);inactive();rows,_=closed_rows()
    parent=ContinuationAuthority(ROOT,read(ROOT/'run.json'));parent.verify()
    assert read(ROOT/'run.json')['source']==str(OLD)
    parent_inv=read(OLD/R/'candidate-inventory.json');assert parent_inv['package_hash']=='e89ca0fbb9c9e7333a18af23014d0d00d4ffbc6dbe1298f0546620523626e348'
    for name,h in parent_inv['files'].items():assert digest(OLD/name)==h,'PARENT_SOURCE_DRIFT:'+name
    owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
    assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
    assert digest(owner/'continuation-v11-receipts/CONTINUATION_FREEZE.json')==p['freeze_manifest']['parent_freeze_file_sha256']
    assert hmac.compare_digest(p['freeze_attestation']['signature'],hmac.new(key,canon(p['freeze_manifest']),'sha256').hexdigest())
    measured=int(cmd(['du','-sb',str(OLD)]).split()[0]);assert measured<2*1024**3,'SOURCE_CLONE_BOUND_STOP'
    assert shutil.disk_usage(ROOT).free>=p['external']['cost']['required_free_before_clone_and_preparation']
    assert digest(Path('/etc/needrestart/conf.d/99-fyp-phase8-defer-restarts.conf'))=='a2fa11ad5a52dce6d32ce8731bf1bc8bea6eee6d76872a55e02bb01cda4cbe73'
    import boto3
    from botocore.config import Config
    s3=boto3.client('s3',region_name='ap-southeast-2',config=Config(connect_timeout=5,read_timeout=15,retries={'total_max_attempts':1}))
    obj=p['delta'];response=s3.get_object(Bucket=obj['bucket'],Key=obj['key'],VersionId=obj['version_id'])
    assert response['VersionId']==obj['version_id'] and response['ContentLength']==obj['bytes']
    path=DEP/'delta.tar.gz';deadline=time.monotonic()+45
    try:
        with path.open('xb') as f:
            for block in response['Body'].iter_chunks(65536):
                assert time.monotonic()<deadline and f.tell()+len(block)<=obj['bytes'];f.write(block)
    finally:response['Body'].close()
    assert path.stat().st_size==obj['bytes'] and digest(path)==obj['sha256']
    assert not SOURCE.exists(),'SOURCE_EXISTS_RECONCILE_NO_REBOOTSTRAP'
    cmd(['cp','-a','--reflink=auto',str(OLD),str(SOURCE)],120)
    with tarfile.open(path) as tf:
        seen=set()
        for item in tf:
            name=Path(item.name)
            assert item.isfile() and not name.is_absolute() and '..' not in name.parts and item.name.startswith(R) and item.name not in seen and item.size<2*1024**2
            seen.add(item.name)
            with (SOURCE/name).open('wb') as f:f.write(tf.extractfile(item).read())
    inv=read(SOURCE/R/'candidate-inventory.json');assert inv['package_hash']==p['package']['package_hash']==hashlib.sha256(canon(inv['files'])).hexdigest()
    assert digest(SOURCE/R/'candidate-inventory.json')==p['freeze_manifest']['source_inventory_sha256']
    for name,h in inv['files'].items():assert digest(SOURCE/name)==h,'NEW_SOURCE_DRIFT:'+name
    assert {x.relative_to(SOURCE).as_posix() for x in (SOURCE/R).glob('*.py')}=={n for n in inv['files'] if n.startswith(R) and n.endswith('.py')}
    baseline=read('/var/lib/p8-combined-v4/deployment/host-health-readiness.json')
    assert sys.version==baseline['python'] and sys.version_info[:3]==(3,12,13)
    environments={}
    for label,folder in [('application','.venv'),('analysis','.venv-analysis'),('transport','.venv-transport')]:
        site=SOURCE/folder/'lib/python3.12/site-packages';packages={};count=0
        for dist in importlib.metadata.distributions(path=[str(site)]):
            packages[dist.metadata['Name'].lower().replace('_','-')]=dist.version
            for row in csv.reader((dist.read_text('RECORD') or '').splitlines()):
                if not row or not row[1]:continue
                algorithm,expected=row[1].split('=',1);target=Path(dist.locate_file(row[0]))
                assert algorithm=='sha256' and target.is_file()
                assert base64.urlsafe_b64encode(bytes.fromhex(digest(target))).decode().rstrip('=')==expected
                count+=1
        assert packages==baseline['dependency_environments'][label]['packages']
        environments[label]={'packages':packages,'record_files':count}
    for name in ('CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json'):
        raw=base64.b64decode(p['authority'][name]);assert hashlib.sha256(raw).hexdigest()==p['freeze_manifest']['files'][name]
        value=json.loads(raw);body={k:v for k,v in value.items() if k!='signature'}
        assert hmac.compare_digest(value['signature'],hmac.new(key,canon(body),'sha256').hexdigest())
    receipts=owner/'continuation-v12-receipts';receipts.mkdir(mode=0o700,exist_ok=False)
    for name in ('CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json'):
        with (receipts/name).open('xb') as f:f.write(base64.b64decode(p['authority'][name]))
        (receipts/name).chmod(0o600)
    qualification=cmd([str(SOURCE/'.venv/bin/python'),'-B',str(SOURCE/R/'check_policy_boundary_v12.py'),str(SOURCE)],45)
    q=json.loads(qualification.splitlines()[-1]);assert q['status']=='PASS' and q['checks']==12 and q['research_executions']==0
    assert snapshot(ROOT/'campaign.sqlite3')[0]==rows and digest(ROOT/'pause.json')==PAUSE
    record('source-and-runtime-verified.json',{'status':'PASS','package_hash':inv['package_hash'],'python':sys.version,'python_sha256':digest(Path(sys.executable).resolve()),'environments':environments,'source_members':len(inv['files']),'source_clone_bytes':measured,'linux_controls':q,'linux_control_output':qualification,'os_zlib':cmd(['dpkg-query','-W','-f=${Version}','zlib1g']),'root_pause_unchanged':True,'main_admissions':0})
    print('PASS_VERIFIED_SOURCE_DEPENDENCIES_AND_12_LINUX_CONTROLS_NO_ADMISSION')

def metadata():
    modules();inactive();rows,_=closed_rows();assert read(DEP/'source-and-runtime-verified.json')['status']=='PASS'
    from closed1297 import MASTER,REL,prepare,verify
    from controls import Journal,write_new
    from handover import bind_host_segment,ContinuationAuthority
    from operational_limits import LIMITS_SHA256
    from runner import campaign_unit,watchdog_unit,unit_text,verify_clock
    run=read(ROOT/'run.json');assert run['source']==str(OLD)
    archive=ROOT.parent/'backup/r1297m/t/e.tar.gz';assert archive.stat().st_size==52843821 and digest(archive)==MASTER
    baseline=prepare(ROOT,archive)
    history=ROOT/'restart-history/v12-prior-controls';history.mkdir(mode=0o700,exist_ok=False)
    parent_authority=history/'parent-v11-authority';parent_authority.mkdir()
    for name in ('CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json','CONTINUATION_LAUNCH.json'):
        shutil.copyfile(Path('/var/lib/fyp-owner/continuation-v11-receipts')/name,parent_authority/name)
    assert digest(parent_authority/'CONTINUATION_FREEZE.json')==payload()['freeze_manifest']['parent_freeze_file_sha256']
    for name in ('run.json','binding-seal.json','continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json','host-clock.json','pause.json'):
        shutil.copyfile(ROOT/name,history/name)
    for name in ('continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json'):(ROOT/name).rename(history/('active-placement-'+name))
    new={**run,'source':str(SOURCE),'manifest':str(SOURCE/'artifacts/phase-8-review-freeze/v2/review-inventory.json'),'operational_limits_sha256':LIMITS_SHA256,'continuation':{**run['continuation'],'manifest':R+'candidate-inventory.json','receipts':'/var/lib/fyp-owner/continuation-v12-receipts','closed1297_sha256':digest(ROOT/REL)}}
    write_new(ROOT/'run.v12-new.json',new);(ROOT/'run.v12-new.json').replace(ROOT/'run.json')
    seal={'run':digest(ROOT/'run.json'),'bindings':digest(ROOT/'bindings.json')}
    write_new(ROOT/'binding-seal.v12-new.json',seal);(ROOT/'binding-seal.v12-new.json').replace(ROOT/'binding-seal.json')
    journal=Journal(ROOT);journal.event('BINDINGS_SEALED',**seal)
    journal.event('V12_AUTHORIZED_CLOSED1297_BINDING',parent_source=str(OLD),source=str(SOURCE),closed1297_sha256=digest(ROOT/REL),no_replay=True)
    a=ContinuationAuthority(ROOT,new);a.verify(prelaunch=True);verify(ROOT,closed=True)
    bind_host_segment(ROOT);verify_clock(ROOT,a.policy)
    service,timer=unit_text(ROOT,a.policy)
    units={'fyp-phase8-campaign.service':campaign_unit(ROOT),'fyp-phase8-watchdog.service':watchdog_unit(ROOT),'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer}
    bootstrap=Path('/etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer')
    text=bootstrap.read_text();assert '2026-10-26 00:00:00 UTC' in text
    units[bootstrap.name]=text.replace('2026-10-26 00:00:00 UTC','2026-10-26 12:00:00 UTC')
    for name,text in units.items():
        shutil.copyfile(Path('/etc/systemd/system',name),history/name)
        Path('/etc/systemd/system',name).write_text(text)
    cutoff=a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds)
    script=DEP/'admission-cutoff.py'
    code="import sys\nfrom pathlib import Path\nfrom datetime import datetime\nsys.path.insert(0,"+repr(str(SOURCE/R))+")\nfrom controls import Journal,read,utc\nroot=Path("+repr(str(ROOT))+")\nassert utc()>=datetime.fromisoformat("+repr(cutoff.isoformat())+")\nassert read(root/'run.json')['source']=="+repr(str(SOURCE))+"\nj=Journal(root);j.pause('V12_ABSOLUTE_ADMISSION_CUTOFF');j.event('V12_CUTOFF_ACTIVE_WINDOW_PRESERVED',admission_guard_usd=76)\n"
    with script.open('x') as f:f.write(code)
    extras={'fyp-v12-admission-cutoff.service':'[Unit]\nDescription=Owned v12 final admission fence\n[Service]\nType=oneshot\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nExecStart='+str(SOURCE/'.venv/bin/python')+' '+str(script)+'\n','fyp-v12-admission-cutoff.timer':'[Unit]\nDescription=Owned v12 cutoff; active window preserved\n[Timer]\nOnCalendar='+cutoff.strftime('%Y-%m-%d %H:%M:%S UTC')+'\nPersistent=true\nAccuracySec=1s\nUnit=fyp-v12-admission-cutoff.service\n[Install]\nWantedBy=timers.target\n'}
    for name,text in extras.items():
        with Path('/etc/systemd/system',name).open('x') as f:f.write(text)
    cmd(['systemctl','daemon-reload']);cmd(['systemctl','restart','fyp-phase8-hardstop.timer',bootstrap.name])
    cmd(['systemctl','enable','--now','fyp-phase8-hardstop.timer',bootstrap.name,'fyp-v12-admission-cutoff.timer'])
    for name in ('fyp-phase8-hardstop.timer',bootstrap.name,'fyp-v12-admission-cutoff.timer'):cmd(['systemctl','is-active','--quiet',name])
    old_fence=Path('/etc/systemd/system/fyp-v11-admission-cutoff.timer');assert '2026-10-25 22:47:50 UTC' in old_fence.read_text()
    for name in ('fyp-v11-admission-cutoff.timer','fyp-v11-admission-cutoff.service'):shutil.copyfile(Path('/etc/systemd/system',name),history/name)
    cmd(['systemctl','disable','--now',old_fence.name]);assert cmd(['systemctl','show',old_fence.name,'--property=ActiveState','--value']).strip()=='inactive'
    assert snapshot_rows()==rows and digest(ROOT/'pause.json')==PAUSE
    record('metadata-and-timers.json',{'status':'PASS','closed1297_sha256':digest(ROOT/REL),'backed_up':1297,'planned':203,'next_execution_id':NEXT,'host_clock_sha256':digest(ROOT/'host-clock.json'),'original_clock_anchor':a.policy.host_started_at.isoformat(),'stop_at':a.policy.stop_at.isoformat(),'cutoff':cutoff.isoformat(),'unit_hashes':{name:digest(Path('/etc/systemd/system',name)) for name in {**units,**extras}},'fence_script_sha256':digest(script),'timer_readback':cmd(['systemctl','show','fyp-phase8-hardstop.timer',bootstrap.name,'fyp-v12-admission-cutoff.timer','--property=Id,ActiveState,NextElapseUSecRealtime']),'main_admissions':0})
    print('PASS_EXACT1297_METADATA_NEW_BOOT_ANCHOR_TIMERS_NO_ADMISSION')

def snapshot_rows():
    from closed145 import snapshot
    return snapshot(ROOT/'campaign.sqlite3')[0]

def live():
    modules();inactive();rows,_=closed_rows()
    from controls import guard
    from closed1297 import verify
    from handover import ContinuationAuthority
    from storage import S3Cloud,ObjectProof
    from runner import meter
    from research.execution_linux_v1.runner import IMAGE_DIGESTS
    a=ContinuationAuthority(ROOT,read(ROOT/'run.json'));a.verify(prelaunch=True);verify(ROOT,closed=True)
    assert read(DEP/'source-and-runtime-verified.json')['linux_controls']['checks']==12
    assert not cmd(['docker','ps','--format','{{.Names}}']).strip()
    for port in (16432,16433,19100,19101,19102,19110):
        with socket.socket() as s:s.bind(('127.0.0.1',port))
    for tag,expected in IMAGE_DIGESTS.items():assert expected in json.loads(cmd(['docker','image','inspect',tag]))[0]['RepoDigests']
    cloud=S3Cloud(a.policy.cloud_bucket,'exports/phase8/'+a.policy.run_id+'/');proofs=[]
    for row in rows[:1297]:
        p=ROOT/'backups'/(row['execution_id']+'.json');assert digest(p)==row['backup_hash'];v=read(p)
        assert v['execution_id']==row['execution_id'] and v['sha256']==v['cloud']['sha256'];proofs.append(v)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks=[pool.submit(cloud.verify,ObjectProof.model_validate(p['cloud'])) for p in proofs]
        for n,p in enumerate(proofs,1):
            path=Path(p['local'])
            if not path.exists() and n<=38:path=Path('/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives')/f'{n:04d}.tar.gz'
            assert digest(path)==p['sha256'],'ORIGINAL_ARCHIVE_DRIFT:'+str(n)
            tasks[n-1].result()
            if n%100==0:print('VERIFIED originals and pinned versions '+str(n)+'/1297',flush=True)
    sample=meter(ROOT);cloudbytes=cloud.inventory();guard(a.policy,sample,datetime.now(UTC),cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    f=forecast(a.policy,sample,cloudbytes,prep=4*1024**3)
    assert rows==snapshot_rows() and digest(ROOT/'pause.json')==PAUSE
    record('live-checks.json',{'status':'PASS','all1297_original_archives_and_pinned_versions_verified':True,'rows_sha256':hashlib.sha256(canon(rows)).hexdigest(),'resource_sample':sample,'forecast':f,'source_runtime_sha256':digest(DEP/'source-and-runtime-verified.json'),'metadata_timers_sha256':digest(DEP/'metadata-and-timers.json'),'preparation_copy_bound_bytes':4*1024**3,'main_admissions':0})
    print(json.dumps({'status':'PASS_LIVE_CLOSED1297','forecast':f,'resource_sample':sample}))

def backup(phase):
    modules();inactive();closed_rows()
    from prelaunch_backup import run
    from storage import S3Cloud
    config=read(ROOT/'cloud.json')
    run(ROOT,ROOT.parent/'backup',phase,S3Cloud(config['bucket'],config['prefix']))
    proof=read(ROOT/(phase+'-backup-proof.json'))
    record(phase+'-stage.json',{'status':'PASS_INDEPENDENT_READBACK','proof':proof,'proof_sha256':digest(ROOT/(phase+'-backup-proof.json'))})
    print(json.dumps({'status':'PASS_INDEPENDENT_READBACK','phase':phase,'proof':proof}))

def readiness():
    modules();inactive();rows,_=closed_rows()
    from controls import guard,Journal,write_new
    from closed1297 import verify
    from handover import ContinuationAuthority,CHECKS
    from prelaunch_backup import verify_proof
    from storage import S3Cloud
    from runner import meter,verify_clock,unit_text
    a=ContinuationAuthority(ROOT,read(ROOT/'run.json'));a.verify(prelaunch=True);verify(ROOT,closed=True)
    live=read(DEP/'live-checks.json');assert live['status']=='PASS' and live['all1297_original_archives_and_pinned_versions_verified']
    assert datetime.fromisoformat(payload()['external']['expires_at'])>datetime.now(UTC)
    cloud=S3Cloud(a.policy.cloud_bucket,'exports/phase8/'+a.policy.run_id+'/');verify_proof(ROOT,'prelaunch',cloud)
    sample=meter(ROOT);cloudbytes=cloud.inventory();guard(a.policy,sample,datetime.now(UTC),cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    growth=sample['backup_bytes']-live['resource_sample']['backup_bytes'];complete_bound=growth+16*1024**2
    assert growth>0 and growth+complete_bound<=live['preparation_copy_bound_bytes'],'MEASURED_PREPARATION_COPY_BOUND_STOP'
    f=forecast(a.policy,sample,cloudbytes,prep=complete_bound)
    for name in ('fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v12-admission-cutoff.timer'):cmd(['systemctl','is-active','--quiet',name])
    _,timer=unit_text(ROOT,a.policy);assert Path('/etc/systemd/system/fyp-phase8-hardstop.timer').read_text()==timer
    meta=read(DEP/'metadata-and-timers.json')
    for name,h in meta['unit_hashes'].items():assert digest(Path('/etc/systemd/system',name))==h
    owner=Path('/var/lib/fyp-owner');assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
    verify_clock(ROOT,a.policy)
    policyhash=hashlib.sha256(canon(a.policy.model_dump(mode='json'))).hexdigest()
    ready={'version':'phase85-continuation-v12','status':'PASS','at_utc':datetime.now(UTC).isoformat(),'run_id':a.policy.run_id,'instance_id':'i-057344e5372faf62f','policy_sha256':policyhash,'operational_limits_sha256':read(ROOT/'run.json')['operational_limits_sha256'],'handover_sha256':digest(ROOT/'handover.json'),'boot_anchor_sha256':digest(ROOT/'host-clock.json'),'checks':dict.fromkeys(CHECKS,True),'backed_up':1297,'planned':203,'next_sequence':1298,'next_execution_id':NEXT,'source_runtime_sha256':digest(DEP/'source-and-runtime-verified.json'),'live_sha256':digest(DEP/'live-checks.json'),'metadata_timers_sha256':digest(DEP/'metadata-and-timers.json'),'prelaunch':read(ROOT/'prelaunch-backup-proof.json'),'independent_guards':payload()['external']['guards'],'resource_sample':sample,'forecast':f,'prelaunch_growth_bytes':growth,'complete_backup_bound_bytes':complete_bound,'driver_calls':0}
    write_new(ROOT/'continuation-readiness.json',ready);Journal(ROOT).event('V12_GENUINE_READINESS_VERIFIED',hash=digest(ROOT/'continuation-readiness.json'),main_admitted=False)
    result={'status':'PASS_GENUINE_READINESS','readiness_sha256':digest(ROOT/'continuation-readiness.json'),'policy_sha256':policyhash,'instance_id':ready['instance_id'],'checks':ready['checks'],'main_admitted':False,'forecast':f}
    record('readiness-result.json',result);print(json.dumps(result))

def release():
    modules();inactive();rows,_=closed_rows()
    from controls import guard
    from runner import verify_run,meter,verify_clock,verify_host_timer,campaign_unit,watchdog_unit
    from handover import release_reviewed_boundary
    from storage import S3Cloud
    from prelaunch_backup import verify_proof
    assert read(DEP/'complete-stage.json')['status']=='PASS_INDEPENDENT_READBACK'
    a=verify_run(ROOT);cloud=S3Cloud(a.policy.cloud_bucket,'exports/phase8/'+a.policy.run_id+'/')
    for phase in ('prelaunch','complete'):verify_proof(ROOT,phase,cloud)
    sample=meter(ROOT);cloudbytes=cloud.inventory();guard(a.policy,sample,datetime.now(UTC),cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
    f=forecast(a.policy,sample,cloudbytes)
    live=read(DEP/'live-checks.json');assert sample['backup_bytes']-live['resource_sample']['backup_bytes']<=live['preparation_copy_bound_bytes']
    for name,text in zip(UNITS,(campaign_unit(ROOT),watchdog_unit(ROOT))):assert Path('/etc/systemd/system',name).read_text()==text
    assert digest(Path('/etc/needrestart/conf.d/99-fyp-phase8-defer-restarts.conf'))=='a2fa11ad5a52dce6d32ce8731bf1bc8bea6eee6d76872a55e02bb01cda4cbe73'
    verify_clock(ROOT,a.policy)
    cmd(['systemctl','start','fyp-phase8-watchdog.service'])
    verify_host_timer(ROOT)
    release_reviewed_boundary(ROOT)
    record('actual-release.json',{'status':'PASS_REVIEWED_RELEASE_NOT_YET_ADMISSION','at':datetime.now(UTC).isoformat(),'next_sequence':1298,'next_execution_id':NEXT,'old_pause_preserved':digest(ROOT/'retained-protocol1297-pause-v12.json'),'forecast':f})
    cmd(['systemctl','start','fyp-phase8-campaign.service'])
    print('PASS_STANDALONE_SERVICE_STARTED_VERIFY_ACTUAL_ADMISSION_SEPARATELY')

def main():
    assert digest(Path(__file__))==payload()['host_controller_sha256'],'EXTERNAL_CONTROLLER_DRIFT'
    action=sys.argv[1]
    if action in ('prelaunch','complete'):backup(action)
    else:{'prepare':prepare,'metadata':metadata,'live':live,'readiness':readiness,'release':release}[action]()

if __name__=='__main__':main()
