"""Record the human's exact acceptance; never launches AWS or signs readiness."""
import json
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parents[1] / 'phase-8-continuation/v7'
STATEMENT = '''I accept the exact v7 combined candidate identified by its candidate-package.json. Record its package/archive hashes, freeze it against frozen v5 and verify the complete authority chain.

I explicitly accept:

- US$60 admission guard, with US$65 total ceiling unchanged.
- 60-GiB cloud all-version and dedicated local-backup caps.
- Removal only of verified redundant future staging under the reviewed safeguards. Preserve all 82 originals, raw evidence, archives, pinned S3 versions and unsuccessful attempts.

After successful freeze verification, I separately authorize the reviewed retained-host AWS deployment and continuation from sequence 83.

Recalculate feasibility and verify the independent preparation-stop guard before boot. Complete all live readiness gates and the prelaunch backup → genuine readiness/launch records → complete backup sequence before admission.

Keep the original deadline, study, analysis, saved identities/order and 600-second windows unchanged. No replay, replacement, broad retesting or silent patching. If a gate fails, preserve evidence and follow the reviewed safe-stop procedure.

Proceed without another confirmation for these authorized actions. Report the actual admitted execution, host state, verified backup status and stop deadline.'''


def main() -> None:
    package = json.loads((CANDIDATE/'candidate-package.json').read_text())
    assert package['package_hash'] == '9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
    assert package['archive_sha256'] == 'c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
    accepted = {k:package[k] for k in ('package_hash','archive_sha256','operational_limits_sha256')}
    accepted.update(explicit_human_acceptance=True,at_utc=datetime.now(UTC).isoformat(),
                    verbatim_user_instruction=STATEMENT,conditional_deployment_authorization=True,
                    actual_host_bound=False,actual_admission=False)
    with (HERE/'human-acceptance.json').open('x',encoding='utf-8') as output:
        json.dump(accepted,output,indent=2,ensure_ascii=False)
    print('Exact acceptance recorded; freeze and live gates still required')


if __name__ == '__main__':
    main()
