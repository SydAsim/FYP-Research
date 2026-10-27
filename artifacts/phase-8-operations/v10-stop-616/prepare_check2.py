from pathlib import Path
import base64,gzip
h=Path(__file__).resolve().parent
packed=base64.b64encode(gzip.compress((h/'candidate/check.py').read_bytes())).decode()
body=f'''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'CHECK'
import base64,gzip,subprocess,hashlib
from pathlib import Path
p=Path('/var/lib/p8-continuation-v10/deployment/candidate616-offline-v1')
with (p/'check-v2.py').open('xb') as f:f.write(gzip.decompress(base64.b64decode('{packed}')))
source=Path('/opt/fyp-phase8-continuation-v10/artifacts/phase-8-runner-amendment/v4-complete/refusal.py');before=hashlib.sha256(source.read_bytes()).hexdigest()
r=subprocess.run(['/opt/fyp-phase8-continuation-v10/.venv/bin/python','-B',str(p/'check-v2.py')],capture_output=True,text=True,timeout=60)
with (p/'attempt2.txt').open('x') as f:f.write(r.stdout+r.stderr)
print(r.stdout+r.stderr)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
r.check_returncode()
CHECK
'''
(h/'qualify-v2.sh').write_text(body,encoding='utf-8',newline='\n')
