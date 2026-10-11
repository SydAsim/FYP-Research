"""Authorized preparation guard and retained-host start; no campaign admission."""
from datetime import UTC, datetime, timedelta
from pathlib import Path
import json
import sys

from ops import HERE, aws
from controls import hash_file, read, write_new

INSTANCE = 'i-057344e5372faf62f'
ACCOUNT = '803656589923'
GROUP = 'fyp-p85-v5'
ROLE = 'FYP-p85-v5-preparation-stop'
NAME = 'retained-host-preparation-stop'

def main():
    repo = HERE.parents[2]
    freeze = read(repo / 'artifacts/phase-8-continuation-freeze/v5/freeze-verification.json')
    feasible = read(HERE / 'feasibility.json')
    if freeze['status'] != 'PASS' or freeze['package_hash'] != '805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627':
        raise ValueError('EXACT_ACCEPTED_FREEZE_REQUIRED')
    if feasible['status'] != 'PASS_CONDITIONAL' or (datetime.now(UTC)-datetime.fromisoformat(feasible['at_utc'])).total_seconds() > 600:
        raise ValueError('CURRENT_FEASIBILITY_REQUIRED')
    write_new(HERE/'actual-deployment-binding.json', {
        'kind':'EXPLICIT_HUMAN_AUTHORIZED_RETAINED_HOST_REUSE', 'at_utc':datetime.now(UTC).isoformat(),
        'instance_id':INSTANCE, 'root_volume_id':'vol-09dbb42bbf607f5de',
        'package_hash':freeze['package_hash'], 'freeze_manifest_sha256':freeze['freeze_manifest_sha256'],
        'run_id':'p85-01a116f7-3b82-7a79-8653-3aee62dc99e9', 'backed_up':82,'planned':1418,'next_sequence':83,
        'authority':'Human explicitly accepted v5, authorized freeze, retained-host update/start, independent preparation-stop and continuation subject to every gate on 9 October 2026',
        'guard_usd':55,'total_usd':65,'original_deadline':'2026-10-22T15:24:23.810674Z','actual_launch':False})
    host=aws('prestart-host',['ec2','describe-instances','--instance-ids',INSTANCE])['Reservations'][0]['Instances'][0]
    volume=aws('prestart-volume',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])['Volumes'][0]
    security=aws('prestart-security',['ec2','describe-security-groups','--group-ids',host['SecurityGroups'][0]['GroupId']])
    assert host['State']['Name']=='stopped' and host['InstanceType']=='m7i-flex.large'
    assert volume['Attachments'][0]['InstanceId']==INSTANCE and not volume['Attachments'][0]['DeleteOnTermination']
    assert volume['Encrypted'] and volume['Size']==160
    assert not security['SecurityGroups'][0]['IpPermissions']
    assert host['MetadataOptions']['HttpTokens']=='required'
    assert dict((t['Key'],t['Value']) for t in host['Tags'])['research.owner']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
    aws('preparation-group-create',['scheduler','create-schedule-group','--name',GROUP])
    group_arn=f'arn:aws:scheduler:ap-southeast-2:{ACCOUNT}:schedule-group/{GROUP}'
    trust={'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'scheduler.amazonaws.com'},'Action':'sts:AssumeRole','Condition':{'StringEquals':{'aws:SourceAccount':ACCOUNT,'aws:SourceArn':group_arn}}}]}
    permission={'Version':'2012-10-17','Statement':[{'Effect':'Allow','Action':'ec2:StopInstances','Resource':f'arn:aws:ec2:ap-southeast-2:{ACCOUNT}:instance/{INSTANCE}'}]}
    write_new(HERE/'preparation-trust.json',trust)
    write_new(HERE/'preparation-permission.json',permission)
    role=aws('preparation-role-create',['iam','create-role','--role-name',ROLE,'--assume-role-policy-document','file://'+str(HERE/'preparation-trust.json'),'--description','Scoped independent v5 preparation stop; no evidence deletion'])['Role']
    aws('preparation-policy-put',['iam','put-role-policy','--role-name',ROLE,'--policy-name','StopOnlyRetainedCampaignHost','--policy-document','file://'+str(HERE/'preparation-permission.json')])
    actual=aws('preparation-role-read',['iam','get-role','--role-name',ROLE])['Role']
    actual_policy=aws('preparation-policy-read',['iam','get-role-policy','--role-name',ROLE,'--policy-name','StopOnlyRetainedCampaignHost'])['PolicyDocument']
    assert actual['AssumeRolePolicyDocument']==trust and actual_policy==permission
    simulation=aws('preparation-permission-simulation',['iam','simulate-principal-policy','--policy-source-arn',role['Arn'],'--action-names','ec2:StopInstances','--resource-arns',permission['Statement'][0]['Resource']])
    assert all(r['EvalDecision']=='allowed' for r in simulation['EvaluationResults']) and simulation['EvaluationResults']
    request_anchor=datetime.now(UTC)
    stop=request_anchor+timedelta(hours=2)
    target={'Arn':'arn:aws:scheduler:::aws-sdk:ec2:stopInstances','RoleArn':role['Arn'],'Input':json.dumps({'InstanceIds':[INSTANCE]}),'RetryPolicy':{'MaximumEventAgeInSeconds':300,'MaximumRetryAttempts':3}}
    write_new(HERE/'preparation-target.json',target)
    expression='at('+stop.strftime('%Y-%m-%dT%H:%M:%S')+')'
    aws('preparation-schedule-create',['scheduler','create-schedule','--name',NAME,'--group-name',GROUP,'--schedule-expression',expression,'--schedule-expression-timezone','UTC','--state','ENABLED','--flexible-time-window','{"Mode":"OFF"}','--target','file://'+str(HERE/'preparation-target.json')])
    schedule=aws('preparation-schedule-read',['scheduler','get-schedule','--name',NAME,'--group-name',GROUP])
    assert schedule['State']=='ENABLED' and schedule['Target']==target and schedule['ScheduleExpression']==expression and schedule['ScheduleExpressionTimezone']=='UTC' and schedule['FlexibleTimeWindow']['Mode']=='OFF'
    write_new(HERE/'prestart-independent-stop-verification.json', {'status':'PASS_CONFIGURATION_AND_PERMISSION_SIMULATION','at_utc':datetime.now(UTC).isoformat(),'stop_at_utc':stop.isoformat(),'instance_id':INSTANCE,'schedule':schedule,'execution_role':role['Arn'],'permission_simulation':'allowed','trust_scoped_to_exact_schedule_group':True,'billing_limit_unchanged':True,'delivery_not_hard_realtime':True})
    actual_start=datetime.now(UTC)
    write_new(HERE/'start-request-anchor.json',{'at_utc':actual_start.isoformat(),'preparation_stop_at':stop.isoformat(),'original_deadline':'2026-10-22T15:24:23.810674Z','clock_reset':False})
    reply=aws('retained-host-start',['ec2','start-instances','--instance-ids',INSTANCE])
    print(json.dumps({'freeze':freeze['freeze_manifest_sha256'],'start_request_utc':actual_start.isoformat(),'preparation_stop_at':stop.isoformat(),'result':reply,'main_admitted':False}))

if __name__=='__main__':
    main()
