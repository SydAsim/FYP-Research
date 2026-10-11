"""Preserve v7 and copy only verified bytes to a new short candidate path."""
from __future__ import annotations
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path('E:/p8v7/source')
SOURCE = Path('E:/p8v8/source')
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
    parent=json.loads((BASE/PREFIX/'candidate-inventory.json').read_text())
    assert hashlib.sha256(canonical(parent['files'])).hexdigest()==parent['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
    assert not SOURCE.exists()
    for n,h in parent['files'].items():
        assert digest(BASE/n)==h,n
        target=SOURCE/n;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(BASE/n,target)
    freeze=HERE.parents[1]/'phase-8-continuation-freeze/v7/freeze-manifest.json'
    assert digest(freeze)=='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46'
    with sqlite3.connect((MASTER/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.execute('BEGIN');db.row_factory=sqlite3.Row
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        rows=[dict(r) for r in db.execute('SELECT * FROM slots ORDER BY sequence')]
    assert len(rows)==1500 and all(r['state']=='BACKED_UP' for r in rows[:120]) and all(r['state']=='PLANNED' for r in rows[120:])
    assert rows[120]['sequence']==121 and rows[120]['arm']=='P1' and rows[120]['attempt']==1
    target=SOURCE/PREFIX/'closed-120';shutil.copytree(MASTER,target)
    write(target/'ledger-read-only.json',{'rows':rows})
    inspection=Path('E:/p8clock120v1/inspection')
    for n in ('summary.json','read-only-ledger.json','campaign-journal.json','clock-journal.json','time-status.json','units-before-quiesce.json','units-after.json'):
        shutil.copyfile(inspection/n,target/n)
    write(HERE/'preservation-before.json',{'parent_package_hash':parent['package_hash'],'parent_files':len(parent['files']),'parent_freeze_sha256':digest(freeze),'master_files':{p.relative_to(MASTER).as_posix():digest(p) for p in MASTER.rglob('*') if p.is_file()},'counts':{'BACKED_UP':120,'PLANNED':1380},'next':rows[120],'mutations':0})
    print('Verified parent and preserved stopped master; candidate source copied.')

if __name__=='__main__':main()
