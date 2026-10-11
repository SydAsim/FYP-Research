#!/bin/bash
set -euo pipefail
umask 077
python3 - <<'PY'
import base64,hashlib,json,os
from pathlib import Path
owner=Path('/var/lib/fyp-owner')
old=owner/'receipt-transfer-attempt1';old.mkdir(exist_ok=False)
files={'launch-policy.json': {'base64': 'ew0KICAidmVyc2lvbiI6ICJwaGFzZTg0LWZpbmFsLXYyIiwNCiAgInJlZ2lvbiI6ICJhcC1zb3V0aGVhc3QtMiIsDQogICJzY29wZSI6ICJDQU1QQUlHTiIsDQogICJydW5faWQiOiAicDg1LTAxYTExNmY3LTNiODItN2E3OS04NjUzLTNhZWU2MmRjOTllOSIsDQogICJob3N0X3N0YXJ0ZWRfYXQiOiAiMjAyNi0xMC0wN1QxNToyNDoyMy44MTA2NzRaIiwNCiAgImhvc3RfaG91cnMiOiAzNjAsDQogICJhZG1pc3Npb25fY3V0b2ZmX3NlY29uZHMiOiAxODAwLA0KICAib2JzZXJ2YXRpb25fc2Vjb25kcyI6IDYwMCwNCiAgImJ1ZGdldF91c2QiOiA2NSwNCiAgImFkbWlzc2lvbl9jb21taXR0ZWRfdXNkIjogNTUsDQogICJ2b2x1bWVfZ2liIjogMTYwLA0KICAic3RvcHBlZF9yZXRlbnRpb25faG91cnMiOiA0OCwNCiAgImFkbWlzc2lvbl9yYW1fYnl0ZXMiOiAyMTQ3NDgzNjQ4LA0KICAiYWN0aXZlX3JhbV9ieXRlcyI6IDEwNzM3NDE4MjQsDQogICJhZG1pc3Npb25fZGlza19ieXRlcyI6IDIxNDc0ODM2NDgwLA0KICAiYWN0aXZlX2Rpc2tfYnl0ZXMiOiAxMDczNzQxODI0MCwNCiAgImNsb3VkX2xpbWl0X2J5dGVzIjogMzIyMTIyNTQ3MjAsDQogICJzbG90X2NhcGFjaXR5X3Jlc2VydmVfYnl0ZXMiOiAxMDczNzQxODI0LA0KICAiY2xvdWRfYnVja2V0IjogImZ5cC1wODItMjAyNjEwMDUtMDE4ZGExZDYtODAzNjU2NTg5OTIzIiwNCiAgImNvbXB1dGVfdXNkX2hvdXIiOiAwLjExOTcsDQogICJpcHY0X3VzZF9ob3VyIjogMC4wMDUsDQogICJkaXNrX3VzZF9naWJfbW9udGgiOiAwLjA5NiwNCiAgInMzX3VzZF9naWJfbW9udGgiOiAwLjAyNSwNCiAgInJlcXVlc3RfdHJhbnNmZXJfcmVzZXJ2ZV91c2QiOiA1LjAsDQogICJwb2xsX3NlY29uZHMiOiA1DQp9DQo=', 'sha256': '80831c99b3def500b86335ef038142148f8f04025ca530e38673de2ef573e61d'}, 'receipts/REVIEW_ACCEPTED.json': {'base64': 'ew0KICAia2luZCI6ICJSRVZJRVdfQUNDRVBURUQiLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiZDA4OTlkMmRiOWY4NThlN2RjMTBiZDljOTVhODgxOWE3MzM1ZjY0MWE1OWEwMGRiNTEzZjA1YzQ2OTZjYmRjMSIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6IG51bGwsDQogICJleHBpcmVzX2F0IjogIjk5OTktMTItMzFUMjM6NTk6NTkrMDA6MDAiLA0KICAic2lnbmVyIjogIkh1bWFuIGFjY2VwdGFuY2UgcmVjb3JkZWQgYnkgdGhlIGxvY2FsIEZZUCBvcGVyYXRvciIsDQogICJzaWduYXR1cmUiOiAiOGUzZjEwYjA2ZDZiZDJlZjgzNGI2NWIxNTMzZTUzMzY2YmEwMjg0ZGFhODA5NTZhNGUwN2ExZDVjZDYyY2QzYiINCn0NCg==', 'sha256': '95e337416773c6ed99cc8bc1caa82736c30ee829c606317a8837b51c4c0d1461'}, 'receipts/FREEZE.json': {'base64': 'ew0KICAia2luZCI6ICJGUkVFWkUiLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiZDA4OTlkMmRiOWY4NThlN2RjMTBiZDljOTVhODgxOWE3MzM1ZjY0MWE1OWEwMGRiNTEzZjA1YzQ2OTZjYmRjMSIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6ICI2NTgxNmUwZTE4NmZlNDJhNzgzM2I0NWJiNTYzZGQwYWY5Y2IzZGVjM2QzM2Y1YTZmNzMwY2RlMjM3NWYzMDliIiwNCiAgImV4cGlyZXNfYXQiOiAiOTk5OS0xMi0zMVQyMzo1OTo1OSswMDowMCIsDQogICJzaWduZXIiOiAiSHVtYW4gYWNjZXB0YW5jZSByZWNvcmRlZCBieSB0aGUgbG9jYWwgRllQIG9wZXJhdG9yIiwNCiAgInNpZ25hdHVyZSI6ICJiNTQwZWFiNDgzMGIwZmI4YTYyOTQxMjEwNGJjOTZmMDk5ZDY1ODgwMDhmNTM5M2QzMGUxNGMwZmMwNTczYWU5Ig0KfQ0K', 'sha256': '0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2'}, 'receipts/LAUNCH.json': {'base64': 'ew0KICAia2luZCI6ICJMQVVOQ0giLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiODdmZjNhYzk4YzhmNzY0NmVjZDI1ZWNiNjQxZTdmZmQ0OWU1MDA4YTFkMGIzYzhmOTdjY2E2YTdkMDkxZTI0NiIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6ICI4N2FlZWIzYmU4YjNiYzdiMzgyYzdhMTVhYzhmMWI0NTY5OWNlMTNhNzNkZDFjNDgwZGU4YzVjMmY5NDc1ZjM4IiwNCiAgImV4cGlyZXNfYXQiOiAiMjAyNi0xMC0yMlQxNToyNDoyMy44MTA2NzQrMDA6MDAiLA0KICAic2lnbmVyIjogIkh1bWFuLWF1dGhvcml6ZWQgbG9jYWwgRllQIGRlcGxveW1lbnQgb3BlcmF0b3IiLA0KICAic2lnbmF0dXJlIjogIjIzMDBhMTE3YjdjNmYwZTk0NGYwODBiZDFmYmE4MGFiZDdkNmIxYjZjMWI5YjExOTZlZDZhMjVhZDIzN2E2ZTIiDQp9DQo=', 'sha256': '35b9d06c9676baadffd4561bf2489b2bc1b08afce28fca5f1e259657f841bcd9'}}
for name,spec in files.items():
 p=owner/name; retained=old/name;retained.parent.mkdir(parents=True,exist_ok=True);p.rename(retained)
 raw=base64.b64decode(spec['base64'])
 if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('RECEIPT_TRANSPORT_DRIFT')
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 p.chmod(0o600)
print('Original receipt bytes restored; rejected copies retained; no resealing')
PY
cd /opt/fyp-phase8-linux-v1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
.venv/bin/python -B - <<'PY'
import json,socket,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-review-freeze/v2'))
from controls import Authority,Policy,guard,hash_file,read,utc,write_new
from storage import S3Cloud
from research.execution_linux_v1.platform import host
r=Path.cwd(); owner=Path('/var/lib/fyp-owner'); policy=Policy.model_validate(read(owner/'launch-policy.json'))
Authority(r,r/'artifacts/phase-8-review-freeze/v2/review-inventory.json',policy,hash_file(r/'artifacts/phase-8-review-freeze/v2/schedule.json'),owner/'receipts',owner/'owner.key').verify()
cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/')
sample=host(Path('/var/lib/p8'),Path('/var/lib/p8'))
sample.update(working_bytes=0,backup_bytes=0)
cloud_bytes=cloud.inventory()
guard(policy,sample,utc(),cloud_bytes,extra_bytes=policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s: s.bind(('127.0.0.1',port))
probe=Path('/var/lib/p8-deployment/permission-probe.json')
write_new(probe,{'classification':'DEPLOYMENT_PERMISSION_CHECK_NOT_SCIENTIFIC_EXECUTION','run_id':policy.run_id,'at':utc().isoformat()})
proof=cloud.put(probe,cloud.prefix+'deployment/permission-probe.json');cloud.verify(proof)
write_new(Path('/var/lib/p8-deployment/preinitialize-readiness.json'),{'status':'PASS','at':utc().isoformat(),'host':sample,'cloud_bytes_before_probe':cloud_bytes,'proof':proof.model_dump(),'owner_key_mode':oct((owner/'owner.key').stat().st_mode&0o777),'authorization_chain':'PASS','ports_free':True,'main_executions':0})
print(json.dumps(read(Path('/var/lib/p8-deployment/preinitialize-readiness.json'))))
PY
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py init --root /var/lib/p8/run --backup /var/lib/p8/backup --source /opt/fyp-phase8-linux-v1 --manifest artifacts/phase-8-review-freeze/v2/review-inventory.json --schedule artifacts/phase-8-review-freeze/v2/schedule.json --policy /var/lib/fyp-owner/launch-policy.json --receipts /var/lib/fyp-owner/receipts --key /var/lib/fyp-owner/owner.key
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py verify --root /var/lib/p8/run
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py install-watchdog --root /var/lib/p8/run
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service
systemctl list-timers fyp-phase8-hardstop.timer fyp-p85-bootstrap-stop.timer --no-pager
# Preparation never starts the campaign service.
printf '%s\n' HOST_INITIALIZED_TIMERS_ACTIVE_MAIN_NOT_STARTED
