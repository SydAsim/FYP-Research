"""Correct only external activation order; preserve failed request and frozen v12."""
import ast,base64,difflib,gzip,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    failed=json.loads((H/'release-v12-read1-result.json').read_bytes())['result']
    assert failed['Status']=='Failed' and 'INDEPENDENT_HOST_CONTROLS_REQUIRED' in failed['StandardErrorContent']
    progress=sorted((H/'progress').glob('*/summary.json'))[-1]
    state=json.loads(progress.read_bytes())
    assert state['counts']=={'BACKED_UP':1297,'PLANNED':203} and not state['active'] and state['pause']['reason']=='PROTOCOL_STOP'
    assert state['next_planned']['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028'
    assert 'ActiveState=active' not in state['units']
    source=(H/'host_deployment_projection_v2.py').read_text()
    before="verify_clock(ROOT,a.policy);verify_host_timer(ROOT)\n    cmd(['systemctl','start','fyp-phase8-watchdog.service'])"
    after="verify_clock(ROOT,a.policy)\n    cmd(['systemctl','start','fyp-phase8-watchdog.service'])\n    verify_host_timer(ROOT)"
    assert source.count(before)==1
    revised=source.replace(before,after).replace("DEP/'external-input-projection-v2.json'","DEP/'external-input-release-order-v3.json'")
    tree=ast.parse(revised)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='release')
    text=ast.get_source_segment(revised,function)
    order=[text.index(x) for x in ("inactive()","cmd(['systemctl','start','fyp-phase8-watchdog.service'])","verify_host_timer(ROOT)","release_reviewed_boundary(ROOT)","cmd(['systemctl','start','fyp-phase8-campaign.service'])")]
    exact=revised.replace("DEP/'external-input-release-order-v3.json'","DEP/'external-input-projection-v2.json'").replace(after,before)==source
    checks={'required_activation_gate_release_order':order==sorted(order),'only_order_and_external_payload_binding_changed':exact,'gate_failures_still_propagate':not any(isinstance(n,ast.Try) for n in ast.walk(function)) and text.count('verify_host_timer(ROOT)')==1 and text.count('release_reviewed_boundary(ROOT)')==1}
    assert all(checks.values())
    compile(revised,'host_deployment_release_order_v3.py','exec')
    with (H/'host_deployment_release_order_v3.py').open('x',newline='\n') as f:f.write(revised)
    with (H/'external-release-order-v3.diff').open('x',newline='\n') as f:f.write(''.join(difflib.unified_diff(source.splitlines(True),revised.splitlines(True),fromfile='external-projection-v2',tofile='external-release-order-v3')))
    q={'status':'PASS','distinct_controls':3,'checks':checks,'frozen_source_changes':0,'failed_request_id':failed['CommandId'],'reconciliation_sha256':hashlib.sha256(progress.read_bytes()).hexdigest(),'cause':'verify_host_timer requires the watchdog active; external wrapper invoked it before starting that unit. Pause-release and campaign start were not reached.','readiness_and_backups_reused':True,'research_executions':0}
    with (H/'release-order-v3-qualification.json').open('x') as f:json.dump(q,f,indent=2)
    p=json.loads((H/'external-input-projection-v2.json').read_bytes());p['host_controller_sha256']=hashlib.sha256(revised.encode()).hexdigest();p['release_order_correction']={'qualification_sha256':hashlib.sha256((H/'release-order-v3-qualification.json').read_bytes()).hexdigest(),'parent_external_payload_sha256':hashlib.sha256((H/'external-input-projection-v2.json').read_bytes()).hexdigest(),'source_freeze_unchanged':True}
    with (H/'external-input-release-order-v3.json').open('x') as f:json.dump(p,f,indent=2)
    blobs={n:base64.b64encode(gzip.compress((H/n).read_bytes())).decode() for n in ('host_deployment_release_order_v3.py','external-input-release-order-v3.json')}
    script="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v12\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages\npython3 -B - <<'EXTERNAL_ORDER_FILES'\nfrom pathlib import Path\nimport base64,gzip\np=Path('/var/lib/p8-continuation-v12/deployment')\nfor name,data in "+repr(blobs)+".items():\n    with (p/name).open('xb') as f:f.write(gzip.decompress(base64.b64decode(data)))\nEXTERNAL_ORDER_FILES\ntimeout --signal=TERM --kill-after=5s 150s .venv/bin/python -B /var/lib/p8-continuation-v12/deployment/host_deployment_release_order_v3.py release\n"
    with (H/'release-order-v3.sh').open('x',newline='\n') as f:f.write(script)
    print(json.dumps({'status':'PASS_3_EXTERNAL_ORDER_CONTROLS','controller_sha256':p['host_controller_sha256'],'frozen_source_unchanged':True,'failed_request_preserved':True,'zero_active_confirmed':True}))
if __name__=='__main__':main()
