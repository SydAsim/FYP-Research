"""Retire only this preparation stop after verified actual admission and active controls."""
import json
from datetime import UTC,datetime
from ops import HERE,aws
from controls import read,write_new

def main():
    result=read(HERE/'progress-admission-v2-status1-result.json')['result']
    assert result['Status']=='Success'
    live=json.loads(result['StandardOutputContent'])
    assert live['sequence83']['execution_id']=='01a11705-11f1-792b-ae1e-36bfc6773842' and live['sequence83']['state']=='RUNNING'
    assert live['pause'] is None and live['counts']=={'BACKED_UP':82,'RUNNING':1,'PLANNED':1417}
    assert len(live['active'])==1 and any(x['execution_id']==live['sequence83']['execution_id'] for x in live['latest_admissions'])
    assert (datetime.now(UTC)-datetime.fromisoformat(live['at_utc'])).total_seconds()<180
    name='retained-host-v7-attempt3-preparation-stop-20261009';group='fyp-p85-v5'
    guard=aws('active-preparation-guard-before-disable',['scheduler','get-schedule','--name',name,'--group-name',group])
    assert guard['State']=='ENABLED' and guard['Target']==read(HERE/'preparation-target.json')
    request={k:guard[k] for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','FlexibleTimeWindow','Target')}
    for optional in ('Description','StartDate','EndDate','KmsKeyArn','ActionAfterCompletion'):
        if optional in guard:request[optional]=guard[optional]
    request['State']='DISABLED';path=HERE/'actual-admission-preparation-disable.json';write_new(path,request)
    aws('active-preparation-guard-disable',['scheduler','update-schedule','--cli-input-json','file://'+str(path)])
    verified=aws('active-preparation-guard-disabled-readback',['scheduler','get-schedule','--name',name,'--group-name',group])
    assert verified['State']=='DISABLED' and verified['Target']==guard['Target']
    host=aws('actual-running-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f'])['Reservations'][0]['Instances'][0]
    assert host['State']['Name']=='running'
    write_new(HERE/'preparation-guard-retired-after-admission.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'actual_sequence83_admission_utc':live['latest_admissions'][-1]['at'],'preparation_schedule':name,'state':'DISABLED','host_state':'running','absolute_deadline_unchanged':True,'superseded_preparation_guards_preboot_verified':True})
    print('Preparation-only Scheduler disabled and read back after actual admission; host running')

if __name__=='__main__':main()
