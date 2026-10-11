"""Verified retained-host authorization and independent pre-boot stop guard."""
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ops import HERE, aws
from controls import canonical, hash_file, read, write_new
from operational_limits import effective_policy, LIMITS_SHA256

INSTANCE='i-057344e5372faf62f'
ROOT='vol-09dbb42bbf607f5de'
GROUP='fyp-p85-v5'
ROLE='FYP-p85-v5-preparation-stop'
NAME='retained-host-v7-attempt3-preparation-stop-20261009'


def main() -> None:
    selection=read(HERE/'wrapper-selection-check.json')
    assert selection['status']=='PASS_BEFORE_BOOT_DEPLOYMENT_ORDER'
    assert hash_file(HERE/'quiesce-old-units-before-readiness.sh')==selection['wrapper_sha256']
    repo=HERE.parents[2]
    frozen=repo/'artifacts/phase-8-continuation-freeze/v7'
    freeze=read(frozen/'freeze-verification.json')
    assert freeze['status']=='PASS' and freeze['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
    assert hash_file(frozen/'freeze-manifest.json')==freeze['freeze_manifest_sha256']
    key=(Path.home()/'.fyp-research/phase8-owner/phase84-final-v2/owner.key').read_bytes()
    manifest=read(frozen/'freeze-manifest.json');attestation=read(frozen/'freeze-attestation.json')
    assert hmac.compare_digest(attestation['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
    feasible=read(HERE/'feasibility.json')
    assert feasible['status']=='PASS_CONDITIONAL' and (datetime.now(UTC)-datetime.fromisoformat(feasible['at_utc'])).total_seconds()<600
    policy=effective_policy(read(Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    now=datetime.now(UTC);finish=now+timedelta(hours=feasible['allowance_hours']+2+.5)
    assert policy.committed_cost(finish)<60 and finish<policy.stop_at
    binding={'kind':'EXPLICIT_HUMAN_AUTHORIZED_RETAINED_HOST_V7_DEPLOYMENT','at_utc':now.isoformat(),
             'instance_id':INSTANCE,'root_volume_id':ROOT,'package_hash':freeze['package_hash'],
             'archive_sha256':freeze['archive_sha256'],'freeze_manifest_sha256':freeze['freeze_manifest_sha256'],
             'operational_limits_sha256':LIMITS_SHA256,'run_id':policy.run_id,'backed_up':82,'planned':1418,
             'next_sequence':83,'next_execution_id':'01a11705-11f1-792b-ae1e-36bfc6773842',
             'human_acceptance_sha256':hash_file(HERE/'human-acceptance.json'),
             'authority':'Verbatim separately authorized deployment after successful freeze, human-acceptance.json',
             'guard_usd':60,'total_usd':65,'original_deadline':policy.stop_at.isoformat(),'actual_launch':False}
    write_new(HERE/'actual-deployment-binding.json',binding)
    write_new(HERE/'deployment-launch-authorization-statement.json', {**binding,'actual_admission':False,
              'condition':'All reviewed live gates, prelaunch/readiness/complete backups must pass'})
    host=aws('prestart-host',['ec2','describe-instances','--instance-ids',INSTANCE])['Reservations'][0]['Instances'][0]
    volume=aws('prestart-volume',['ec2','describe-volumes','--volume-ids',ROOT])['Volumes'][0]
    security=aws('prestart-security',['ec2','describe-security-groups','--group-ids',host['SecurityGroups'][0]['GroupId']])
    assert host['State']['Name']=='stopped' and host['InstanceType']=='m7i-flex.large'
    assert volume['Size']==160 and volume['Encrypted'] and volume['Attachments'][0]['InstanceId']==INSTANCE and not volume['Attachments'][0]['DeleteOnTermination']
    assert not security['SecurityGroups'][0]['IpPermissions'] and host['MetadataOptions']['HttpTokens']=='required'
    assert {t['Key']:t['Value'] for t in host['Tags']}['research.owner']==policy.run_id
    group=aws('preparation-group-read',['scheduler','get-schedule-group','--name',GROUP])
    role=aws('preparation-role-read',['iam','get-role','--role-name',ROLE])['Role']
    permission=aws('preparation-policy-read',['iam','get-role-policy','--role-name',ROLE,'--policy-name','StopOnlyRetainedCampaignHost'])['PolicyDocument']
    assert group['State']=='ACTIVE'
    assert role['AssumeRolePolicyDocument']==read(HERE.parent/'v5/preparation-trust.json')
    assert permission==read(HERE.parent/'v5/preparation-permission.json')
    simulation=aws('preparation-permission-simulation',['iam','simulate-principal-policy','--policy-source-arn',role['Arn'],
               '--action-names','ec2:StopInstances','--resource-arns',permission['Statement'][0]['Resource'],
               '--context-entries','ContextKeyName=aws:RequestedRegion,ContextKeyValues=ap-southeast-2,ContextKeyType=string'])
    assert simulation['EvaluationResults'] and all(r['EvalDecision']=='allowed' and r['OrganizationsDecisionDetail']['AllowedByOrganizations'] for r in simulation['EvaluationResults'])
    stop=datetime.now(UTC)+timedelta(hours=2)
    target={'Arn':'arn:aws:scheduler:::aws-sdk:ec2:stopInstances','RoleArn':role['Arn'],
            'Input':json.dumps({'InstanceIds':[INSTANCE]}),'RetryPolicy':{'MaximumEventAgeInSeconds':300,'MaximumRetryAttempts':3}}
    write_new(HERE/'preparation-target.json',target)
    expression='at('+stop.strftime('%Y-%m-%dT%H:%M:%S')+')'
    aws('preparation-schedule-create',['scheduler','create-schedule','--name',NAME,'--group-name',GROUP,
          '--schedule-expression',expression,'--schedule-expression-timezone','UTC','--state','ENABLED',
          '--flexible-time-window','{"Mode":"OFF"}','--target','file://'+str(HERE/'preparation-target.json')])
    actual=aws('preparation-schedule-read',['scheduler','get-schedule','--name',NAME,'--group-name',GROUP])
    assert actual['State']=='ENABLED' and actual['Target']==target and actual['ScheduleExpression']==expression and actual['ScheduleExpressionTimezone']=='UTC' and actual['FlexibleTimeWindow']['Mode']=='OFF'
    write_new(HERE/'prestart-independent-stop-verification.json',{'status':'PASS_CONFIGURATION_AND_REGION_CONTEXT_PERMISSION_SIMULATION',
              'at_utc':datetime.now(UTC).isoformat(),'stop_at_utc':stop.isoformat(),'instance_id':INSTANCE,
              'schedule':actual,'role_scoped_to_exact_host':True,'existing_role_trust_verified':True,'delivery_not_hard_realtime':True})
    # Replacement is verified before disabling only exact owned, obsolete preparation guards.
    schedules=aws('preparation-schedules-inventory',['scheduler','list-schedules','--group-name',GROUP])
    obsolete=[]
    known={'retained-host-preparation-stop','retained-host-v7-preparation-stop-20261009','retained-host-v7-attempt2-preparation-stop-20261009'}
    for entry in schedules.get('Schedules',[]):
        if entry['Name']==NAME:
            continue
        detail=aws('old-guard-'+entry['Name']+'-read',['scheduler','get-schedule','--name',entry['Name'],'--group-name',GROUP])
        if entry['Name'] not in known:
            if detail['State']=='ENABLED' and detail['Target'].get('RoleArn')==role['Arn'] and json.loads(detail['Target'].get('Input','{}')).get('InstanceIds')==[INSTANCE]:
                raise ValueError('UNREVIEWED_OWNED_PREPARATION_SCHEDULE')
            continue
        assert detail['Target']['Arn']==target['Arn'] and detail['Target']['RoleArn']==role['Arn']
        assert json.loads(detail['Target']['Input'])=={'InstanceIds':[INSTANCE]}
        if detail['State']=='ENABLED':
            payload={k:detail[k] for k in ('Name','GroupName','ScheduleExpression','ScheduleExpressionTimezone','FlexibleTimeWindow','Target')}
            for optional in ('Description','StartDate','EndDate','KmsKeyArn','ActionAfterCompletion'):
                if optional in detail:
                    payload[optional]=detail[optional]
            payload['State']='DISABLED'
            payload_path=HERE/(entry['Name']+'-disable.json')
            write_new(payload_path,payload)
            aws('old-guard-'+entry['Name']+'-disable',['scheduler','update-schedule','--cli-input-json','file://'+str(payload_path)])
            disabled=aws('old-guard-'+entry['Name']+'-readback',['scheduler','get-schedule','--name',entry['Name'],'--group-name',GROUP])
            assert disabled['State']=='DISABLED' and disabled['Target']==detail['Target']
        obsolete.append({'name':entry['Name'],'prior_state':detail['State'],'new_state':'DISABLED'})
    replacement=aws('preparation-replacement-final-read',['scheduler','get-schedule','--name',NAME,'--group-name',GROUP])
    assert replacement['State']=='ENABLED' and replacement['Target']==target
    write_new(HERE/'superseded-preparation-guards.json',{'status':'PASS','replacement_verified_before_changes':True,'obsolete':obsolete,'hard_deadline_guards_modified':False})
    # Original clock and signed cost model remain active even during preparation.
    start=datetime.now(UTC)
    assert policy.committed_cost(start+timedelta(hours=feasible['allowance_hours']+2+.5))<60
    write_new(HERE/'start-request-anchor.json',{'at_utc':start.isoformat(),'preparation_stop_at':stop.isoformat(),
              'original_deadline':policy.stop_at.isoformat(),'clock_reset':False})
    response=aws('retained-host-start',['ec2','start-instances','--instance-ids',INSTANCE])
    print(json.dumps({'freeze_manifest_sha256':freeze['freeze_manifest_sha256'],'start_utc':start.isoformat(),
                     'preparation_stop_at':stop.isoformat(),'response':response,'actual_admission':False},indent=2))


if __name__=='__main__':
    main()
