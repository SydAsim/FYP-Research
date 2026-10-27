"""Bounded read-only inspection of the initiating pause and service restarts."""
from pathlib import Path
import importlib.util
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location('bounded_transport', ROOT/'artifacts/phase-8-results-share/v3/download.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.HERE = HERE
body = r'''
import json, subprocess
from pathlib import Path
from datetime import datetime, UTC
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=30)
    return {'code':p.returncode,'out':p.stdout,'err':p.stderr}
j=run(['journalctl','--since','2026-10-23 06:13:45 UTC','--until','2026-10-23 06:15:10 UTC','--no-pager','-o','json'])
events=[]
for line in j['out'].splitlines():
    x=json.loads(line); msg=x.get('MESSAGE','')
    if any(k in msg.lower() for k in ['phase8','needrestart','unattended','restarting','stopping','stopped','apt','upgrade','sigint','keyboardinterrupt']):
        events.append({'time':x.get('__REALTIME_TIMESTAMP'),'unit':x.get('_SYSTEMD_UNIT'),'comm':x.get('_COMM'),'message':msg[:900]})
units=run(['systemctl','cat','fyp-phase8-campaign.service','fyp-phase8-watchdog.service'])
u=run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,Result,KillSignal,Restart,ExecMainStartTimestamp,ExecMainExitTimestamp'])
logs={}
for name in ['/var/log/unattended-upgrades/unattended-upgrades.log','/var/log/unattended-upgrades/unattended-upgrades-dpkg.log','/var/log/apt/history.log','/var/log/dpkg.log']:
    p=Path(name)
    if p.exists():
        lines=p.read_text(errors='replace').splitlines()
        matched=[s for s in lines if '2026-10-23' in s or 'needrestart' in s or 'fyp-phase8' in s]
        logs[name]=matched[-35:]
nr={str(p):p.read_text(errors='replace')[:2500] for p in Path('/etc/needrestart/conf.d').glob('*') if p.is_file()}
print(json.dumps({'at':datetime.now(UTC).isoformat(),'journal_count':len(events),'journal':events[-70:],'units':units,'state':u,'package_logs':logs,'needrestart_overrides':nr}))
'''
command="export PYTHONDONTWRITEBYTECODE=1\npython3 -B - <<'READ_ONLY'\n"+body+"\nREAD_ONLY\n"
result=json.loads(m.run('initiating-pause',command,100))
m.save('initiating-pause-summary.json',result)
print(json.dumps(result,indent=2))
history=m.aws('ssm-control-history',['ssm','list-commands','--instance-id',m.HOST,'--filters','key=InvokedAfter,value=2026-10-23T06:00:00Z','key=InvokedBefore,value=2026-10-23T06:20:00Z','--max-results','50'])
print(json.dumps({'ssm_history':[{'CommandId':c['CommandId'],'Comment':c.get('Comment'),'RequestedDateTime':c.get('RequestedDateTime'),'Status':c.get('Status'),'DocumentName':c.get('DocumentName')} for c in history['Commands']]}))
