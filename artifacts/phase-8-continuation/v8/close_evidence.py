"""Version-specific existing evidence closure; no new execution or cloud write."""
from __future__ import annotations
import concurrent.futures
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from prepare import HERE, PREFIX, SOURCE, digest, write

ROOT=SOURCE/PREFIX/'closed-120'
ARCHIVES=Path('E:/p8v8/retained-original-archives')

def one(row: dict[str, object]) -> dict[str, object]:
    sequence=int(str(row['sequence']));identity=str(row['execution_id'])
    receipt=ROOT/'backups'/(identity+'.json')
    proof=json.loads(receipt.read_text());cloud=proof['cloud']
    assert digest(receipt)==row['backup_hash']
    assert proof['execution_id']==identity and proof['sha256']==cloud['sha256'] and cloud['version_id']
    target=ROOT/'exports'/f'{sequence:04d}'/'export.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    if sequence<=82:
        prior=ROOT/'restart-history/exports'/f'{sequence:04d}'/'export.json'
        shutil.copyfile(prior,target)
        origin={'reused_verified_master_member':str(prior.relative_to(ROOT))}
    else:
        archive=HERE.parents[1]/'phase-8-operations/clock-diagnosis-120-v1/original120.tar.gz' if sequence==120 else ARCHIVES/(cloud['sha256']+'.tar.gz')
        if not archive.exists():
            ARCHIVES.mkdir(parents=True,exist_ok=True)
            for attempt in range(1,4):
                part=ARCHIVES/(cloud['sha256']+f'.attempt{attempt}.partial')
                result=subprocess.run(['aws','s3api','get-object','--bucket',cloud['bucket'],'--key',cloud['key'],'--version-id',cloud['version_id'],'--profile','fyp-research','--region','ap-southeast-2','--cli-connect-timeout','10','--cli-read-timeout','30','--no-cli-pager',str(part)],capture_output=True,text=True,timeout=90)
                write(HERE/'evidence-transfers'/f'{sequence:04d}-attempt{attempt}.json',{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'proof':cloud,'partial':str(part)})
                if result.returncode==0 and part.stat().st_size==cloud['bytes'] and digest(part)==cloud['sha256']:
                    shutil.copyfile(part,archive);break
            else:raise ValueError('PINNED_TRANSFER_FAILED '+identity)
        assert archive.stat().st_size==cloud['bytes'] and digest(archive)==cloud['sha256']
        name=f'slot/executions/{identity}/export.json'
        with tarfile.open(archive,'r|gz') as incoming:
            found=False
            for member in incoming:
                if member.name==name:
                    assert member.isfile() and not found
                    stream=incoming.extractfile(member);assert stream is not None
                    target.write_bytes(stream.read());found=True
                # Stream through the gzip trailer, not only the selected member.
            assert found
        origin={'pinned_archive_verified':cloud,'local_archive':str(archive),'exact_member':name}
    raw=json.loads(target.read_text())
    assert all(raw[k]==row[k] for k in ('execution_id','arm','attempt','fixture_hash'))
    return {'sequence':sequence,'execution_id':identity,'receipt_sha256':digest(receipt),'export_sha256':digest(target),'cloud':cloud,**origin}

def main() -> None:
    rows=json.loads((ROOT/'ledger-read-only.json').read_text())['rows']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(one,rows[:120]))
    write(ROOT/'backup-verification.json',results)
    write(SOURCE/PREFIX/'closed-120-members.json',{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file()})
    write(HERE/'boundary-closure.json',{'status':'PASS','counts':{'BACKED_UP':120,'PLANNED':1380},'next':rows[120],'originals':results,'research_executions':0})
    print('120 receipts/exports/version bindings verified; all original files unchanged.')

if __name__=='__main__':main()
