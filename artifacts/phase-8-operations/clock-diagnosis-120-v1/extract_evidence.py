"""Read-only diagnostic extraction; never restores an application or campaign."""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
DEST = Path('E:/p8clock120v1')

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def extract(path: Path, target: Path) -> dict[str, str]:
    target.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}
    total = 0
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or ':' in member.name or '\\' in member.name:
                raise ValueError('UNSAFE_ARCHIVE_MEMBER')
            if member.isdir():
                (target / member.name).mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or member.name in files:
                raise ValueError('LINK_OR_DUPLICATE_MEMBER')
            total += member.size
            if total > 512 * 1024 * 1024:
                raise ValueError('EXTRACTION_SIZE_LIMIT')
            output = target / member.name
            output.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            assert stream is not None
            with output.open('xb') as destination:
                destination.write(stream.read())
            assert output.stat().st_size == member.size
            files[member.name] = sha(output)
    return files

archive = HERE / 'inspection.tar.gz'
assert sha(archive) == '7dbfc44f3df08717acd802cd6fda7b79c9e6e281cd87a7e4fbb423747ac59859'
files = extract(archive, DEST)
manifest = json.loads((DEST / 'inspection/manifest.json').read_text())
for name, digest in manifest['files'].items():
    assert sha(DEST / 'inspection' / name) == digest
master = DEST / 'inspection/verified-master.tar.gz'
assert sha(master) == '5892e3b90b577537c99720debd87726ed424c06b319f404edd60169a449ca7e7'
master_files = extract(master, DEST / 'master')
with (HERE / 'extraction-verification.json').open('x', encoding='utf-8') as output:
    json.dump({'status': 'PASS', 'inspection_sha256': sha(archive), 'master_sha256': sha(master),
               'destination': str(DEST), 'inspection_members': files, 'master_members': master_files}, output, indent=2)
print(json.dumps({'status': 'PASS', 'destination': str(DEST), 'master_files': len(master_files)}))
