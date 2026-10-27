"""Exact-byte external export handover; no grades, drivers or application writes."""
from __future__ import annotations

import hashlib
import json
import os
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

MAX_EXPORT = 32 * 1024**2
MAX_MANIFEST = 16 * 1024**2


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def json_object(data: bytes) -> dict[str, Any]:
    """Isolated JSON boundary; duplicate object keys are rejected."""
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    value = json.loads(data, object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError('JSON_OBJECT_REQUIRED')
    return cast(dict[str, Any], value)


@dataclass(frozen=True)
class Identity:
    sequence: int
    execution_id: str
    arm: str
    attempt: int
    fixture_hash: str

    def check(self, data: bytes) -> None:
        if len(data) > MAX_EXPORT:
            raise ValueError('EXPORT_SIZE_LIMIT')
        raw = json_object(data)
        if any(raw.get(key) != getattr(self, key) for key in ('execution_id', 'arm', 'attempt', 'fixture_hash')):
            raise ValueError('EXPORT_IDENTITY_DRIFT')
        if not isinstance(raw.get('status'), str):
            raise ValueError('ORIGINAL_RAW_STATUS_REQUIRED')


def archive_record(archive: Path, expected_hash: str, expected_size: int,
                   identity: Identity) -> tuple[bytes, str, str]:
    """Pinned full archive plus exact export/member manifest binding.

    Read-only streaming: original make_backup archives order manifest before
    master metadata; return after these required members, without extracting any
    directory or copying the historical master again. Full archive hash commits
    all bytes; the original qualified producer and frozen receipt bind the object.
    """
    if archive.stat().st_size != expected_size or file_hash(archive) != expected_hash:
        raise ValueError('ORIGINAL_ARCHIVE_HASH_OR_SIZE_DRIFT')
    member = 'executions/' + identity.execution_id + '/export.json'
    data: bytes | None = None
    manifest: dict[str, Any] | None = None
    seen: set[str] = set()
    with tarfile.open(archive, 'r|gz') as incoming:
        for item in incoming:
            path = PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or '\\' in item.name or not (item.isfile() or item.isdir()):
                raise ValueError('UNSAFE_ORIGINAL_ARCHIVE_MEMBER')
            if item.name in ('slot/' + member, 'slot/manifest.json'):
                if item.name in seen:
                    raise ValueError('DUPLICATE_REQUIRED_ARCHIVE_MEMBER')
                seen.add(item.name)
                maximum = MAX_EXPORT if item.name.endswith('/export.json') else MAX_MANIFEST
                if item.size > maximum:
                    raise ValueError('REQUIRED_MEMBER_SIZE_LIMIT')
                stream = incoming.extractfile(item)
                if stream is None:
                    raise ValueError('REQUIRED_MEMBER_NOT_REGULAR')
                with stream:
                    content = stream.read(maximum + 1)
                if len(content) != item.size:
                    raise ValueError('INCOMPLETE_REQUIRED_MEMBER')
                if item.name.endswith('/export.json'):
                    data = content
                else:
                    manifest = json_object(content)
            if data is not None and manifest is not None:
                break
    if data is None or manifest is None:
        raise ValueError('ORIGINAL_EXPORT_OR_MANIFEST_MISSING')
    expected = manifest.get('files', {}).get(member)
    if not isinstance(expected, str) or digest(data) != expected:
        raise ValueError('ORIGINAL_EXPORT_MEMBER_HASH_DRIFT')
    identity.check(data)
    return data, expected, member


def choose_exact(archive_data: bytes, committed_hash: str,
                 candidates: list[Path], identity: Identity) -> tuple[bytes, str]:
    identity.check(archive_data)
    if digest(archive_data) != committed_hash:
        raise ValueError('COMMITTED_EXPORT_HASH_DRIFT')
    selected = 'pinned-original-archive-member'
    for path in candidates:
        if path.exists():
            if not path.is_file() or path.stat().st_size != len(archive_data) or file_hash(path) != committed_hash:
                raise ValueError('CONFLICTING_RETAINED_EXPORT:' + str(path))
            candidate = path.read_bytes()
            identity.check(candidate)
            if candidate != archive_data:
                raise ValueError('RETAINED_EXPORT_BYTES_DRIFT')
            if selected == 'pinned-original-archive-member':
                selected = str(path)
    return archive_data, selected


def committed_local_record(candidates: list[Path], committed_hash: str,
                           identity: Identity) -> tuple[bytes, str] | None:
    """Previously frozen member commitment can prove an existing history copy."""
    selected: tuple[bytes, str] | None = None
    for path in candidates:
        if path.exists():
            if not path.is_file() or path.stat().st_size > MAX_EXPORT or file_hash(path) != committed_hash:
                raise ValueError('CONFLICTING_FROZEN_HISTORY:' + str(path))
            data = path.read_bytes()
            identity.check(data)
            if selected is not None and selected[0] != data:
                raise ValueError('CONFLICTING_FROZEN_HISTORY_BYTES')
            if selected is None:
                selected = (data, str(path))
    return selected


def atomic_exact(path: Path, data: bytes, *, maximum_tree_bytes: int,
                 budget_root: Path) -> None:
    """Resume a matching partial temp; publish with no-replace hard link.

    Both names, allocated blocks and logical bytes are measured later. A link
    never implies zero archival cost. Original source files are never changed.
    """
    wanted = digest(data)
    if path.exists():
        if not path.is_file() or path.stat().st_size != len(data) or file_hash(path) != wanted:
            raise ValueError('DESTINATION_COLLISION_RETAIN_EXISTING')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial-' + wanted)
    offset = 0
    if temporary.exists():
        offset = temporary.stat().st_size
        if offset > len(data) or temporary.read_bytes() != data[:offset]:
            raise ValueError('PARTIAL_PREFIX_DRIFT_RETAIN_EXISTING')
    used = sum(p.stat().st_size for p in budget_root.rglob('*') if p.is_file())
    if used + (len(data)-offset) + len(data) > maximum_tree_bytes:
        raise ValueError('HANDOVER_STAGING_CAPACITY_STOP')
    with temporary.open('ab' if temporary.exists() else 'xb') as out:
        for start in range(offset, len(data), 1024**2):
            block = data[start:start+1024**2]
            if sum(p.stat().st_size for p in budget_root.rglob('*') if p.is_file()) + len(block) > maximum_tree_bytes:
                raise ValueError('HANDOVER_STREAM_CAPACITY_STOP')
            out.write(block)
        out.flush()
        os.fsync(out.fileno())
    if file_hash(temporary) != wanted:
        raise ValueError('STAGED_BYTES_DRIFT')
    try:
        os.link(temporary, path)
    except FileExistsError:
        if file_hash(path) != wanted or path.stat().st_size != len(data):
            raise ValueError('PUBLICATION_COLLISION_RETAIN_BOTH') from None


def publish_exact(staged: Path, destination: Path, committed_hash: str) -> None:
    if file_hash(staged) != committed_hash:
        raise ValueError('STAGED_EXPORT_HASH_DRIFT')
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(staged, destination)
    except FileExistsError:
        if not destination.is_file() or destination.stat().st_size != staged.stat().st_size or file_hash(destination) != committed_hash:
            raise ValueError('ADOPTION_COLLISION_RETAIN_BOTH') from None
    if file_hash(destination) != committed_hash:
        raise ValueError('ADOPTION_READBACK_DRIFT')
