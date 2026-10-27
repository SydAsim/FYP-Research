"""Reconcile the completed correction and stopped preservation command, no resend."""
from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('read_transport',ROOT/'artifacts/phase-8-results-share/v3/download.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE
body=r'''
import json,hashlib,subprocess
from pathlib import Path
dep=Path('/var/lib/p8-continuation-v11/deployment');dirs=list(dep.glob('stop1297-*'))
assert len(dirs)==1
p=dirs[0]
print(json.dumps({'directory':str(p),'files':[{'name':str(f.relative_to(p)),'bytes':f.stat().st_size} for f in p.rglob('*') if f.is_file()],'correction':json.loads((p/'correction-checks.json').read_text()),'blocker':json.loads((p/'resume-blocker.json').read_text()),'units':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID'],capture_output=True,text=True,check=True,timeout=10).stdout,'unfinished_archives':[str(f) for f in Path('/var/lib/p8-continuation-v9/backup').glob('diagnostic1297-*')]}))
'''
x=json.loads(m.run('reconcile-preservation',"python3 -B - <<'READ_ONLY'\n"+body+"\nREAD_ONLY\n",45))
m.save('reconciled-preservation.json',x);print(json.dumps(x,indent=2))
