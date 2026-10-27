set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -B - <<'READ'
import json,tarfile,hashlib
from pathlib import Path
root=Path('/var/lib/p8-continuation-v9/run')
eid='01a11705-11f2-7c66-8710-43c921046e1b'
receipt=json.loads((root/'backups'/(eid+'.json')).read_bytes())
archive=Path('/var/lib/p8-continuation-v9/backup/0616/attempt-1792158556532307065.tar.gz')
h=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
assert h==receipt['sha256']=='4002ff9a474c3afaae216ab8a14260801910ca82043419a3e0afd5a70dd95c89'
with tarfile.open(archive,'r:gz') as tf:
    names=tf.getnames()
    ep=[n for n in names if n.endswith('/'+eid+'/export.json')]
    assert len(ep)==1,ep
    raw=tf.extractfile(ep[0]).read()
    export=json.loads(raw)
    print(json.dumps({'archive_sha256':h,'export_member':ep[0],'export_sha256':hashlib.sha256(raw).hexdigest(),'keys':list(export),'failure':export.get('failure'),'observations':export.get('observations'),'status':export.get('status'),'receipt':receipt,'related_members':[n for n in names if any(s in n for s in ['manifest','inventory','checkpoint'])]},default=str))
READ
