"""Retire only this temporary guard after positive actual-admission evidence."""
from __future__ import annotations
import json
from datetime import UTC,datetime
from control import HERE,ops

def main():
    r=ops.r
    result=json.loads((HERE/'post-launch-v2-read1-result.json').read_bytes())['result']
    assert result['Status']=='Success' and result['ResponseCode']==0
    data=json.loads(result['StandardOutputContent'].splitlines()[-1])
    assert data['current_pause'] is None and data['counts']=={'BACKED_UP':1315,'PLANNED':184,'RUNNING':1}
    assert data['sequence1316']['execution_id']=='01a11705-11f4-7875-b6f4-62729851bd64' and data['sequence1316']['state']=='RUNNING'
    assert len(data['admitted'])==1 and datetime.fromisoformat(data['admitted'][0]['at'])>datetime.fromisoformat('2026-10-23T19:35:07+00:00')
    assert data['services'].count('ActiveState=active')==2 and len(data['effective_credential_environment'])==2
    assert data['original1315_prefix_unchanged'] and data['all1500_identities_order_unchanged'] and data['original1315_backup_receipt_hashes_unchanged']
    r.record('actual-admission.json',data)
    a=r.call('postlaunch-absolute',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v12-absolute-stop-20261026'])
    assert a['State']=='ENABLED' and a['ScheduleExpression']=='at(2026-10-26T12:00:00)' and json.loads(a['Target']['Input'])=={'InstanceIds':[ops.HOST]}
    p=r.call('preparation-before-retire',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v12-recovery1315-stop-20261023'])
    assert p['State']=='ENABLED' and p['Target']==a['Target']
    request={k:p[k] for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target','ActionAfterCompletion')}
    request['State']='DISABLED';r.record('disable-preparation.json',request)
    r.call('disable-preparation',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'disable-preparation.json'),'--client-token','v12-recovery1315-after-actual-admission'])
    v=r.call('verify-preparation-disabled',['scheduler','get-schedule','--group-name',p['GroupName'],'--name',p['Name']])
    assert v['State']=='DISABLED' and v['Target']==a['Target']
    all_schedules=r.call('after-guard-retirement',['scheduler','list-schedules','--group-name','fyp-p85-v5','--max-results','100','--no-paginate'])
    assert not all_schedules.get('NextToken') and {x['Name'] for x in all_schedules['Schedules'] if x['State']=='ENABLED'}=={a['Name']}
    host=r.call('actual-running-host',['ec2','describe-instances','--instance-ids',ops.HOST,'--query','Reservations[0].Instances[0].State.Name'])
    assert host=='running'
    r.record('admission-verification.json',{'status':'PASS_ACTUAL_GUARDED_RESUME','at':datetime.now(UTC).isoformat(),'sequence':1316,'arm':'B3','attempt':1,'execution_id':data['sequence1316']['execution_id'],'admitted_at':data['admitted'][0]['at'],'counts':data['counts'],'host':host,'preparation_guard':'DISABLED_AFTER_ACTUAL_ADMISSION','absolute_guard':'ENABLED_VERIFIED','stop_at':'2026-10-26T12:00:00Z','frozen_package':'cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d','source_unchanged':True,'recovery_backup_sha256':data['recovery_backup']['cloud']['sha256'],'no_replay_regrade_or_replacement':True})
    print('PASS_ACTUAL_SEQUENCE1316_ADMISSION_AND_INDEPENDENT_GUARD_RETIREMENT')

if __name__=='__main__':main()
