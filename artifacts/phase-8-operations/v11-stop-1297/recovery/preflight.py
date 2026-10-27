"""One bounded preflight command. No admissions or service changes."""
import importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('transport',ROOT/'artifacts/phase-8-results-share/v3/download.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE
body=(HERE/'preflight_remote.py').read_text()
command="cd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages\ntimeout --signal=TERM --kill-after=5s 150s .venv/bin/python -B - <<'PREFLIGHT'\n"+body+"\nPREFLIGHT\n"
result=json.loads(m.run('closed1297-preflight',command,165))
m.save('closed1297-preflight-summary.json',result)
print(json.dumps(result,indent=2))
