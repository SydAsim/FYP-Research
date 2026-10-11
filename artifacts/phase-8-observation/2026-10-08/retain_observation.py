import json,sys,tarfile,hashlib
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'phase-8-continuation-deployment/v3'))
import ops
raw=ops.read(ops.HERE/'pattern-observation-2-status1-result.json')['result']
assert raw['Status']=='Success'
value=json.loads(raw['StandardOutputContent']);p=value['evidence']
ops.write_new(HERE/'remote-observation-result.json',value)
destination=Path('E:/FYP Project/p8-observation-20261008-1');destination.mkdir(exist_ok=False)
archive=destination/'evidence.tar.gz'
ops.aws('pattern-observation-download',['s3api','get-object','--bucket',p['bucket'],'--key',p['key'],'--version-id',p['version_id'],'--checksum-mode','ENABLED',str(archive)],180)
assert ops.hash_file(archive)==p['sha256'] and archive.stat().st_size==p['bytes']
target=destination/'x';target.mkdir()
with tarfile.open(archive,'r:gz') as source:
 for m in source:
  part=PurePosixPath(m.name)
  if part.is_absolute() or '..' in part.parts or m.issym() or m.islnk() or not (m.isfile() or m.isdir()):raise ValueError('UNSAFE_EVIDENCE_MEMBER')
  path=target.joinpath(*part.parts)
  if target.resolve() not in path.resolve().parents:raise ValueError('OUTSIDE_EVIDENCE_ROOT')
  if m.isdir():path.mkdir(exist_ok=True,parents=True)
  else:
   path.parent.mkdir(exist_ok=True,parents=True)
   with source.extractfile(m) as f,path.open('xb') as out:
    while b:=f.read(1024**2):out.write(b)
folder=target/'inspection';manifest=ops.read(folder/'manifest.json')
assert all(ops.hash_file(folder/n)==h for n,h in manifest['files'].items())
ops.write_new(HERE/'evidence-readback.json',{'status':'PASS','proof':p,'local_archive':str(archive),'extracted':str(folder),'verified_files':len(manifest['files'])})
details=ops.read(folder/'completed-details.json');groups={}
for d in details:groups.setdefault(d['case_id'],{})[d['arm']]=d
paired={k:v for k,v in groups.items() if set(v)=={'B3','P1','P2'}}
durations=[]
from datetime import datetime
for d in details:
 if d['historical_original']:continue
 anchor=d['request_anchors'][-1]['issued_at'] if d['request_anchors'] else None
 if anchor:durations.append((datetime.fromisoformat(d['finished_at'])-datetime.fromisoformat(anchor)).total_seconds())
endpoints={}
for arm in ('B3','P1','P2'):
 endpoints[arm]={'n':0,'values':{}}
 for d in details:
  if d['arm']!=arm:continue
  endpoints[arm]['n']+=1
  for k,v in d['values'].items():
   counter=endpoints[arm]['values'].setdefault(k,{})
   counter[v]=counter.get(v,0)+1
result={'full_triples':len(paired),'distinct_inputs_started':len(groups),'all_retained_endpoint_counts':endpoints,
 'completed_window_seconds_min':min(durations),'completed_window_seconds_max':max(durations),
 'same_values_across_complete_triples':{k:len({json.dumps(v['values'],sort_keys=True) for v in arms.values()})==1 for k,arms in paired.items()},
 'no_formal_interim_testing':True,'historical_timing_classifications_not_overwritten':True}
ops.write_new(HERE/'descriptive-patterns.json',result)
print(json.dumps(result))
