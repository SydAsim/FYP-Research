"""Read-only review integrity and main-unstarted check; no acceptance or launch."""

import hashlib
import json
from pathlib import Path

from transport import load, sha

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def verify() -> None:
    fingerprints = load(HERE / "review-fingerprints.json")
    if fingerprints["status"] != "REVIEW_ONLY_NOT_FROZEN":
        raise ValueError("REVIEW_MANIFEST_STATUS_DRIFT")
    for name, expected in fingerprints["files"].items():
        path = REPO / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"REVIEW_HASH_DRIFT: {name}")
    canonical = json.dumps(fingerprints["files"], sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(canonical.encode()).hexdigest() != fingerprints["inventory_sha256"]:
        raise ValueError("INVENTORY_HASH_DRIFT")
    for name, expected in load(HERE / "preserved-before.json").items():
        if sha(REPO / name) != expected:
            raise ValueError(f"HISTORICAL_HASH_DRIFT: {name}")
    slots = load(REPO / "artifacts/phase-8-study-design/v4/main-slots.json")
    if (len(slots) != 1500 or any(s["status"] != "NOT_STARTED"
                                 or s["execution_id"] is not None for s in slots)):
        raise ValueError("MAIN_STARTED_OR_SCOPE_DRIFT")
    status = load(HERE / "acceptance-status.json")
    if (status["review_accepted"] or status["review_receipt"] is not None
            or status["freeze_hash"] is not None or status["launch_authorization"] is not None):
        raise ValueError("UNREVIEWED_ACCEPTANCE_FREEZE_OR_LAUNCH")
    print("PASS: review and historical hashes; 1500 NOT_STARTED; no freeze/launch receipt.")


if __name__ == "__main__":
    verify()
