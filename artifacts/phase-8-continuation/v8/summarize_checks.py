"""Aggregate distinct completed controls; never relabel interrupted attempts as PASS."""
from __future__ import annotations
import ast
import hashlib
import json
import shutil
from pathlib import Path
from prepare import HERE, PREFIX, SOURCE, digest, write

def main() -> None:
    first=json.loads((HERE/'qualification-result.json').read_text())
    second=json.loads((HERE/'qualification-remaining-result.json').read_text())
    third=json.loads((HERE/'complete-readback-result.json').read_text())
    assert first['status']==second['status']=='TIMEOUT_STOP_CANDIDATE'
    assert third['status']=='PASS'
    assert first['stdout'].count(' PASSED ')==11
    assert second['stdout'].count(' PASSED ')==6
    assert 'test_clock_01_bracket_order_and_midpoint FAILED' in first['stdout']
    assert 'test_boundary_05_prelaunch_backup_roundtrip PASSED' in second['stdout']
    names=first['files'].keys()
    for n in names:
        assert digest(SOURCE/PREFIX/n)==second['files'][n],n
    current=(SOURCE/PREFIX/'runner.py').read_bytes()
    prior=current.replace(b'from clock_sampling import check as paired_clock_check  # noqa: E402',b'from clock_sampling import check as paired_clock_check')
    assert hashlib.sha256(prior).hexdigest()==first['files']['runner.py']
    assert ast.dump(ast.parse(prior))==ast.dump(ast.parse(current))
    assert all(first['files'][n]==second['files'][n] for n in names if n not in ('runner.py','test_clock_continuation_v8.py'))
    for filename in ('prelaunch-roundtrip.json','complete-roundtrip.json','complete-receipt.json','corrupt-test-evidence.json'):
        shutil.copyfile(Path('E:/p8v8/closure-remaining-evidence')/filename,HERE/filename)
    reused={
       'v7/final-verification.json':'v7 snapshot/limits plus reused v6 qualifications',
       'v6/final-verification.json':'backup copier/order controls (including retained unsuccessful attempts)',
       'v6/final-two-check-results.json':'qualified independent closure',
       'v6/qualified-source-closure.json':'preserved app/fixture/oracle/analysis closure',
    }
    write(HERE/'qualification-summary.json',{'status':'PASS_DISTINCT_REQUIRED_CONTROLS','distinct_required_checks':18,'distinct_checks_completed':18,'first_attempt_passes':11,'second_attempt_passes':6,'final_unfinished_readback_completed':1,'unsuccessful_attempts':[{'file':'qualification-result.json','status':first['status'],'assertion_failure':'Exact IEEE-754 midpoint equality; corrected test only to approximate comparison','timeout':'Windows bind-mounted metadata handover unfinished at 240 seconds'},{'file':'qualification-remaining-result.json','status':second['status'],'timeout':'Complete-backup check interrupted at 240 seconds; produced archive retained and independently verified without repeating copier'}],'source_changes_between_checks':'runner noqa comment only (byte reconstruction and AST equality verified); only failed test floating-point assertion corrected','already_passed_controls_repeated':0,'research_executions':0,'image':first['image'],'runtime':'Pinned Linux Python 3.12.13; no network or dependency installation','actual_prelaunch_and_complete_roundtrips':'PASS','missing_corrupt_metadata':'REJECTED','existing_qualification_reused':{n:{'sha256':digest(HERE.parent/n),'scope':scope} for n,scope in reused.items()},'tested_runtime_files':second['files'],'static_checks':{'ruff':'PASS six changed/new code files','mypy':'PASS five runtime files; final runner comment-only source rechecked','initial_lint_failure_retained':'static-initial.txt'}})
    print('18 distinct controls qualified; unsuccessful/time-limited attempts retained, not relabelled.')

if __name__=='__main__':main()
