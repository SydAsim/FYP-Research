"""Bounded external all145 handover; measure before adopting, never run a driver."""
from __future__ import annotations
import fcntl
import json
import os
import signal
import sys
import tarfile
import time
from dataclasses import asdict
from datetime import UTC,datetime,timedelta
from pathlib import Path
from typing import Any
from core import Identity,archive_record,atomic_exact,choose_exact,committed_local_record,digest,file_hash,json_object,publish_exact

SOURCE=Path('/opt/fyp-phase8-continuation-v10')
RUNTIME=SOURCE/'artifacts/phase-8-runner-amendment/v4-complete'
ROOT=Path('/var/lib/p8-continuation-v9/run')
STAGE=Path('/var/lib/p8-continuation-v10/deployment/export-layout-v1')
CAP=2*1024**3
RESERVE=16*1024**2
CLOUD_CLIENT: Any = None  # Isolated SDK boundary, reused for all bounded GETs.
sys.path.insert(0,str(RUNTIME))

def stamp() -> str:return datetime.now(UTC).isoformat()
def read(path: Path) -> dict[str,Any]:return json_object(path.read_bytes())
def encode(value: object) -> bytes:return json.dumps(value,sort_keys=True,indent=2).encode()
def save(name: str,value: object) -> None:atomic_exact(STAGE/name,encode(value),maximum_tree_bytes=CAP-RESERVE,budget_root=STAGE)

def budget(state: dict[str,Any]) -> None:
    if datetime.now(UTC)>=datetime.fromisoformat(state['deadline']):raise TimeoutError('ORIGINAL_HANDOVER_DEADLINE_EXHAUSTED')
    if sum(p.stat().st_size for p in STAGE.rglob('*') if p.is_file())>=CAP-RESERVE:raise ValueError('HANDOVER_TOTAL_STAGING_STOP')
    if __import__('shutil').disk_usage('/').free<21*1024**3:raise ValueError('HANDOVER_DISK_RESERVATION_STOP')

def cloud_archive(proof: dict[str,Any],state: dict[str,Any]) -> Path:
    """One pinned GET only when required archive is absent locally. No retry loop."""
    import boto3
    from botocore.config import Config
    budget(state)
    attempts=list((STAGE/'cloud-attempts').glob('*.json')) if (STAGE/'cloud-attempts').exists() else []
    if len(attempts)>=4:raise ValueError('CLOUD_GET_BUDGET_EXHAUSTED')
    if proof['bytes']>128*1024**2 or sum(read(p)['bytes'] for p in attempts)+proof['bytes']>512*1024**2:raise ValueError('CLOUD_BYTE_BUDGET_EXHAUSTED')
    target=STAGE/'cloud'/f"{proof['sha256']}.tar.gz"
    if target.exists():
        if target.stat().st_size==proof['bytes'] and file_hash(target)==proof['sha256']:return target
        raise ValueError('PARTIAL_CLOUD_ARCHIVE_RETAIN_NO_RETRY')
    if proof['bucket']!='fyp-p82-20261005-018da1d6-803656589923' or not proof['key'].startswith('exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/') or not proof['version_id']:raise ValueError('UNTRUSTED_CLOUD_BINDING')
    save('cloud-attempts/'+proof['sha256']+'.json',{'at':stamp(),'bytes':proof['bytes'],'proof':proof,'automatic_retries':0,'process_get_seconds':180})
    global CLOUD_CLIENT
    if CLOUD_CLIENT is None:
        CLOUD_CLIENT=boto3.client('s3',region_name='ap-southeast-2',config=Config(connect_timeout=5,read_timeout=25,retries={'total_max_attempts':1,'mode':'standard'}))
    s3=CLOUD_CLIENT
    deadline=time.monotonic()+180
    response=s3.get_object(Bucket=proof['bucket'],Key=proof['key'],VersionId=proof['version_id'])
    if response.get('VersionId')!=proof['version_id'] or response['ContentLength']!=proof['bytes']:
        response['Body'].close();raise ValueError('PINNED_GET_IDENTITY_DRIFT')
    target.parent.mkdir(exist_ok=True)
    try:
        with target.open('xb') as f:
            for block in response['Body'].iter_chunks(1024**2):
                budget(state)
                if time.monotonic()>=deadline:raise TimeoutError('PINNED_GET_DEADLINE_RETAIN_PARTIAL')
                if f.tell()+len(block)>proof['bytes']:raise ValueError('PINNED_GET_SIZE_BOUND')
                f.write(block)
            f.flush();os.fsync(f.fileno())
    finally:response['Body'].close()
    if target.stat().st_size!=proof['bytes'] or file_hash(target)!=proof['sha256']:raise ValueError('PINNED_GET_HASH_DRIFT')
    return target

