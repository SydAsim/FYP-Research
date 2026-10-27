"""Render one bounded executable transfer without secrets or dependency installation."""
import base64,gzip,sys
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    name,label,seconds=sys.argv[1:]
    p=H/name;packed=base64.b64encode(gzip.compress(p.read_bytes())).decode()
    script="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages\npython3 - <<'WRITE'\nimport base64,gzip\nfrom pathlib import Path\np=Path('/var/lib/p8-continuation-v11/deployment/')/'"+name+"'\nwith p.open('xb') as f:f.write(gzip.decompress(base64.b64decode('"+packed+"')))\nWRITE\ntimeout --signal=TERM --kill-after=5s "+seconds+"s .venv/bin/python -B /var/lib/p8-continuation-v11/deployment/"+name+"\n"
    (H/(label+'.sh')).write_text(script,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
