"""Bind returned control evidence, unchanged allowance and fresh stop guard."""
from __future__ import annotations
import hashlib
import json
from datetime import UTC,datetime,timedelta
from pathlib import Path
from ops import HERE,HOST,record,call

def read(path: Path) -> dict:
    return json.loads(path.read_text())

def main() -> None:
    bundle=Path('C:/Users/syeda/Downloads/control-evidence.tar.gz')
    assert bundle.stat().st_size==207205 and hashlib.sha256(bundle.read_bytes()).hexdigest()=='3a4744dbbffd90d7c233a2f7117e5743bfe3dd891309f7ff62771b844e3bbd70'
    returned=Path('D:/FYP-ResearchBackups/v10-control/returned-attempt2')
    summary=read(returned/'summary.json')
    inventory=read(returned/'versions-1-result.json')['result']
    assert inventory['IsTruncated'] is False and sum(v['Size'] for v in inventory['Versions'])==summary['cloud_all_versions_bytes']
    identity=read(returned/'identity-result.json')['result'];assert identity['Account']=='803656589923'
    host=read(returned/'host-result.json')['result']['Reservations'][0]
    assert host['OwnerId']=='803656589923' and host['Instances'][0]['InstanceId']==HOST and host['Instances'][0]['State']['Name']=='stopped'
    assert all(not read(returned/n)['result'].get('NextToken') for n in ('commands-2-result.json','cloudtrail-1-result.json','invocations-result.json'))
    local=read(HERE.parent/'returned-control/identity-result.json');assert local['exit']==0 and local['result']['Account']=='803656589923'
    assert read(HERE.parent/'returned-control/ssm-result.json')['exit']==0
    now=datetime.now(UTC)
    assert now-datetime.fromisoformat(summary['at'])<timedelta(minutes=30),'RETURNED_CONTROL_TOO_OLD'
    anchor=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=anchor+timedelta(hours=432)
    remaining=290*1355/1498;finish=now+timedelta(hours=remaining+2.5);uncertain=finish+timedelta(hours=24)
    rate=.1197+.005+160*.096/730;reserves=48*160*.096/730+80*.025+5+1.25
    forecast=lambda t:(t-anchor).total_seconds()/3600*rate+reserves
    previous=read(HERE.parents[2]/'phase-8-continuation/classifier-145-v2/feasibility-refresh.json')['storage']
    projection=previous['capacity_projection_bytes']+max(0,summary['cloud_all_versions_bytes']-previous['cloud_all_version_bytes'])
    assert uncertain<stop-timedelta(seconds=1800) and forecast(uncertain)<70 and forecast(stop)<75,'TIME_OR_COST_FEASIBILITY_STOP'
    assert projection+1073741824<85899345920,'FUTURE_STORAGE_PROJECTION_STOP'
    expiry=datetime.fromisoformat('2026-10-12T17:14:50.228195+00:00')
    assert now>expiry
    record('returned-control-verification.json',{'status':'PASS_RETURNED_HASH_AND_READS_NOT_READINESS',
        'bundle_sha256':'3a4744dbbffd90d7c233a2f7117e5743bfe3dd891309f7ff62771b844e3bbd70','bytes':207205,
        'original_execution_status':'UNKNOWN','empty_lists_not_proof_of_nonexecution':True,
        'expiry_fence':expiry.isoformat(),'fence_basis':'60+1200 delivery timeout; extra1200 execution,90 caller,300 uncertainty; stopped host; root effect inspection mandatory before writes',
        'cloud_versions':summary['cloud_versions'],'cloud_bytes':summary['cloud_all_versions_bytes'],
        'source_version':summary['source_version_verified'],'at':now.isoformat()})
    record('feasibility.json',{'status':'PASS_BEFORE_BOOT_NOT_LIVE_CAPACITY','at':now.isoformat(),
        'remaining':1355,'remaining_allowance_hours':remaining,'preparation_shutdown_hours':2.5,'uncertainty_hours':24,
        'completion_utc':finish.isoformat(),'uncertain_completion_utc':uncertain.isoformat(),
        'completion_forecast_usd':forecast(finish),'uncertainty_forecast_usd':forecast(uncertain),'full_deadline_forecast_usd':forecast(stop),
        'accepted_rates_unchanged':True,'all_paused_elapsed_history_included':True,'actual_billing_not_substituted':True,
        'future_storage_projection_bytes':projection,'future_storage_plus_reservation_bytes':projection+1073741824,
        'cloud_limit_bytes':85899345920,'all_original_1500_slot_slope_metadata_allowances_preserved':True,
        'further_metadata_growth_must_be_measured_before_admission':True,'stop_at':stop.isoformat(),
        'credits':summary['plan']['accountPlanRemainingCredits']})
    template=read(HERE.parent/'preparation-schedule-input.json')
    template.update(Name='retained-host-v10-guarded-resume-stop-20261012',
                    ScheduleExpression='at('+ (now+timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S')+')')
    record('preparation-input.json',template)
    print(json.dumps({'status':'PASS_PREBOOT_PLAN','completion_usd':forecast(finish),'uncertain_usd':forecast(uncertain),
                      'projected_storage_with_reservation_gib':(projection+1073741824)/1024**3,'preparation_stop':template['ScheduleExpression']}))

if __name__=='__main__':main()
