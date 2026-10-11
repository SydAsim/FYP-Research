"""Stop idle compute after independently read-back, pinned external preservation."""
import json
from datetime import UTC,datetime
from ops import HERE,aws
from controls import read,write_new

def main():
    reply=read(HERE/'preserve-stop-120-status1-result.json')['result']
    assert reply['Status']=='Success' and reply['ResponseCode']==0
    retained=json.loads(reply['StandardOutputContent'].splitlines()[-1])
    summary=retained['summary']
    assert summary['counts']=={'BACKED_UP':120,'PLANNED':1380} and summary['full_readback']=='PASS' and summary['all_120_pinned_backups_verified']
    write_new(HERE/'preservation-proof.json',retained)
    for label,proof in (('master',summary['master_backup']),('inspection',retained['inspection'])):
        import base64
        head=aws(label+'-independent-version-head',['s3api','head-object','--bucket',proof['bucket'],'--key',proof['key'],'--version-id',proof['version_id'],'--checksum-mode','ENABLED'])
        assert head['VersionId']==proof['version_id'] and head['ContentLength']==proof['bytes'] and head['Metadata']['sha256']==proof['sha256']
        assert base64.b64decode(head['ChecksumSHA256']).hex()==proof['sha256']
    aws('idle-host-stop',['ec2','stop-instances','--instance-ids','i-057344e5372faf62f'])
    aws('wait-host-stopped',['ec2','wait','instance-stopped','--instance-ids','i-057344e5372faf62f'],90)
    host=aws('verified-stopped-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f'])['Reservations'][0]['Instances'][0]
    root=aws('verified-retained-root',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])['Volumes'][0]
    assert host['State']['Name']=='stopped' and root['Attachments'][0]['InstanceId']==host['InstanceId'] and not root['Attachments'][0]['DeleteOnTermination']
    value={'status':'PAUSED_PRESERVED_HOST_STOPPED','at_utc':datetime.now(UTC).isoformat(),'host_id':host['InstanceId'],'host_state':'stopped','root':root['VolumeId'],'root_deleted':False,'counts':summary['counts'],'completed_execution_percentage':120/1500*100,'pause':summary['pause'],'next':summary['next'],'master_backup':summary['master_backup'],'inspection_backup':retained['inspection'],'independent_master_readback':'PASS_ON_HOST_FROM_PINNED_S3_VERSION','local_independent_S3_version_heads':'PASS','full_local_archive_download':'NOT_YET_REQUESTED; external pinned copy and retained root verified','campaign_restarted':False,'pause_cleared':False,'source_modified':False,'originals_replayed':False,'original_deadline':'2026-10-22T15:24:23.810674Z','retained_root_decision_deadline':'2026-10-11T09:33:51.252814Z','root_cause':'Clock guard observed wall elapsed >5 seconds behind monotonic elapsed; underlying cause not yet established'}
    write_new(HERE/'final-status.json',value)
    report=f'''# Phase 8 progress and guarded stop — 10 October 2026

## Verified state

- **120 BACKED_UP / 1,380 PLANNED / zero active** — 8% of 1,500 original executions
  retained, not a claim that every business or speech outcome passed.
- Paused at 2026-10-09 23:14:41.760070 UTC (10 October 04:14:41 Pakistan time).
- Reason: `WALL_CLOCK_BACKWARD_STOP_ADMISSIONS`.
- Campaign service failed; watchdog was still running when inspected. Neither
  was restarted. Watchdog was quiesced solely for consistent preservation.
- Host `{host['InstanceId']}` is **verified stopped** at {value['at_utc']}.
  Encrypted 160-GiB owned root `{root['VolumeId']}` retained, no deletion.
- Next unchanged identity: sequence 121, P1, attempt 1,
  `{summary['next']['execution_id']}`. No admission/replay/replacement occurred.

## Trigger and limits of diagnosis

The frozen guard compares wall-clock elapsed time with monotonic elapsed time
from the sealed host anchor and refuses admissions if wall elapsed is more than
five seconds behind monotonic elapsed (`controls.py:290–302`). The exact durable
pause is retained. This message does not prove a discrete wall-clock jump or its
cause. Campaign/watchdog journals, clock-service journals, time status and anchor
were preserved for later review. No code, clock setting, policy or guard changed.

## Preservation before stop

Every completed slot's backup receipt hash and all **120 pinned S3 archive versions**
were verified. A consistent complete master archive was uploaded using frozen
code and independently downloaded/read back from its pinned S3 version into a
separate directory on the host; archive/member/continuation checks and all 1,500
rows passed. A second inspection archive retains that master, complete read-only
ledger, raw pause/anchor, service state and diagnostics. Both external version
heads, exact sizes, metadata and S3 SHA-256 checksums were independently verified
from the local terminal before requesting idle-host stop. No full local archive
download is claimed; external pinned evidence and retained root remain available.

Master SHA-256: `{summary['master_backup']['sha256']}`.
Pinned version: `{summary['master_backup']['version_id']}`.
Inspection SHA-256: `{retained['inspection']['sha256']}`.
Pinned version: `{retained['inspection']['version_id']}`.

Original/raw grades, identities, order, earlier failed attempts, source/freeze and
all S3/local evidence remain unchanged. AWS compute was stopped through the
standing authorized preservation/shutdown procedure. The original US$60 guard,
US$65 ceiling and 22 October 2026 15:24:23.810674 UTC deadline remain unchanged;
this task did not authorize or attempt continuation or a feasibility reset.

Retained-root decision bound remains **11 October 2026, 09:33:51.252814 UTC**
(14:33:51 Pakistan time). Root removal has not been authorized here. Clock-cause
review and a qualified continuation decision remain outstanding.
'''
    with (HERE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report)
    print(json.dumps(value,indent=2))

if __name__=='__main__':main()
