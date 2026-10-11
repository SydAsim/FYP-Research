"""Finite post-return collector probe, separately recorded before transmission."""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.execution_setup.core import Ledger, immutable, now

root = Path('E:/FYP-Research/phase8-setup-v1-attempt2')
ledger = Ledger(root)
slot = ledger.rows()[0]
assert slot['state'] == 'RUNNING' and slot['case_id'].startswith('cal-v4-setup-v1-')
trace = ledger.recover_checkpoint(slot['execution_id'])
assert trace['driver_finished_at']
original = next(p['request'] for p in trace['client_playback']
                if p['request']['event_type'] == 'COMPLETED' and p['status'] == 202)
body = {**original, 'event_id': str(uuid4()), 'client_time': now()}
plan = {
    'classification': 'SEPARATE_COLLECTOR_CONTROL_NOT_MAIN_NOT_DRIVER_RERUN',
    'control_id': 'cal-collector-late-ack-v1', 'execution_id': slot['execution_id'],
    'declared_at': now(), 'purpose': 'Capture a new durable ACK after normal driver return',
    'request': body, 'expected': '202 and event ID retained in a subsequent poll',
    'deadline': slot['deadline'], 'main_started': False,
    'scope': 'Semantically duplicate completion with new event ID; scripted ACK only',
    'qualification_amendment': 'Additional observer control; original driver fixture retained',
}
plan_path = root / 'controls/late-ack-v1-plan.json'
immutable(plan_path, plan)
ledger.seal(plan_path)
ledger.event('COLLECTOR_CONTROL_DECLARED', control_id=plan['control_id'], path=str(plan_path))
url = f"http://127.0.0.1:19100/v1/calls/{trace['call_id']}/playback-events"
sent = now()
try:
    with urlopen(Request(url, data=json.dumps(body).encode(), method='POST',
                         headers={'Content-Type': 'application/json'}), timeout=40) as response:
        result = {'status': response.status, 'body': json.load(response)}
except HTTPError as error:
    result = {'status': error.code, 'body': json.loads(error.read())}
record = {**result, 'sent_at': sent, 'received_at': now(), 'request': body,
          'execution_id': slot['execution_id'], 'deadline_unchanged': slot['deadline']}
path = root / 'controls/late-ack-v1-response.json'
immutable(path, record)
ledger.seal(path)
ledger.event('COLLECTOR_CONTROL_RESPONSE', status=result['status'], path=str(path))
print(record)
