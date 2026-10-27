"""Stop only the verified owned idle host after successful closed-boundary readback."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ops import recorder

here=Path(__file__).resolve().parent
def main():
    p=json.loads((here/'preserve616-read3-result.json').read_text())['result']
    assert p['Status']=='Success'
    summary=json.loads(p['StandardOutputContent'].splitlines()[-1])
    assert summary['counts']=={'BACKED_UP':616,'PLANNED':884} and summary['units_quiesced']
    assert summary['master_backup']['version_id'] and summary['readback_sha256']
    assert not summary['feasibility']['time_gate'] and not summary['feasibility']['admission_forecast_gate']
    read=json.loads((here/'host-before-stop-result.json').read_text())['result']['Reservations'][0]
    assert read['OwnerId']=='803656589923'
    instance=read['Instances'][0]
    assert instance['InstanceId']=='i-057344e5372faf62f'
    assert {t['Key']:t['Value'] for t in instance['Tags']}['research.owner']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
    assert instance['BlockDeviceMappings'][0]['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de'
    assert not instance['BlockDeviceMappings'][0]['Ebs']['DeleteOnTermination']
    result=recorder.call('stop-idle-closed616',['ec2','stop-instances','--instance-ids',instance['InstanceId']])
    print(json.dumps(result))
if __name__=='__main__':main()
