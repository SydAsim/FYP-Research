"""Bind signed external gates only to successful actual preparation evidence."""
import hashlib,hmac,json
from datetime import UTC,datetime,timedelta
from pathlib import Path
from ops import HERE,aws
from controls import canonical,read,write_new,hash_file

def main():
    invocation=read(HERE/'live-checks-attempt3-status2-result.json')['result']
    assert invocation['Status']=='Success' and invocation['ResponseCode']==0
    live=json.loads(invocation['StandardOutputContent'])
    assert live['status']=='PASS' and live['originals_verified']==82 and live['planned']==1418 and live['driver_calls']==0
    quiet=json.loads(read(HERE/'quiesce-old-units-status1-result.json')['result']['StandardOutputContent'])
    assert quiet['status']=='PASS' and quiet['old_pause_preserved'] and quiet['all_1500_original_rows_unchanged']
    host=aws('reuse-running-host',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f'])['Reservations'][0]['Instances'][0]
    volume=aws('reuse-retained-volume',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de'])['Volumes'][0]
    security=aws('reuse-security',['ec2','describe-security-groups','--group-ids',host['SecurityGroups'][0]['GroupId']])
    versioning=aws('reuse-bucket-versioning',['s3api','get-bucket-versioning','--bucket','fyp-p82-20261005-018da1d6-803656589923'])
    scheduler=aws('reuse-preparation-guard',['scheduler','get-schedule','--group-name','fyp-p85-v5','--name','retained-host-v7-attempt3-preparation-stop-20261009'])
    assert host['State']['Name']=='running' and host['InstanceType']=='m7i-flex.large'
    assert host['MetadataOptions']['HttpTokens']=='required' and not security['SecurityGroups'][0]['IpPermissions']
    assert volume['Size']==160 and volume['Encrypted'] and volume['Attachments'][0]['InstanceId']==host['InstanceId'] and not volume['Attachments'][0]['DeleteOnTermination']
    assert {x['Key']:x['Value'] for x in host['Tags']}['research.owner']=='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
    assert versioning['Status']=='Enabled'
    expected=read(HERE/'preparation-target.json')
    assert scheduler['State']=='ENABLED' and scheduler['Target']==expected and scheduler['ScheduleExpressionTimezone']=='UTC'
    assert read(HERE/'superseded-preparation-guards.json')['status']=='PASS'
    frozen=read(HERE.parents[1]/'phase-8-continuation-freeze/v7/freeze-verification.json')
    assert frozen['status']=='PASS'
    feasible=read(HERE/'feasibility.json')
    from operational_limits import effective_policy
    policy=effective_policy(read(Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    now=datetime.now(UTC);finish=now+timedelta(hours=feasible['allowance_hours']+2+.5)
    assert finish<policy.stop_at and policy.committed_cost(finish)<60
    checks={'freeze_verified':True,'explicit_deployment_authorization':True,'host_ownership':True,'prestart_independent_preparation_stop':True,'source_archive_and_members':True,'dependency_records_and_versions':True,'same_instance_and_root':True,'no_inbound_access':True,'original_deadline_and_budget_fit':True}
    body={'at_utc':now.isoformat(),'expires_at':(now+timedelta(minutes=30)).isoformat(),'package_hash':frozen['package_hash'],'instance_id':host['InstanceId'],'checks':checks,'evidence':{'live_checks':hash_file(HERE/'live-checks-attempt3-status2-result.json'),'quiescence':hash_file(HERE/'quiesce-old-units-status1-result.json'),'authorization':hash_file(HERE/'human-acceptance.json'),'prestart_stop':hash_file(HERE/'prestart-independent-stop-verification.json'),'current_scheduler':scheduler,'host':host,'volume':volume,'security':security,'versioning':versioning,'feasibility':feasible}}
    key=(Path.home()/'.fyp-research/phase8-owner/phase84-final-v2/owner.key').read_bytes()
    proof={**body,'signature':hmac.new(key,canonical(body),'sha256').hexdigest()}
    write_new(HERE/'external-reuse-gates.json',proof)
    header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
    prefix="python3 - <<'GATES'\nfrom pathlib import Path\np=Path('/var/lib/p8-continuation-v7/deployment/external-reuse-gates-attempt3.json')\nwith p.open('x') as f:f.write("+repr((HERE/'external-reuse-gates.json').read_text())+")\nGATES\n"
    command='timeout --signal=TERM --kill-after=5s 180s .venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/reuse_prepare.py --root /var/lib/p8-continuation-v7/run --external-gates /var/lib/p8-continuation-v7/deployment/external-reuse-gates-attempt3.json\n'
    with (HERE/'prepare-metadata-attempt3.sh').open('x',encoding='utf-8',newline='\n') as out:out.write(header+prefix+command)
    print('Actual signed preparation gates PASS; metadata wrapper prepared; no admission')

if __name__=='__main__':main()