def archive_for(sequence: int,receipt: dict[str,Any],state: dict[str,Any],*,allow_get: bool=True) -> Path | None:
    primary=Path(receipt['local'])
    if primary.is_file():return primary
    candidates=[Path('/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives')/f'{sequence:04d}.tar.gz']
    # Exact retained owned backup directories only; no transport switching.
    for base in ('/var/lib/p8-continuation-v9/backup','/var/lib/p8-continuation-v7/backup','/var/lib/p8-combined-v4/backup'):
        directory=Path(base)/f'{sequence:04d}'
        if directory.is_dir():candidates.extend(sorted(directory.glob('*.tar.gz')))
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size==receipt['cloud']['bytes'] and file_hash(candidate)==receipt['sha256']:return candidate
    return cloud_archive(receipt['cloud'],state) if allow_get else None

def archives_size(folder: Path) -> int:return sum(p.stat().st_size for p in folder.rglob('*.tar.gz'))

def measure(provenance: dict[str,Any],state: dict[str,Any]) -> dict[str,Any]:
    from controls import Journal
    from storage import final_backup
    # Use real frozen copier with existing genuine v9 readiness. These archives
    # are labelled measurements, not new PRELAUNCH/COMPLETE or authorization.
    budget(state)
    if (STAGE/'measurement.json').exists():return read(STAGE/'measurement.json')
    config=read(ROOT/'run.json')
    dirs=[ROOT/'restart-history',ROOT/'backups',ROOT/'postboot-old-operational-evidence',Path(config['receipts']),Path(config['continuation']['receipts'])]
    names=('campaign.sqlite3','campaign.sqlite3-wal','run.json','bindings.json','binding-seal.json','cloud.json','handover.json','saved-identities.json','host-clock.json','restart-boundary.json','continuation-readiness.json','historical-evidence.tar.gz','pause.json','retained-import-pause.json','reuse-preparation.json','prelaunch-backup-proof.json')
    raw_bound=sum(p.stat().st_size for d in dirs if d.exists() for p in d.rglob('*') if p.is_file())+sum((ROOT/n).stat().st_size for n in names if (ROOT/n).is_file())
    raw_bound+=32*1024**2  # SQLite snapshot, tar headers and manifest closure.
    used=sum(p.stat().st_size for p in STAGE.rglob('*') if p.is_file())
    # One copied raw tree and two worst-case compressed streams, reserved before
    # invoking the unchanged copier; no zero-cost link/compression assumption.
    if used+3*raw_bound+len(encode(provenance))*3>=CAP-RESERVE:raise ValueError('BOUNDED_MEASUREMENT_RESERVATION_STOP')
    dest=STAGE/'measure';dest.mkdir(exist_ok=True)
    baseline=final_backup(Journal(ROOT),dest,prelaunch=False)
    folder=baseline.with_suffix('').with_suffix('')
    if not folder.is_dir():raise ValueError('FROZEN_MEASUREMENT_FOLDER_MISSING')
    path=folder/'restart-history/export-layout-v1/provenance.json'
    atomic_exact(path,encode(provenance),maximum_tree_bytes=CAP-RESERVE,budget_root=STAGE)
    # Re-seal measurement closure after adding only the future provenance file.
    continuation=read(folder/'continuation-backup.json')
    continuation['files']={p.relative_to(folder).as_posix():file_hash(p) for p in folder.rglob('*') if p.is_file() and p.name not in ('continuation-backup.json','manifest.json')}
    (folder/'continuation-backup.json').write_bytes(encode(continuation))
    manifest=read(folder/'manifest.json');manifest['files']={p.relative_to(folder).as_posix():file_hash(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (folder/'manifest.json').write_bytes(encode(manifest))
    candidate=dest/'with-provenance.measurement.tar.gz'
    with tarfile.open(candidate,'x:gz') as out:out.add(folder,arcname='slot')
    budget(state)
    with tarfile.open(candidate) as tar:
        archive_names=tar.getnames()
    if any(n.startswith('slot/exports/') for n in archive_names):raise ValueError('UNEXPECTED_EXPORT_VIEW_ARCHIVAL_DUPLICATION')
    if 'slot/restart-history/export-layout-v1/provenance.json' not in archive_names:raise ValueError('PROVENANCE_NOT_IN_MEASURED_ARCHIVE')
    baseline_bytes=baseline.stat().st_size;candidate_bytes=candidate.stat().st_size
    full=83218519158.73685+max(0,state['cloud_bytes']-3066593484)+max(0,candidate_bytes-37194083)*1500
    current_backups=archives_size(ROOT.parent/'backup')
    # The accepted whole1500 cloud projection already includes all original
    # archive allowance and current inventory. Add only demonstrated local
    # extra copies, plus the two upcoming independent readback archives, rather
    # than counting every original a second time. Hash every current local gzip.
    groups: dict[str,list[int]]={}
    for p in ROOT.parent.joinpath('backup').rglob('*.tar.gz'):
        groups.setdefault(file_hash(p),[]).append(p.stat().st_size)
    extra_local_copies=sum(sum(sizes[1:]) for sizes in groups.values())
    projected_local=full+extra_local_copies+2*candidate_bytes
    logical_export_bytes=sum(record['export_bytes'] for record in provenance['records'])
    logical_stage_bytes=sum(p.stat().st_size for p in STAGE.rglob('*') if p.is_file())
    unique={}
    for p in STAGE.rglob('*'):
        if p.is_file():
            st=p.stat();unique[(st.st_dev,st.st_ino)]=st.st_blocks*512
    measurement={'kind':'FROZEN_COPIER_MEASUREMENT_NOT_BACKUP_OR_LAUNCH','at':stamp(),
        'baseline_archive':str(baseline),'baseline_sha256':file_hash(baseline),'baseline_bytes':baseline_bytes,
        'candidate_archive':str(candidate),'candidate_sha256':file_hash(candidate),'candidate_bytes':candidate_bytes,
        'positive_compressed_metadata_change_bytes':max(0,candidate_bytes-baseline_bytes),
        'per_slot_master_metadata_increment_bytes':max(0,candidate_bytes-37194083),
        'projection_multiplier':1500,'projected_cloud_bytes':full,'plus_reservation_gib':(full+1073741824)/1024**3,
        'local_backup_bytes_now':current_backups,'projected_local_backup_bound_bytes':projected_local,
        'measured_duplicate_local_archive_bytes':extra_local_copies,'future_readback_archive_reservation_bytes':2*candidate_bytes,
        'projection_local_note':'Preserve whole1500 cloud allowance/current inventory; add measured extra local copies and both upcoming readback archives; no reduction of historical or per-slot allowance',
        'export_view_raw_bytes':logical_export_bytes,'stage_logical_bytes':logical_stage_bytes,
        'stage_unique_allocated_bytes':sum(unique.values()),'export_view_archived_in_master':False,
        'provenance_archived_in_master':True,'archival_inclusion_verified_from_actual_tar':True,
        'disk_free_now':__import__('shutil').disk_usage('/').free,'raw_exports_not_copied_into_restart_history':True}
    measurement['prewrite_raw_bound_bytes']=raw_bound
    # Main copied archive cloud limit and dedicated backup capacity both retained.
    if full+1073741824>=80*1024**3 or projected_local+1073741824>=80*1024**3:
        save('measurement-failed-capacity.json',measurement);raise ValueError('MEASURED_FUTURE_BACKUP_CAP_STOP')
    save('measurement.json',measurement)
    return measurement

def work() -> None:
    from closed145 import check_rows,snapshot,verify_retained_root
    from controls import hash_file
    rows,notices=snapshot(ROOT/'campaign.sqlite3');saved=read(RUNTIME/'closed-145/read-only-ledger.json')['rows'];check_rows(rows,saved)
    refs=read(RUNTIME/'closed-145/backup-reference-index.json')
    if file_hash(ROOT/'pause.json')!=file_hash(RUNTIME/'closed-145/pause.json'):raise ValueError('HISTORICAL_PAUSE_DRIFT')
    frozen120=read(RUNTIME/'closed-120-members.json')
    STAGE.mkdir(mode=0o700,exist_ok=True)
    if (STAGE/'state.json').exists():state=read(STAGE/'state.json')
    else:
        state={'boundary_sha256':file_hash(RUNTIME/'closed-145/read-only-ledger.json'),'started_at':stamp(),
            'deadline':(datetime.now(UTC)+timedelta(seconds=1500)).isoformat(),'original_count':145,
            'cloud_bytes':int(os.environ['HANDOVER_CLOUD_BYTES']),'max_staging_bytes':CAP,'max_gets':4}
        save('state.json',state)
    if state['boundary_sha256']!=file_hash(RUNTIME/'closed-145/read-only-ledger.json'):raise ValueError('RESUME_BOUNDARY_DRIFT')
    budget(state)
    records=[]
    for row in rows[:145]:
        budget(state);sequence=row['sequence'];identity=Identity(sequence,row['execution_id'],row['arm'],row['attempt'],row['fixture_hash'])
        receipt_path=ROOT/'backups'/(identity.execution_id+'.json');receipt=read(receipt_path)
        if file_hash(receipt_path)!=row['backup_hash'] or file_hash(receipt_path)!=refs[identity.execution_id]['receipt_sha256'] or receipt['cloud']!=refs[identity.execution_id]['cloud'] or receipt['execution_id']!=identity.execution_id or receipt['sha256']!=receipt['cloud']['sha256']:raise ValueError('ORIGINAL_RECEIPT_BINDING_DRIFT')
        checkpoint=STAGE/'records'/f'{sequence:04d}.json'
        staged=STAGE/'records'/f'{sequence:04d}.export.json'
        if checkpoint.exists():
            record=read(checkpoint)
            if record['identity']!=asdict(identity) or record['receipt_sha256']!=row['backup_hash'] or not staged.is_file() or file_hash(staged)!=record['export_sha256']:raise ValueError('RESUME_EXPORT_BINDING_DRIFT')
            identity.check(staged.read_bytes());records.append(record);continue
        candidates=[ROOT/'restart-history/exports'/f'{sequence:04d}'/'export.json',ROOT/'exports'/f'{sequence:04d}'/'export.json',ROOT/'slots'/f'{sequence:04d}'/'executions'/identity.execution_id/'export.json']
        if sequence==1:candidates.append(ROOT/'historical/first-slot/executions'/identity.execution_id/'export.json')
        if sequence==2:candidates.append(ROOT/'historical/second-slot/executions'/identity.execution_id/'export.json')
        history_commit=frozen120.get(f'exports/{sequence:04d}/export.json') if sequence<=120 else None
        local=committed_local_record(candidates,history_commit,identity) if history_commit else None
        archive=archive_for(sequence,receipt,state,allow_get=local is None)
        member='executions/'+identity.execution_id+'/export.json'
        if archive is None:
            if local is None or not history_commit:raise ValueError('REQUIRED_RECORD_NOT_VERIFIABLE')
            data,selected=local;committed=history_commit
            binding={'type':'FROZEN_CLOSED120_MEMBER_AND_PINNED_ORIGINAL_RECEIPT','commitment_file_sha256':file_hash(RUNTIME/'closed-120-members.json'),'historical_member':f'exports/{sequence:04d}/export.json','archive_locally_reverified':False}
        else:
            data,committed,member=archive_record(archive,receipt['sha256'],receipt['cloud']['bytes'],identity)
            if history_commit and history_commit!=committed:raise ValueError('FROZEN_HISTORY_EXPORT_COMMITMENT_DRIFT')
            data,selected=choose_exact(data,committed,candidates,identity)
            binding={'type':'PINNED_ARCHIVE_AND_ORIGINAL_MEMBER_MANIFEST','archive_locally_reverified':True}
        atomic_exact(staged,data,maximum_tree_bytes=CAP-RESERVE,budget_root=STAGE)
        record={'identity':asdict(identity),'receipt_sha256':row['backup_hash'],'cloud':receipt['cloud'],
            'archive_local':str(archive) if archive else None,'archive_sha256':receipt['sha256'],'archive_bytes':receipt['cloud']['bytes'],'member_binding':binding,
            'archive_export_member':member,'manifest_committed_export_sha256':committed,'export_sha256':committed,
            'export_bytes':len(data),'selected_existing_record':selected,'raw_status':json_object(data)['status'],
            'target':f'exports/{sequence:04d}/export.json','outcome_bytes_changed':False}
        save('records/'+f'{sequence:04d}.json',record);records.append(record)
        if sequence%25==0:print(json.dumps({'kind':'HANDOVER_PROGRESS_NOT_MAIN','verified_originals':sequence,'required':145}),flush=True)
    provenance={'kind':'EXACT145_EXPORT_LAYOUT_HANDOVER_NOT_OUTCOME_REPLACEMENT','boundary_sha256':state['boundary_sha256'],
        'package_hash':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c','records':records,
        'raw_bytes_unchanged':True,'grades_recomputed':False,'drivers_replayed':False}
    save('provenance.json',provenance)
    measured=measure(provenance,state);budget(state)
    # Adopt only after all145 and measured archival/disk reservations pass.
    if ROOT.stat().st_dev!=STAGE.stat().st_dev:raise ValueError('ATOMIC_PUBLICATION_DIFFERENT_FILESYSTEM')
    for record in records:
        sequence=record['identity']['sequence'];publish_exact(STAGE/'records'/f'{sequence:04d}.export.json',ROOT/record['target'],record['export_sha256'])
    path=ROOT/'restart-history/export-layout-v1/provenance.json'
    atomic_exact(path,encode(provenance),maximum_tree_bytes=50*1024**3,budget_root=ROOT)
    checked=verify_retained_root(ROOT)
    if checked['backed_up']!=145 or checked['planned']!=1355:raise ValueError('CLOSED_BOUNDARY_CHANGED')
    save('adoption.json',{'status':'PASS_ALL145_EXACT_LAYOUT_AND_FROZEN_VALIDATOR','at':stamp(),'backed_up':145,'planned':1355,
        'original_pause_sha256':file_hash(ROOT/'pause.json'),'provenance_sha256':file_hash(path),'measurement':measured,
        'cloud_gets':len(list((STAGE/'cloud-attempts').glob('*.json'))) if (STAGE/'cloud-attempts').exists() else 0,
        'root_working_logical_bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),'driver_calls':0})
    print(json.dumps({'status':'PASS_ALL145_EXACT_LAYOUT_AND_FROZEN_VALIDATOR','provenance_sha256':file_hash(path),
        'projected_storage_with_reservation_gib':measured['plus_reservation_gib'],'baseline_metadata_bytes':measured['baseline_bytes'],
        'candidate_metadata_bytes':measured['candidate_bytes'],'all145_verified':True,'driver_calls':0}),flush=True)

def stop(_signal: int,_frame: object) -> None:raise TimeoutError('HANDOVER_PROCESS_DEADLINE')

def main() -> int:
    STAGE.mkdir(mode=0o700,exist_ok=True)
    signal.signal(signal.SIGALRM,stop);signal.alarm(1500)
    try:
        with (STAGE/'handover.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);work()
        return 0
    except Exception as exc:
        # Durable evidence, exact reason, no silent repair/retry or admissions.
        failure={'status':'FAILED_HANDOVER_NO_ADMISSION','at':stamp(),'type':type(exc).__name__,'detail':str(exc)}
        with (STAGE/f'failure-{time.time_ns()}.json').open('x') as f:json.dump(failure,f,indent=2)
        print(json.dumps(failure),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
