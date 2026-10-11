#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import base64,csv,gzip,hashlib,importlib.metadata,json,os,socket,subprocess,sys,tomllib
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,canonical,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from runner import verify_clock
from storage import ObjectProof,S3Cloud
from transport import Receipt,S3Store
from research.execution_linux_v1.runner import IMAGE_DIGESTS
from research.execution_linux_v1 import runtime
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined-v4/run');dep=Path('/var/lib/p8-combined-v4/deployment');owner=Path('/var/lib/fyp-owner')
if read(dep/'import-and-backup-readiness.json')['status']!='PASS':raise ValueError('IMPORT_BACKUP_NOT_READY')
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('OWNER_PERMISSIONS')
authority=ContinuationAuthority(root,read(root/'run.json'));authority.verify(prelaunch=True)
verify_imported_first(root);closed_boundary(Journal(root).rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_clock(root,authority.policy,utc())
proof=ObjectProof.model_validate(read(dep/'import-and-backup-readiness.json')['prelaunch_backup'])
store=S3Store('fyp-research');store.head(Receipt.model_validate(proof.model_dump()))
verify_members(root.parent/'prelaunch-readback/x/slot')
for obj in read(dep/'import-and-backup-readiness.json')['original_backups']:
 store.head(Receipt.model_validate(obj))
verify_imported_first(root)
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
# One empty, separate diagnostic stack. No study fixture, intent or provider write.
diag=dep/'diag-complete-v4-host-readiness-01';diag.mkdir(exist_ok=False)
resource='p85cv4-ready-057344e5';names=[resource+'-'+x for x in ('app','truth','cache')]
write_new(diag/'resources.json',{'resource_id':resource,'containers':names,'database':'postgresql://setup_app:setup_local_only@127.0.0.1:16432/setup_app','sim_database':'postgresql://setup_truth:setup_local_only@127.0.0.1:16433/setup_truth','services':[19100,19101,19102,19110],'validation_network':None,'image_digests':IMAGE_DIGESTS,'concurrency':1})
execution=diag/'empty-services';execution.mkdir()
runtime.install_process_boundary();runtime.provision(diag);services=runtime.Runtime(diag,execution);services.start_all()
health={}
for name,port in (('api',19100),('voice',19101),('worker',19102),('simulator',19110)):
 with urlopen(f'http://127.0.0.1:{port}/health/live',timeout=3) as reply:health[name]={'status':reply.status,'body':reply.read().decode()}
sample=host(root,Path('/var/lib/p8-combined-v4/backup'));cloud=S3Cloud(authority.policy.cloud_bucket,f'exports/phase8/{authority.policy.run_id}/');guard(authority.policy,sample,utc(),cloud.inventory(),extra_bytes=authority.policy.slot_capacity_reserve_bytes)
services.stop_all()
for index,name in enumerate(names):
 info=runtime.inspect_owned(name,resource)
 if info is None:raise ValueError('DIAGNOSTIC_RESOURCE_LOST')
 if index<2:
  user=('setup_app','setup_truth')[index];dump=subprocess.run(['docker','exec',name,'pg_dump','-U',user,user],check=True,capture_output=True,timeout=45).stdout
  with gzip.open(diag/(user+'.sql.gz'),'xb') as out:out.write(dump)
 subprocess.run(['docker','stop',name],check=True,capture_output=True,timeout=20)
 subprocess.run(['docker','rm',name],check=True,capture_output=True,timeout=20)
 if index<2:subprocess.run(['docker','volume','rm',name+'-data'],check=True,capture_output=True,timeout=20)
write_new(dep/'host-health-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-057344e5372faf62f','source_files_verified':len(read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')['files']),'dependency_environments':dependencies,'python':sys.version,'image_digests':IMAGE_DIGESTS,'diagnostic_id':diag.name,'health':health,'host_with_empty_services':sample,'diagnostic_logs_and_dumps_retained':True,'diagnostic_resources_retired':True,'scientific_driver_calls':0,'main_admitted':False})
print(json.dumps({'status':'PASS','source_files':len(read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')['files']),'available_memory_bytes':sample['available_memory_bytes'],'disk_free_bytes':sample['system_free_bytes'],'dependency_record_hashes_verified':sum(x['record_hashed_files'] for x in dependencies.values()),'health':health,'driver_calls':0}))
PY
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer
systemctl list-timers fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer --no-pager
