"""Four bounded, pinned read-only ranges; retain pieces on any failure."""
from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
proof = json.loads((Path('E:/p8clock120v1/master/slot/backups') /
    '01a11705-11f1-7762-8513-93ef9d42c433.json').read_text())['cloud']
size = proof['bytes']
def piece(number: int) -> Path:
    begin, end = size*number//4, size*(number+1)//4-1
    target = HERE/f'original120-part-{number}.bin'
    assert not target.exists()
    command = ['aws','s3api','get-object','--profile','fyp-research','--region','ap-southeast-2',
        '--bucket',proof['bucket'],'--key',proof['key'],'--version-id',proof['version_id'],
        '--range',f'bytes={begin}-{end}','--no-cli-pager',str(target)]
    with (HERE/f'original120-part-{number}-request.json').open('x') as output:
        json.dump({'command': command, 'timeout_seconds':240}, output, indent=2)
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=240)
        record = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as error:
        record = {'exit':'TIMEOUT', 'detail': str(error)}
    with (HERE/f'original120-part-{number}-result.json').open('x') as output:
        json.dump(record, output, indent=2)
    if record['exit'] != 0:
        raise RuntimeError(f'FAILED_RANGE_{number}_RETAINED')
    response = json.loads(record['stdout'])
    assert response['VersionId'] == proof['version_id']
    assert response['ContentRange'] == f'bytes {begin}-{end}/{size}'
    assert target.stat().st_size == end-begin+1
    return target

with ThreadPoolExecutor(max_workers=4) as pool:
    pieces = list(pool.map(piece, range(4)))
archive = HERE/'original120.tar.gz'
with archive.open('xb') as output:
    for part in pieces:
        output.write(part.read_bytes())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert digest == proof['sha256'] and archive.stat().st_size == size
with (HERE/'original120-download-proof.json').open('x') as output:
    json.dump({'status':'PASS','pinned': proof,'local_sha256':digest,'local_bytes':size},output,indent=2)
print(json.dumps({'status':'PASS','bytes':size,'sha256':digest}))
