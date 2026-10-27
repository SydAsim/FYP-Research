set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 180s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'DIAGNOSTIC'
import hashlib,json,os,subprocess,sys,urllib.request
from datetime import UTC,datetime,timedelta
from pathlib import Path
SOURCE=Path('/opt/fyp-phase8-continuation-v12');ROOT=Path('/var/lib/p8-continuation-v9/run')
sys.path.insert(0,str(SOURCE/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from handover import ContinuationAuthority
from runner import meter,verify_clock,verify_host_timer
from storage import S3Cloud
def read(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(k,**v):print(json.dumps({'kind':k,**v},default=str),flush=True)
rows,notices=snapshot(ROOT/'campaign.sqlite3')
assert len(rows)==1500 and all(x['state']=='BACKED_UP' for x in rows[:1315]) and all(x['state']=='PLANNED' for x in rows[1315:])
assert rows[1315]['execution_id']=='01a11705-11f4-7875-b6f4-62729851bd64'
emit('BOUNDARY',at=datetime.now(UTC).isoformat(),counts={'BACKED_UP':1315,'PLANNED':185},next=rows[1315],pause=read(ROOT/'pause.json'),pause_sha256=digest(ROOT/'pause.json'),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    q=subprocess.run(['systemctl','show',unit,'--property=Id,MainPID,ActiveState,SubState,Result,User,Group,ExecStart,FragmentPath'],capture_output=True,text=True,timeout=10,check=True)
    emit('SERVICE',unit=unit,details=q.stdout)
    text=Path('/etc/systemd/system',unit).read_text()
    emit('SERVICE_ENVIRONMENT',unit=unit,lines=[line for line in text.splitlines() if line.startswith(('Environment=','EnvironmentFile=','WorkingDirectory=','User=')) and not any(w in line.upper() for w in ('SECRET','TOKEN','ACCESS_KEY','PASSWORD'))],sha256=digest(Path('/etc/systemd/system',unit)))
pid=int(subprocess.run(['systemctl','show','fyp-phase8-watchdog.service','--property=MainPID','--value'],capture_output=True,text=True,check=True,timeout=5).stdout.strip())
if pid:
    env=dict(x.split('=',1) for x in Path(f'/proc/{pid}/environ').read_bytes().decode().split('\0') if '=' in x)
    emit('WATCHDOG_ENVIRONMENT',aws_names=sorted(k for k in env if k.startswith('AWS_')),nonsecret={k:env[k] for k in ('AWS_EC2_METADATA_DISABLED','AWS_METADATA_SERVICE_TIMEOUT','AWS_METADATA_SERVICE_NUM_ATTEMPTS','AWS_PROFILE','AWS_REGION','AWS_DEFAULT_REGION','AWS_EC2_METADATA_V1_DISABLED') if k in env},proxy_names=[k for k in env if k.upper() in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY')])
try:
    req=urllib.request.Request('http://169.254.169.254/latest/api/token',method='PUT',headers={'X-aws-ec2-metadata-token-ttl-seconds':'60'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req,timeout=3) as resp:token=resp.read(4096).decode();assert len(token)<4096
    req=urllib.request.Request('http://169.254.169.254/latest/meta-data/iam/security-credentials/',headers={'X-aws-ec2-metadata-token':token})
    with opener.open(req,timeout=3) as resp:roles=resp.read(4096).decode().splitlines()
    emit('IMDS_ROLE_NAMES',roles=roles)
except Exception as e:emit('IMDS_ERROR',type=type(e).__name__,detail=str(e))
a=ContinuationAuthority(ROOT,read(ROOT/'run.json'));a.verify();verify_clock(ROOT,a.policy);verify_host_timer(ROOT)
sample=meter(ROOT);config=read(ROOT/'cloud.json')
emit('AUTHORITY_RESOURCES',policy=read(ROOT/'campaign-policy.json') if (ROOT/'campaign-policy.json').exists() else {'stop_at':str(a.policy.stop_at)},sample=sample,source=str(SOURCE))
for x in rows[1313:1315]:
    p=ROOT/'backups'/(x['execution_id']+'.json');assert digest(p)==x['backup_hash'];emit('RECENT_BACKUP',sequence=x['sequence'],receipt=read(p))
cloud=S3Cloud(config['bucket'],config['prefix'])
size=cloud.inventory()
at=datetime.now(UTC);finish=at+timedelta(hours=185*262.31642189586114/1355+2.5);uncertain=finish+timedelta(hours=24,minutes=30)
extra=0.6551338996026301
emit('INVENTORY_AND_FORECAST',at=at.isoformat(),cloud_bytes=size,completion=finish.isoformat(),uncertainty_plus_margin=uncertain.isoformat(),uncertainty_cost=a.policy.committed_cost(uncertain)+extra,full_deadline_cost=a.policy.committed_cost(a.policy.stop_at)+extra,stop_at=a.policy.stop_at.isoformat(),remaining=185,accepted_allowances_unchanged=True)
emit('READ_ONLY_DIAGNOSTIC_COMPLETE')
DIAGNOSTIC
