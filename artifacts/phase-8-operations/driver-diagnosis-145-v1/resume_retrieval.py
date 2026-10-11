"""Read-only diagnostic adapter; frozen transport and campaign source untouched."""
import sys
import time
from pathlib import Path

sys.path.insert(0, "E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete")
from transport import Receipt, S3Store, download, extract, load, record
from urllib3.exceptions import ReadTimeoutError


class DiagnosticStore(S3Store):
    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        try:
            return super().read(receipt, start, end)
        except ReadTimeoutError as error:
            # Actual raw SDK-boundary timeout; only this read can be retried.
            record(Path("E:/p8driver145v1/transport2") / f"raw-timeout-{time.time_ns()}.json",
                   {"type": type(error).__name__, "range": [start, end], "read_only": True})
            raise OSError("DIAGNOSTIC_RAW_BODY_TIMEOUT") from error


def main() -> None:
    root = Path("E:/p8driver145v1/transport2")
    receipt = Receipt.model_validate(load(Path(__file__).parent / "inspection-receipt.json"))
    archive = download(DiagnosticStore("fyp-research"), receipt, root)
    proof = extract(archive, root / "x", receipt.sha256)
    record(root / "extraction-verified.json", proof)
    print(proof)


if __name__ == "__main__":
    main()
