"""Delete only the authorized previous stopped host/root after copy verification."""
import base64
import concurrent.futures
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNTIME=Path('E:/p8v4/source/artifacts/phase-8-runner-amendment/v4-complete')
sys.path.insert(0,str(RUNTIME))
from controls import hash_file,read,write_new
from closed_prefix import archive_proof,verify_master
from ops import aws

RUN='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
OLD='i-002b63326e1566005'
DISK='vol-04fa91b4840804295'

def check(n: int,proof: dict) -> None:
    h=aws('cleanup-retained-head-'+str(n),['s3api','head-object','--bucket',proof['bucket'],'--key',proof['key'],'--version-id',proof['version_id'],'--checksum-mode','ENABLED'])
    if h['VersionId']!=proof['version_id'] or h['ContentLength']!=proof['bytes'] or h['Metadata']['sha256']!=proof['sha256'] or base64.b64decode(h['ChecksumSHA256']).hex()!=proof['sha256']:
        raise ValueError('INDEPENDENT_RETAINED_COPY_DRIFT')

def main() -> None:
    result=read(HERE/'complete-prelaunch-backup-status1-result.json')['result']
    assert result['Status']=='Success' and result['ResponseCode']==0
    imported=json.loads(result['StandardOutputContent'])
    assert imported['status']=='PASS' and imported['backed_up']==38 and imported['planned']==1462
    new=read(HERE/'actual-deployment-binding.json')['instance_id'];assert new!=OLD
    verify_master(RUNTIME/'boundary')
    proofs=read(RUNTIME/'retained-slot-proofs.json')
    for p in proofs:archive_proof(RUNTIME/'boundary',p)
    boundary=read(RUNTIME/'stopped-boundary-reference.json')
    local=RUNTIME/'boundary/authoritative-snapshot.tar.gz'
    assert hash_file(local)==boundary['sha256'] and local.stat().st_size==boundary['bytes']
    cloud=[p['cloud'] for p in proofs]+[boundary,imported['prelaunch_backup']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(check,n,p) for n,p in enumerate(cloud)]
        for f in futures:f.result()
    node=aws('cleanup-stopped-ownership',['ec2','describe-instances','--instance-ids',OLD])['Reservations'][0]['Instances'][0]
    volume=aws('cleanup-root-ownership',['ec2','describe-volumes','--volume-ids',DISK])['Volumes'][0]
    assert node['State']['Name']=='stopped'
    assert dict((t['Key'],t['Value']) for t in node['Tags'])['research.owner']==RUN
    assert dict((t['Key'],t['Value']) for t in volume['Tags'])['research.owner']==RUN
    assert len(volume['Attachments'])==1 and volume['Attachments'][0]['InstanceId']==OLD and volume['Attachments'][0]['Device']=='/dev/sda1'
    assert node['BlockDeviceMappings'][0]['Ebs']['VolumeId']==DISK
    write_new(HERE/'cleanup-evidence-gate.json',{'status':'PASS','old_host':OLD,'old_root':DISK,'new_host_untouched':new,'original_archives_local_and_pinned_s3_verified':38,'boundary_local_and_pinned_s3_verified':True,'new_host_import_and_backup_readback':'PASS','prelaunch_backup':imported['prelaunch_backup'],'no_s3_or_local_deletion':True,'authority':'Explicit current user authorization after reviewed handover and independent copy checks'})
    aws('old-host-termination',['ec2','terminate-instances','--instance-ids',OLD])
    aws('old-host-terminated-wait',['ec2','wait','instance-terminated','--instance-ids',OLD],120)
    aws('old-root-available-wait',['ec2','wait','volume-available','--volume-ids',DISK],120)
    aws('old-root-deletion',['ec2','delete-volume','--volume-id',DISK])
    write_new(HERE/'old-cleanup-complete.json',{'status':'PASS','old_host':OLD,'old_root':DISK,'new_host_untouched':new,'evidence_preserved':True,'new_root_deletion_authorized':False})
    print(json.dumps(read(HERE/'old-cleanup-complete.json')))

if __name__=='__main__':main()
