"""LF transport copy only; preserve failed wrapper, frozen package and pause."""
from ops import HERE
from controls import hash_file,read,write_new

failed=read(HERE/'launch-service-status1-result.json')['result']
assert failed['Status']=='Failed' and failed['ResponseCode']==2
assert 'pipefail\r: invalid option name' in failed['StandardErrorContent']
source=HERE/'launch-service.sh';before=source.read_bytes()
normalized=before.replace(b'\r\n',b'\n')
assert b'\r' not in normalized
target=HERE/'launch-service-lf.sh'
with target.open('xb') as f:f.write(normalized)
write_new(HERE/'retained-external-line-ending-failure.json',{
 'status':'FAILED_EXTERNAL_INVOCATION_PRESERVED','failed_SSM_command':failed['CommandId'],
 'failed_wrapper_sha256':hash_file(source),'LF_transport_copy_sha256':hash_file(target),
 'logical_script_changed':False,'frozen_code_changed':False,
 'error_before_Python_gates_or_service_start':True,'original_pause_not_released':True,
 'main_research_execution_started':False,'next_invocation_requires_all_original_gates':True})
print('Only external transport LF normalized; failed script retained.')
