"""Correct the operator verifier's receipt-versus-manifest anchor; retain attempt 1."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
text=(HERE/'verify_authority_history.py').read_text()
text=text.replace("assert digest(root/'freeze-manifest.json')=='0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2'",
    "original_freeze_sha=digest(owner/'receipts/FREEZE.json')\n    assert original_freeze_sha=='0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2'")
text=text.replace("previous=digest(root/'freeze-manifest.json')", "previous=original_freeze_sha")
text=text.replace("manifest['parent_freeze_sha256']==digest(root/'freeze-manifest.json')", "manifest['parent_freeze_sha256']==original_freeze_sha")
text=text.replace("'transitive_history':records", "'transitive_history':records,'original_parent_anchor':'Signed original FREEZE receipt SHA, not manifest SHA','first_operator_reference_assertion_retained':True")
path=HERE/'verify_authority_history_v2.py'
with path.open('x') as output:output.write(text)
print('Separate operator verifier corrected; original failure retained; frozen source unchanged')
