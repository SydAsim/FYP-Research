"""Four bounded read-only checks; failures prohibit boot."""
import json
from read_control import call, record, HERE

def main() -> None:
    proof=json.loads((HERE.parent/'source-proof.json').read_text())
    record('preflight-plan.json', {'requests_max':4,'process_limit_per_request_seconds':45,
        'retry_count':0,'no_host_mutations':True,'all_version_inventory_must_not_be_truncated':True})
    calls=[
        ('plan',['freetier','get-account-plan-state']),
        ('source-head',['s3api','head-object','--bucket',proof['bucket'],'--key',proof['key'],
                       '--version-id',proof['version_id'],'--checksum-mode','ENABLED']),
        ('versions',['s3api','list-object-versions','--bucket',proof['bucket'],
            '--prefix','exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/',
            '--max-keys','1000','--no-paginate']),
        ('absolute',['scheduler','get-schedule','--group-name','fyp-p85-v5',
            '--name','retained-host-v10-absolute-stop-20261025']),
    ]
    for label,args in calls:
        try:
            data=call(label,args)
            print(json.dumps({'label':label,'status':'READ_OK','truncated':data.get('IsTruncated',False)}),flush=True)
        except RuntimeError:
            print(json.dumps({'label':label,'status':'FAILED_PRESERVED_NO_BOOT'}),flush=True)

if __name__=='__main__':
    main()
