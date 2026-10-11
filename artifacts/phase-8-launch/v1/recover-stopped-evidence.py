"""Recover version-pinned evidence through MCP-signed URLs; never admits a driver."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import requests

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'artifacts/phase-8-review-freeze/v2'))
from postflight import recover
from storage import ObjectProof
from transport import Receipt


class SignedStore:
    def __init__(self, url: str, head: dict[str, object]) -> None:
        self.url = url
        self.metadata = head

    def head(self, receipt: Receipt) -> None:
        value = self.metadata
        metadata = value.get('Metadata', {})
        if not isinstance(metadata, dict):
            raise ValueError('INVALID_HEAD_METADATA')
        if (value.get('VersionId') != receipt.version_id
                or value.get('ContentLength') != receipt.bytes
                or metadata.get('sha256') != receipt.sha256
                or base64.b64decode(str(value.get('ChecksumSHA256', ''))).hex() != receipt.sha256):
            raise ValueError('MCP_HEAD_PROOF_DRIFT')

    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        try:
            with requests.get(self.url, headers={'Range': f'bytes={start}-{end}'}, timeout=(10, 30), stream=True) as response:
                if (response.status_code != 206
                        or response.headers.get('x-amz-version-id') != receipt.version_id
                        or response.headers.get('Content-Range') != f'bytes {start}-{end}/{receipt.bytes}'):
                    raise ValueError('SIGNED_VERSION_OR_RANGE_DRIFT')
                data = response.raw.read(end-start+2)
        except requests.RequestException as error:
            raise OSError(type(error).__name__) from error
        if len(data) != end-start+1:
            raise ValueError('SIGNED_BODY_LENGTH_DRIFT')
        return data


def main() -> None:
    config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    root = Path(sys.argv[2])
    records = []
    for item in config:
        proof = ObjectProof.model_validate(item['proof'])
        extracted = recover(proof, root/item['label'], SignedStore(item['url'], item['head']))
        records.append({'label': item['label'], 'proof': proof.model_dump(), 'extracted': str(extracted), 'verified': True})
    output = PROJECT / 'artifacts/phase-8-launch/v1/local-postflight.json'
    with output.open('x', encoding='utf-8') as handle:
        json.dump({'status': 'PASS', 'main_driver_replays': 0, 'objects': records}, handle, indent=2)
    print(json.dumps({'status': 'PASS', 'objects': len(records), 'main_driver_replays': 0}))


if __name__ == '__main__':
    main()
