set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
/opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'READ_ONLY_PREPARED'
import hashlib,json,subprocess
from pathlib import Path
dep=Path('/var/lib/p8-continuation-v12/deployment')
source=json.loads((dep/'source-and-runtime-verified.json').read_bytes())
meta=json.loads((dep/'metadata-and-timers.json').read_bytes())
timers={}
for path in Path('/etc/systemd/system').glob('fyp*.timer'):
    result=subprocess.run(['systemctl','show',path.name,'--property=Id,ActiveState,SubState,NextElapseUSecRealtime'],capture_output=True,text=True,check=True,timeout=10).stdout
    timers[path.name]=result
active={name for name,text in timers.items() if 'ActiveState=active' in text}
assert active=={'fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v12-admission-cutoff.timer'},'UNEXPECTED_OWNED_TIMER_REQUIRES_REVIEW'
for name in ('fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer'):
    assert 'Mon 2026-10-26 12:00:00 UTC' in timers[name]
assert 'Mon 2026-10-26 11:30:00 UTC' in timers['fyp-v12-admission-cutoff.timer']
print(json.dumps({'status':'PASS_ACTUAL_LINUX_RUNTIME_AND_OWNED_TIMERS','python':source['python'],'python_sha256':source['python_sha256'],'linux_controls':source['linux_controls'],'dependency_record_counts':{k:v['record_files'] for k,v in source['environments'].items()},'os_zlib':source['os_zlib'],'source_clone_bytes':source['source_clone_bytes'],'metadata':meta,'timers':timers,'source_record_sha256':hashlib.sha256((dep/'source-and-runtime-verified.json').read_bytes()).hexdigest()}))
READ_ONLY_PREPARED
