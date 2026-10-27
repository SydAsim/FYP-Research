set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'READ'
import json,sys,tarfile,hashlib,linecache
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from refusal import recognize
p=Path('/var/lib/p8-continuation-v9/backup/0616/attempt-1792158556532307065.tar.gz')
assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='4002ff9a474c3afaae216ab8a14260801910ca82043419a3e0afd5a70dd95c89'
with tarfile.open(p) as tf:
    raw=tf.extractfile('slot/executions/01a11705-11f2-7c66-8710-43c921046e1b/export.json').read()
    manifest=json.load(tf.extractfile('slot/manifest.json'))
row=json.loads(raw)
events=[]
def trace(frame,event,arg):
    if frame.f_code.co_filename.endswith('/refusal.py'):
        if event=='return':events.append({'function':frame.f_code.co_name,'line':frame.f_lineno,'source':linecache.getline(frame.f_code.co_filename,frame.f_lineno).strip(),'result':arg})
    return trace
sys.settrace(trace);result=recognize(row);sys.settrace(None)
history=row['snapshot']['history']
fail=[c for c in row['http'] if isinstance(c.get('status'),int) and c['status']>=400]
print(json.dumps({'manifest':manifest,'export_sha256':hashlib.sha256(raw).hexdigest(),'recognition':result,'recognizer_returns':events,'input':row['input'],'targets':row['targets'],'http_failures':fail,'operations':history['operations'],'effects':history['effects'],'revisions':history['revisions'],'observations':row['snapshot']['observations'][-6:],'grades':{k:row.get(k) for k in ['original_instrument_grade','revised_grade','analysis_row']},'checkpoints':row['checkpoints'][-8:]},default=str))
READ
