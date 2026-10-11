"""Fresh unchanged-clock cost/capacity and read-only AWS gates before boot."""
from __future__ import annotations
import concurrent.futures
import importlib.util
import json
import sys
from datetime import UTC,datetime,timedelta
from pathlib import Path
from ops import HERE
from controls import read,write_new
from operational_limits import effective_policy

def main():
    previous=HERE.parents[1]/'phase-8-continuation/v6/preflight.py'
    spec=importlib.util.spec_from_file_location('lookup',previous);assert spec and spec.loader
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m.HERE=HERE
    jobs={
      'plan':lambda:m.call('plan',['freetier','get-account-plan-state']),
      'hosts':lambda:m.call('hosts',['ec2','describe-instances','--instance-ids','i-057344e5372faf62f']),
      'volumes':lambda:m.call('volumes',['ec2','describe-volumes','--volume-ids','vol-09dbb42bbf607f5de']),
      'versions':lambda:m.call('versions',['s3api','list-object-versions','--bucket',m.BUCKET,'--prefix','exports/phase8/'+m.RUN+'/']),
      'compute':lambda:m.price('compute','AmazonEC2',{'regionCode':'ap-southeast-2','instanceType':'m7i-flex.large','operatingSystem':'Linux','tenancy':'Shared','preInstalledSw':'NA','capacitystatus':'Used'}),
      'disk':lambda:m.price('disk','AmazonEC2',{'regionCode':'ap-southeast-2','volumeApiName':'gp3','productFamily':'Storage'}),
      'ipv4':lambda:m.price('ipv4','AmazonVPC',{'regionCode':'ap-southeast-2','usagetype':'APS2-PublicIPv4:InUseAddress'}),
      's3':lambda:m.price('s3','AmazonS3',{'regionCode':'ap-southeast-2','volumeType':'Standard','productFamily':'Storage'})}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        tasks={n:pool.submit(f) for n,f in jobs.items()};data={n:f.result() for n,f in tasks.items()}
    rates={n:m.rates(data[n]) for n in ('compute','disk','ipv4','s3')}
    assert all(v in rates[n] for n,v in {'compute':.1197,'disk':.096,'ipv4':.005,'s3':.025}.items())
    actual=data['hosts']['Reservations'][0]['Instances'][0]
    assert actual['State']['Name']=='stopped'
    assert data['plan']['accountPlanType']=='FREE' and data['plan']['accountPlanStatus']=='ACTIVE'
    assert float(data['plan']['accountPlanRemainingCredits']['amount'])>=65
    assert not data['versions'].get('IsTruncated') and not data['versions'].get('NextToken')
    cloud=sum(v['Size'] for v in data['versions'].get('Versions',[]))
    prior=read(HERE.parents[1]/'phase-8-continuation/v9/estimates.json')
    policy=effective_policy(read(Path('E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete/original-launch-policy.json')))
    now=datetime.now(UTC);allowance=290*1380/1498;finish=now+timedelta(hours=allowance+2.5)
    cost=policy.committed_cost(finish)
    projected=prior['capacity_planning_bytes']+max(0,cloud-prior['current_cloud_all_versions_bytes'])+600*1024**2
    assert finish<policy.stop_at-timedelta(seconds=policy.admission_cutoff_seconds) and cost<60
    assert projected+policy.slot_capacity_reserve_bytes<policy.cloud_limit_bytes
    write_new(HERE/'feasibility.json',{'status':'PASS_CONDITIONAL','at_utc':now.isoformat(),
       'allowance_hours':allowance,'remaining':1380,'projected_shutdown_utc':finish.isoformat(),
       'projected_conservative_usd':cost,'guard_usd':60,'total_usd':65,'cloud_limit_bytes':policy.cloud_limit_bytes,
       'projected_evidence_bytes':projected,'all_version_evidence_bytes':cloud,'rates':rates,'plan':data['plan'],
       'original_deadline':policy.stop_at.isoformat(),'prior_spending_and_retained_storage_included':True,
       'all_original_elapsed_hours_charged_including_paused_hours':True,'clock_reset':False,
       'host':actual,'volumes':data['volumes'],'actual_main_admission':False})
    print(json.dumps({'status':'PASS_CONDITIONAL','cost':cost,'projected_shutdown':finish.isoformat(),'cloud_projection_gib':projected/1024**3}))

if __name__=='__main__':main()
