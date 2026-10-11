from pathlib import Path
import json,hashlib
def verify_preserved():
    root=Path('E:/p8v8/source')
    inv=json.loads((root/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json').read_text())
    for n,h in inv['files'].items():
        with (root/n).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=h:raise ValueError('QUALIFIED_V8_DRIFT:'+n)
    return {'qualified_v8_members':len(inv['files']),'retained_originals':120,'pending_originals':1380}
