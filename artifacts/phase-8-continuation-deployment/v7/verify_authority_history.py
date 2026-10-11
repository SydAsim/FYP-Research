"""Verify transitive signed history; no source changes, scenarios or AWS actions."""
import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]


def canonical(value: object) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main() -> None:
    owner=Path.home()/'.fyp-research/phase8-owner/phase84-final-v2'
    key=(owner/'owner.key').read_bytes()
    root=REPO/'artifacts/phase-8-freeze/v1'
    original=json.loads((root/'freeze-manifest.json').read_text())
    assert digest(root/'freeze-manifest.json')=='0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2'
    body={k:v for k,v in original.items() if k!='signature'}
    assert hmac.compare_digest(original['signature'],hmac.new(key,canonical(body),'sha256').hexdigest())
    predecessor=None
    for kind in ('REVIEW_ACCEPTED','FREEZE','LAUNCH'):
        raw=json.loads((owner/'receipts'/(kind+'.json')).read_text())
        assert raw['kind']==kind and raw['predecessor_hash']==predecessor
        body={k:v for k,v in raw.items() if k!='signature'}
        assert hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest())
        predecessor=hashlib.sha256(canonical(raw)).hexdigest()
    anchor=predecessor
    previous=digest(root/'freeze-manifest.json')
    records=[]
    for version in ('v1','v3','v4','v5','v7'):
        folder=REPO/'artifacts/phase-8-continuation-freeze'/version
        manifest=json.loads((folder/'freeze-manifest.json').read_text())
        att=json.loads((folder/'freeze-attestation.json').read_text())
        sha=digest(folder/'freeze-manifest.json')
        assert att['manifest_sha256']==sha
        assert hmac.compare_digest(att['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
        assert manifest['parent_freeze_sha256']==digest(root/'freeze-manifest.json')
        if version!='v1':assert manifest['immediate_parent_freeze_sha256']==previous
        predecessor=anchor
        for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
            path=folder/(kind+'.json');raw=json.loads(path.read_text())
            body={k:v for k,v in raw.items() if k!='signature'}
            assert raw['kind']==kind and raw['predecessor_hash']==predecessor
            assert raw['package_hash']==manifest['package_hash']
            assert hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest())
            assert digest(path)==manifest['files'][path.name]
            predecessor=hashlib.sha256(canonical(raw)).hexdigest()
        archives=[name for name in manifest['files'] if '/' not in name and name.endswith('.tar.gz')]
        for name in archives:assert digest(folder/name)==manifest['files'][name]
        records.append({'version':version,'freeze_manifest_sha256':sha,'parent':previous,
                        'manifest_and_receipt_HMACs':'PASS','top_level_archive_hashes':'PASS'})
        previous=sha
    result={'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'original_authority':'PASS',
            'transitive_history':records,'current_full_member_verification':'freeze-verification.json 2454 members PASS',
            'private_key_disclosed':False,'main_admission':False}
    with (HERE/'authority-chain-verification.json').open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
