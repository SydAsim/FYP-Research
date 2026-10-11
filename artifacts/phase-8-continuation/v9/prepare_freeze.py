"""Record actual conditional human authority and build external freeze wrapper."""
from __future__ import annotations
import json
from pathlib import Path
from prepare import HERE,write,digest

INSTRUCTION='''I authorize completing the storage correction, freezing the verified package, deploying it and resuming the campaign in one workflow, subject to the conditions below. Do not request another confirmation for actions within this authorization.
Reuse qualified v8, including the clock correction and exact 120-original handover. Resolve storage using the simplest justified option: caps up to 80 GiB for cloud/local backups, or reduced duplication of immutable historical metadata with independently verifiable recovery. I authorize either option if measured capacity, disk headroom and cost feasibility pass.
Keep the US$60 admission guard, US$65 total ceiling, original deadline, application behaviour, study, analysis and 600-second windows unchanged.
Preserve all 120 originals, grades, archives, pinned versions and unsuccessful attempts. Keep all 1,380 pending identities/order; next is sequence 121, P1, attempt 1. No replay, replacement or historical evidence deletion.
Run only focused checks required by the new change; reuse completed qualification. Assemble and verify the exact package against frozen v7, citing v8 evidence. Record this conditional authorization honestly, without claiming I personally reviewed unseen final code. Freeze its exact hashes and record deployment authority from this instruction.
Then verify fresh feasibility and the independent preparation-stop guard before starting the retained AWS host. Follow the reviewed deployment order and complete live readiness, backup-readback and timer gates before admission.
If any condition fails or work exceeds this scope, preserve evidence and stop safely. Do not bypass gates or silently patch frozen code. Report the exact package, actual admission, host state, backups and stop deadline.'''

def main():
    pkg=json.loads((HERE/'candidate-package.json').read_text())
    verification=json.loads((HERE/'final-verification.json').read_text())
    assert verification['status']=='PASS' and verification['overall_deployment_readiness']=='PASS_PREBOOT_CONDITIONAL_LIVE_GATES_REQUIRED'
    write(HERE/'conditional-human-authorization.json',{
      'kind':'CONDITIONAL_HUMAN_AUTHORIZATION_FOR_VERIFIED_STORAGE_COMPLETION_FREEZE_AND_DEPLOYMENT',
      'conditional_human_authorization':True,'personal_review_of_unseen_final_code_claimed':False,
      'package_hash':pkg['package_hash'],'archive_sha256':pkg['archive_sha256'],
      'operational_limits_sha256':pkg['operational_limits_sha256'],
      'verbatim_user_instruction':INSTRUCTION,
      'condition_evidence':{n:digest(HERE/n) for n in ('final-verification.json','qualification-result.json','estimates.json','resource-planning.json')},
      'fresh_actual_host_headroom_backup_timer_readiness_conditions_remain_required':True,
      'actual_deployment_or_admission':False})
    source=(HERE.parent/'v7/freeze_accepted.py').read_text()
    source=source.replace('v7 acceptance','v9 conditional authority').replace('continuation/v7','continuation/v9').replace('E:/p8v7/source','E:/p8v9/source')
    source=source.replace('IMMEDIATE_PARENT = "95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26"','IMMEDIATE_PARENT = "3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46"')
    source=source.replace('accepted.get("explicit_human_acceptance")','accepted.get("conditional_human_authorization")')
    source=source.replace('CURRENT_EXACT_HUMAN_ACCEPTANCE_REQUIRED','CONDITIONAL_HUMAN_AUTHORIZATION_AND_VERIFIED_CONDITIONS_REQUIRED')
    source=source.replace('v7-complete-continuation-review-candidate.tar.gz','v9-complete-continuation-candidate.tar.gz')
    source=source.replace('phase-8-continuation-freeze/v5','phase-8-continuation-freeze/v7')
    source=source.replace('phase-8-continuation-freeze/v7"\n    if sys.platform', 'phase-8-continuation-freeze/v9"\n    if sys.platform',1) if False else source
    # Only the newly created destination changes; the parent stays frozen v7.
    source=source.replace('frozen = REPO / "artifacts/phase-8-continuation-freeze/v7"','frozen = REPO / "artifacts/phase-8-continuation-freeze/v9"')
    source=source.replace('phase85-continuation-v7','phase85-continuation-v9')
    source=source.replace('"EXPLICIT_HUMAN_ACCEPTANCE"','"CONDITIONAL_HUMAN_AUTHORIZATION_CONDITIONS_VERIFIED_FOR_EXACT_FREEZE"')
    source=source.replace('"82-original metadata handover"','"120-original metadata handover and qualified v8 paired clock sampling"')
    source=source.replace('"60USD admission/60GiB evidence proposal"','"60USD admission/80GiB evidence conditional authorization"')
    source=source.replace('"acceptance_is_not_actual_launch": True,','"acceptance_is_not_actual_launch": True,\n        "personal_review_of_unseen_final_code_claimed": False,\n        "conditional_authorization_record": accepted,')
    (HERE/'freeze_authorized.py').write_text(source)
    preserve='''from pathlib import Path
import json,hashlib
def verify_preserved():
    root=Path('E:/p8v8/source')
    inv=json.loads((root/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json').read_text())
    for n,h in inv['files'].items():
        with (root/n).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=h:raise ValueError('QUALIFIED_V8_DRIFT:'+n)
    return {'qualified_v8_members':len(inv['files']),'retained_originals':120,'pending_originals':1380}
'''
    (HERE/'preserve.py').write_text(preserve)
    print(json.dumps({'package_hash':pkg['package_hash'],'archive_sha256':pkg['archive_sha256'],'conditional_authority_recorded':True,'personal_unseen_code_review_claimed':False},indent=2))

if __name__=='__main__':main()
