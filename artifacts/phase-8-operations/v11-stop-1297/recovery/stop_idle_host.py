"""Stop only the verified owned idle host after completed preservation readbacks."""
import json
from pathlib import Path
from ops import r,HOST,HERE

def main():
    # The preservation controller stopped at its additional-copy target AFTER
    # both successful readbacks. Reuse the separate read-only reconciliation;
    # do not rerun the backup or misreport that controller as successful.
    summary=json.loads((HERE/'verified-preservation-summary.json').read_text())
    assert summary['status']=='VERIFIED_PRESERVATION_WITH_RETAINED_OPERATIONAL_BOUND_FAILURE_NO_RESUME'
    assert summary['counts']=={'BACKED_UP':1297,'PLANNED':203}
    assert summary['units_quiesced'] and summary['no_main_admission']
    assert summary['master_backup']['version_id'] and summary['master_readback_sha256']
    assert summary['diagnostic_backup']['version_id'] and summary['diagnostic_readback_sha256']
    assert summary['forecast']['storage_caps_pass']
    reservation=r.call('fresh-owned-host-stop-check',['ec2','describe-instances','--instance-ids',HOST])['Reservations'][0]
    assert reservation['OwnerId']=='803656589923'
    instance=reservation['Instances'][0]
    assert instance['State']['Name']=='running'
    assert {t['Key']:t['Value'] for t in instance['Tags']}['research.owner']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
    assert instance['BlockDeviceMappings'][0]['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de'
    assert instance['BlockDeviceMappings'][0]['Ebs']['DeleteOnTermination'] is False
    v=json.loads((HERE/'root-before-shutdown-result.json').read_text())['result']['Volumes'][0]
    assert v['Encrypted'] and v['Size']==176 and v['Attachments'][0]['InstanceId']==HOST
    result=r.call('stop-owned-idle-1297',['ec2','stop-instances','--instance-ids',HOST])
    print(json.dumps(result))
if __name__=='__main__':main()
