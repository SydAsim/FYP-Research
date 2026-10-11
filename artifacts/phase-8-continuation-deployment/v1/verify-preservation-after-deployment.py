"""Read-only final preservation check; no AWS or main execution."""
import hashlib,hmac,json,sys
from pathlib import Path
from datetime import datetime,timezone
repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'artifacts/phase-8-continuation/v1'))
from controls import canonical,hash_file,read,write_new
from verify_package import verify
checks=verify()
frozen=Path('\\\\?\\'+str(repo/'artifacts/phase-8-continuation-freeze/v1')) if sys.platform=='win32' else repo/'artifacts/phase-8-continuation-freeze/v1'
manifest=read(frozen/'freeze-manifest.json')
for name,expected in manifest['files'].items():
 if hash_file(frozen/name)!=expected:raise ValueError('FROZEN_MEMBER_DRIFT: '+name)
key=(Path.home()/'.fyp-research/phase8-owner/phase84-final-v2/owner.key').read_bytes()
att=read(frozen/'freeze-attestation.json')
if hash_file(frozen/'freeze-manifest.json')!=att['manifest_sha256'] or not hmac.compare_digest(hmac.new(key,canonical(manifest),'sha256').hexdigest(),att['signature']):raise ValueError('FREEZE_ATTESTATION_DRIFT')
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE','CONTINUATION_LAUNCH'):
 raw=read(Path.home()/'.fyp-research/phase8-owner/phase85-continuation-v1/receipts'/f'{kind}.json')
 if not hmac.compare_digest(hmac.new(key,canonical({k:v for k,v in raw.items() if k!='signature'}),'sha256').hexdigest(),raw['signature']):raise ValueError('RECEIPT_SIGNATURE_DRIFT')
result={'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),'history':checks,'freeze_members_verified':len(manifest['files']),'freeze_manifest_sha256':hash_file(frozen/'freeze-manifest.json'),'freeze_attestation_sha256':hash_file(frozen/'freeze-attestation.json'),'accepted_package_hash':manifest['package_hash'],'continuation_receipt_signatures':'PASS','note':'Historical preview counts are deliberately unchanged; actual AWS ledger status is recorded separately.'}
write_new(Path(__file__).parent/'postdeployment-preservation-verification.json',result)
print(json.dumps(result))

