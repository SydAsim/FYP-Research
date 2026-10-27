"""18 bounded offline controls. No driver, writes to originals, grading or scenarios."""
import copy,hashlib,importlib.util,json,sys,tarfile
from datetime import timedelta
from pathlib import Path

source=Path('/opt/fyp-phase8-continuation-v10')
overlay=source/'artifacts/phase-8-runner-amendment/v4-complete'
sys.path.insert(0,str(overlay));sys.path.insert(1,str(source))
from research.scenario_dsl.models import stable_hash

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result);return result

old=module(overlay/'refusal.py','old_refusal616')
new=module(Path(__file__).parent/'refusal.py','new_refusal616')
archive=Path('/var/lib/p8-continuation-v9/backup/0616/attempt-1792158556532307065.tar.gz')
assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()=='4002ff9a474c3afaae216ab8a14260801910ca82043419a3e0afd5a70dd95c89'
with tarfile.open(archive) as tf:
    raw=tf.extractfile('slot/executions/01a11705-11f2-7c66-8710-43c921046e1b/export.json').read()
assert hashlib.sha256(raw).hexdigest()=='e70007cf43de2d0ad37a40f65dbbe7a23cf8dc6ba3a86d17b00a4e59c41c6c70'
original=json.loads(raw)
passed=[]
def check(name,condition):
    assert condition,name
    passed.append(name)
    print('PASS '+name,flush=True)
def failed_call(row):return [c for c in row['http'] if c.get('status')==409][-1]
def sync(row,call):row['failure']['detail']=f"HTTP {call['status']}: {call['path']}: {call['response']}"

check('frozen-refusal-remains-unrecognized',old.recognize(original) is None)
before=stable_hash(original);proof=new.recognize(original)
check('candidate-unknown-refusal-no-mutation',proof is not None and proof['predicate_result']=='UNKNOWN' and not proof['retry_performed'] and not proof['business_success_inferred_from_refusal'] and stable_hash(original)==before)
row=copy.deepcopy(original);row['driver_classification']=proof
check('full-original-window-retained',new.timing_eligible(row))
for label,arm in [('first','B3'),('second','P1'),('second','P2')]:
    row=json.loads((overlay/f'retained-{label}-original.json').read_bytes());row['arm']=arm
    check('legacy-'+arm,old.recognize(row)==new.recognize(row) is not None)
for arm in ['P1','P2']:
    row=copy.deepcopy(original);row['arm']=arm;row['execution_id']='cal-offline616-'+arm
    call=failed_call(row);idx=row['http'].index(call)
    operation=proof['operation_id'];receipt_id='44444444-4444-4444-8444-444444444444';trace_id='55555555-5555-4555-8555-555555555555'
    verify=copy.deepcopy(call);verify.update(path='/internal/phase3/verifications',status=201,trace_id=trace_id)
    verify['request']={'command_id':'66666666-6666-4666-8666-666666666666','operation_id':operation,'expected_intent_revision':2,'claim_type':'RESCHEDULED_APPOINTMENT'}
    verify['response']={'receipt_id':receipt_id,'claim_type':'RESCHEDULED_APPOINTMENT','intent_revision':2,'result':'UNKNOWN','observed_resource_version':None,'valid_until':(new.instant(call['received_at'])+timedelta(seconds=30)).isoformat()}
    call['path']='/internal/phase3/claims';call['request']={'command_id':'77777777-7777-4777-8777-777777777777','receipt_id':receipt_id,'expected_intent_revision':2}
    call['response']={'type':'https://example.invalid/problems/receipt-not-applicable','title':'Receipt not applicable','status':409,'detail':'A current SATISFIED receipt is required','instance':call['path'],'trace_id':'88888888-8888-4888-8888-888888888888','retryable':False}
    call['sent_at']=(new.instant(verify['received_at'])+timedelta(milliseconds=10)).isoformat();call['received_at']=(new.instant(call['sent_at'])+timedelta(milliseconds=10)).isoformat()
    row['http'].insert(idx,verify)
    for o in row['snapshot']['observations']:
        row['snapshot']['raw_provider_events'].append({'event_kind':'VERIFICATION_READ','trace_id':trace_id,'operation_id':operation,'raw_json':o['raw'],'content_hash':stable_hash(o['raw']),'normalized_json':{'result':'UNKNOWN','claim_type':'RESCHEDULED_APPOINTMENT'}})
    sync(row,call);p=new.recognize(row)
    check('synthetic-unknown-receipt-'+arm,p is not None and p['predicate_result']=='UNKNOWN' and p['receipt_id']==receipt_id)
for change in ['outer500','provider500','hash','missing','action','effect','unrelated409','retryable','undeclared','resource_message']:
    row=copy.deepcopy(original);call=failed_call(row);obs=row['snapshot']['observations']
    if change=='outer500':call['status']=500
    elif change=='provider500':obs[1]['raw']['status']=500;obs[1]['raw_hash']=stable_hash(obs[1]['raw'])
    elif change=='hash':obs[0]['raw_hash']='0'*64
    elif change=='missing':row['snapshot']['observations']=[]
    elif change=='action':obs[1]['query']['action']='RESCHEDULE'
    elif change=='effect':row['snapshot']['history']['operations'][-1]['target_resource_id']='wrong'
    elif change=='unrelated409':call['response']['type']='https://example.invalid/problems/other'
    elif change=='retryable':
        prefix,nested=call['response']['detail'].split(': 409 ',1);problem=json.loads(nested);problem['retryable']=True;call['response']['detail']=prefix+': 409 '+json.dumps(problem)
    elif change=='undeclared':row['input']['provider']['resource_lookup']=True
    elif change=='resource_message':obs[0]['raw']['body']={'detail':'Technical failure'};obs[0]['raw_hash']=stable_hash(obs[0]['raw'])
    sync(row,call);check('fail-closed-'+change,new.recognize(row) is None)
assert len(passed)==18
assert hashlib.sha256(raw).hexdigest()=='e70007cf43de2d0ad37a40f65dbbe7a23cf8dc6ba3a86d17b00a4e59c41c6c70'
print(json.dumps({'status':'PASS','controls':len(passed),'research_executions':0,'original_export_unchanged':True,'source_runtime':sys.version,'candidate_sha256':hashlib.sha256((Path(__file__).parent/'refusal.py').read_bytes()).hexdigest()}))
