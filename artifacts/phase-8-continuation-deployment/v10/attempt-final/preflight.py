"""Bounded fresh preboot reads and accepted feasibility; no boot or admission."""
import json
from datetime import UTC,datetime,timedelta
from ops import HERE,HOST,call,record

def main():
    host=call('preboot-host',['ec2','describe-instances','--instance-ids',HOST])
    instance=host['Reservations'][0]['Instances'][0]
    assert host['Reservations'][0]['OwnerId']=='803656589923' and instance['State']['Name']=='stopped'
    assert any(b['Ebs']['VolumeId']=='vol-09dbb42bbf607f5de' and not b['Ebs']['DeleteOnTermination'] for b in instance['BlockDeviceMappings'])
    security=call('preboot-security',['ec2','describe-security-groups','--group-ids',*[g['GroupId'] for g in instance['SecurityGroups']]])
    assert all(g['OwnerId']=='803656589923' and not g['IpPermissions'] for g in security['SecurityGroups'])
    plan=call('preboot-plan',['freetier','get-account-plan-state'])
    assert plan['accountId']=='803656589923' and plan['accountPlanType']=='FREE' and plan['accountPlanStatus']=='ACTIVE'
    versions=call('preboot-versions',['s3api','list-object-versions','--bucket','fyp-p82-20261005-018da1d6-803656589923',
        '--prefix','exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/','--max-keys','1000','--no-paginate'])
    assert versions['IsTruncated'] is False,'STORAGE_PAGINATION_INCOMPLETE'
    cloud_bytes=sum(v['Size'] for v in versions.get('Versions',[]))
    now=datetime.now(UTC);anchor=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=anchor+timedelta(hours=432)
    remaining=290*1355/1498;finish=now+timedelta(hours=remaining+2.5);uncertain=finish+timedelta(hours=24)
    rate=.1197+.005+160*.096/730;reserves=48*160*.096/730+80*.025+5+1.25
    forecast=lambda at:(at-anchor).total_seconds()/3600*rate+reserves
    projected=83218519158.73685+max(0,cloud_bytes-3066593484)
    assert uncertain<stop-timedelta(seconds=1800) and forecast(uncertain)<70 and forecast(stop)<75,'TIME_OR_COST_FEASIBILITY_STOP'
    assert projected+1073741824<85899345920,'FUTURE_STORAGE_PROJECTION_STOP'
    record('feasibility.json',{'status':'PASS_PREBOOT_NOT_READINESS','at':now.isoformat(),'cloud_bytes':cloud_bytes,'cloud_versions':len(versions.get('Versions',[])),
        'future_storage_projection_bytes':projected,'with_reservation_gib':(projected+1073741824)/1024**3,
        'remaining_allowance_hours':remaining,'preparation_shutdown_hours':2.5,'uncertainty_hours':24,
        'completion_forecast_usd':forecast(finish),'uncertainty_forecast_usd':forecast(uncertain),'full_deadline_forecast_usd':forecast(stop),
        'completion_utc':finish.isoformat(),'uncertain_completion_utc':uncertain.isoformat(),'absolute_stop':stop.isoformat(),
        'accounting_unchanged':'All elapsed stopped/running history, full80GiB S3 month,48h root and fixed request/handover reserves; no billed-cost substitution',
        'fresh_metadata_growth_and_capacity_check_still_required':True,'credits':plan['accountPlanRemainingCredits']})
    template=json.loads((HERE.parent/'preparation-schedule-input.json').read_text())
    template.update(Name='retained-host-v10-final-prep-20261013',ScheduleExpression='at('+(now+timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S')+')')
    record('preparation-input.json',template)
    print(json.dumps({'status':'PASS_PREBOOT_FEASIBILITY','completion_usd':forecast(finish),'reserve_usd':forecast(uncertain),'storage_gib':(projected+1073741824)/1024**3,'guard':template['ScheduleExpression']}))

if __name__=='__main__':main()
