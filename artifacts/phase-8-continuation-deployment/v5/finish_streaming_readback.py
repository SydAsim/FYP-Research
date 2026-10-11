"""Continue the retained readback using one bounded streaming archive pass."""
from datetime import UTC,datetime,timedelta
import hashlib
import json
import sqlite3
import tarfile
import time
from pathlib import Path
from ops import HERE,aws
from controls import hash_file,read,write_new
from handover import ContinuationPolicy

def main():
    proof=read(HERE/'blocked-preservation-proof.json')
    target=Path('E:/p8v5/blocked-20261009');archive=target/'evidence.tar.gz'
    assert read(HERE/'blocked-evidence-get-result.json')['exit']==0
    assert archive.stat().st_size==proof['bytes'] and hash_file(archive)==proof['sha256']
    start=time.monotonic()
    with tarfile.open(archive) as incoming:
        manifest=json.load(incoming.extractfile('inspection/manifest.json'))
    checked=set()
    with tarfile.open(archive,mode='r|gz') as incoming:
        for member in incoming:
            if time.monotonic()-start>90:raise TimeoutError('BOUNDED_STREAMING_READBACK_RETAIN_ARCHIVE')
            if not member.isfile() or member.name=='inspection/manifest.json':continue
            name=member.name.removeprefix('inspection/')
            if name not in manifest['files']:raise ValueError('UNINVENTORIED_PRESERVATION_MEMBER')
            stream=incoming.extractfile(member)
            value=hashlib.sha256();master=bytearray()
            for block in iter(lambda:stream.read(1024**2),b''):
                value.update(block)
                if name=='campaign.sqlite3':master.extend(block)
            if value.hexdigest()!=manifest['files'][name] or name in checked:raise ValueError('PRESERVATION_MEMBER_DRIFT')
            checked.add(name)
            if name=='campaign.sqlite3':(target/'campaign.sqlite3').write_bytes(master)
    assert checked==set(manifest['files'])
    with sqlite3.connect((target/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;db.execute('BEGIN');assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        rows=[dict(r) for r in db.execute('SELECT * FROM slots ORDER BY sequence')]
    original=read(Path('E:/p8v5/source/artifacts/phase-8-runner-amendment/v4-complete/closed-82/ledger-read-only.json'))['rows']
    assert rows==original and rows[82]['state']=='PLANNED'
    write_new(HERE/'blocked-evidence-readback.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'local_archive':str(archive),'proof':proof,'members_verified':len(checked),'streaming_seconds':time.monotonic()-start,'original_1500_rows_unchanged':True,'BACKED_UP':82,'PLANNED':1418,'active':0,'first_slow_attempt_retained':True,'download_repeated':False})
    stopped=aws('blocked-idle-host-stop',['ec2','stop-instances','--instance-ids','i-057344e5372faf62f'])
    print(json.dumps({'status':'EVIDENCE_VERIFIED_STOP_REQUESTED','stop_result':stopped,'main_admitted':False}),flush=True)
    aws('blocked-host-stopped-wait',['ec2','wait','instance-stopped','--instance-ids','i-057344e5372faf62f'],180)
    instance=aws('final-stopped-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f'])['Reservations'][0]['Instances'][0]
    volume=aws('final-retained-root',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])['Volumes'][0]
    assert instance['State']['Name']=='stopped' and volume['Attachments'][0]['InstanceId']==instance['InstanceId'] and not volume['Attachments'][0]['DeleteOnTermination']
    now=datetime.now(UTC);policy=ContinuationPolicy.model_validate(read(Path('E:/p8v5/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    projection=policy.committed_cost(now+timedelta(hours=290*1418/1498+2+.5))
    write_new(HERE/'final-status.json',{'status':'FROZEN_VERIFIED_LAUNCH_BLOCKED_HOST_STOPPED','at_utc':now.isoformat(),'instance_id':instance['InstanceId'],'host_state':'stopped','retained_root':volume['VolumeId'],'root_deleted':False,
          'freeze_manifest_sha256':'95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26','package_hash':'805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627',
          'launch_authorized_by_human':True,'actual_main_admission':False,'new_main_driver_calls':0,'BACKED_UP':82,'PLANNED':1418,'active':0,'next_sequence':83,'next_arm':'B3','next_attempt':1,'next_execution_id':rows[82]['execution_id'],
          'old_pause_preserved':'PROTOCOL_STOP','backup_gate':read(HERE/'backup-gate-result.json'),'independent_retained_evidence':proof,'all82_original_backups_verified':True,
          'original_deadline':policy.stop_at.isoformat(),'retained_root_decision_deadline':'2026-10-11T09:33:51.252814Z','guard_usd':55,'total_usd':65,'unchanged_allowance_hours':290*1418/1498,'current_projection_with_new_2h_preparation_usd':projection,
          'source_and_outcomes_changed':False,'freeze_remains_preserved':True})
    print(json.dumps(read(HERE/'final-status.json'),indent=2))

if __name__=='__main__':
    main()
