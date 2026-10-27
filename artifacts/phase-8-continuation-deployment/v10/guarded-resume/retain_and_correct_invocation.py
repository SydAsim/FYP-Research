"""Preserve failed wrapper; prepare only its justified external selection correction."""
import ast
import hashlib
import json
import difflib
from datetime import UTC,datetime,timedelta
from ops import HERE,record

def load(name):return json.loads((HERE/name).read_text())

def main():
    host=load('verify-stopped1-result.json')['result']['Reservations'][0]['Instances'][0]
    assert host['State']['Name']=='stopped'
    assert load('verify-preparation-retired-result.json')['result']['State']=='DISABLED'
    reply=load('runtime-binding-status1-result.json')['result']
    assert reply['Status']=='Success' and reply['ResponseCode']==0
    runtime=json.loads(reply['StandardOutputContent'])
    assert runtime['python']==runtime['qualified_host_python']
    assert not runtime['v10_source_exists'] and not runtime['new_source_archive_exists']
    failed=(HERE/'prepare-source.sh').read_text()
    wrong="assert hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()=='0e6475dfda68a9b2d93501449fc47593ca169010e8f4881577b97463fd0c1263'"
    assert failed.count(wrong)==1
    correct="qualified=json.loads(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json').read_text())\nassert sys.version==qualified['python'],'QUALIFIED_HOST_PYTHON_BUILD_DRIFT'\nprint(json.dumps({'kind':'EXISTING_HOST_TRANSPORT_BINDING','python':sys.version,'binary_sha256':hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()}))"
    # The existing import check gains only json for the recorded qualified-build comparison.
    fixed=failed.replace('import boto3,botocore,sys,hashlib\n','import boto3,botocore,sys,hashlib,json\n').replace(wrong,correct)
    block=fixed.split("<<'IMPORT_CHECK'\n",1)[1].split('\nIMPORT_CHECK\n',1)[0]
    ast.parse(block)
    with (HERE/'prepare-source.corrected.sh').open('x',encoding='utf-8',newline='\n') as f:f.write(fixed)
    with (HERE/'external-invocation.diff').open('x',encoding='utf-8',newline='\n') as f:
        f.write(''.join(difflib.unified_diff(failed.splitlines(True),fixed.splitlines(True),fromfile='prepare-source.sh (retained failed invocation)',tofile='prepare-source.corrected.sh (not executed)')))
    record('external-invocation-correction.json',{'status':'PREPARED_NOT_EXECUTED_AFTER_VERIFIED_STOP',
        'cause':'Controller compared qualified EC2 uv/Clang Python against the test-container Python binary hash',
        'incorrect_container_binary_sha256':'0e6475dfda68a9b2d93501449fc47593ca169010e8f4881577b97463fd0c1263',
        'actual_host_binary_sha256':runtime['actual_binary_sha256'],
        'qualified_python_build':runtime['qualified_host_python'],
        'baseline_has_binary_hash':False,'actual_hash_not_relabelled_as_historical_baseline':True,
        'corrected_check':'Same Python version and full build string as retained qualified host baseline; log actual binary hash. Remaining source/dependency-record gates still required.',
        'verification':'Retained successful runtime read proves exact build-string equality; corrected import block parsed; no live re-execution or test repetitions',
        'failed_wrapper_sha256':hashlib.sha256(failed.encode()).hexdigest(),
        'corrected_wrapper_sha256':hashlib.sha256(fixed.encode()).hexdigest(),
        'frozen_code_changed':False,'new_freeze':False,'new_boot':False})
    now=datetime.now(UTC);anchor=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')
    stop=anchor+timedelta(hours=432);remaining=290*1355/1498;rate=.1197+.005+160*.096/730;reserve=48*160*.096/730+80*.025+5+1.25
    finish=now+timedelta(hours=remaining+2.5);uncertain=finish+timedelta(hours=24)
    forecast=lambda at:(at-anchor).total_seconds()/3600*rate+reserve
    record('final-status.json',{'status':'BLOCKED_EXTERNAL_INTERPRETER_SELECTION_SAFE_STOP_VERIFIED',
        'at':now.isoformat(),'host_id':host['InstanceId'],'host_state':'stopped',
        'verified_stopped_at':load('verify-stopped1-result.json')['at'],
        'service_state':'Both owned units quiesced before source attempt; EC2 stopped, no services executing',
        'root_retained':'vol-09dbb42bbf607f5de','evidence_deleted':False,
        'bundle_sha256':'3a4744dbbffd90d7c233a2f7117e5743bfe3dd891309f7ff62771b844e3bbd70','bundle_bytes':207205,
        'historical_command_execution':'UNKNOWN; expiry and actual closed-root inspection justify conditional quiescence, not a claim of nonexecution',
        'retained_boundary':{'BACKED_UP':145,'PLANNED':1355,'active':0,'all_1500_rows_exactly_verified':True},
        'next':{'sequence':146,'arm':'P2','attempt':1,'execution_id':'01a11705-11f1-772d-8190-c43552871801'},
        'failure':'prepare-v10-source import check line4: test-container binary SHA compared to qualified EC2 Python binary',
        'correction':'prepare-source.corrected.sh prepared, not executed; full source/dependency readiness remains mandatory',
        'package_hash':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c',
        'archive_sha256':'212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37',
        'source_downloads':0,'archive_uploads':0,'new_refreezes':0,'driver_calls':0,
        'new_prelaunch_backup':None,'new_complete_backup':None,'readiness_issued':False,'launch_receipt_issued':False,'pause_released':False,
        'preparation_guard':'DISABLED_READ_BACK_AFTER_VERIFIED_STOPPED',
        'absolute_aws_guard':'ENABLED_READ_BACK_BEFORE_BOOT; no modification during retirement',
        'absolute_stop':stop.isoformat(),'retention_decision_deadline':'2026-10-27T15:24:23.810674Z',
        'admission_guard_usd':70,'total_ceiling_usd':75,'caps_gib':80,
        'updated_completion_forecast_usd':forecast(finish),'updated_uncertainty_forecast_usd':forecast(uncertain),
        'full_deadline_forecast_usd':forecast(stop),'original_clock_anchor_preserved':True,
        'future_storage_projection_with_reservation_bytes':load('feasibility.json')['future_storage_plus_reservation_bytes'],
        'new_metadata_base_and_actual_resources':'NOT_REACHED; must be measured before admission',
        'historical_backup_references':json.loads((HERE.parent/'final-status.json').read_text())['existing_research_backups']})
    print(json.dumps(load('final-status.json'),indent=2))

if __name__=='__main__':main()
