"""Retire only the owned preparation stop after verified actual admission."""
import hashlib,json
from datetime import UTC,datetime
from pathlib import Path
from ops import r,HERE
def main():
    progress=sorted((HERE/'progress').glob('*/summary.json'))[-1]
    state=json.loads(progress.read_bytes())
    assert state['counts']=={'BACKED_UP':1297,'PLANNED':202,'RUNNING':1}
    assert state['pause'] is None and state['source']=='/opt/fyp-phase8-continuation-v12'
    assert state['units'].count('ActiveState=active')==2 and state['units'].count('SubState=running')==2
    active=state['active'][0]
    assert active['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028' and active['sequence']==1298 and active['arm']=='B3' and active['attempt']==1
    assert active['deadline'] is not None and state['checkpoints'],'ACTUAL_COLLECTOR_ANCHOR_REQUIRED'
    guards=json.loads((HERE/'independent-guards-verified.json').read_bytes())['guards']
    wanted=guards['preparation']
    old=r.call('preparation-before-retirement',['scheduler','get-schedule','--group-name',wanted['GroupName'],'--name',wanted['Name']])
    assert old['Target']==wanted['Target'] and old['State']=='ENABLED' and old['ScheduleExpression']==wanted['ScheduleExpression']
    fields=('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target')
    request={k:old[k] for k in fields};request['State']='DISABLED'
    r.record('retire-preparation-input.json',request)
    r.call('retire-owned-preparation',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'retire-preparation-input.json'),'--client-token','v12-1298-admitted-20261023'])
    got=r.call('retired-preparation-readback',['scheduler','get-schedule','--group-name',wanted['GroupName'],'--name',wanted['Name']])
    assert all(got[k]==request[k] for k in fields)
    wanted=guards['absolute'];absolute=r.call('absolute-after-admission',['scheduler','get-schedule','--group-name',wanted['GroupName'],'--name',wanted['Name']])
    assert all(absolute[k]==wanted[k] for k in fields) and absolute['State']=='ENABLED'
    schedules=r.call('final-running-guard-inventory',['scheduler','list-schedules','--group-name','fyp-p85-v5','--max-results','100','--no-paginate'])
    assert not schedules.get('NextToken') and {x['Name'] for x in schedules['Schedules'] if x['State']=='ENABLED'}=={wanted['Name']}
    admitted=next((n for n in state['last_notices'] if n.get('kind')=='ADMITTED' and n.get('execution_id')==active['execution_id']),None)
    if admitted is None:
        for prior in sorted((HERE/'progress').glob('*/summary.json')):
            old_state=json.loads(prior.read_bytes())
            admitted=next((n for n in old_state['last_notices'] if n.get('kind')=='ADMITTED' and n.get('execution_id')==active['execution_id']),None)
            if admitted is not None:break
    assert admitted is not None,'RETAINED_ACTUAL_ADMISSION_NOTICE_REQUIRED'
    checkpoint=state['checkpoints'][0]['data']
    r.record('actual-admission.json',{'status':'PASS_ACTUAL_ADMISSION_NOT_COMPLETED_OUTCOME','verified_at':datetime.now(UTC).isoformat(),'progress_record':str(progress),'progress_sha256':hashlib.sha256(progress.read_bytes()).hexdigest(),'run_id':state['run_id'],'counts':state['counts'],'execution':active,'admitted_notice':admitted,'collector_checkpoint':checkpoint,'host':'i-057344e5372faf62f','service_state':state['units'],'preparation_stop_retired_and_read_back':True,'absolute_aws_guard_active':True,'stop_at':'2026-10-26T12:00:00Z','observations_or_grades_replaced':False})
    print('PASS_ACTUAL_SEQUENCE1298_COLLECTOR_RUNNING_PREPARATION_STOP_RETIRED_ABSOLUTE_GUARD_RETAINED')
if __name__=='__main__':main()
