"""Seal this stopped-run record without altering any earlier freeze or outcome."""
from __future__ import annotations
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    root = Path(__file__).resolve().parents[3]
    folder = root/'artifacts/phase-8-launch/v1'
    files = {p.relative_to(root).as_posix():sha(p) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='operational-checksums.json'}
    report = root/'artifacts/phase-8.5-report.md'
    files[report.relative_to(root).as_posix()] = sha(report)
    recovery = Path('C:/fyp-p85/stopped-attempt1')
    evidence = {p.relative_to(recovery).as_posix():sha(p) for p in recovery.rglob('*') if p.is_file()}
    output = folder/'operational-checksums.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump({'kind':'STOPPED_RUN_OPERATIONAL_CHECKSUMS_NOT_PROTOCOL_FREEZE','at_utc':datetime.now(UTC).isoformat(),'run_id':'p85-01a116f7-3b82-7a79-8653-3aee62dc99e9','campaign_completed':False,'project_files':files,'recovery_root':str(recovery),'recovered_files':evidence,'new_freeze_or_launch_authorization':False},stream,indent=2)
    loaded = json.loads(output.read_text())
    if any(sha(root/n)!=v for n,v in loaded['project_files'].items()) or any(sha(recovery/n)!=v for n,v in loaded['recovered_files'].items()):
        raise ValueError('OPERATIONAL_EVIDENCE_HASH_DRIFT')
    print(json.dumps({'status':'PASS','project_files':len(files),'recovered_files':len(evidence),'checksums_sha256':sha(output),'campaign_completed':False}))

if __name__ == '__main__':
    main()
