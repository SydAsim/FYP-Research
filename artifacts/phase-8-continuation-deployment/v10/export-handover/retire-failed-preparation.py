import json,sys
sys.path.insert(0,'artifacts/phase-8-continuation-deployment/v10/export-handover')
from ops import HERE,call,record
host=json.loads((HERE/'safe-stop-state2-result.json').read_text())['result']['Reservations'][0]['Instances'][0]
assert host['State']['Name']=='stopped' and host['InstanceId']=='i-057344e5372faf62f'
requested=json.loads((HERE/'preparation-input.json').read_text())
actual=call('failed-preparation-guard-before-disable',['scheduler','get-schedule','--name',requested['Name'],'--group-name',requested['GroupName']])
for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','State','FlexibleTimeWindow','Target'):assert actual[k]==requested[k]
requested['State']='DISABLED';record('failed-preparation-disable-input.json',requested)
call('disable-failed-preparation',['scheduler','update-schedule','--cli-input-json','file://'+str(HERE/'failed-preparation-disable-input.json')])
after=call('readback-failed-preparation-disabled',['scheduler','get-schedule','--name',requested['Name'],'--group-name',requested['GroupName']])
assert after['State']=='DISABLED' and after['Target']==requested['Target']
print('PASS_STOPPED_HOST_AND_DISABLED_OWNED_PREPARATION_GUARD')
