"""Ten pure diagnostic controls against frozen code, without live clock changes."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete')
started = time.perf_counter()
source_hashes = {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()
                 for name in ('controls.py', 'runner.py', 'handover.py', 'collector.py')}

def function(name: str, file: str, env: dict[str, Any]) -> Any:
    node = next(n for n in ast.parse((SOURCE/file).read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE/file), 'exec'), env)
    return env[name]

env: dict[str, Any] = {'Any': Any, 'datetime': datetime, 'Policy': Any}
check = function('clock_check', 'controls.py', env)
origin = datetime(2026, 10, 9, 16, tzinfo=UTC)
policy = SimpleNamespace(stop_at=datetime(2026, 10, 22, 15, 24, 23, 810674, tzinfo=UTC))
anchor = {'boot_id': 'offline-same-boot', 'monotonic': 100.0, 'wall': origin.isoformat()}
results: list[dict[str, Any]] = []

def run_case(name: str, wall: float, mono: float, expected: str,
             boot: str = 'offline-same-boot', selected: dict[str, Any] | None = None) -> None:
    observed = 'PASS'
    try:
        check(policy, selected or anchor, origin + timedelta(seconds=wall), 100 + mono, boot)
    except ValueError as error:
        observed = str(error)
    results.append({'name': name, 'wall_elapsed': wall, 'monotonic_elapsed': mono,
                    'expected': expected, 'observed': observed, 'pass': observed == expected})

run_case('paired_clocks', 100, 100, 'PASS')
run_case('stale_read_4_999', 100, 104.999, 'PASS')
run_case('stale_read_exactly_5', 100, 105, 'PASS')
run_case('stale_read_5_001', 100, 105.001, 'WALL_CLOCK_BACKWARD_STOP_ADMISSIONS')
run_case('fresh_pair_after_eight_seconds_work', 108, 108, 'PASS')
run_case('true_six_second_rollback', 94, 100, 'WALL_CLOCK_BACKWARD_STOP_ADMISSIONS')
run_case('anchor_wall_six_seconds_ahead', 100, 100, 'WALL_CLOCK_BACKWARD_STOP_ADMISSIONS',
         selected={**anchor, 'wall': (origin + timedelta(seconds=6)).isoformat()})
run_case('boot_mismatch', 100, 100, 'HOST_REBOOT_UNQUALIFIED', boot='different-boot')
run_case('monotonic_decreased', 100, -1, 'MONOTONIC_CLOCK_DRIFT')

# Evaluate exactly the frozen main() while-call arguments, left to right. No loop.
elapsed = [100.0]
pauses: list[str] = []
trace: list[dict[str, Any]] = []
class FakeJournal:
    def __init__(self, root: Path) -> None:
        pass
    def pause(self, reason: str) -> None:
        pauses.append(reason)
    def event(self, *args: Any, **kwargs: Any) -> None:
        pass
def utc() -> datetime:
    trace.append({'reading': 'wall_argument', 'elapsed': elapsed[0]})
    return origin + timedelta(seconds=elapsed[0])
def meter(root: Path) -> dict[str, Any]:
    elapsed[0] += 2
    return {}
class Cloud:
    def inventory(self) -> int:
        elapsed[0] += 6
        return 1
def verify_clock(root: Path, checked_policy: Any, at: datetime) -> None:
    trace.append({'reading': 'monotonic_in_verify_clock', 'elapsed': elapsed[0]})
    check(checked_policy, anchor, at, 100 + elapsed[0], anchor['boot_id'])
watch_env: dict[str, Any] = {
    'Path': Path, 'datetime': datetime, 'Any': Any, 'Journal': FakeJournal,
    'authority_for': lambda root: SimpleNamespace(policy=policy),
    'sys': SimpleNamespace(platform='linux'), 'verify_clock': verify_clock,
    'verify_run': lambda root: None, 'guard': lambda *args: None,
}
tick = function('watchdog_tick', 'runner.py', watch_env)
main_node = next(n for n in ast.parse((SOURCE/'runner.py').read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name == 'main')
call = next(n.test for n in ast.walk(main_node) if isinstance(n, ast.While)
            and isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Name)
            and n.test.func.id == 'watchdog_tick')
eval(compile(ast.Expression(call), str(SOURCE/'runner.py'), 'eval'),
     {'watchdog_tick': tick, 'root': Path('offline-only'), 'utc': utc, 'meter': meter, 'cloud': Cloud()})
results.append({'name': 'exact_watchdog_argument_order', 'expected': ['WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'],
                'observed': pauses, 'trace': trace,
                'perfect_clocks': True, 'pass': pauses == ['WALL_CLOCK_BACKWARD_STOP_ADMISSIONS']})
after = {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in source_hashes}
duration = time.perf_counter() - started
report = {'status': 'PASS' if all(r['pass'] for r in results) and after == source_hashes and duration < 30 else 'FAIL',
          'controls': len(results), 'duration_seconds': duration, 'python': sys.version,
          'source_hashes_before': source_hashes, 'source_hashes_after': after,
          'synthetic_diagnostic_only': True, 'results': results}
with (HERE/'offline-results.json').open('x', encoding='utf-8') as out:
    json.dump(report, out, indent=2)
print(json.dumps(report))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
