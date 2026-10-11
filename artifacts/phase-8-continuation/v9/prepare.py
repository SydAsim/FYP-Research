"""Verified copy and authorized storage overlay; no historical mutation."""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path('E:/p8v7/source')
QUALIFIED = Path('E:/p8v8/source')
SOURCE = Path('E:/p8v9/source')
PREFIX = 'artifacts/phase-8-runner-amendment/v4-complete'
MASTER = Path('E:/p8clock120v1/master/slot')

def digest(p: Path) -> str:
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def canonical(v: object) -> bytes:
    return json.dumps(v,sort_keys=True,separators=(',',':')).encode()

def write(p: Path, v: object) -> None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:
        json.dump(v,f,indent=2,default=str)

def main() -> None:
    inv=json.loads((HERE.parent/'v8/candidate-inventory.json').read_text())
    assert hashlib.sha256(canonical(inv['files'])).hexdigest()==inv['package_hash']=='715881dec6368acc40d89fa0a772e8fa285f7a40018002b566fbe8b0a5eed051'
    assert digest(HERE.parent/'v8/v8-complete-continuation-review-candidate.tar.gz')=='848523bfcc08957bee0157373421ce62405959bcd169ba02746972d0ddfa01e0'
    assert not SOURCE.exists()
    for n,h in inv['files'].items():
        assert digest(QUALIFIED/n)==h,n
        target=SOURCE/n;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(QUALIFIED/n,target)
    runtime=SOURCE/PREFIX
    proposal=json.loads((runtime/'operational-limit-proposal.json').read_text())
    proposal.update(version='phase85-continuation-v9',cloud_limit_bytes=80*1024**3,backup_archive_limit_bytes=80*1024**3,
        retention='Only newly completed redundant staging may be removed under the unchanged verified-copy safeguards. Preserve all 120 retained originals, every archive, raw trace, grade, receipt, pinned S3 version and unsuccessful attempt. No historical evidence deletion.')
    (runtime/'operational-limit-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    overlay=digest(runtime/'operational-limit-proposal.json')
    old='60d8dbb2b7f3f6a83bd442ac491316e9a9e17d45a039e4b59d9400821d377791'
    for name in ('operational_limits.py','handover.py','closed_restart.py'):
        path=runtime/name;text=path.read_text().replace(old,overlay).replace('phase85-continuation-v8','phase85-continuation-v9')
        if name=='operational_limits.py':
            text=text.replace('phase85-continuation-v7','phase85-continuation-v9').replace('Literal[64424509440]','Literal[85899345920]')
            text=text.replace('full 60GiB','full 80GiB').replace('+ 30 * self.s3_usd_gib_month','+ 50 * self.s3_usd_gib_month')
        if name=='closed_restart.py':text=text.replace('continuation-v8','continuation-v9')
        path.write_text(text)
    path=runtime/'controls.py'
    text=path.read_text().replace('Literal[32212254720, 64424509440]','Literal[32212254720, 64424509440, 85899345920]')
    path.write_text(text)
    write(HERE/'preparation-proof.json',{'status':'PASS','reused_v8_package':inv['package_hash'],
       'reused_v8_archive_sha256':'848523bfcc08957bee0157373421ce62405959bcd169ba02746972d0ddfa01e0',
       'parent_freeze_sha256':'3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46',
       'operational_limits_sha256':overlay,'verified_v8_files':len(inv['files']),
       'runtime_changed':['controls.py','operational_limits.py','operational-limit-proposal.json','handover.py','closed_restart.py'],
       'clock_sampling_runner_reuse_prepare_unchanged':all(digest(runtime/n)==digest(QUALIFIED/PREFIX/n) for n in ('clock_sampling.py','runner.py','reuse_prepare.py'))})
    print(json.dumps(json.loads((HERE/'preparation-proof.json').read_text()),indent=2))

if __name__=='__main__':main()
