"""Bind final handover bytes and make only the external code install resumable."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    old=HERE/'handover-live.sh';old.rename(HERE/'handover-live.before-history-addendum.sh')
    header=(HERE.parent/'attempt-final/HEADER.txt').read_text()
    script=header+".venv/bin/python -B - <<'INSTALL'\nimport base64,gzip,hashlib\nfrom pathlib import Path\nd=Path('/var/lib/p8-continuation-v10/deployment/export-handover-code-v1');d.mkdir(mode=0o700,exist_ok=True)\n"
    hashes={}
    for name in ('core.py','handover.py'):
        b=(HERE/name).read_bytes();h=hashlib.sha256(b).hexdigest();hashes[name]=h;packed=base64.b64encode(gzip.compress(b)).decode()
        script+="b=gzip.decompress(base64.b64decode("+repr(packed)+"));assert hashlib.sha256(b).hexdigest()=="+repr(h)+"\np=d/"+repr(name)+"\nif p.exists():\n    assert p.read_bytes()==b,'EXTERNAL_CODE_COLLISION_RETAIN_EXISTING'\nelse:\n    with p.open('xb') as f:f.write(b)\n"
    cloud=json.loads((HERE/'feasibility.json').read_text())['cloud_bytes']
    script+='INSTALL\nexport HANDOVER_CLOUD_BYTES='+str(cloud)+'\ntimeout --signal=TERM --kill-after=5s 1510s .venv/bin/python -B /var/lib/p8-continuation-v10/deployment/export-handover-code-v1/handover.py\n'
    with old.open('x',encoding='utf-8',newline='\n') as f:f.write(script)
    ast.parse(script.split("<<'INSTALL'\n",1)[1].split('\nINSTALL\n',1)[0])
    record={'status':'FINAL_EXTERNAL_CODE_BINDING_NOT_FREEZE','hashes':hashes,'script_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
        'staging_cap_bytes':2147483648,'finite_live_deadline_seconds':1500,'max_cloud_gets':4,
        'offline_controls_passed':9,'original8_repeated':False,'history_addendum_seconds':0.009,
        'change':'No GET solely for missing archive when frozen-committed history record is present; preserve pinned receipt/member provenance. Reuse same external code files by exact hash on resume.',
        'frozen_source_changed':False,'source_bootstrap_used':False}
    with (HERE/'final-code-binding.json').open('x') as f:json.dump(record,f,indent=2)
    print('Final handover payload hashes bound')

if __name__=='__main__':main()
