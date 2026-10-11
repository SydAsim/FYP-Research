"""Adapt deployment wrappers only; never alter accepted source or operate AWS."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'v5'
for name in ('ops.py','host_checks.py','make_transfer.py','source_script.py','render_checks.py'):
    text=(PREVIOUS/name).read_text().replace('p8v5','p8v7').replace('continuation-v5','continuation-v7')
    if name=='make_transfer.py':
        text=text.replace('phase-8-continuation-freeze/v5','phase-8-continuation-freeze/v7')
        text=text.replace('phase-8-continuation/v5/v5-complete','phase-8-continuation/v7/v7-complete')
    if name=='source_script.py':
        text=text.replace('95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26', 'V7_FREEZE_HASH_AFTER_VERIFICATION')
        text=text.replace('805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627',
                          '9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817')
        text=text.replace('V5_', 'V7_')
        # Transfer already writes source-ready; additional authority verification
        # must retain it and produce its own evidence instead of overwriting.
        text=text.replace("write_new(dep/'source-ready.json'", "write_new(dep/'source-and-authority-ready.json'")
        text=text.replace("read(dep/'source-ready.json')", "read(dep/'source-and-authority-ready.json')")
    if name=='host_checks.py':
        text=text.replace('from handover import ContinuationPolicy,ro_rows','from handover import ro_rows\nfrom operational_limits import effective_policy')
        text=text.replace("ContinuationPolicy.model_validate(read(RUNTIME/'original-launch-policy.json'))", "effective_policy(read(RUNTIME/'original-launch-policy.json'))")
        # Dedicated v7 root does not yet exist; measured free space is real while
        # fresh working/staging bytes are zero only after explicit absence checks.
    (HERE/name).write_text(text,encoding='utf-8',newline='\n')
print('Prepared separate deployment wrappers; accepted runtime unchanged')
