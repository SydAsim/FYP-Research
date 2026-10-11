"""Prepare read-only price/credit checks and accepted-policy arithmetic."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
previous=(HERE.parents[1]/'phase-8-continuation/v6/preflight.py').read_text()
head=previous[:previous.index('def main() -> None:')]
head=head.replace('p8v6','p8v7').replace('from handover import ContinuationPolicy', 'from operational_limits import effective_policy')
body='''def main() -> None:
    jobs = {
        "plan": lambda: call("plan", ["freetier", "get-account-plan-state"]),
        "hosts": lambda: call("hosts", ["ec2", "describe-instances", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "volumes": lambda: call("volumes", ["ec2", "describe-volumes", "--filters", "Name=tag:research.owner,Values=" + RUN]),
        "versions": lambda: call("versions", ["s3api", "list-object-versions", "--bucket", BUCKET, "--prefix", "exports/phase8/" + RUN + "/"]),
        "compute": lambda: price("compute", "AmazonEC2", {"regionCode": "ap-southeast-2", "instanceType": "m7i-flex.large", "operatingSystem": "Linux", "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"}),
        "disk": lambda: price("disk", "AmazonEC2", {"regionCode": "ap-southeast-2", "volumeApiName": "gp3", "productFamily": "Storage"}),
        "ipv4": lambda: price("ipv4", "AmazonVPC", {"regionCode": "ap-southeast-2", "usagetype": "APS2-PublicIPv4:InUseAddress"}),
        "s3": lambda: price("s3", "AmazonS3", {"regionCode": "ap-southeast-2", "volumeType": "Standard", "productFamily": "Storage"}),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        running = {name: pool.submit(fn) for name, fn in jobs.items()}
        data = {name: future.result() for name, future in running.items()}
    actual_rates={name:rates(data[name]) for name in ("compute","disk","ipv4","s3")}
    expected={"compute":.1197,"disk":.096,"ipv4":.005,"s3":.025}
    assert all(v in actual_rates[k] for k,v in expected.items()), "FROZEN_PRICE_ASSUMPTION_DRIFT"
    hosts=[i for r in data['hosts']['Reservations'] for i in r['Instances']]
    current=next(h for h in hosts if h['InstanceId']=='i-057344e5372faf62f')
    assert current['State']['Name']=='stopped'
    assert not any(h['State']['Name'] in ('running','pending') for h in hosts)
    assert data['plan']['accountPlanType']=='FREE' and data['plan']['accountPlanStatus']=='ACTIVE'
    assert float(data['plan']['accountPlanRemainingCredits']['amount'])>=65
    assert not data['versions'].get('IsTruncated',False), "INCOMPLETE_CLOUD_INVENTORY"
    cloud_bytes=sum(v['Size'] for v in data['versions'].get('Versions',[]))
    prior=read(HERE.parents[1]/'phase-8-continuation/v7/estimates.json')
    policy=effective_policy(read(RUNTIME/'original-launch-policy.json'))
    now=datetime.now(UTC);finish=now+timedelta(hours=prior['reviewed_remaining_hours']+2+.5)
    cost=policy.committed_cost(finish)
    elapsed=(now-datetime.fromisoformat(prior['at_utc'])).total_seconds()/3600
    explicit=prior['projected_explicit_resources_usd']+elapsed*160*.096/730
    projected_bytes=prior['capacity_planning_bytes']+max(0,cloud_bytes-prior['existing_cloud_all_versions_bytes'])
    status='PASS_CONDITIONAL' if cost<60 and explicit<60 and finish<policy.stop_at and projected_bytes+policy.slot_capacity_reserve_bytes<policy.cloud_limit_bytes else 'FAIL_DO_NOT_START'
    result={'status':status,'at_utc':now.isoformat(),'original_deadline':policy.stop_at.isoformat(),
            'clock_reset':False,'remaining':1418,'allowance_hours':prior['reviewed_remaining_hours'],
            'preparation_hours':2,'shutdown_hours':.5,'projected_shutdown_utc':finish.isoformat(),
            'projected_conservative_usd':cost,'projected_explicit_usd':explicit,'guard_usd':60,'total_usd':65,
            'prior_spending_and_retained_storage_included':True,'basis':str(HERE.parents[1]/'phase-8-continuation/v7/estimates.json'),
            'rates':actual_rates,'plan':data['plan'],'all_version_evidence_bytes':cloud_bytes,
            'projected_evidence_bytes':projected_bytes,'cloud_limit_bytes':policy.cloud_limit_bytes,
            'host':current,'volumes':data['volumes'],'actual_main_admission':False}
    write_new(HERE/'feasibility.json',result)
    print(json.dumps({k:result[k] for k in ('status','at_utc','projected_shutdown_utc','projected_conservative_usd','projected_explicit_usd','projected_evidence_bytes','all_version_evidence_bytes','plan')},indent=2))
    if status!='PASS_CONDITIONAL':raise SystemExit(1)

if __name__=='__main__':
    main()
'''
(HERE/'preflight.py').write_text(head+body,encoding='utf-8')
print('Read-only preflight prepared')
