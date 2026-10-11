"""Reuse bounded qualified transfer with actual frozen v9 object bindings."""
import json
import tarfile
from pathlib import Path
from ops import HERE
from controls import read,write_new

def main():
    repo=HERE.parents[2];frozen=repo/'artifacts/phase-8-continuation-freeze/v9'
    receipts=Path.home()/'.fyp-research/phase8-owner/phase85-continuation-v9/receipts'
    with tarfile.open(HERE/'public-authority.tar.gz','x:gz') as out:
        for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
            out.add(receipts/(kind+'.json'),arcname=kind+'.json',recursive=False)
        for name in ('freeze-manifest.json','freeze-attestation.json','freeze-verification.json','acceptance-statement.json'):
            out.add(frozen/name,arcname=name,recursive=False)
        out.add(HERE/'actual-deployment-binding.json',arcname='explicit-deployment-authorization.json',recursive=False)
    proof=read(HERE/'source-proof.json')
    archive=repo/'artifacts/phase-8-continuation/v9/v9-complete-continuation-candidate.tar.gz'
    with tarfile.open(archive) as incoming:proof['expanded_bytes']=sum(m.size for m in incoming)
    proof['label']='package.tar.gz';write_new(HERE/'source-expanded-proof.json',proof)

if __name__=='__main__':main()
