from pathlib import Path
import json
import tarfile
from ops import HERE
from controls import read

def main():
    pkg=read(HERE/'deployment-manifest.json')['candidate'];freeze=read(HERE/'deployment-manifest.json')['freeze']
    source=read(HERE/'source-expanded-proof.json');authority=read(HERE/'authority-proof.json');authority['label']='authority.tar.gz'
    with tarfile.open(HERE/'public-authority.tar.gz') as incoming:authority['expanded_bytes']=sum(m.size for m in incoming)
    original=(HERE.parent/'v7-attempt2/prepare-source-attempt2.sh').read_text()
    original=original.replace('continuation-v7','continuation-v9').replace('c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152',pkg['archive_sha256']).replace('9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817',pkg['package_hash']).replace('3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46',freeze['freeze_manifest_sha256'])
    prefix="set -euo pipefail\numask 077\ninstall -d -m 700 /var/lib/p8-continuation-v9/deployment\ncat >/var/lib/p8-continuation-v9/deployment/bootstrap-objects.json <<'OBJECTS'\n"+json.dumps([source,authority])+"\nOBJECTS\ncat >/var/lib/p8-continuation-v9/deployment/bootstrap-transfer.py <<'TRANSFER'\n"+(HERE/'bootstrap-transfer.py').read_text()+"\nTRANSFER\n"
    with (HERE/'prepare-source.sh').open('x',encoding='utf-8',newline='\n') as out:out.write(prefix+original)
    # Explicit actual interpreter import precedes transfer, dependencies reused.
    assert original.index('import boto3,botocore')<original.index('bootstrap-transfer.py')
    assert original.index('export PYTHONPATH=')<original.index('TRANSPORT_CHECK')
    print('Version-pinned bounded transfer and interpreter/environment order verified.')

if __name__=='__main__':main()
