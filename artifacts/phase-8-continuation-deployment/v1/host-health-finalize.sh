#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import base64,csv,gzip,hashlib,importlib.metadata,json,os,socket,subprocess,sys,tomllib
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from runner import verify_clock
from storage import ObjectProof,S3Cloud
from transport import Receipt,S3Store
from research.execution_linux_v1.runner import IMAGE_DIGESTS
from research.execution_linux_v1 import runtime
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation/run');dep=Path('/var/lib/p8-continuation/deployment');owner=Path('/var/lib/fyp-owner')
if read(dep/'import-and-backup-readiness.json')['status']!='PASS':raise ValueError('IMPORT_BACKUP_NOT_READY')
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS')
authority=ContinuationAuthority(root,read(root/'run.json'));authority.verify(prelaunch=True)
verify_imported_first(root);closed_boundary(Journal(root).rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_clock(root,authority.policy,utc())
proof=ObjectProof.model_validate(read(dep/'import-and-backup-readiness.json')['prelaunch_backup'])
store=S3Store('fyp-research');store.head(Receipt.model_validate(proof.model_dump()))
verify_members(root.parent/'prelaunch-readback/x/slot')
for obj in read(Path.cwd()/'artifacts/phase-8-launch/v1/local-postflight.json')['objects']:
 store.head(Receipt.model_validate(obj['proof']))
 verify_members(root.parent/'retained'/obj['label']/'x/slot')
dependencies={}
lock=tomllib.loads(Path('uv.lock').read_text());locked={}
for package in lock['package']:locked.setdefault(package['name'].lower().replace('_','-'),set()).add(package['version'])
for label,environment in (('application',Path('.venv')),('analysis',Path('.venv-analysis')),('transport',Path('.venv-transport'))):
 packages={};site=environment/'lib/python3.12/site-packages';file_count=0
 for dist in importlib.metadata.distributions(path=[str(site)]):
  name=dist.metadata['Name'].lower().replace('_','-');packages[name]=dist.version
  if label=='application' and name not in ('pip','setuptools','wheel') and dist.version not in locked.get(name,set()):raise ValueError('INSTALLED_LOCK_VERSION_DRIFT: '+name)
  for line in csv.reader((dist.read_text('RECORD') or '').splitlines()):
   if not line or not line[1]:continue
   algorithm,digest=line[1].split('=',1);target=Path(dist.locate_file(line[0]))
   if algorithm!='sha256' or not target.is_file():raise ValueError('DEPENDENCY_RECORD_MISSING')
   got=base64.urlsafe_b64encode(hashlib.sha256(target.read_bytes()).digest()).decode().rstrip('=')
   if got!=digest:raise ValueError('DEPENDENCY_RECORD_HASH_DRIFT: '+name)
   file_count+=1
 if label!='application':
  requirements=Path('research/study/requirements.txt') if label=='analysis' else Path('artifacts/phase-8-review-freeze/v2/requirements.txt')
  for line in requirements.read_text().splitlines():
   if '==' in line and not line.startswith('#'):
    name,version=line.split('==');name=name.lower().replace('_','-')
    if packages.get(name)!=version:raise ValueError('REQUIREMENT_VERSION_DRIFT: '+name)
 dependencies[label]={'packages':packages,'record_hashed_files':file_count,'installed_versions_sha256':hashlib.sha256(canonical(packages)).hexdigest()}
if sys.version_info[:3]!=(3,12,13):raise ValueError('PYTHON_RUNTIME_DRIFT')
for tag,digest in IMAGE_DIGESTS.items():
 image=json.loads(subprocess.run(['docker','image','inspect',tag],check=True,capture_output=True,text=True,timeout=10).stdout)[0]
 if digest not in image['RepoDigests']:raise ValueError('IMAGE_DIGEST_DRIFT')
# Verify the already exercised and retired empty diagnostic; do not reprovision.
diag=dep/'cal-v4-continuation-host-readiness-01';execution=diag/'empty-services'
state=read(execution/'services.json')
if state['records']:raise ValueError('DIAGNOSTIC_SERVICES_STILL_OWNED')
if len([e for e in state['events'] if e['event']=='PROCESS_STOPPED'])!=4:raise ValueError('DIAGNOSTIC_STOP_EVIDENCE_MISSING')
health={}
for name in ('api','voice','worker','simulator'):
 logs=list((execution/'logs').glob(name+'-*.log'))
 if len(logs)!=1 or 'GET /health/live HTTP/1.1\" 200' not in logs[0].read_text():raise ValueError('RECORDED_HEALTH_SUCCESS_MISSING: '+name)
 health[name]={'status':200,'evidence':'retained service HTTP access log','response_body_retained':False,'log_sha256':hash_file(logs[0])}
for name in ('setup_app','setup_truth'):
 with gzip.open(diag/(name+'.sql.gz'),'rb') as source:
  while source.read(1024**2):pass
for name in read(diag/'resources.json')['containers']:
 if runtime.inspect_owned(name,read(diag/'resources.json')['resource_id']) is not None:raise ValueError('DIAGNOSTIC_CONTAINER_NOT_RETIRED')
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
sample=host(root,Path('/var/lib/p8-continuation/backup'));cloud=S3Cloud(authority.policy.cloud_bucket,f'exports/phase8/{authority.policy.run_id}/');guard(authority.policy,sample,utc(),cloud.inventory(),extra_bytes=authority.policy.slot_capacity_reserve_bytes)
write_new(dep/'host-health-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-034252c3e9b083abf','source_files_verified':1903,'dependency_environments':dependencies,'python':sys.version,'image_digests':IMAGE_DIGESTS,'diagnostic_id':diag.name,'health':health,'host_after_diagnostic_retirement':sample,'diagnostic_logs_and_dumps_retained':True,'diagnostic_resources_retired':True,'scientific_driver_calls':0,'main_admitted':False,'prior_readiness_attempt':'d52ac76d-ed19-4fc6-b034-a57dd01ce0bb','prior_final_port_check_failed':True,'no_diagnostic_replay':True})
Journal(root).event('PREPARATION_READINESS_ATTEMPTS_RETAINED',first='45d44dc7-04fc-4e24-8a89-2928890416e4',import_complete='eacf3722-940e-47a6-8e95-1a7f86037f0b',prior_port_check='d52ac76d-ed19-4fc6-b034-a57dd01ce0bb',all_ports_now_available=True,main_admitted=False)
print(json.dumps({'status':'PASS','source_files':1903,'available_memory_bytes':sample['available_memory_bytes'],'disk_free_bytes':sample['system_free_bytes'],'dependency_record_hashes_verified':sum(x['record_hashed_files'] for x in dependencies.values()),'health':health,'driver_calls':0}))
PY
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer
systemctl list-timers fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer --no-pager
