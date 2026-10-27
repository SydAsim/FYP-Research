"""Single-send operational transport; retained results and no automatic retries."""
import base64,gzip,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('recorded_control',ROOT/'artifacts/phase-8-continuation-deployment/v10/attempt2/read_control.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.HERE=HERE
HOST='i-057344e5372faf62f'
def main():
    action,label,*args=sys.argv[1:]
    if action=='send':
        packed=base64.b64encode(gzip.compress(Path(args[0]).read_bytes())).decode()
        body="import base64,gzip,subprocess\nsubprocess.run(['bash','-s'],input=gzip.decompress(base64.b64decode('"+packed+"')),check=True)"
        params={'commands':["python3 -B - <<'AUTHORIZED_OPERATION'\n"+body+"\nAUTHORIZED_OPERATION\n"],'executionTimeout':[args[1] if len(args)>1 else '360']}
        r.record(label+'-parameters.json',params)
        x=r.call(label,['ssm','send-command','--instance-ids',HOST,'--document-name','AWS-RunShellScript','--parameters','file://'+str(HERE/(label+'-parameters.json')),'--timeout-seconds','60','--comment','Authorized guarded v12 continuation; reviewed gates required'])
        print(json.dumps({'CommandId':x['Command']['CommandId'],'Status':x['Command']['Status']}))
    elif action=='poll':
        print(json.dumps(r.call(label,['ssm','get-command-invocation','--command-id',args[0],'--instance-id',HOST])))
    elif action=='aws':
        print(json.dumps(r.call(label,args)))
    else:raise ValueError('UNKNOWN_ACTION')
if __name__=='__main__':main()
