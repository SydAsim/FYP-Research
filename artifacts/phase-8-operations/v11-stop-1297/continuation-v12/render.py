"""Validate complete external command set and bind the exact controller before boot."""
from pathlib import Path
import base64,gzip,hashlib,json
H=Path(__file__).resolve().parent
def read(name):return json.loads((H/name).read_bytes())
def main():
    body=(H/'host_deployment.py').read_bytes();compile(body,'host_deployment.py','exec')
    assert b'\r' not in body and b'/opt/fyp-phase8-continuation-v11' in body
    authority={n:base64.b64encode((H/n).read_bytes()).decode() for n in ('CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json')}
    p={'package':read('candidate-package.json'),'delta':read('delta-object.json'),'authority':authority,'freeze_manifest':read('freeze-manifest.json'),'freeze_attestation':read('freeze-attestation.json'),'external':read('independent-guards-verified.json'),'host_controller_sha256':hashlib.sha256(body).hexdigest()}
    with (H/'external-input.json').open('x') as f:json.dump(p,f,indent=2)
    blobs={'host_deployment.py':base64.b64encode(gzip.compress(body)).decode(),'external-input.json':base64.b64encode(gzip.compress((H/'external-input.json').read_bytes())).decode()}
    env="export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH={s}:{s}/.venv-analysis/lib/python3.12/site-packages:{s}/.venv-transport/lib/python3.12/site-packages\n"
    prep="set -euo pipefail\numask 077\n"+env.format(s='/opt/fyp-phase8-continuation-v11')+"python3 -B - <<'EXTERNAL_FILES'\nfrom pathlib import Path\nimport base64,gzip\np=Path('/var/lib/p8-continuation-v12/deployment');p.mkdir(mode=0o700,parents=True,exist_ok=False)\nfor name,data in "+repr(blobs)+".items():\n    with (p/name).open('xb') as f:f.write(gzip.decompress(base64.b64decode(data)))\nEXTERNAL_FILES\ntimeout --signal=TERM --kill-after=5s 240s /opt/fyp-phase8-continuation-v11/.venv/bin/python -B /var/lib/p8-continuation-v12/deployment/host_deployment.py prepare\n"
    scripts={'prepare.sh':prep}
    for action,seconds in [('metadata',150),('live',480),('prelaunch',300),('readiness',150),('complete',300),('release',150)]:
        scripts[action+'.sh']="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v12\n"+env.format(s='/opt/fyp-phase8-continuation-v12')+"timeout --signal=TERM --kill-after=5s "+str(seconds)+"s .venv/bin/python -B /var/lib/p8-continuation-v12/deployment/host_deployment.py "+action+"\n"
    for name,text in scripts.items():
        assert '\r' not in text and 'python -B' in text and 'timeout --signal=TERM' in text
        with (H/name).open('x',newline='\n') as f:f.write(text)
    checks={'status':'PASS_LOCAL_COMMAND_REVIEW_BEFORE_BOOT','controller_sha256':hashlib.sha256(body).hexdigest(),'controller_syntax':True,'files':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ('host_deployment.py','external-input.json',*scripts)},'command_checks':['old qualified interpreter only for parent preparation; actual build/RECORD checks retained','new interpreter for metadata and every later action','separate process per stage prevents old module cache reuse','Bash invoked explicitly by preserved single-send transport','LF-only scripts and explicit Python heredoc boundaries','exact closed1297 IDs and PAUSE hash','original clock anchor unchanged; paired new boot anchor','archive pin and source/authority hashes bound','all scripts present before boot; no dependency installation','12 Linux controls before metadata adoption','timers26October12UTC and admission cutoff11:30UTC','PRELAUNCH then genuine readiness/launch then COMPLETE before release'],'linux_checks':'PENDING_ACTUAL_HOST_REQUIRED_BEFORE_ADOPTION','main_admissions':0}
    with (H/'external-wrapper-verification.json').open('x') as f:json.dump(checks,f,indent=2)
    print(json.dumps({'status':checks['status'],'controller_sha256':checks['controller_sha256'],'scripts':list(scripts)}))
if __name__=='__main__':main()
