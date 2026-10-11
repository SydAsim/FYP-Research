"""Only wrapper invocation correction; preserve accepted source and failed attempt."""
import ast
import difflib
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'v7'


def main() -> None:
    for name in ('ops.py','preflight.py','host_checks.py','render_checks.py'):
        content=(PREVIOUS/name).read_text()
        if name=='preflight.py':
            content=content.replace("explicit=prior['projected_explicit_resources_usd']+elapsed*160*.096/730",
                                   "explicit=prior['projected_explicit_resources_usd']+elapsed*160*.096/730+read(HERE.parent/'v7/feasibility-at-stop.json')['new_boot_compute_upper_bound_usd']")
        (HERE/name).write_text(content,encoding='utf-8',newline='\n')
    # Reuse the exact version-pinned objects already uploaded; no fresh PUT.
    for name in ('source-expanded-proof.json','authority-proof.json','source-proof.json'):
        (HERE/name).write_bytes((PREVIOUS/name).read_bytes())
    qualified=(HERE.parent/'v5/transfer-env-attempt2.sh').read_text()
    script=qualified.replace('continuation-v5','continuation-v7')
    script=script.replace('95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26',
                          '3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46')
    script=script.replace('805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627',
                          '9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817')
    script=script.replace('V5_', 'V7_')
    script=script.replace("write_new(dep/'source-ready.json'", "write_new(dep/'source-and-authority-ready.json'")
    script=script.replace("read(dep/'source-ready.json')", "read(dep/'source-and-authority-ready.json')")
    invocation='timeout --signal=TERM --kill-after=5s 600s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v7/deployment/bootstrap-transfer.py'
    assert invocation in script
    environment='export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages'
    assert environment in script and script.index(environment)<script.index(invocation)
    probe='''/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'TRANSPORT_CHECK'
import importlib.metadata,json,sys
from pathlib import Path
import boto3,botocore
assert sys.version_info[:3]==(3,12,13)
assert sys.executable=='/opt/fyp-phase8-combined-v4/.venv/bin/python'
assert Path(boto3.__file__).resolve().is_relative_to(Path('/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages').resolve())
record={'status':'PASS','interpreter':sys.executable,'python':sys.version,'boto3':boto3.__version__,'botocore':botocore.__version__,'boto3_path':boto3.__file__,'qualified_v5_transport_environment':True,'dependency_install':False}
with Path('/var/lib/p8-continuation-v7/deployment/transport-import-attempt2.json').open('x') as output:json.dump(record,output,indent=2)
print(json.dumps(record))
TRANSPORT_CHECK
'''
    ast.parse(probe.split("<<'TRANSPORT_CHECK'\n",1)[1].rsplit('TRANSPORT_CHECK',1)[0])
    script=script.replace(invocation,probe+invocation)
    (HERE/'prepare-source-attempt2.sh').write_text(script,encoding='utf-8',newline='\n')
    (HERE/'wrapper.diff').write_text(''.join(difflib.unified_diff((PREVIOUS/'prepare-source.sh').read_text().splitlines(keepends=True),script.splitlines(keepends=True),fromfile='retained-failed-wrapper',tofile='qualified-v5-environment-wrapper')))
    package=HERE.parents[1]/'phase-8-continuation/v7/v7-complete-continuation-review-candidate.tar.gz'
    with package.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
    check={'status':'PASS_BEFORE_BOOT_COMMAND_SELECTION','at_utc':datetime.now(UTC).isoformat(),
           'qualified_reference_sha256':hashlib.sha256(qualified.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(script.encode()).hexdigest(),
           'interpreter':'/opt/fyp-phase8-combined-v4/.venv/bin/python','transport_pythonpath':'/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages',
           'environment_set_before_bootstrap':True,'read_only_import_probe_before_transfer':True,
           'frozen_archive_unchanged':True,'completed_qualification_repeated':False,'live_import_required':True,'dependencies_installed':False}
    (HERE/'wrapper-selection-check.json').write_text(json.dumps(check,indent=2))
    authorization={'at_utc':datetime.now(UTC).isoformat(),'kind':'EXPLICIT_HUMAN_AUTHORIZATION_SECOND_GUARDED_V7_PREPARATION',
        'package_hash':'9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817',
        'verbatim_user_instruction':'''Correct only the deployment-wrapper invocation using the already-qualified v5 transport environment. Set it before executing bootstrap-transfer.py. Check the command and interpreter/environment selection before another boot. Retain the failed attempt; do not install dependencies, modify frozen v7 or repeat completed qualification.
I authorize another guarded preparation attempt and continuation under the accepted v7 package and existing limits.
Recheck feasibility and establish/read back a fresh independent preparation-stop guard before starting the retained host. Account for superseded preparation schedules so an old trigger cannot unexpectedly stop the resumed campaign; replace or disable only owned obsolete preparation guards after their replacement is verified.
Verify the exact transport interpreter can import boto3 before transfer. Complete the existing source, metadata, backup, readiness and timer gates, then resume at slot 83.
Preserve all 82 originals and 1,418 pending identities. No replay, replacement, silent patching or gate bypass. If frozen-code changes are required, stop and report them.
Report actual admission or the exact failed gate, plus host state. Follow the reviewed preservation/shutdown procedure on failure.''',
        'actual_admission':False,'guard_usd':60,'total_usd':65,'original_deadline':'2026-10-22T15:24:23.810674Z'}
    (HERE/'human-acceptance.json').write_text(json.dumps(authorization,indent=2))
    print(json.dumps(check,indent=2))


if __name__=='__main__':
    main()
