"""One owned recovery stop guard; preserve previous schedules and authority."""
from __future__ import annotations
import json
from datetime import UTC,datetime,timedelta
from pathlib import Path
from control import ops,HERE

def main():
    r=ops.r
    absolute=json.loads((HERE/'current-absolute-result.json').read_bytes())['result']
    assert absolute['State']=='ENABLED' and absolute['ScheduleExpression']=='at(2026-10-26T12:00:00)'
    assert json.loads(absolute['Target']['Input'])=={'InstanceIds':[ops.HOST]}
    p={k:absolute[k] for k in ('Name','GroupName','State','ScheduleExpression','ScheduleExpressionTimezone','FlexibleTimeWindow','Target','ActionAfterCompletion')}
    p['Name']='retained-host-v12-recovery1315-stop-20261023'
    at=datetime.now(UTC)+timedelta(minutes=60)
    p['ScheduleExpression']='at('+at.strftime('%Y-%m-%dT%H:%M:%S')+')'
    r.record('preparation-schedule.json',p)
    r.call('create-preparation',['scheduler','create-schedule','--cli-input-json','file://'+str(HERE/'preparation-schedule.json'),'--client-token','v12-recovery1315-20261023'])
    found=r.call('verify-preparation',['scheduler','get-schedule','--group-name',p['GroupName'],'--name',p['Name']])
    assert all(found[k]==v for k,v in p.items())
    schedules=r.call('owned-schedules',['scheduler','list-schedules','--group-name',p['GroupName'],'--max-results','100','--no-paginate'])
    assert not schedules.get('NextToken')
    assert {x['Name'] for x in schedules['Schedules'] if x['State']=='ENABLED'}=={p['Name'],absolute['Name']}
    authority={'kind':'EXPLICIT_REPAIR_AND_RESUME','user_instruction':'yeah repair the isue and reusme the checks','at':datetime.now(UTC).isoformat(),'source_package':'cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d','frozen_code_unchanged':True,'backed_up':1315,'planned':185,'next_sequence':1316,'next_execution':'01a11705-11f4-7875-b6f4-62729851bd64','guard_usd':76,'ceiling_usd':77,'stop_at':'2026-10-26T12:00:00Z','caps_gib':80,'expires_at':at.isoformat(),'independent_preparation':found,'absolute':absolute,'retry_environment':{'AWS_METADATA_SERVICE_TIMEOUT':'3','AWS_METADATA_SERVICE_NUM_ATTEMPTS':'3'},'no_replay_or_regrade':True,'same_host_and_boot':True,'reuse_frozen_readiness_and_launch':True,'additional_recovery_backup_bound_bytes':1610612736,'forecast_allowances_unchanged':True}
    r.record('recovery-authorization.json',authority)
    print('PASS_OWNED_PREPARATION_GUARD_INDEPENDENTLY_VERIFIED '+at.isoformat())

if __name__=='__main__':main()
