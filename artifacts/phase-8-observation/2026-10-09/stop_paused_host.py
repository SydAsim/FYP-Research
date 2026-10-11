"""Previously authorized bounded shutdown after durable pause and independent evidence."""
import sys
from pathlib import Path
from datetime import datetime,UTC,timedelta
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import ops
proof=ops.read(HERE/'evidence-readback.json');assert proof['status']=='PASS'
snapshot=ops.read(HERE/'remote-observation-result.json')['summary']
assert snapshot['counts']=={'BACKED_UP':82,'PLANNED':1418} and snapshot['backup_count_verified']==82
assert snapshot['backup_receipts_match_rows'] and snapshot['pause']['reason']=='PROTOCOL_STOP'
host='i-057344e5372faf62f'
info=ops.aws('observation-prestop-host',['ec2','describe-instances','--instance-ids',host])['Reservations'][0]['Instances'][0]
assert info['State']['Name']=='running'
assert any(t['Value']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9' for t in info['Tags'])
mapping=info['BlockDeviceMappings'][0]['Ebs']
assert mapping['VolumeId']=='vol-09dbb42bbf607f5de' and mapping['DeleteOnTermination'] is False
assert snapshot['active']==0 and not snapshot['live_owned_application_processes']
assert snapshot['ledger_integrity']=='ok' and snapshot['notice_hash_chain_valid'] and not snapshot['transition_mismatches']
requested_at=datetime.now(UTC)
ops.write_new(HERE/'retention-clock.json',{'anchor':'earliest_stop_request','stop_requested_at_utc':requested_at.isoformat(),'retention_decision_due_no_later_than_utc':(requested_at+timedelta(hours=48)).isoformat(),'root_delete_authorized':False})
ops.aws('observation-stop-host',['ec2','stop-instances','--instance-ids',host])
ops.aws('observation-wait-stopped',['ec2','wait','instance-stopped','--instance-ids',host],120)
after=ops.aws('observation-poststop-host',['ec2','describe-instances','--instance-ids',host])['Reservations'][0]['Instances'][0]
assert after['State']['Name']=='stopped'
at=datetime.now(UTC)
ops.write_new(HERE/'stopped-state.json',{'status':'STOPPED','verified_at_utc':at.isoformat(),'instance_id':host,'owned_root_retained':'vol-09dbb42bbf607f5de','evidence_readback_verified':True,'backed_up':82,'unstarted':1418,'active':0,'new_root_deletion_authorized':False,'retention_decision_due_no_later_than_utc':(requested_at+timedelta(hours=48)).isoformat(),'deadline_unchanged':'2026-10-22T15:24:23.810674Z','source_changed':False,'outcomes_replaced':False,'admissions_resumed':False})
volume=ops.aws('observation-poststop-root',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])
assert volume['Volumes'][0]['Encrypted'] and volume['Volumes'][0]['Attachments'][0]['InstanceId']==host
print(ops.read(HERE/'stopped-state.json'))
