"""One read-only pooled-summary request; no scenarios, grading or campaign writes."""
from __future__ import annotations
import hashlib,importlib.util,json,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('recorded_read',ROOT/'artifacts/phase-8-continuation-deployment/v10/attempt2/read_control.py')
assert spec and spec.loader
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.HERE=HERE

def main():
    sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
    body=(HERE/'collect-summary.py').read_text(encoding='utf-8');compile(body,'collect-summary.py','exec')
    command="cd /opt/fyp-phase8-continuation-v12\nexport PYTHONDONTWRITEBYTECODE=1\ntimeout --signal=TERM --kill-after=5s 250s .venv/bin/python -B - <<'READ_SAVED_POOLED_ONLY'\n"+body+"\nREAD_SAVED_POOLED_ONLY\n"
    params={'commands':[command],'executionTimeout':['260']};r.record('pooled-parameters.json',params)
    sent=r.call('pooled-send',['ssm','send-command','--instance-ids','i-057344e5372faf62f','--document-name','AWS-RunShellScript','--parameters','file://'+str(HERE/'pooled-parameters.json'),'--timeout-seconds','60','--comment','Read-only pooled existing grades for scope-review draft; no campaign changes'])
    cid=sent['Command']['CommandId'];print('Read-only request '+cid,flush=True)
    for n in range(1,13):
        time.sleep(10)
        x=r.call('pooled-read'+str(n),['ssm','get-command-invocation','--command-id',cid,'--instance-id','i-057344e5372faf62f'])
        if x['Status']=='Success':
            result=json.loads(x['StandardOutputContent'].splitlines()[-1]);summary=result['summary']
            raw=json.dumps(summary,sort_keys=True,separators=(',',':')).encode()
            assert len(raw)==result['canonical_json_bytes'] and hashlib.sha256(raw).hexdigest()==result['summary_sha256']
            assert summary['available_grades']==summary['completed_originals'] and not summary['verification_failures']
            r.record('pooled-outcomes.json',summary)
            r.record('verification.json',{'status':'PASS_RECORDED_GRADE_EXTRACTION','summary_sha256':result['summary_sha256'],'bytes':len(raw),'collector_sha256':hashlib.sha256(body.encode()).hexdigest(),'grading_or_campaign_mutations':False,'fresh_archive_or_cloud_revalidation':False,'read_only_request':cid})
            print(json.dumps(summary,indent=2));return
        if x['Status'] in ('Failed','TimedOut','Cancelled'):raise RuntimeError('BOUNDED_EXTRACTION_FAILED_RETAINED:'+cid+':'+x.get('StandardErrorContent','')[-1000:])
    raise TimeoutError('READ_REQUEST_UNRESOLVED_NO_RESEND:'+cid)

if __name__=='__main__':main()
