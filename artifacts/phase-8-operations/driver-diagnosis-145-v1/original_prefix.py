"""Bounded partial original archive read for triage; no full-hash claim."""
import hashlib
import io
import json
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from path_retrieval import PathStore, Receipt, load, record

def main() -> None:
    here = Path(__file__).parent
    proof = Receipt.model_validate(load(here / "original145-receipt.json"))
    root = Path("E:/p8driver145v1/original145-prefix")
    root.mkdir(exist_ok=False)
    store = PathStore("fyp-research")
    store.head(proof)
    deadline = time.monotonic() + 240
    def piece(index: int) -> bytes:
        start, end = index * 65536, (index + 1) * 65536 - 1
        for attempt in range(1, 4):
            if time.monotonic() >= deadline:
                raise TimeoutError("DIAGNOSTIC_PREFIX_LIMIT")
            try:
                data = store.read(proof, start, end)
                with (root / f"{index:04d}.bin").open("xb") as target:
                    target.write(data)
                record(root / f"{index:04d}-PASS.json", {"range": [start, end], "version_id": proof.version_id,
                       "sha256": hashlib.sha256(data).hexdigest(), "attempt": attempt})
                return data
            except OSError as error:
                record(root / f"{index:04d}-failure-{attempt}.json", {"type": type(error).__name__, "detail": str(error)})
                if attempt == 3:
                    raise
        raise RuntimeError("UNREACHABLE")
    with ThreadPoolExecutor(max_workers=8) as pool:
        data = b"".join(pool.map(piece, range(32)))
    out = root / "x"
    out.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r|gz") as archive:
        for member in archive:
            if member.name.startswith("slot/master"):
                break
            if member.isdir():
                (out / member.name).mkdir(parents=True, exist_ok=True)
                continue
            assert member.isfile() and member.size < 60 * 1024**2
            target = out / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            assert stream is not None
            with target.open("xb") as output:
                output.write(stream.read())
    for p in out.rglob("export.json"):
        row = load(p)
        print(json.dumps({k: row.get(k) for k in ("execution_id", "case_id", "arm", "status", "failure", "driver_finished_at", "driver_classification")}, indent=2))
    print("PARTIAL_ARCHIVE_ONLY_FULL_ARCHIVE_VERIFICATION_REQUIRED")

if __name__ == "__main__":
    main()
