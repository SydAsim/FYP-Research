from pathlib import Path
here=Path(__file__).resolve().parent
body=(here/'finish_preservation.py').read_text()
compile(body,'finish_preservation.py','exec')
script="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages\ntimeout --signal=TERM --kill-after=5s 360s .venv/bin/python -B - <<'PRESERVE_ONLY'\n"+body+"\nPRESERVE_ONLY\n"
with (here/'finish-preservation.sh').open('x',newline='\n') as f:f.write(script)
print('LOCAL_SYNTAX_PASS_NO_REPEAT_QUALIFICATION')
