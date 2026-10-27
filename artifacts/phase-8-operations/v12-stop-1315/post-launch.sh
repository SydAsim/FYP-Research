set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 60s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'READ_ONLY'
import json,sys,subprocess
from datetime import UTC,datetime
from pathlib import Path
SOURCE=Path('/opt/fyp-phase8-continuation-v12');ROOT=Path('/var/lib/p8-continuation-v9/run');DEP=Path('/var/lib/p8-continuation-v12/recovery1315')
sys.path.insert(0,str(SOURCE/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from controls import read,hash_file
rows,notices=snapshot(ROOT/'campaign.sqlite3')
before=read(DEP/'boundary-before.json')['rows']
assert rows[:1315]==before[:1315]
assert [{k:r[k] for k in ('sequence','case_id','arm','attempt','execution_id','fixture_hash')} for r in rows]==[{k:r[k] for k in ('sequence','case_id','arm','attempt','execution_id','fixture_hash')} for r in before]
for row in rows[:1315]:assert hash_file(ROOT/'backups'/(row['execution_id']+'.json'))==row['backup_hash']
assert hash_file(ROOT/'retained-protocol1315-pause.json')=='89bf7369aaa355e52c0bd3f59afb101d87701db33d85379b2b64549f24c4a95c'
unit_state=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,MainPID,ActiveState,SubState,Result'],capture_output=True,text=True,check=True,timeout=10).stdout
effective=[]
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    pid=int(subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],capture_output=True,text=True,check=True,timeout=5).stdout.strip())
    if pid:
        env=dict(x.split('=',1) for x in Path(f'/proc/{pid}/environ').read_bytes().decode().split('\0') if '=' in x)
        assert env.get('AWS_METADATA_SERVICE_TIMEOUT')=='3' and env.get('AWS_METADATA_SERVICE_NUM_ATTEMPTS')=='3'
        effective.append({'unit':u,'pid':pid,'metadata_timeout':3,'metadata_attempts':3})
admitted=[x for x in notices if x.get('kind')=='ADMITTED' and x.get('execution_id')=='01a11705-11f4-7875-b6f4-62729851bd64']
checkpoint=ROOT/'slots/1316/executions/01a11705-11f4-7875-b6f4-62729851bd64/checkpoint.json'
small=None
if checkpoint.exists():
    d=read(checkpoint);small={k:d.get(k) for k in ('status','started_at','driver_finished_at','original_deadline','failure')}
print(json.dumps({'at':datetime.now(UTC).isoformat(),'counts':{s:sum(x['state']==s for x in rows) for s in sorted({x['state'] for x in rows})},'original1315_prefix_unchanged':True,'all1500_identities_order_unchanged':True,'original1315_backup_receipt_hashes_unchanged':True,'preserved_pause_verified':True,'current_pause':read(ROOT/'pause.json') if (ROOT/'pause.json').exists() else None,'sequence1316':rows[1315],'admitted':admitted,'checkpoint':small,'services':unit_state,'effective_credential_environment':effective,'recovery_backup':read(DEP/'recovery-backup-verified.json'),'readiness':read(DEP/'actual-recovery-readiness.json'),'stop_at':'2026-10-26T12:00:00Z','read_only':True},default=str))
READ_ONLY
