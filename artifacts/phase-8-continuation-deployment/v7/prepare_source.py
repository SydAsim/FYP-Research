"""Bind already verified freeze to the reviewed bounded transfer wrapper."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
freeze=json.loads((HERE.parents[1]/'phase-8-continuation-freeze/v7/freeze-verification.json').read_text())
assert freeze['status']=='PASS'
path=HERE/'source_script.py'
text=path.read_text()
assert text.count('V7_FREEZE_HASH_AFTER_VERIFICATION')==1
path.write_text(text.replace('V7_FREEZE_HASH_AFTER_VERIFICATION',freeze['freeze_manifest_sha256']),encoding='utf-8',newline='\n')
print('Deployment wrapper bound to verified freeze; accepted package unchanged')
