"""Existing immutable traces only: bound future retained slot payload growth."""
import json
import tarfile
from pathlib import Path
from prepare import HERE,SOURCE,PREFIX,write

def main():
    rows=json.loads((SOURCE/PREFIX/'closed-120/ledger-read-only.json').read_text())['rows']
    records=[]
    for row in rows[82:120]:
        proof=json.loads((SOURCE/PREFIX/'closed-120/backups'/ (row['execution_id']+'.json')).read_text())
        archive=HERE.parents[1]/'phase-8-operations/clock-diagnosis-120-v1/original120.tar.gz' if row['sequence']==120 else Path('E:/p8v8/retained-original-archives')/(proof['sha256']+'.tar.gz')
        with tarfile.open(archive) as incoming:
            members=incoming.getmembers()
            # Retained slot payload; continuation master/history copies are fixed
            # metadata, not retained as another working slot after staging removal.
            prefix='slot/executions/'+row['execution_id']+'/'
            payload=sum(m.size for m in members if m.isfile() and m.name.startswith(prefix))
        records.append({'sequence':row['sequence'],'raw_execution_payload_bytes':payload,'pinned_archive_sha256':proof['sha256']})
    maximum=max(r['raw_execution_payload_bytes'] for r in records)
    planned=2*maximum*1380+2*1024**3
    write(HERE/'working-growth-measurements.json',{'status':'MEASURED_PLANNING_NOT_GUARANTEE',
      'records':records,'max_raw_execution_bytes':maximum,'future_working_allowance_bytes':planned,
      'basis':'Twice maximum measured 83–120 retained raw execution payload for all remaining slots, plus 2GiB mutable master/operational/source transfer allowance. Existing immutable raw payload unchanged; only qualified redundant future staging removed.',
      'working_guard_unchanged_bytes':50*1024**3,'limits':'Additional recipe payload can exceed measurement; unchanged 50GiB working and 20/10GiB free-space guards must stop safely.'})
    print(json.dumps({'maximum':maximum,'future_working_gib':planned/1024**3}))

if __name__=='__main__':main()
