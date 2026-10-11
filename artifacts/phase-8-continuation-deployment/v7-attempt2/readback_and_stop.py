"""Verify independent blocked-boundary copy, then stop idle compute; preserve disk."""
import hashlib
import json
import sqlite3
import tarfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ops import HERE, aws
from controls import hash_file, read, write_new


def main() -> None:
    invocation=read(HERE/'preserve-readiness-attempt2-status1-result.json')['result']
    assert invocation['Status']=='Success' and invocation['ResponseCode']==0
    payload=json.loads(invocation['StandardOutputContent']);proof=payload['evidence']
    write_new(HERE/'blocked-preservation-proof.json',proof)
    target=Path('E:/p8v7/blocked-20261009-v7-attempt2')
    target.mkdir(exist_ok=False)
    archive=target/'evidence.tar.gz'
    result=aws('blocked-evidence-get',['s3api','get-object','--bucket',proof['bucket'],'--key',proof['key'],
               '--version-id',proof['version_id'],'--checksum-mode','ENABLED',str(archive)],180)
    assert result['VersionId']==proof['version_id']
    assert archive.stat().st_size==proof['bytes'] and hash_file(archive)==proof['sha256']
    actual={};manifest=None
    with tarfile.open(archive,'r|gz') as incoming:
        for member in incoming:
            if not member.isfile():continue
            assert member.name.startswith('inspection/') and '..' not in Path(member.name).parts
            stream=incoming.extractfile(member);assert stream is not None
            body=stream.read();name=member.name.removeprefix('inspection/')
            if name=='manifest.json':manifest=json.loads(body)
            else:actual[name]=hashlib.sha256(body).hexdigest()
            if name=='campaign.sqlite3':(target/'campaign.sqlite3').write_bytes(body)
    assert manifest is not None and actual==manifest['files']
    with sqlite3.connect((target/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;db.execute('BEGIN')
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        rows=[dict(row) for row in db.execute('SELECT * FROM slots ORDER BY sequence')]
    original=read(Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete/closed-82/ledger-read-only.json'))['rows']
    assert rows==original and Counter(row['state'] for row in rows)=={'BACKED_UP':82,'PLANNED':1418}
    write_new(HERE/'blocked-evidence-readback.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),
              'local_archive':str(archive),'proof':proof,'verified_members':len(actual),'all_1500_original_rows_unchanged':True,
              'BACKED_UP':82,'PLANNED':1418,'active':0,'next_execution_id':rows[82]['execution_id']})
    aws('blocked-idle-host-stop',['ec2','stop-instances','--instance-ids','i-057344e5372faf62f'])
    print('Independent evidence copy verified; idle-host stop requested; root preserved')
    aws('blocked-host-stopped-wait',['ec2','wait','instance-stopped','--instance-ids','i-057344e5372faf62f'],180)
    instance=aws('final-stopped-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f'])['Reservations'][0]['Instances'][0]
    volume=aws('final-retained-root',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])['Volumes'][0]
    assert instance['State']['Name']=='stopped'
    assert volume['Attachments'][0]['InstanceId']==instance['InstanceId'] and not volume['Attachments'][0]['DeleteOnTermination']
    freeze=read(HERE.parents[1]/'phase-8-continuation-freeze/v7/freeze-verification.json')
    write_new(HERE/'final-status.json',{'status':'V7_FROZEN_VERIFIED_READINESS_BLOCKED_HOST_STOPPED','at_utc':datetime.now(UTC).isoformat(),
              'package_hash':freeze['package_hash'],'archive_sha256':freeze['archive_sha256'],'freeze_manifest_sha256':freeze['freeze_manifest_sha256'],
              'instance_id':instance['InstanceId'],'host_state':'stopped','retained_root':volume['VolumeId'],'root_deleted':False,
              'authorized':True,'actual_main_admission':False,'driver_calls':0,'BACKED_UP':82,'PLANNED':1418,'active':0,
              'next_sequence':83,'next_arm':'B3','next_attempt':1,'next_execution_id':rows[82]['execution_id'],
              'exact_trigger':"OLD_OPERATIONAL_UNIT_RUNNING: a pre-existing enabled operational unit restarted at boot; read-only live gate failed before metadata import or main admission",
              'failed_command_id':'34df8031-b7d8-4ddf-8d87-116a8d8b76b4','pause_preserved':payload['summary']['pause'],
              'preservation':proof,'independent_readback':'PASS','prelaunch_backup':'NOT_STARTED','readiness_and_launch_receipt':'NOT_CREATED',
              'complete_backup':'NOT_STARTED','frozen_code_patched':False,'replay':False,'replacement':False,
              'original_deadline':'2026-10-22T15:24:23.810674Z','retained_root_decision_deadline':'2026-10-11T09:33:51.252814Z',
              'guard_usd':60,'total_usd':65,'cloud_cap_gib':60,'independent_preparation_guard_retained':True})
    print(json.dumps(read(HERE/'final-status.json'),indent=2))


if __name__=='__main__':
    main()
