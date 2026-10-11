import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest
from transport import Receipt, download, extract, load, sha


class FakeStore:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.fail_at: int | None = None
        self.reads: list[int] = []
        self.head_bad = False

    def head(self, receipt: Receipt) -> None:
        if self.head_bad:
            raise ValueError("S3_VERSION_SIZE_HASH_DRIFT")

    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        self.reads.append(start)
        if start == self.fail_at:
            raise OSError("scripted body interruption")
        return self.data[start : end + 1]


def receipt(data: bytes) -> Receipt:
    return Receipt(
        bucket="test-calibration",
        key="cal-only/archive",
        version_id="v1",
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )


def test_resume_retains_failure_and_same_deadline(tmp_path: Path) -> None:
    data = b"123456789"
    store = FakeStore(data)
    store.fail_at = 3
    with pytest.raises(OSError):
        download(store, receipt(data), tmp_path, workers=1, chunk=3)
    saved = load(tmp_path / "identity.json")
    failure = next(tmp_path.glob("failure-*.json"))
    original_failure = failure.read_bytes()
    store.fail_at = None
    store.reads.clear()
    archive = download(store, receipt(data), tmp_path, workers=1, chunk=3)
    assert archive.read_bytes() == data and store.reads == [3, 6]
    assert load(tmp_path / "identity.json") == saved
    assert failure.read_bytes() == original_failure
    assert len(list((tmp_path / "reads").glob("*.json"))) == 6


def test_hash_drift_is_not_silently_redownloaded(tmp_path: Path) -> None:
    data = b"abcdef"
    store = FakeStore(data)
    archive = download(store, receipt(data), tmp_path, workers=1, chunk=3)
    archive.rename(tmp_path / "retained-original.tar.gz")
    (tmp_path / "pieces/00000000.bin").write_bytes(b"bad")
    store.reads.clear()
    with pytest.raises(ValueError, match="PIECE_DRIFT"):
        download(store, receipt(data), tmp_path, workers=1, chunk=3)
    assert not store.reads and (tmp_path / "pieces/00000000.bin").read_bytes() == b"bad"


def test_expired_original_deadline_blocks_missing_pieces(tmp_path: Path) -> None:
    data = b"abcdef"
    store = FakeStore(data)
    store.fail_at = 0
    with pytest.raises(OSError):
        download(store, receipt(data), tmp_path, workers=1, chunk=3)
    saved = load(tmp_path / "identity.json")
    saved["deadline"] = 0
    (tmp_path / "identity.json").write_text(json.dumps(saved))
    store.fail_at = None
    store.reads.clear()
    with pytest.raises(TimeoutError, match="ORIGINAL_TRANSPORT"):
        download(store, receipt(data), tmp_path, workers=1, chunk=3)
    assert not store.reads


def test_changed_version_and_head_are_rejected(tmp_path: Path) -> None:
    store = FakeStore(b"abc")
    original = receipt(b"abc")
    download(store, original, tmp_path, workers=1)
    changed = original.model_copy(update={"version_id": "v2"})
    with pytest.raises(ValueError, match="IDENTITY_DRIFT"):
        download(store, changed, tmp_path)
    store.head_bad = True
    with pytest.raises(ValueError, match="S3_VERSION"):
        download(store, original, tmp_path)


def test_small_archive_uses_fewer_than_eight_workers(tmp_path: Path) -> None:
    result = download(FakeStore(b"x"), receipt(b"x"), tmp_path)
    assert result.read_bytes() == b"x"


def test_unproven_piece_and_existing_lock_are_retained(tmp_path: Path) -> None:
    (tmp_path / "pieces").mkdir()
    piece = tmp_path / "pieces/00000000.bin"
    piece.write_bytes(b"abc")
    with pytest.raises(ValueError, match="UNPROVEN"):
        download(FakeStore(b"abc"), receipt(b"abc"), tmp_path)
    assert piece.read_bytes() == b"abc"
    (tmp_path / "transport.lock").write_text("unreconciled process")
    with pytest.raises(FileExistsError):
        download(FakeStore(b"abc"), receipt(b"abc"), tmp_path)
    assert (tmp_path / "transport.lock").exists()


def tar(path: Path, names: list[str], *, link: bool = False) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                archive.addfile(member)
            else:
                member.size = 4
                archive.addfile(member, io.BytesIO(b"data"))


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "C:/escape", "a\\b", "a:stream", "con.txt", "a.", "a?"]
)
def test_unsafe_tar_rejected_before_extraction(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "e.tar.gz"
    tar(archive, [name])
    with pytest.raises(ValueError, match="UNSAFE"):
        extract(archive, tmp_path / "x", sha(archive))
    assert not (tmp_path / "x").exists()


def test_link_collision_path_and_growth_limits(tmp_path: Path) -> None:
    archive = tmp_path / "e.tar.gz"
    tar(archive, ["link"], link=True)
    with pytest.raises(ValueError, match="UNSAFE"):
        extract(archive, tmp_path / "x", sha(archive))
    tar(archive, ["A/file", "a/file"])
    with pytest.raises(ValueError, match="DUPLICATE"):
        extract(archive, tmp_path / "x", sha(archive))
    tar(archive, ["a" * 200])
    with pytest.raises(ValueError, match="PATH_BUDGET"):
        extract(archive, tmp_path / "x", sha(archive))
    tar(archive, ["safe"])
    with pytest.raises(ValueError, match="CAPACITY"):
        extract(archive, tmp_path / "x", sha(archive), max_bytes=3)


def test_short_extract_and_no_overwrite(tmp_path: Path) -> None:
    archive = tmp_path / "e.tar.gz"
    tar(archive, ["deep/folder/file"])
    proof = extract(archive, tmp_path / "x", sha(archive))
    assert proof["members"] == 1 and (tmp_path / "x/deep/folder/file").read_bytes() == b"data"
    with pytest.raises(ValueError, match="NEW_EXTRACTION"):
        extract(archive, tmp_path / "x", sha(archive))
