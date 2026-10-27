"""Bounded external v11 control requests with immutable responses; no automatic resend."""
from pathlib import Path
import sys,json,base64,gzip,hashlib
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO/'artifacts/phase-8-continuation-deployment/v10/attempt2'))
import read_control as recorder
recorder.HERE=HERE
HOST='i-057344e5372faf62f'
def main():
    action,label,*args=sys.argv[1:]
    if action=='send':
        packed=base64.b64encode(gzip.compress(Path(args[0]).read_bytes())).decode()
        body="import base64,gzip,subprocess\nsubprocess.run(['bash','-s'],input=gzip.decompress(base64.b64decode('"+packed+"')),check=True)"
        params={'commands':["python3 - <<'EXTERNAL'\n"+body+"\nEXTERNAL"],'executionTimeout':[args[1] if len(args)>1 else '300']}
        recorder.record(label+'-parameters.json',params)
        r=recorder.call(label,['ssm','send-command','--instance-ids',HOST,'--document-name','AWS-RunShellScript','--parameters','file://'+str(HERE/(label+'-parameters.json')),'--comment','Authorized closed616 v11 '+label,'--timeout-seconds','60'])
        print(json.dumps({'CommandId':r['Command']['CommandId'],'Status':r['Command']['Status']}))
    elif action=='poll':
        print(json.dumps(recorder.call(label,['ssm','get-command-invocation','--instance-id',HOST,'--command-id',args[0]])))
    else:
        result=recorder.call(label,args)
        print(json.dumps({'status':'RECORDED','label':label,'summary':result if len(json.dumps(result))<2500 else {'keys':list(result),'Versions':len(result.get('Versions',[])),'IsTruncated':result.get('IsTruncated'),'NextKeyMarker':result.get('NextKeyMarker'),'NextVersionIdMarker':result.get('NextVersionIdMarker')}}))
if __name__=='__main__':main()
