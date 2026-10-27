set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 30s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'OFFLINE'
import contextlib,hashlib,io,json,os,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from botocore.session import Session
from botocore.utils import InstanceMetadataFetcher
from botocore.exceptions import ReadTimeoutError,NoCredentialsError
assert hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()=='021044895e95be79dc2f110367607e684119afbc8ce75f6f0eec94844e0acec7'
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from inventory_read import read_inventory
checks=[]
with patch.dict(os.environ,{},clear=True):
    s=Session();assert s.get_config_variable('metadata_service_timeout')==1 and s.get_config_variable('metadata_service_num_attempts')==1
    checks.append('qualified_sdk_defaults_one_second_one_attempt')
with patch.dict(os.environ,{'AWS_METADATA_SERVICE_TIMEOUT':'3','AWS_METADATA_SERVICE_NUM_ATTEMPTS':'3'},clear=True):
    s=Session();assert s.get_config_variable('metadata_service_timeout')==3 and s.get_config_variable('metadata_service_num_attempts')==3
    checks.append('explicit_bounded_metadata_environment')
class FakeHTTP:
    def __init__(self,failures):self.failures=failures;self.calls=0
    def send(self,request,**kwargs):
        self.calls+=1
        if self.calls<=self.failures:raise ReadTimeoutError(endpoint_url='http://offline.invalid')
        return SimpleNamespace(status_code=200,text='offline-role')
def fetch(failures):
    f=InstanceMetadataFetcher(timeout=3,num_attempts=3)
    f._session=FakeHTTP(failures)
    return f
f=fetch(1);assert f._get_request('latest/meta-data/iam/security-credentials/',lambda r:False,token='offline').text=='offline-role' and f._session.calls==2
checks.append('metadata_timeout_then_success')
f=fetch(3)
try:f._get_request('latest/meta-data/iam/security-credentials/',lambda r:False,token='offline')
except Exception as e:
    assert type(e).__name__=='_RetriesExceededError' and f._session.calls==3
else:raise AssertionError('METADATA_FAILURE_NOT_PROPAGATED')
checks.append('metadata_exhaustion_is_finite')
class MissingCredentials:
    calls=0
    def list_object_versions(self,**kwargs):self.calls+=1;raise NoCredentialsError()
c=MissingCredentials();log=io.StringIO()
try:
    with contextlib.redirect_stderr(log):read_inventory(c,'offline-bucket','offline/')
except NoCredentialsError:assert c.calls==1 and '"retryable": false' in log.getvalue()
else:raise AssertionError('MISSING_CREDENTIALS_NOT_FAIL_CLOSED')
checks.append('inventory_missing_credentials_still_fail_closed')
print(json.dumps({'status':'PASS','checks':checks,'total':len(checks),'python':sys.version,'aws_calls':0,'research_executions':0,'dependencies_installed':0}))
OFFLINE
