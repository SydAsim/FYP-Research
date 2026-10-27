"""Immutable, bounded external SSM records; no campaign retry loop."""
from pathlib import Path
import sys,json,base64,gzip
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'phase-8-continuation-deployment/v10/attempt2'))
import read_control as recorder
recorder.HERE=HERE
def main():
    action,label,*args=sys.argv[1:]
    if action=='send':
        body=gzip.compress(Path(args[0]).read_bytes())
        packed=base64.b64encode(body).decode()
        commands=["python3 - <<'EXTERNAL'\nimport base64,gzip,subprocess\nsubprocess.run(['bash','-s'],input=gzip.decompress(base64.b64decode('"+packed+"')),check=True)\nEXTERNAL"]
        recorder.record(label+'-parameters.json',{'commands':commands,'executionTimeout':['300']})
        r=recorder.call(label,['ssm','send-command','--instance-ids','i-057344e5372faf62f','--document-name','AWS-RunShellScript','--comment','Authorized v10 paused-boundary '+label,'--parameters','file://'+str(HERE/(label+'-parameters.json')),'--timeout-seconds','60'])
        print(json.dumps({'CommandId':r['Command']['CommandId'],'Status':r['Command']['Status']}))
    elif action=='poll':
        r=recorder.call(label,['ssm','get-command-invocation','--instance-id','i-057344e5372faf62f','--command-id',args[0]])
        print(json.dumps(r))
    elif action=='aws':
        print(json.dumps(recorder.call(label,args)))
if __name__=='__main__':main()
