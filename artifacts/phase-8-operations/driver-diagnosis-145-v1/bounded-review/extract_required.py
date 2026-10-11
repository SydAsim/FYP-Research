"""PREPARED ONLY: extract required members from a hash-verified original archive."""
import argparse, hashlib, json, sqlite3, tarfile
from pathlib import Path

SHA='8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24'
SIZE=37906551
EXECUTION='01a11705-11f1-7386-a804-76b957c218d5'

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('archive',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.archive.stat().st_size!=SIZE:raise ValueError('ARCHIVE_SIZE')
    with args.archive.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=SHA:raise ValueError('ARCHIVE_HASH')
    required=['ledger.sqlite3',f'executions/{EXECUTION}/export.json',f'executions/{EXECUTION}/checkpoint.json']
    with tarfile.open(args.archive,'r:gz') as tar:
        manifest_member=tar.getmember('slot/manifest.json')
        if not manifest_member.isfile() or manifest_member.size>2*1024**2:raise ValueError('MANIFEST_SIZE_TYPE')
        manifest_raw=tar.extractfile(manifest_member).read()
        manifest=json.loads(manifest_raw)['files'];records={}
        for name in required:
            member=tar.getmember('slot/'+name)
            if not member.isfile() or member.size>16*1024**2:raise ValueError('REQUIRED_MEMBER_SIZE_TYPE')
            raw=tar.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest()!=manifest[name]:raise ValueError('REQUIRED_MEMBER_HASH')
            records[name]=raw
    # No output exists until all required hashes pass. Never overwrite evidence.
    args.output.mkdir(exist_ok=False)
    (args.output/'manifest.json').write_bytes(manifest_raw)
    for name,raw in records.items():
        destination=args.output/name;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
    export=json.loads(records[f'executions/{EXECUTION}/export.json'])
    if export['execution_id']!=EXECUTION:raise ValueError('EXECUTION_IDENTITY')
    with sqlite3.connect((args.output/'ledger.sqlite3').resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        integrity=db.execute('PRAGMA integrity_check').fetchall()
        if integrity!=[('ok',)]:raise ValueError('LEDGER_INTEGRITY')
        tables=db.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
        # Save schema first; no guesses about checkpoint/notice table columns.
        (args.output/'ledger-schema.json').write_text(json.dumps(tables,indent=2))
    diagnostic={'archive_sha256':SHA,'execution_id':EXECUTION,'status':export['status'],'failure':export.get('failure'),'http':export.get('http'),'checkpoints':export.get('checkpoints'),'driver_finished_at':export.get('driver_finished_at'),'finished_at':export.get('finished_at'),'original_deadline':export.get('original_deadline'),'manifest_hash':hashlib.sha256(manifest_raw).hexdigest(),'required_hashes':{n:manifest[n] for n in required}}
    (args.output/'diagnostic-records.json').write_text(json.dumps(diagnostic,indent=2))
    print(json.dumps({'status':'VERIFIED_REQUIRED_MEMBERS_EXTRACTED','execution_id':EXECUTION,'output':str(args.output)}))

if __name__=='__main__':main()
