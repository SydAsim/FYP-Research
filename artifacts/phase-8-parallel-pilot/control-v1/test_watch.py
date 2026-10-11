"""The local postflight must not clean up an unverified or replaced export."""

import base64
from pathlib import Path

import pytest
from watch import Receipt, check_head, copy_verified

from research.execution_setup.core import digest


def receipt() -> Receipt:
    checksum = "ab" * 32
    return Receipt(key=f"exports/phase83-evidence-{checksum}.tar.gz", sha256=checksum,
                   bytes=100, version_id="original", upload_exit=0, main_started=False,
                   action="verified export")


def test_version_and_checksum_cannot_be_replaced() -> None:
    value = receipt()
    head = {"VersionId": "original", "ContentLength": 100,
            "Metadata": {"sha256": value.sha256},
            "ChecksumSHA256": base64.b64encode(bytes.fromhex(value.sha256)).decode()}
    check_head(value, head)
    for key, replacement in (("VersionId", "replacement"), ("ContentLength", 101),
                             ("ChecksumSHA256", base64.b64encode(b"x" * 32).decode())):
        with pytest.raises(ValueError, match="DRIFT"):
            check_head(value, {**head, key: replacement})


def test_unexpected_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="UNEXPECTED_EXPORT_KEY"):
        receipt().model_copy(update={"key": "source/unrelated"}).validate_key()


def test_existing_failed_copy_not_overwritten(tmp_path: Path) -> None:
    source, target = tmp_path / "source", tmp_path / "backup"
    source.write_bytes(b"original")
    copy_verified(source, target, digest(source))
    target.write_bytes(b"unsuccessful-copy")
    with pytest.raises(ValueError, match="HASH_DRIFT"):
        copy_verified(source, target, digest(source))
    assert target.read_bytes() == b"unsuccessful-copy"
