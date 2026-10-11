"""Reuse existing preservation procedure after a failed bootstrap gate; no retry."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
previous=(HERE.parent/'v5/preserve_blocked.py').read_text()
previous=previous.replace("dep=Path('/var/lib/p8-continuation-v5/deployment')", "dep=Path('/var/lib/p8-continuation-v7/deployment')")
previous=previous.replace("'p8-continuation-v5/run'", "'p8-continuation-v7/run'")
previous=previous.replace("'2026-10-09 11:17:00 UTC'", "'2026-10-09 14:46:00 UTC'")
previous=previous.replace("controls_result=read(dep/'backup-gate-control-result.json')", "controls_result=read(dep/'source-transfer-failure.json')")
previous=previous.replace("'backup_defect':controls_result", "'bootstrap_failure':controls_result")
previous=previous.replace("'live_original_backup_check':'PASS_ALL_82'", "'original_backup_qualification':'Historical v5 PASS_ALL_82; fresh v7 host gates unstarted'")
failure=json.loads((HERE/'prepare-source-status1-result.json').read_text())['result']
assert failure['Status']=='Failed' and 'ModuleNotFoundError' in failure['StandardErrorContent']
script='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v5
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v5:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
cat >/var/lib/p8-continuation-v7/deployment/source-transfer-failure.json <<'FAILURE'
'''+json.dumps(failure)+'''
FAILURE
cat >/var/lib/p8-continuation-v7/deployment/preserve_failed_bootstrap.py <<'PRESERVE'
'''+previous+'''
PRESERVE
timeout --signal=TERM --kill-after=5s 300s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/preserve_failed_bootstrap.py
'''
(HERE/'preserve-failed-bootstrap.sh').write_text(script,encoding='utf-8',newline='\n')
print('Preservation only; bootstrap is not retried; no source patch or scenario')
