"""Finite read-only state/pricing/inventory refresh; no paid Cost Explorer queries."""
from __future__ import annotations
import concurrent.futures
import importlib.util
import json
import sys
from pathlib import Path
from prepare import HERE, write

previous=HERE.parent/'v6/preflight.py'
spec=importlib.util.spec_from_file_location('previous_preflight',previous)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
spec.loader.exec_module(module)
module.HERE=HERE
RUN=module.RUN

def main() -> None:
    jobs={
      'plan':lambda:module.call('plan',['freetier','get-account-plan-state']),
      'hosts':lambda:module.call('hosts',['ec2','describe-instances','--filters','Name=tag:research.owner,Values='+RUN]),
      'volumes':lambda:module.call('volumes',['ec2','describe-volumes','--filters','Name=tag:research.owner,Values='+RUN]),
      'versions':lambda:module.call('versions',['s3api','list-object-versions','--bucket',module.BUCKET,'--prefix','exports/phase8/'+RUN+'/']),
      'compute':lambda:module.price('compute','AmazonEC2',{'regionCode':'ap-southeast-2','instanceType':'m7i-flex.large','operatingSystem':'Linux','tenancy':'Shared','preInstalledSw':'NA','capacitystatus':'Used'}),
      'disk':lambda:module.price('disk','AmazonEC2',{'regionCode':'ap-southeast-2','volumeApiName':'gp3','productFamily':'Storage'}),
      'ipv4':lambda:module.price('ipv4','AmazonVPC',{'regionCode':'ap-southeast-2','usagetype':'APS2-PublicIPv4:InUseAddress'}),
      's3':lambda:module.price('s3','AmazonS3',{'regionCode':'ap-southeast-2','volumeType':'Standard','productFamily':'Storage'}),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results={n:pool.submit(f) for n,f in jobs.items()}
        data={n:f.result() for n,f in results.items()}
    hosts=[h for r in data['hosts']['Reservations'] for h in r['Instances']]
    current=next(h for h in hosts if h['InstanceId']=='i-057344e5372faf62f')
    assert current['State']['Name']=='stopped'
    assert not any(h['State']['Name'] in ('pending','running') for h in hosts)
    rates={n:module.rates(data[n]) for n in ('compute','disk','ipv4','s3')}
    assert all(v in rates[n] for n,v in {'compute':.1197,'disk':.096,'ipv4':.005,'s3':.025}.items())
    versions=data['versions']
    assert not versions.get('NextToken')
    write(HERE/'aws-stopped-readonly.json',{'State':'stopped','instance_id':current['InstanceId'],'plan':data['plan'],'rates':rates,'all_version_evidence_bytes':sum(v['Size'] for v in versions.get('Versions',[])),'versions':len(versions.get('Versions',[])),'retained_volumes':data['volumes'],'paid_cost_explorer_calls':0,'AWS_mutations':0})
    print(json.dumps({'host':'stopped','rates':rates,'bytes':sum(v['Size'] for v in versions.get('Versions',[])),'plan':data['plan']},indent=2))

if __name__=='__main__':main()
