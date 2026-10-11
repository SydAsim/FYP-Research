"""Prepare public receipts and qualified version-specific transfer; no AWS start."""
import json
import tarfile
from pathlib import Path
from ops import HERE
from controls import read, write_new

def main():
    repo=HERE.parents[2]
    receipts=Path.home()/'.fyp-research/phase8-owner/phase85-continuation-v5/receipts'
    freeze=repo/'artifacts/phase-8-continuation-freeze/v5'
    with tarfile.open(HERE/'public-authority.tar.gz','x:gz') as target:
        for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
            target.add(receipts/(kind+'.json'),arcname=kind+'.json',recursive=False)
        for kind in ('freeze-manifest.json','freeze-attestation.json','freeze-verification.json'):
            target.add(freeze/kind,arcname=kind,recursive=False)
        target.add(HERE/'actual-deployment-binding.json',arcname='explicit-deployment-authorization.json',recursive=False)
    source=read(HERE/'source-proof.json')
    with tarfile.open(repo/'artifacts/phase-8-continuation/v5/v5-complete-continuation-review-candidate.tar.gz') as archive:
        source['expanded_bytes']=sum(m.size for m in archive.getmembers())
    source['label']='package.tar.gz'
    write_new(HERE/'source-expanded-proof.json',source)
    reference=(repo/'artifacts/phase-8-continuation-deployment/v4/bootstrap-transfer.py').read_text()
    reference=reference.replace('/var/lib/p8-combined-v4/deployment','/var/lib/p8-continuation-v5/deployment').replace('/opt/fyp-phase8-combined-v4','/opt/fyp-phase8-continuation-v5')
    (HERE/'bootstrap-transfer.py').write_text(reference,encoding='utf-8')

if __name__=='__main__':
    main()
