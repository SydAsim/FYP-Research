"""Assemble one external shell command with the exact reviewed snippet."""
import json
from pathlib import Path
here=Path(__file__).resolve().parent
body=(here/'preserve_remote.py').read_text().replace('__SNIPPET_JSON__',repr((here/'99-fyp-phase8-defer-restarts.conf').read_text()))
compile(body,'preserve_remote.py','exec')
script="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages\ntimeout --signal=TERM --kill-after=5s 360s .venv/bin/python -B - <<'PRESERVE_ONLY'\n"+body+"\nPRESERVE_ONLY\n"
with (here/'preserve.sh').open('x',newline='\n') as f:f.write(script)
print(json.dumps({'status':'LOCAL_SYNTAX_PASS','script':'preserve.sh','scenarios':0,'admissions':0}))
