"""Remove only reviewed local calibration containers after preserving evidence."""
from pathlib import Path, PurePosixPath
import gzip,hashlib,json,subprocess,tarfile,time
from datetime import datetime,UTC

OUT=Path('E:/FYP Project/local-container-cleanup-20261008')
OUT.mkdir(exist_ok=False)
NAMES=(
 'p85-v3-native-packed','p85-v3-packed-final','p85-v3-offline-attempt2','p85-v3-offline1',
 'p85b-attempt1','p85-continuation-type-final2','p85-continuation-final-offline',
 'p85-continuation-type-v2','p85-continuation-offline-v1','p85a-attempt2','p85a-calibration-v1',
 'p8-linux-v1-1d9f386587-cache','p8-linux-v1-1d9f386587-truth','p8-linux-v1-1d9f386587-app',
 'p8-setup-v1-432df82482-cache','p8-setup-v1-432df82482-truth','p8-setup-v1-432df82482-app',
 'phase8-calibration-v4-redis')
def run(args):
 p=subprocess.run(['docker',*args],capture_output=True,timeout=90)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 return p.stdout
def record(path,v):
 with path.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=True)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024**2):h.update(b)
 return h.hexdigest()
def archive(command,path,tar=True):
 p=subprocess.Popen(['docker',*command],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert p.stdout is not None
 deadline=time.monotonic()+180
 with gzip.open(path,'xb') as out:
  while b:=p.stdout.read(1024**2):
   if time.monotonic()>deadline:p.kill();raise TimeoutError('BACKUP_TIMEOUT_RETAIN_CONTAINER')
   out.write(b)
 err=p.stderr.read() if p.stderr else b''
 if p.wait(timeout=20):raise RuntimeError(err.decode(errors='replace'))
 if tar:
  with tarfile.open(path,'r:gz') as t:
   for m in t:
    if m.isfile():
     f=t.extractfile(m)
     assert f is not None
     while f.read(1024**2):pass
 else:
  with gzip.open(path,'rb') as f:
   while f.read(1024**2):pass
 return {'file':str(path),'sha256':digest(path),'bytes':path.stat().st_size}

before=json.loads(run(['inspect',*NAMES]))
protected=json.loads(run(['inspect','n8n','eager_goldberg']))
records=[]
for c in before:
 name=c['Name'].lstrip('/');assert name in NAMES
 assert name not in ('n8n','eager_goldberg') and not name.startswith('commit-aware-voice-agent')
 if c['State']['Running']:assert name.startswith(('p8-linux-v1-','p8-setup-v1-','phase8-calibration-'))
 folder=OUT/name;folder.mkdir()
 clean={k:c[k] for k in ('Id','Name','State','Image','Mounts','NetworkSettings')}
 clean['command']={'Entrypoint':c['Config']['Entrypoint'],'Cmd':c['Config']['Cmd']}
 record(folder/'container.json',clean)
 logs=subprocess.run(['docker','logs',c['Id']],capture_output=True,timeout=90)
 (folder/'stdout.log').write_bytes(logs.stdout);(folder/'stderr.log').write_bytes(logs.stderr)
 if logs.returncode:raise RuntimeError('LOG_PRESERVATION_FAILED')
 diff=run(['diff',c['Id']]).decode();(folder/'writable-diff.txt').write_text(diff,encoding='utf-8')
 proofs=[]
 if c['State']['Running'] and c['Config']['Image'].startswith('postgres:'):
  # Explicit container-local identity only; no secret/environment contents exported.
  user=next((x.split('=',1)[1] for x in c['Config']['Env'] if x.startswith('POSTGRES_USER=')),'postgres')
  proofs.append(archive(['exec',c['Id'],'pg_dumpall','-U',user],folder/'databases.sql.gz',False))
 if not c['State']['Running']:
  added=[line[2:] for line in diff.splitlines() if line.startswith('A ')]
  mounts=[m['Destination'].rstrip('/') for m in c['Mounts']]
  # Added roots preserve unique outputs without archiving the entire reusable image.
  roots=[p for p in added if not any(p==m or p.startswith(m+'/') for m in mounts)
         and not any(p!=q and p.startswith(q.rstrip('/')+'/') for q in added)]
  for i,p in enumerate(roots):
   proofs.append(archive(['cp',c['Id']+':'+p,'-'],folder/f'added-{i:03d}.tar.gz'))
  record(folder/'added-roots.json',roots)
 record(folder/'preservation.json',{'status':'PASS','proofs':proofs,'volumes_retained':True,'bind_mounts_untouched':True})
 records.append({'name':name,'id':c['Id'],'running_before':c['State']['Running'],'evidence':str(folder),'proofs':proofs})
 print('Evidence preserved:',name,flush=True)

record(OUT/'before-removal.json',{'at_utc':datetime.now(UTC).isoformat(),'reviewed':records,'protected':[{'id':c['Id'],'name':c['Name'],'state':c['State']} for c in protected]})
for c in before:
 current=json.loads(run(['inspect',c['Id']]))[0]
 assert current['Id']==c['Id'] and current['Name']==c['Name']
 if current['State']['Running']:run(['stop','--time','20',c['Id']])
 run(['rm',c['Id']]) # Deliberately no --volumes or broad prune.
 print('Removed:',c['Name'],flush=True)
remaining=json.loads(run(['inspect','n8n','eager_goldberg']))
assert all(a['Id']==b['Id'] and a['State']==b['State'] for a,b in zip(protected,remaining))
after=run(['ps','-a','--format','{{.Names}}']).decode().splitlines()
assert not set(NAMES)&set(after)
manifest={str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file()}
record(OUT/'hashes.json',manifest)
record(OUT/'result.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'removed_count':len(NAMES),'remaining_names':after,'protected_containers_unchanged':True,'volumes_deleted':False,'images_deleted':False,'aws_touched':False,'evidence_directory':str(OUT)})
print(json.dumps(json.loads((OUT/'result.json').read_text())),flush=True)
