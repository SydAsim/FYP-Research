"""Minimal owned-root resize within existing up-to192GiB authorization and74/75 limits."""
import json,math,sys
from pathlib import Path
from datetime import datetime,UTC,timedelta
from ops import HERE,recorder

def main():
    r=json.loads((HERE/'live-checks-read3-result.json').read_text())['result'];assert r['Status']=='Success'
    v=json.loads(r['StandardOutputContent'].splitlines()[-1]);sample=v['resource_sample']
    required=(v['backup_full_projection_bytes']-sample['backup_bytes'])+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3
    short=max(0,required-sample['system_free_bytes']);added=math.ceil(short/(.95*1024**3));size=167+added
    assert added>0 and size<=192
    now=datetime.now(UTC);stop=datetime(2026,10,26,tzinfo=UTC);retain=stop+timedelta(hours=48)
    extra=added*.096/730*(retain-now).total_seconds()/3600
    old=json.loads((HERE/'preboot-feasibility.json').read_text())
    start=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');rate=.1197+.005+160*.096/730;reserves=48*160*.096/730+80*.025+5+1.25
    uncertain=now+timedelta(hours=884*262.31642189586114/1355+2.5+24)
    totalextra=old['extra_root_reserve']+extra
    cost=lambda t:(t-start).total_seconds()/3600*rate+reserves+totalextra
    assert uncertain<stop-timedelta(minutes=30) and cost(uncertain+timedelta(minutes=30))<74 and cost(stop)<75
    fence=start+timedelta(hours=(74-reserves-totalextra)/rate-.5)
    fence=min(fence,stop-timedelta(minutes=30))
    plan={'status':'PASS_BEFORE_OWNED_ROOT_MODIFICATION','at':now.isoformat(),'volume_id':'vol-09dbb42bbf607f5de','old_size_gib':167,'new_size_gib':size,'added_gib':added,'required_free_bytes':required,'measured_free_bytes':sample['system_free_bytes'],'shortfall_bytes':short,'usable_fraction':.95,'included_final_margin_bytes':1024**3,'working_cap_bytes':50*1024**3,'admission_free_bytes':20*1024**3,'full_backup_projection_bytes':v['backup_full_projection_bytes'],'new_storage_reserve_usd':extra,'previous_extra_storage_reserve_usd':old['extra_root_reserve'],'total_extra_storage_reserve_usd':totalextra,'uncertainty_cost_usd':cost(uncertain),'uncertainty_plus_lookahead_usd':cost(uncertain+timedelta(minutes=30)),'full_deadline_cost_usd':cost(stop),'external_admission_fence':fence.isoformat(),'full_stop':stop.isoformat(),'accepted_retention_until':retain.isoformat(),'rate_usd_gib_month':.096,'authority':'Prior explicit smallest-justified root growth up to192GiB, persistent authorization; current continuation74/75 limits unchanged','no_evidence_deletion':True,'backup_caps_unchanged':True}
    recorder.record('root-resize-plan.json',plan)
    current=recorder.call('resize-current-volume',['ec2','describe-volumes','--volume-ids',plan['volume_id']])['Volumes'][0]
    assert current['Size']==167 and current['Encrypted'] and current['Attachments'][0]['InstanceId']=='i-057344e5372faf62f'
    prior=recorder.call('resize-prior-modification',['ec2','describe-volumes-modifications','--volume-ids',plan['volume_id']])['VolumesModifications']
    assert not prior or all(p['ModificationState']=='completed' for p in prior)
    result=recorder.call('resize-owned-root',['ec2','modify-volume','--volume-id',plan['volume_id'],'--size',str(size)])
    print(json.dumps({'plan':plan,'modification':result}))
if __name__=='__main__':main()
