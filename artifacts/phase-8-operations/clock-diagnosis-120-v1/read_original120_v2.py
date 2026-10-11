"""Scope timing to the retained original, excluding nested historical evidence."""
from __future__ import annotations
import hashlib
import json
import tarfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = '01a11705-11f1-7762-8513-93ef9d42c433'
PREFIX = f'slot/executions/{ID}/'
archive = HERE/'original120.tar.gz'
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
prior = json.loads((HERE/'original120-timing-review.json').read_text())
assert digest == prior['original_archive_sha256']
# Reuse the completed whole-archive/member verification; do not repeat it.
selected = {}
with tarfile.open(archive,'r|gz') as source:
    for member in source:
        if member.isfile() and member.name.startswith(PREFIX) and (
            member.name in (PREFIX+'export.json',PREFIX+'linux-boot.json')
            or (member.name.startswith(PREFIX+'polls/') and member.name.endswith('.json'))
        ):
            stream = source.extractfile(member)
            assert stream is not None
            selected[member.name] = stream.read()
row = json.loads(selected[PREFIX+'export.json'])
boot = json.loads(selected[PREFIX+'linux-boot.json'])
assert row['execution_id'] == ID and row['arm'] == 'P2' and row['attempt'] == 1
assert hashlib.sha256(selected[PREFIX+'export.json']).hexdigest() == prior['export_sha256']
polls = [json.loads(selected[name]) for name in sorted(selected) if name.startswith(PREFIX+'polls/')]
assert len(polls) == len(row['polls'])
for name, record in zip(sorted(n for n in selected if n.startswith(PREFIX+'polls/')),row['polls'],strict=True):
    assert name.endswith(record['path'].split('/polls/')[-1])
    assert hashlib.sha256(selected[name]).hexdigest() == record['hash']
at = [datetime.fromisoformat(p['at']) for p in polls]
gaps = [(b-a).total_seconds() for a,b in zip(at,at[1:])]
deadline = datetime.fromisoformat(row['original_deadline'])
assert not any(g < 0 for g in gaps)
assert at[-1] >= deadline
near = [{'at':p['at'],'ended_at':p.get('ended_at'),'host_at':p['host'].get('at')}
    for p in polls if '2026-10-09T23:14:20'<=p['at']<='2026-10-09T23:15:10']
result = {**prior,'status':'PASS_SCOPED_TO_EXACT_ORIGINAL','poll_count':len(polls),
    'min_poll_gap_seconds':min(gaps),'max_poll_gap_seconds':max(gaps),'negative_poll_gaps':0,
    'first_poll_at':polls[0]['at'],'last_poll_at':polls[-1]['at'],
    'last_poll_ended_at':polls[-1].get('ended_at'),
    'last_poll_minus_original_deadline_seconds':(at[-1]-deadline).total_seconds(),
    'near_trigger_poll_times':near,'exact_execution_prefix':PREFIX,
    'all_own_poll_hashes_verified':True,'historical_polls_excluded':prior['poll_count']-len(polls),
    'reused_whole_archive_manifest_verification':str(HERE/'original120-timing-review.json')}
with (HERE/'original120-timing-review-v2.json').open('x',encoding='utf-8') as out:
    json.dump(result,out,indent=2)
with (HERE/'retained-diagnostic-issue.json').open('x',encoding='utf-8') as out:
    json.dump({'status':'INVALID_V1_TIMING_SUMMARY_RETAINED','file':'original120-timing-review.json',
        'cause':'V1 included nested historical /polls/ records; boot/export/archive hashes remain valid.',
        'correction':'V2 binds exact execution prefix, ID, arm, attempt and exported poll hashes.',
        'raw_evidence_changed':False,'research_outcomes_replaced':False},out,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ('export_keys','near_trigger_poll_times')},indent=2))
