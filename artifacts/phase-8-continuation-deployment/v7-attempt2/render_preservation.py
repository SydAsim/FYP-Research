import json
from pathlib import Path

here=Path(__file__).resolve().parent
old=(here.parent/'v7/preserve-failed-bootstrap.sh').read_text(encoding='utf-8')
body=old.split("<<'PRESERVE'\n",1)[1].split('\nPRESERVE\n',1)[0]
body=body.replace('/opt/fyp-phase8-continuation-v5','/opt/fyp-phase8-continuation-v7')
body=body.replace("'2026-10-09 14:46:00 UTC'", "'2026-10-09 15:42:00 UTC'")
body=body.replace("dep/'source-transfer-failure.json'", "dep/'live-preparation-failure-attempt2.json'")
body=body.replace("dep/'blocked-preservation-proof.json'", "dep/'blocked-preservation-proof-attempt2.json'")
body=body.replace("'bootstrap_failure':controls_result", "'live_readiness_failure':controls_result")
body=body.replace("'Historical v5 PASS_ALL_82; fresh v7 host gates unstarted'", "'Historical v5 PASS_ALL_82; attempt2 source PASS, live check stopped at OLD_OPERATIONAL_UNIT_RUNNING before fresh backup qualification'")
marker="    out=dep/('blocked-preservation-'+str(time.time_ns()));out.mkdir()"
addition="""    before=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,ExecStart,Result'],check=True,capture_output=True,text=True,timeout=20).stdout
    write_new(dep/'units-before-quiesce-attempt2.json',{'at_utc':utc().isoformat(),'output':before})
    subprocess.run(['systemctl','stop','fyp-phase8-campaign.service','fyp-phase8-watchdog.service'],check=True,timeout=40)
"""
assert marker in body
body=body.replace(marker,addition+marker)
failure=json.loads((here/'live-checks-attempt2-status1-result.json').read_text())['result']
assert failure['Status']=='Failed' and 'OLD_OPERATIONAL_UNIT_RUNNING' in failure['StandardErrorContent']
script='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
cat >/var/lib/p8-continuation-v7/deployment/live-preparation-failure-attempt2.json <<'FAILURE'
'''+json.dumps(failure)+'''
FAILURE
cat >/var/lib/p8-continuation-v7/deployment/preserve_failed_readiness_attempt2.py <<'PRESERVE'
'''+body+'''
PRESERVE
timeout --signal=TERM --kill-after=5s 300s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/preserve_failed_readiness_attempt2.py
'''
with (here/'preserve-readiness-attempt2.sh').open('x',encoding='utf-8',newline='\n') as f:
    f.write(script)
