"""Complete the guard after a retained missing-Region simulation failure."""
from datetime import UTC, datetime, timedelta
from pathlib import Path
import json
import sys
from ops import HERE, aws
from controls import read, write_new
from handover import ContinuationPolicy

def main():
    proof=read(HERE/'preparation-permission-sydney-context-result.json')['result']
    assert proof['EvaluationResults'] and all(x['EvalDecision']=='allowed' and x['OrganizationsDecisionDetail']['AllowedByOrganizations'] for x in proof['EvaluationResults'])
    request=read(HERE/'preparation-permission-sydney-context-request.json')['arguments']
    assert 'ContextKeyName=aws:RequestedRegion,ContextKeyValues=ap-southeast-2,ContextKeyType=string' in request
    policy=ContinuationPolicy.model_validate(read(Path('E:/p8v5/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    now=datetime.now(UTC); finish=now+timedelta(hours=290*1418/1498+2+.5)
    cost=policy.committed_cost(finish)
    assert cost<55 and finish<policy.stop_at
    write_new(HERE/'feasibility-before-start.json', {'at_utc':now.isoformat(),'status':'PASS','cost_usd':cost,'allowance_hours':290*1418/1498,'preparation_hours':2,'shutdown_hours':.5,'original_deadline':policy.stop_at.isoformat(),'rates_plan_and_prior_storage_evidence':'feasibility.json','clock_reset':False})
    role=read(HERE/'preparation-role-read-result.json')['result']['Role']
    target={'Arn':'arn:aws:scheduler:::aws-sdk:ec2:stopInstances','RoleArn':role['Arn'],'Input':json.dumps({'InstanceIds':['i-057344e5372faf62f']}),'RetryPolicy':{'MaximumEventAgeInSeconds':300,'MaximumRetryAttempts':3}}
    stop=datetime.now(UTC)+timedelta(hours=2)
    expression='at('+stop.strftime('%Y-%m-%dT%H:%M:%S')+')'
    write_new(HERE/'preparation-target.json',target)
    aws('preparation-schedule-create',['scheduler','create-schedule','--name','retained-host-preparation-stop','--group-name','fyp-p85-v5','--schedule-expression',expression,'--schedule-expression-timezone','UTC','--state','ENABLED','--flexible-time-window','{"Mode":"OFF"}','--target','file://'+str(HERE/'preparation-target.json')])
    actual=aws('preparation-schedule-read',['scheduler','get-schedule','--name','retained-host-preparation-stop','--group-name','fyp-p85-v5'])
    assert actual['Target']==target and actual['State']=='ENABLED' and actual['ScheduleExpression']==expression and actual['ScheduleExpressionTimezone']=='UTC' and actual['FlexibleTimeWindow']['Mode']=='OFF'
    write_new(HERE/'prestart-independent-stop-verification.json',{'status':'PASS_CONFIGURATION_AND_REGION_CONTEXT_PERMISSION_SIMULATION','at_utc':datetime.now(UTC).isoformat(),'stop_at_utc':stop.isoformat(),'instance_id':'i-057344e5372faf62f','schedule':actual,'initial_context_omission_retained':True,'permission_context':'Actual ap-southeast-2 StopInstances request','no_policy_or_SCP_bypass':True,'delivery_not_hard_realtime':True})
    start=datetime.now(UTC)
    write_new(HERE/'start-request-anchor.json', {'at_utc':start.isoformat(),'preparation_stop_at':stop.isoformat(),'original_deadline':policy.stop_at.isoformat(),'clock_reset':False})
    host=aws('retained-host-start',['ec2','start-instances','--instance-ids','i-057344e5372faf62f'])
    print(json.dumps({'start_request_utc':start.isoformat(),'preparation_stop_at':stop.isoformat(),'host':host,'main_admitted':False}))

if __name__=='__main__':
    main()
