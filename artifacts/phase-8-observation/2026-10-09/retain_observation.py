import json,sys,tarfile,hashlib
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import ops
raw=ops.read(HERE/'preserve-status1-result.json')['result']
assert raw['Status']=='Success'
value=json.loads(raw['StandardOutputContent']);p=value['evidence']
ops.write_new(HERE/'remote-observation-result.json',value)
destination=Path('E:/FYP Project/p8-observation-20261009-1');destination.mkdir(exist_ok=False)
archive=destination/'evidence.tar.gz'
ops.aws('paused-evidence-download',['s3api','get-object','--bucket',p['bucket'],'--key',p['key'],'--version-id',p['version_id'],'--checksum-mode','ENABLED',str(archive)],180)
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
print(ops.read(HERE/'evidence-readback.json'))
