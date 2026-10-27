"""Bind the external controller and already passed qualification; no AWS calls."""
from __future__ import annotations
import ast,base64,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    files={}
    for name in ('control.py','preparation_guard.py','recover1315.py','render.py'):
        raw=(HERE/name).read_bytes();ast.parse(raw);files[name]=hashlib.sha256(raw).hexdigest()
    response=json.loads((HERE/'qualification-1-read1-result.json').read_bytes())['result']
    assert response['Status']=='Success' and response['ResponseCode']==0
    qualification=json.loads(response['StandardOutputContent'].splitlines()[-1])
    assert qualification['total']==5 and qualification['status']=='PASS' and qualification['aws_calls']==0
    (HERE/'qualification-pass.json').write_text(json.dumps(qualification,indent=2),encoding='utf-8')
    payload={'authorization.json':(HERE/'recovery-authorization.json').read_bytes(),'qualification.json':(HERE/'qualification-pass.json').read_bytes(),'recover1315.py':(HERE/'recover1315.py').read_bytes()}
    parts=["set -euo pipefail","umask 077","export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AWS_METADATA_SERVICE_TIMEOUT=3 AWS_METADATA_SERVICE_NUM_ATTEMPTS=3","export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages","python3 -B - <<'INSTALL_EXTERNAL'","import base64,hashlib,os","from pathlib import Path","d=Path('/var/lib/p8-continuation-v12/recovery1315');d.mkdir(mode=0o700,exist_ok=False)"]
    for name,raw in payload.items():
        parts += [f"b=base64.b64decode('{base64.b64encode(raw).decode()}');assert hashlib.sha256(b).hexdigest()=='{hashlib.sha256(raw).hexdigest()}'",f"with (d/{name!r}).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())"]
    parts+=['INSTALL_EXTERNAL','timeout --signal=TERM --kill-after=5s 300s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B /var/lib/p8-continuation-v12/recovery1315/recover1315.py prepare','']
    with (HERE/'prepare.sh').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(parts))
    for stage in ('backup','release'):
        # Reuse only the shell environment prefix, not the installation heredoc.
        body='\n'.join(parts[:4]+['timeout --signal=TERM --kill-after=5s '+('600s' if stage=='backup' else '180s')+' /opt/fyp-phase8-continuation-v12/.venv/bin/python -B /var/lib/p8-continuation-v12/recovery1315/recover1315.py '+stage,''])
        with (HERE/(stage+'.sh')).open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    for name in ('prepare.sh','backup.sh','release.sh','qualify.sh','PLAN.md','recovery-authorization.json','qualification-pass.json'):
        files[name]=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
    with (HERE/'external-inventory.json').open('x',encoding='utf-8') as f:json.dump({'files':files,'frozen_v12_unchanged':True,'new_freeze':False},f,indent=2)
    print(json.dumps({'status':'PASS_LOCAL_COMMAND_BINDINGS','external_controller_sha256':files['recover1315.py'],'qualification_checks':5,'shell_line_endings':'LF'}))

if __name__=='__main__':main()
