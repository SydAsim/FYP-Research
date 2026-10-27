"""One bounded extraction and finite read-only result transfer; no automatic resend."""
import base64
import csv
import gzip
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = 'i-057344e5372faf62f'
START = time.monotonic()


def save(name, obj):
    with (HERE / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)


def aws(label, args):
    if time.monotonic() - START > 550:
        raise TimeoutError('CONTROLLER_DEADLINE_NO_RETRY')
    command = ['aws', *args, '--profile', 'fyp-research', '--region', 'ap-southeast-2', '--cli-connect-timeout', '5', '--cli-read-timeout', '15', '--output', 'json', '--no-cli-pager']
    save(label + '-request.json', {'command': command, 'process_deadline_seconds': 25, 'automatic_retries': 0})
    p = subprocess.run(command, capture_output=True, text=True, timeout=25, env={**os.environ, 'AWS_MAX_ATTEMPTS': '1', 'AWS_RETRY_MODE': 'standard', 'AWS_PAGER': ''})
    result = {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    save(label + '-response.json', result)
    if p.returncode:
        raise RuntimeError('REQUEST_FAILED_PRESERVED_' + label)
    return json.loads(p.stdout)


def run(label, command, seconds=240):
    params = HERE / (label + '-parameters.json')
    save(params.name, {'commands': [command], 'executionTimeout': [str(seconds)]})
    response = aws(label + '-send', ['ssm', 'send-command', '--instance-ids', HOST, '--document-name', 'AWS-RunShellScript', '--parameters', 'file://' + str(params), '--timeout-seconds', '60', '--comment', 'Read-only saved results review; no campaign mutations'])
    cid = response['Command']['CommandId']
    print(json.dumps({'label': label, 'command_id': cid}), flush=True)
    for n in range(1, 26):
        time.sleep(3)
        result = aws(label + '-poll' + str(n), ['ssm', 'get-command-invocation', '--command-id', cid, '--instance-id', HOST])
        if result['Status'] == 'Success':
            return result['StandardOutputContent']
        if result['Status'] in ('Failed', 'Cancelled', 'TimedOut'):
            raise RuntimeError('REMOTE_FAILED_RETAINED_' + label + ':' + result.get('StandardErrorContent', ''))
    raise TimeoutError('COMMAND_UNRESOLVED_DO_NOT_RESEND_' + cid)


def main():
    body = (HERE / 'collect_saved.py').read_text()
    command = "cd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1\n.venv/bin/python -B - <<'SAVED_GRADES_ONLY'\n" + body + "\nSAVED_GRADES_ONLY\n"
    manifest = json.loads(run('collect', command))
    save('download-manifest.json', manifest)
    parts = []
    assert manifest['chunks'] <= 8
    for n in range(manifest['chunks']):
        start = n * 18000
        command = "python3 -B - <<'CHUNK'\nfrom pathlib import Path\np=Path('/var/tmp/fyp-phase8-saved-results-20261018-v2/download.base64')\nwith p.open('rb') as f:\n f.seek(" + str(start) + ")\n print(f.read(18000).decode())\nCHUNK\n"
        text = run('chunk' + str(n), command, 30).strip()
        if not text or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in text):
            raise ValueError('CHUNK_ENCODING_OR_TRUNCATION')
        with (HERE / ('chunk' + str(n) + '.base64')).open('x') as f:
            f.write(text)
        parts.append(text)
    packed = base64.b64decode(''.join(parts), validate=True)
    assert len(packed) == manifest['gzip_bytes'] and hashlib.sha256(packed).hexdigest() == manifest['gzip_sha256']
    decoded = gzip.decompress(packed)
    assert len(decoded) == manifest['json_bytes'] and hashlib.sha256(decoded).hexdigest() == manifest['json_sha256']
    with (HERE / 'saved-results.json.gz').open('xb') as f:
        f.write(packed)
    with (HERE / 'saved-results.json').open('xb') as f:
        f.write(decoded)
    data = json.loads(decoded)
    endpoint_keys = sorted({k for r in data['rows'] if r['available'] for k in r['values']})
    keys = ['sequence', 'case_id', 'arm', 'attempt', 'execution_id', 'available', 'raw_status', 'stratum', 'generator_family', 'censor_reason', 'voice_evidence', 'export_sha256', *endpoint_keys]
    with (HERE / 'execution-results.csv').open('x', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        for row in data['rows']:
            writer.writerow({**row, **row.get('values', {})})
    save('verification.json', {'download_hashes_match': True, **manifest, 'controller_seconds': time.monotonic() - START, 'regrading': False, 'campaign_mutations': False})
    print(json.dumps({k: v for k, v in data.items() if k not in ('rows', 'snapshot_rows', 'pooled_values_by_stratum')}), flush=True)


if __name__ == '__main__':
    main()
