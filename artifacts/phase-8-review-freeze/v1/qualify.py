"""One retained archive, all its saved replays, and one read-only S3 range."""

import hashlib
import importlib.metadata
import sys
from datetime import UTC, datetime
from pathlib import Path

from transport import Receipt, S3Store, extract, load, record, sha

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path[:0] = [str(REPO), str(REPO / "artifacts/phase-8-parallel-pilot/v1")]
from measure_p82 import execution  # noqa: E402


def main() -> None:
    identity = "cal-p84-postflight-v1-01"
    original = load(REPO / "artifacts/phase-8-parallel-pilot/recovery-v7/verified-backups.json")
    proof = original["receipt"]
    receipt = Receipt(bucket="fyp-p82-20261005-018da1d6-803656589923", key=proof["key"],
                      version_id=proof["version_id"], sha256=proof["sha256"], bytes=proof["bytes"])
    record(HERE / "pilot-receipt.json", receipt.model_dump())
    archive = Path(original["primary"])
    before = sha(archive)
    result_path = HERE / "qualification.json"
    try:
        local = extract(archive, Path("E:/P84Q1/x"), receipt.sha256)
        rows = [execution(p) for p in sorted(Path("E:/P84Q1/x/fyp-p83-v1").rglob("export.json"))]
        if len(rows) != 24 or any(r["oracle_replay"] != "IDENTICAL" for r in rows):
            raise ValueError("RETAINED_PILOT_REPLAY_DRIFT")
        store = S3Store("fyp-research")
        store.head(receipt)
        data = store.read(receipt, 0, 65535)
        with archive.open("rb") as incoming:
            if data != incoming.read(65536):
                raise ValueError("PINNED_REAL_RANGE_DIFFERS_FROM_ARCHIVE")
        record(result_path, {
            "at": datetime.now(UTC).isoformat(), "id": identity,
            "classification": "EVIDENCE_ONLY_CALIBRATION_NO_NEW_BUSINESS_RUNS",
            "main_started": False, "freeze_created": False,
            "extraction": local, "independent_replays": rows,
            "real_s3_range": {"bytes": len(data), "version_id": receipt.version_id,
                              "sha256": hashlib.sha256(data).hexdigest()},
            "full_network_download_repeated": False,
            "full_network_download_reference":
                "phase-8-parallel-pilot/recovery-v6/verified-download.json",
            "archive_unchanged": sha(archive) == before,
            "dependencies": {p: importlib.metadata.version(p) for p in
                             ["boto3", "botocore", "pydantic"]},
        })
        print("PASS: real short-path archive, 24 identical saved replays, pinned S3 range.")
    except BaseException as error:
        record(HERE / "qualification-failure.json", {
            "at": datetime.now(UTC).isoformat(), "id": identity, "type": type(error).__name__,
            "partial_retained": "E:/P84Q1/x", "main_started": False})
        raise


if __name__ == "__main__":
    main()
