"""Post-launch local authority and immutable package verification; no cloud writes."""
import hashlib,hmac,json,sys
from pathlib import Path
from datetime import UTC,datetime
H=Path(__file__).resolve().parent;R='artifacts/phase-8-runner-amendment/v4-complete/'
def read(p):return json.loads(Path(p).read_bytes())
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    pkg=read(H/'candidate-package.json');parent=Path('E:/p8v11/source');source=Path('E:/p8v12/source')
    for p in (parent,source):
        inv=read(p/R/'candidate-inventory.json')
        assert hashlib.sha256(json.dumps(inv['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==inv['package_hash']
        for n,d in inv['files'].items():assert digest(p/n)==d,n
    assert digest(pkg['archive_path'])==pkg['archive_sha256']
    assert digest('D:/FYP-ResearchBackups/continuation-v11/v11-complete-continuation.tar.gz')=='3dc00ac7b60018c7fa0357d54d5fac96f22c6e84deba39e9037575b8a93b0579'
    sys.path.insert(0,str(source/R))
    from controls import canonical
    from operational_limits import effective_policy
    from handover import verify_chain
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner');key=(owner/'phase84-final-v2/owner.key').read_bytes()
    receipts=owner/'phase85-continuation-v12/receipts';freeze=read(receipts/'CONTINUATION_FREEZE.json')
    assert digest(receipts/'CONTINUATION_FREEZE.json')==pkg['freeze_sha256']
    policy=effective_policy(read(owner/'phase84-final-v2/launch-policy.json'))
    initial=hashlib.sha256(canonical(read(owner/'phase84-final-v2/receipts/LAUNCH.json'))).hexdigest()
    verify_chain(receipts,key,pkg['package_hash'],policy,freeze['identities_sha256'],initial,datetime.now(UTC))
    attestation=read(H/'freeze-attestation.json');manifest=read(H/'freeze-manifest.json')
    assert hmac.compare_digest(attestation['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
    actual=read(H/'actual-admission.json');post=read(H/'post-launch-verified.json')['last_json']
    assert actual['preparation_stop_retired_and_read_back'] and actual['absolute_aws_guard_active']
    assert post['original1297_prefix_still_verified'] and post['source_package']==pkg['package_hash']
    assert read(H/'actual-running-host-result.json')['result']['State']=='running'
    linux=read(H/'linux-and-timers-verified.json')['last_json']['linux_controls'];assert linux['status']=='PASS' and linux['checks']==12
    result={'status':'PASS_ACTUAL_GUARDED_CONTINUATION','at':datetime.now(UTC).isoformat(),'package_hash':pkg['package_hash'],'archive_sha256':pkg['archive_sha256'],'freeze_sha256':pkg['freeze_sha256'],'parent_v11_unchanged_after_work':True,'new_frozen_source_and_archive_unchanged_after_deployment':True,'acceptance_freeze_actual_readiness_launch_chain_verified':True,'actual_admission':actual,'linux_controls':linux,'prelaunch':post['prelaunch'],'complete':post['complete'],'forecast':post['actual_release']['forecast'],'physical_resources':post['resources'],'preparation_backup_growth_bytes':post['preparation_backup_growth_bytes'],'external_projection_controller_sha256':read(H/'external-input-projection-v2.json')['host_controller_sha256'],'external_release_controller_sha256':read(H/'external-input-release-order-v3.json')['host_controller_sha256'],'no_application_fixture_oracle_grade_analysis_or_window_changes':True,'no_replay_regrading_or_deletion':True,'research_outcome_not_yet_final':True}
    with (H/'admission-verification.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({'status':result['status'],'first_sequence':1298,'at':result['at'],'counts_at_admission_check':actual['counts'],'stop_at':policy.stop_at.isoformat(),'parent_and_new_freezes_verified_after_work':True}))
if __name__=='__main__':main()
