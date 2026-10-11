from pathlib import Path
import json,hashlib

def verify_preserved() -> dict[str, int]:
    parent=Path('E:/p8v4/source')
    inv=json.loads((parent/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json').read_text())
    for name,digest in inv['files'].items():
        if hashlib.sha256((parent/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('PARENT_SOURCE_DRIFT: '+name)
    return {'parent_members':len(inv['files'])}
