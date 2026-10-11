"""Bounded read-only regional path-style retrieval, retaining prior attempts."""
import shutil
import sys
import time
from pathlib import Path
import boto3
from botocore.config import Config
from urllib3.exceptions import ReadTimeoutError

sys.path.insert(0, "E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete")
from transport import Receipt, S3Store, download, extract, load, record, sha

ROOT = Path("E:/p8driver145v1/transport3")

class PathStore(S3Store):
    def __init__(self, profile: str) -> None:
        self.client = boto3.Session(profile_name=profile, region_name="ap-southeast-2").client(
            "s3", config=Config(connect_timeout=5, read_timeout=10, max_pool_connections=8,
                                s3={"addressing_style": "path"},
                                retries={"total_max_attempts": 2, "mode": "standard"}))

    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        try:
            return super().read(receipt, start, end)
        except ReadTimeoutError as error:
            record(ROOT / f"raw-timeout-{time.time_ns()}.json",
                   {"type": type(error).__name__, "range": [start, end], "read_only": True})
            raise OSError("DIAGNOSTIC_RAW_BODY_TIMEOUT") from error

def main() -> None:
    previous = Path("E:/p8driver145v1/transport2")
    ROOT.mkdir(exist_ok=False)
    shutil.copyfile(previous / "identity.json", ROOT / "identity.json")
    (ROOT / "pieces").mkdir()
    copied = []
    for proof in (previous / "pieces").glob("*.json"):
        data = proof.with_suffix(".bin")
        saved = load(proof)
        assert sha(data) == saved["sha256"]
        shutil.copyfile(data, ROOT / "pieces" / data.name)
        shutil.copyfile(proof, ROOT / "pieces" / proof.name)
        copied.append(data.name)
    record(ROOT / "read-only-route.json", {"route": "regional_path_style", "reused_verified_pieces": copied,
           "original_transport_deadline_preserved": True, "frozen_source_changed": False})
    receipt = Receipt.model_validate(load(Path(__file__).parent / "inspection-receipt.json"))
    archive = download(PathStore("fyp-research"), receipt, ROOT)
    proof = extract(archive, ROOT / "x", receipt.sha256)
    record(ROOT / "extraction-verified.json", proof)
    print(proof)

if __name__ == "__main__":
    main()
