"""Previously authorized bounded shutdown after durable pause and independent evidence."""
import sys
from pathlib import Path
from datetime import datetime,UTC,timedelta
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'phase-8-continuation-deployment/v3'))
import ops
proof=ops.read(HERE/'evidence-readback.json');assert proof['status']=='PASS'
snapshot=ops.read(HERE/'remote-observation-result.json')['summary']
assert snapshot['counts']=={'BACKED_UP':38,'PLANNED':1462} and snapshot['backup_count_verified']==38
assert snapshot['backup_receipts_match_rows'] and snapshot['pause']['reason']=='ValueError:LEDGER_TRANSITION_DRIFT'
host='i-002b63326e1566005'
info=ops.aws('observation-prestop-host',['ec2','describe-instances','--instance-ids',host])['Reservations'][0]['Instances'][0]
assert info['State']['Name']=='running'
assert any(t['Value']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9' for t in info['Tags'])
mapping=info['BlockDeviceMappings'][0]['Ebs']
assert mapping['VolumeId']=='vol-04fa91b4840804295' and mapping['DeleteOnTermination'] is False
ops.aws('observation-stop-host',['ec2','stop-instances','--instance-ids',host])
ops.aws('observation-wait-stopped',['ec2','wait','instance-stopped','--instance-ids',host],120)
after=ops.aws('observation-poststop-host',['ec2','describe-instances','--instance-ids',host])['Reservations'][0]['Instances'][0]
assert after['State']['Name']=='stopped'
at=datetime.now(UTC)
ops.write_new(HERE/'stopped-state.json',{'status':'STOPPED','verified_at_utc':at.isoformat(),'instance_id':host,'owned_root_retained':'vol-04fa91b4840804295','evidence_readback_verified':True,'backed_up':38,'unstarted':1462,'active':0,'new_root_deletion_authorized':False,'retention_decision_due_no_later_than_utc':(at+timedelta(hours=48)).isoformat(),'deadline_unchanged':'2026-10-22T15:24:23.810674Z','source_changed':False,'outcomes_replaced':False,'admissions_resumed':False})
print(ops.read(HERE/'stopped-state.json'))
