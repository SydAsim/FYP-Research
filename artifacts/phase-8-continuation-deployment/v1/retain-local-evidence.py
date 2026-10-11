"""Version-pinned evidence readback via private presigned URLs; never launches research."""
import json,sys,urllib.request,urllib.error
from pathlib import Path
repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'artifacts/phase-8-continuation/v1'))
from controls import read,write_new
from transport import download,Receipt
from postflight import recover
from storage import ObjectProof
from handover import verify_members
urls=read(Path.home()/'.fyp-research/phase8-owner/phase85-continuation-v1/poststop-download-urls.json')['structuredContent']['result']
proofs=read(Path(__file__).parent/'poststop-download-proofs.json')
class PinnedURLStore:
 def __init__(self,url):self.url=url
 def read(self,receipt,start,end):
  try:
   with urllib.request.urlopen(urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}'}),timeout=30) as response:
    if response.status!=206 or response.headers.get('x-amz-version-id')!=receipt.version_id or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{receipt.bytes}':raise ValueError('PINNED_VERSION_RANGE_DRIFT')
    data=response.read()
  except (urllib.error.URLError,TimeoutError) as error:
   raise OSError(type(error).__name__) from None
  if len(data)!=end-start+1:raise ValueError('INCOMPLETE_RANGE')
  return data
 def head(self,receipt):self.read(receipt,0,0)
result=[]
for label,p,u in zip(('s','m','o'),proofs,urls,strict=True):
 if p['bucket']!=u['bucket'] or p['key']!=u['key']:raise ValueError('PRIVATE_URL_PROOF_BINDING_DRIFT')
 root=Path('C:/p8c1')/label;proof=ObjectProof.model_validate(p)
 archive=download(PinnedURLStore(u['url']),Receipt.model_validate(p),root/'t',workers=4,seconds=600)
 destination=recover(proof,root,local_archive=archive);verify_members(destination/'slot')
 result.append({'label':label,'proof':p,'extracted':str(destination/'slot'),'verified':'PASS'})
write_new(Path(__file__).parent/'poststop-local-evidence.json',{'status':'PASS','objects':result,'originals_replayed':0,'source':'VERSION_PINNED_HTTPS_RANGES_PLUS_FULL_ARCHIVE_AND_MEMBER_HASHES'})
print(json.dumps({'status':'PASS','local_roots':[x['extracted'] for x in result],'originals_replayed':0}))

