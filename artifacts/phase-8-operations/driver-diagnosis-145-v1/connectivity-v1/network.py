"""Bounded connectivity diagnosis; safe configuration output, read-only calls."""
import configparser, http.client, json, os, socket, ssl, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit

HERE=Path(__file__).parent
HOSTS=['s3.ap-southeast-2.amazonaws.com','fyp-p82-20261005-018da1d6-803656589923.s3.ap-southeast-2.amazonaws.com','ec2.ap-southeast-2.amazonaws.com','example.com']

def endpoint(value):
    try:
        u=urlsplit(value if '://' in value else '//'+value)
        return {'scheme':u.scheme,'host':u.hostname,'port':u.port,'userinfo_present':u.username is not None}
    except ValueError:return {'unparseable':True}

def worker():
    import boto3
    from botocore.config import Config
    if (HERE/'network-results.json').exists():raise RuntimeError('NO_AUTOMATIC_DIAGNOSTIC_RESTART')
    results={'started_at':datetime.now(timezone.utc).isoformat(),'configuration':{},'network':[],'aws':[]}
    def save():
        (HERE/'network-results.json').write_text(json.dumps(results,indent=2))
    config=configparser.RawConfigParser();config.read(Path.home()/'.aws/config')
    safe={s:{k:v for k,v in config.items(s) if k in ('region','output','retry_mode','max_attempts')} for s in config.sections()}
    results['configuration']={'proxy':{k:endpoint(v) for k,v in urllib.request.getproxies().items() if k!='no'},'no_proxy_present':bool(os.environ.get('NO_PROXY') or os.environ.get('no_proxy')),'aws_config_safe':safe,'credential_environment_variable_names':[k for k in os.environ if k.startswith('AWS_') and any(x in k for x in ('KEY','TOKEN','CREDENTIAL'))],'certificate_overrides_present':{k:bool(os.environ.get(k)) for k in ('AWS_CA_BUNDLE','REQUESTS_CA_BUNDLE','SSL_CERT_FILE')},'aws_endpoint_override_present':{k:True for k in os.environ if k.startswith('AWS_ENDPOINT_URL')}}
    hosts_path=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/drivers/etc/hosts'
    results['configuration']['aws_hosts_entries']=[line.strip() for line in hosts_path.read_text(errors='replace').splitlines() if 'amazonaws.com' in line and not line.lstrip().startswith('#')]
    session=boto3.Session(profile_name='fyp-research',region_name='ap-southeast-2')
    credentials=session.get_credentials()
    results['configuration']['credential_provider']=credentials.method if credentials else None
    save()
    for host in HOSTS:
        row={'host':host};results['network'].append(row);start=time.monotonic()
        try:
            addresses=list(dict.fromkeys(a[4][0] for a in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM,family=socket.AF_INET)))[:2]
            row['dns']={'addresses':addresses,'seconds':time.monotonic()-start}
        except OSError as exc:row['dns']={'error_type':type(exc).__name__,'errno':exc.errno};save();continue
        row['connections']=[]
        for address in addresses:
            item={'address':address};row['connections'].append(item);start=time.monotonic()
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(5)
            try:
                sock.connect((address,443));item['tcp_seconds']=time.monotonic()-start
                tls=ssl.create_default_context().wrap_socket(sock,server_hostname=host)
                item['tls']={'version':tls.version(),'cipher':tls.cipher()[0],'verification':'DEFAULT_TRUST_AND_HOSTNAME_PASS'}
                # No auth or signed URL. Only the public endpoint root is requested.
                tls.sendall(f'HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n'.encode())
                response=http.client.HTTPResponse(tls);response.begin()
                item['http']={'status':response.status,'request_id_present':bool(response.getheader('x-amz-request-id'))}
                tls.close();break
            except (OSError,ssl.SSLError,http.client.HTTPException) as exc:
                item['error_type']=type(exc).__name__;item['errno']=getattr(exc,'errno',None);item['seconds']=time.monotonic()-start
            finally:sock.close();save()
    config=Config(connect_timeout=5,read_timeout=10,retries={'total_max_attempts':1,'mode':'standard'},s3={'addressing_style':'path'})
    for service,operation in [('s3','head_object'),('ec2','describe_instances'),('sts','get_caller_identity'),('freetier','get_account_plan_state')]:
        # Only try AWS APIs if at least the regional S3 and EC2 TLS checks pass.
        if not all(any('http' in c for c in r.get('connections',[])) for r in results['network'] if r['host'] in HOSTS[:1]+HOSTS[2:3]):break
        row={'service':service,'operation':operation};results['aws'].append(row);start=time.monotonic()
        try:
            client=session.client(service,config=config)
            if service=='s3':
                receipt=json.loads((HERE.parent/'original145-receipt.json').read_text())
                r=client.head_object(Bucket=receipt['bucket'],Key=receipt['key'],VersionId=receipt['version_id'],ChecksumMode='ENABLED')
                row['result']={'bytes':r['ContentLength'],'version_id':r['VersionId'],'checksum_sha256':r.get('ChecksumSHA256')}
            elif service=='ec2':
                r=client.describe_instances(InstanceIds=['i-057344e5372faf62f'])
                row['result']=[{'instance_id':i['InstanceId'],'state':i['State']['Name']} for reservation in r['Reservations'] for i in reservation['Instances']]
            elif service=='sts':r=client.get_caller_identity();row['result']={'authenticated':True,'principal_type':r['Arn'].split(':')[5].split('/')[0]}
            else: r=client.get_account_plan_state();row['result']={k:v for k,v in r.items() if k!='ResponseMetadata'}
        except Exception as exc:
            row['error_type']=type(exc).__name__
            if hasattr(exc,'response'):row['aws_error_code']=exc.response.get('Error',{}).get('Code');row['http_status']=exc.response.get('ResponseMetadata',{}).get('HTTPStatusCode')
        row['seconds']=time.monotonic()-start;save()
    results['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps(results,indent=2))

def main():
    if '--worker' in sys.argv:return worker()
    HERE.mkdir(exist_ok=True)
    policy=HERE/'policy.json'
    if policy.exists():raise RuntimeError('DIAGNOSTIC_ALREADY_RECORDED_NO_RESET')
    policy.write_text(json.dumps({'overall_seconds':600,'dns_host_budget':4,'tcp_address_budget':8,'tls_http_budget':4,'read_only_aws_call_budget':4,'sdk_attempts_per_call':1,'archive_get_budget':0,'started_at':datetime.now(timezone.utc).isoformat()},indent=2))
    with (HERE/'process-stdout.log').open('x') as out,(HERE/'process-stderr.log').open('x') as err:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=out,stderr=err)
        (HERE/'process.json').write_text(json.dumps({'pid':child.pid,'interpreter':sys.executable,'script':str(Path(__file__).resolve()),'timeout_seconds':600},indent=2))
        try:code=child.wait(timeout=600)
        except subprocess.TimeoutExpired:
            # This exact Popen object identifies the owned child; never kill by name.
            child.kill();child.wait();code='PROCESS_DEADLINE_KILLED_OWNED_CHILD'
    (HERE/'process-result.json').write_text(json.dumps({'exit':code,'finished_at':datetime.now(timezone.utc).isoformat()},indent=2))
    print((HERE/'network-results.json').read_text() if (HERE/'network-results.json').exists() else 'No completed worker results; see retained process logs')

if __name__=='__main__':main()
