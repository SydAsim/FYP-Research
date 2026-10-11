"""Final two cheap negative copier controls and static checks, no backup rebuild."""
from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from prepare_candidate import HERE, PREFIX, SOURCE


def main() -> None:
    plan = {'at_utc': datetime.now(UTC).isoformat(), 'checks': ['configured continuation cannot silently omit handover in complete mode', 'same omission rejected in prelaunch mode'], 'execution_count': 2, 'maximum_wall_seconds': 60, 'new_scenarios': 0, 'reason': 'Final review of the missing-metadata guard; no repeated roundtrip or research execution.'}
    (HERE / 'final-two-check-plan.json').write_text(json.dumps(plan, indent=2))
    image = 'sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
    code = '''from pathlib import Path
import tempfile,json,sys,sqlite3
from storage import copy_continuation_metadata
assert sys.version_info[:3]==(3,12,13)
with tempfile.TemporaryDirectory(prefix='cal-missing-handover-') as temp:
    source=Path(temp)/'in';source.mkdir();(source/'run.json').write_text(json.dumps({'continuation':{'kind':'CALIBRATION_ONLY'}}))
    for mode in (False,True):
        try: copy_continuation_metadata(source,Path(temp)/'out',prelaunch=mode)
        except ValueError as error: assert str(error)=='PRELAUNCH_CONTINUATION_REQUIRED'
        else: raise AssertionError('MISSING_HANDOVER_ACCEPTED')
print('PASS: 2 missing-handover copier rejections; pinned Linux; no archives or research executions')
'''
    args = ['docker', 'run', '--pull=never', '--name', 'p85-v6-final-metadata-guards', '--network', 'none', '--memory', '512m', '--cpus', '1', '-v', str(SOURCE) + ':/candidate:ro', '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTHONPATH=/candidate:/candidate/' + PREFIX + ':/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages', image, 'python', '-c', code]
    reply = subprocess.run(args, capture_output=True, text=True, timeout=60)
    (HERE / 'final-two-check-results.json').write_text(json.dumps({'exit': reply.returncode, 'stdout': reply.stdout, 'stderr': reply.stderr, 'args': args}, indent=2))
    reply.check_returncode()
    runtime = SOURCE / PREFIX
    files = [str(runtime / name) for name in ('storage.py', 'postflight.py', 'prelaunch_backup.py', 'handover.py', 'closed_restart.py')]
    checks = {}
    for name, args in [('ruff', ['.venv/Scripts/python.exe', '-m', 'ruff', 'check', *files, str(runtime / 'test_backup_closure.py')]), ('mypy', ['.venv/Scripts/python.exe', '-m', 'mypy', '--follow-imports=silent', '--ignore-missing-imports', *files])]:
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        checks[name] = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
        result.check_returncode()
    (HERE / 'static-final.json').write_text(json.dumps(checks, indent=2))
    # Refresh only arithmetic against recently measured unchanged AWS state/prices.
    data = json.loads((HERE / 'feasibility.json').read_text())
    now = datetime.now(UTC)
    original = datetime.fromisoformat(data['at_utc'])
    rate = .1197 + .005 + 160 * .096 / 730
    elapsed = (now - original).total_seconds() / 3600
    data['conservative_original_elapsed_clock_cost_usd'] += elapsed * rate
    data['explicit_resources_cost_usd'] += elapsed * 160 * .096 / 730
    finish = now + timedelta(hours=data['reviewed_allowance_remaining_hours'] + 2)
    threshold = datetime.fromisoformat(data['conservative_guard_time_utc'])
    data.update(at_utc=now.isoformat(), AWS_measurements_at_utc=original.isoformat(), arithmetic_only_refresh=True, allowance_finish_utc_if_started_now=finish.isoformat(), review_and_deployment_slack_hours=(threshold - finish - timedelta(minutes=30)).total_seconds()/3600)
    data['status'] = 'FAIL_DO_NOT_DEPLOY' if data['conservative_original_elapsed_clock_cost_usd'] >= 55 or finish >= datetime.fromisoformat(data['original_deadline']) - timedelta(minutes=30) else 'PASS_CONDITIONAL_NO_LAUNCH'
    data['latest_preparation_start_unchanged_allowance'] = '2026-10-09T12:48:54.676567+00:00'
    (HERE / 'feasibility-final.json').write_text(json.dumps(data, indent=2))
    print(json.dumps({'static': checks, 'feasibility': {k: data[k] for k in ('status', 'at_utc', 'conservative_original_elapsed_clock_cost_usd', 'explicit_resources_cost_usd', 'review_and_deployment_slack_hours')}}))


if __name__ == '__main__':
    main()
