"""Read a retained original; no oracle rerun or outcome edits."""
from __future__ import annotations
import hashlib
import json
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
archive = HERE/'original120.tar.gz'
before = hashlib.sha256(archive.read_bytes()).hexdigest()
assert before == 'f061057a2dec11196dd82231e37e6ae8502416e5402cba2d9b7524c3df59e2b2'
with tarfile.open(archive, 'r:gz') as source:
    def read(name: str) -> Any:
        handle = source.extractfile(name)
        assert handle is not None
        return json.load(handle)
    names = source.getnames()
    manifest = read('slot/manifest.json')
    for name, digest in manifest['files'].items():
        stream = source.extractfile('slot/'+name)
        assert stream is not None
        assert hashlib.sha256(stream.read()).hexdigest() == digest
    boot_name = next(n for n in names if n.endswith('/linux-boot.json'))
    export_name = next(n for n in names if n.endswith('/export.json'))
    boot, row = read(boot_name), read(export_name)
    polls = [read(n) for n in sorted(names) if '/polls/' in n and n.endswith('.json')]
    at = [datetime.fromisoformat(p['at']) for p in polls]
    gaps = [(b-a).total_seconds() for a,b in zip(at,at[1:])]
    anchor = json.loads(Path('E:/p8clock120v1/inspection/host-clock.json').read_text())
    assert boot['boot_id'] == anchor['boot_id']
    deadline = datetime.fromisoformat(row['original_deadline'])
    near = [{'at':p['at'],'ended_at':p.get('ended_at'),'host_at':p['host'].get('at')}
            for p in polls if '2026-10-09T23:14:20'<=p['at']<='2026-10-09T23:15:10']
    result = {
        'status':'PASS', 'original_archive_sha256':before,
        'all_manifest_files_verified':len(manifest['files']), 'boot':boot,
        'boot_matches_clock_anchor':True, 'export_sha256': manifest['files'][export_name.removeprefix('slot/')],
        'export_keys':list(row),'original_deadline':row['original_deadline'],
        'started_at':row.get('started_at'),'finished_at':row.get('finished_at'),
        'driver_error':row.get('driver_error'),'collection_errors':row.get('collection_errors',[]),
        'poll_count':len(polls), 'min_poll_gap_seconds':min(gaps),'max_poll_gap_seconds':max(gaps),
        'negative_poll_gaps':sum(g<0 for g in gaps),'first_poll_at':polls[0]['at'],
        'last_poll_at':polls[-1]['at'],'last_poll_ended_at':polls[-1].get('ended_at'),
        'last_poll_minus_original_deadline_seconds':(at[-1]-deadline).total_seconds(),
        'near_trigger_poll_times':near,
        'recorded_final_requests':row.get('final_requests'),
        'observation_windows':[{k:v for k,v in w.items() if k not in ('polls','snapshot')}
                               for w in row.get('observation_windows',[])],
        'real_time_pairs_recorded':False,
        'grade_recomputed':False,'raw_export_modified':False,
    }
assert hashlib.sha256(archive.read_bytes()).hexdigest() == before
with (HERE/'original120-timing-review.json').open('x',encoding='utf-8') as out:
    json.dump(result,out,indent=2)
print(json.dumps(result,indent=2))
