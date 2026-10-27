"""Verify existing immutable package, never freeze/sign/modify it."""
import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path
from read_control import record

def read(p: Path) -> dict:
    return json.loads(p.read_text(encoding='utf-8'))

def canonical(v: object) -> bytes:
    return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def sha(p: Path) -> str:
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def main() -> None:
    repo=Path(__file__).resolve().parents[4]
    frozen=repo/'artifacts/phase-8-continuation-freeze/v10'
    manifest=read(frozen/'freeze-manifest.json')
    key=Path('C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2/owner.key').read_bytes()
    assert hmac.compare_digest(read(frozen/'freeze-attestation.json')['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
    for name,want in manifest['files'].items():
        assert sha(frozen/name)==want, 'FREEZE_RECEIPT_DRIFT'
        value=read(frozen/name);signature=value.pop('signature')
        assert hmac.compare_digest(signature,hmac.new(key,canonical(value),'sha256').hexdigest()), 'RECEIPT_SIGNATURE_DRIFT'
    archive=Path(manifest['archive_path'])
    assert archive.stat().st_size==manifest['archive_bytes']
    assert sha(archive)==manifest['archive_sha256']=='212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37'
    source=Path('E:/p8v10/source');inv=source/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json'
    assert sha(inv)==manifest['source_inventory_sha256']
    inventory=read(inv)
    assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']==manifest['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
    for name,digest in inventory['files'].items():
        assert sha(source/name)==digest, 'SOURCE_DRIFT:'+name
    assert sha(repo/'artifacts/phase-8-continuation-freeze/v9/freeze-manifest.json')==manifest['parent_frozen_v9_manifest_sha256']
    record('existing-freeze-verification.json',{'status':'PASS_EXISTING_HASHES_AND_RECEIPT_SIGNATURES',
        'at':datetime.now(UTC).isoformat(),'package_hash':inventory['package_hash'],'archive_sha256':manifest['archive_sha256'],
        'freeze_manifest_sha256':sha(frozen/'freeze-manifest.json'),'source_files':len(inventory['files']),
        'qualification_repeated':False,'refreeze':False,'launch_receipt_issued':False})
    print('PASS_EXISTING_FREEZE_UNCHANGED')

if __name__=='__main__':
    main()
