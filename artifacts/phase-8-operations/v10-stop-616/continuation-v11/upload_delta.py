from pathlib import Path
import json,hashlib,base64
from ops import HERE,recorder
def main():
    package=json.loads((HERE/'candidate-package.json').read_text());path=Path(package['delta_path']);digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==package['delta_sha256']
    bucket='fyp-p82-20261005-018da1d6-803656589923';key='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v11/deployment/'+digest+'-delta.tar.gz'
    checksum=base64.b64encode(bytes.fromhex(digest)).decode()
    r=recorder.call('put-delta',['s3api','put-object','--bucket',bucket,'--key',key,'--body',str(path),'--if-none-match','*','--server-side-encryption','AES256','--metadata',json.dumps({'sha256':digest}),'--checksum-sha256',checksum])
    head=recorder.call('verify-delta-head',['s3api','head-object','--bucket',bucket,'--key',key,'--version-id',r['VersionId'],'--checksum-mode','ENABLED'])
    assert head['ContentLength']==path.stat().st_size and head['ChecksumSHA256']==checksum and head['Metadata']['sha256']==digest
    recorder.record('delta-object.json',{'bucket':bucket,'key':key,'version_id':r['VersionId'],'sha256':digest,'bytes':path.stat().st_size})
    print('PASS_VERSIONED_DELTA_UPLOAD_AND_HEAD')
if __name__=='__main__':main()
