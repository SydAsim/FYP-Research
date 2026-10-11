"""Inspect preserved metadata through immutable, read-only SQLite connections."""
from __future__ import annotations

import collections
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = Path('E:/p8clock120v1/master/slot')
INSPECT = Path('E:/p8clock120v1/inspection')
def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

before = {str(p.relative_to(ROOT)): sha(p) for p in ROOT.rglob('*') if p.is_file()}
manifest = read(ROOT/'manifest.json')
for name, digest in manifest['files'].items():
    assert sha(ROOT/name) == digest
db = sqlite3.connect((ROOT/'campaign.sqlite3').as_uri()+'?mode=ro&immutable=1', uri=True)
db.row_factory = sqlite3.Row
assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
rows = [dict(row) for row in db.execute('SELECT * FROM slots ORDER BY sequence')]
assert rows == read(INSPECT/'read-only-ledger.json')['rows']
assert collections.Counter(row['state'] for row in rows) == {'BACKED_UP':120, 'PLANNED':1380}
bindings = read(ROOT/'bindings.json')
assert [{k: row[k] for k in bindings[0]} for row in rows] == bindings
previous = 'GENESIS'
events: list[dict[str, Any]] = []
for row in db.execute('SELECT * FROM notices ORDER BY n'):
    assert row['previous'] == previous
    assert hashlib.sha256((row['body']+previous).encode()).hexdigest() == row['hash']
    previous = row['hash']
    events.append({'n': row['n'], **json.loads(row['body'])})
db.close()
for row in rows[:120]:
    proof = ROOT/'backups'/(row['execution_id']+'.json')
    assert sha(proof) == row['backup_hash']
    assert read(proof)['execution_id'] == row['execution_id']
anchor = read(ROOT/'host-clock.json')
assert anchor == read(INSPECT/'host-clock.json')
assert read(ROOT/'continuation-readiness.json')['boot_anchor_sha256'] == sha(ROOT/'host-clock.json')
assert any(e['kind']=='HOST_CLOCK_SEALED' and e['hash']==sha(ROOT/'host-clock.json') for e in events)
pause = read(ROOT/'pause.json')
clock_stops = [e for e in events if e.get('reason')=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS']
other_clock = [e for e in events if any(s in json.dumps(e) for s in
    ('HOST_REBOOT_UNQUALIFIED','MONOTONIC_CLOCK_DRIFT','WALL_CLOCK_BACKWARD','CLOCK_OR_GAP'))]
near = [e for e in events if '2026-10-09T23:14:20' <= e['at'] <= '2026-10-09T23:15:10']
closing = [e for e in events if '2026-10-09T23:20:20' <= e['at'] <= '2026-10-09T23:22:00']
counts = collections.Counter((e['kind'],e.get('reason') or e.get('detail') or '')
    for e in events if e['kind'] in ('STOP_NEW_ADMISSIONS','WATCHDOG_STOP_ADMISSIONS','PROTOCOL_STOP'))
campaign = read(INSPECT/'campaign-journal.json')['stdout'].splitlines()
relevant = [line for line in campaign if any(s in line for s in ('23:14:','23:20:3','23:21:','STOP:','BACKUP'))]
result = {
    'status': 'PASS', 'anchor': anchor, 'anchor_sha256': sha(ROOT/'host-clock.json'),
    'pause': pause, 'pause_minus_anchor_wall_seconds': (datetime.fromisoformat(pause['at'])-datetime.fromisoformat(anchor['wall'])).total_seconds(),
    'clock_stop_events': clock_stops, 'other_clock_events': other_clock,
    'near_trigger_events': near, 'closing_events': closing,
    'stop_counts': [{'kind': k[0], 'detail': k[1], 'count': v} for k,v in counts.items()],
    'all_notices': len(events), 'notice_chain_last_hash': previous,
    'verified_identities': len(rows), 'counts': {'BACKED_UP':120, 'PLANNED':1380},
    'next': rows[120], 'last_original': rows[119],
    'last_backup': read(ROOT/'backups'/(rows[119]['execution_id']+'.json')),
    'campaign_journal_excerpt': relevant,
    'preserved_files_before': before,
}
after = {str(p.relative_to(ROOT)): sha(p) for p in ROOT.rglob('*') if p.is_file()}
assert after == before
result['preserved_hashes_after_equal_before'] = True
with (HERE/'retained-facts.json').open('x', encoding='utf-8') as output:
    json.dump(result, output, indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('preserved_files_before','last_backup','other_clock_events','closing_events','campaign_journal_excerpt')}, indent=2))
