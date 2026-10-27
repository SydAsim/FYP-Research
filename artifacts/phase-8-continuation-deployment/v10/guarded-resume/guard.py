"""Fresh independently read-back AWS stop protection before host boot."""
import json
from datetime import UTC,datetime,timedelta
from ops import HERE,HOST,call,record

def read(name):return json.loads((HERE/name).read_text())

def main():
    expected_role=json.loads((HERE.parent/'guard-role-result.json').read_text())['result']['Role']
    current=read('guard-role-result.json')['result']['Role']
    assert current['Arn']==expected_role['Arn'] and current['AssumeRolePolicyDocument']==expected_role['AssumeRolePolicyDocument']
    expected_policy=json.loads((HERE.parent/'guard-permission-result.json').read_text())['result']['PolicyDocument']
    assert read('guard-permission-result.json')['result']['PolicyDocument']==expected_policy
    requested=read('preparation-input.json')
    call('create-preparation',['scheduler','create-schedule','--cli-input-json','file://'+str(HERE/'preparation-input.json'),
        '--client-token','v10-guarded-resume-20261012'])
    actual=call('readback-preparation',['scheduler','get-schedule','--group-name',requested['GroupName'],'--name',requested['Name']])
    for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target'):
        assert actual[k]==requested[k],'PREPARATION_GUARD_DRIFT:'+k
    deadline=datetime.fromisoformat(actual['ScheduleExpression'][3:-1]+'+00:00')
    assert datetime.now(UTC)+timedelta(minutes=90)<deadline,'PREPARATION_GUARD_TOO_CLOSE'
    absolute=call('readback-absolute',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v10-absolute-stop-20261025'])
    assert absolute['State']=='ENABLED' and absolute['ScheduleExpression']=='at(2026-10-25T15:24:23)' and absolute['Target']==requested['Target']
    schedules=call('owned-schedule-inventory',['scheduler','list-schedules','--group-name','fyp-p85-v5','--max-results','100','--no-paginate'])
    assert not schedules.get('NextToken'),'INCOMPLETE_SCHEDULE_INVENTORY'
    expected_enabled={requested['Name'],absolute['Name']}
    assert {s['Name'] for s in schedules['Schedules'] if s['State']=='ENABLED'}==expected_enabled,'UNACCOUNTED_ACTIVE_OWNED_GUARD'
    record('independent-guards-verified.json',{'status':'PASS_BEFORE_BOOT','preparation':actual,'absolute':absolute,
        'prior_preparation_schedules':'all disabled; no changes required','permission_unchanged':True,
        'at':datetime.now(UTC).isoformat(),'host_id':HOST,'hard_realtime_guarantee':False})
    print('PASS_FRESH_PREPARATION_AND_ABSOLUTE_GUARDS')

if __name__=='__main__':main()
