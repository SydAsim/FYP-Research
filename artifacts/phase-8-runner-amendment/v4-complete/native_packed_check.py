"""One fixed offline native-filesystem metadata diagnostic; no application state restore."""

from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

from controls import hash_file, read
from handover import ro_rows, stage, verify_imported_first
from imported_analysis import imported_row
from storage import verify_local


def main() -> None:
    base = Path("/tmp/p85-v3-native")
    base.mkdir(exist_ok=False)
    digests = {
        "master": "f39e75",  # Complete digest is supplied from the retained archive receipt.
        "first": "cc38346ff273b2f04ef8022345654708991fd40ff8ab3ffc9c8b8f4de5bfb8f1",
        "second": "8fb4547bd0eee33743997f9ad602fb4c03d0243ce117cbd5c11f1fb765daf739",
    }
    master_digest = read(Path("/tmp/native-archive-hashes.json"))["master"]
    digests["master"] = master_digest
    for label, expected in digests.items():
        archive = Path("/tmp") / (label + ".tar.gz")
        verify_local(archive, expected)
        target = base / label
        target.mkdir()
        with tarfile.open(archive, "r:gz") as source:
            source.extractall(target, filter="data")
    root = base / "import"
    result = stage(
        base / "master/slot",
        base / "first/slot",
        root,
        second=base / "second/slot",
        first_archive=Path("/tmp/first.tar.gz"),
        second_archive=Path("/tmp/second.tar.gz"),
    )
    verify_imported_first(root)
    recovered = base / "packed-recovery"
    recovered.mkdir()
    for name in (
        "campaign.sqlite3",
        "saved-identities.json",
        "handover.json",
        "historical-evidence.tar.gz",
    ):
        shutil.copyfile(root / name, recovered / name)
    shutil.copytree(root / "backups", recovered / "backups")
    verify_imported_first(recovered)
    rows = ro_rows(recovered)
    assert len(rows) == 1500 and sum(r["state"] == "BACKED_UP" for r in rows) == 2
    assert sum(r["state"] == "PLANNED" for r in rows) == 1498 and rows[2]["arm"] == "P2"
    analysis = [
        imported_row(recovered, r["execution_id"])[0].model_dump(mode="json") for r in rows[:2]
    ]
    proof = {
        "status": "PASS",
        "scope": "LOCAL_NATIVE_METADATA_DIAGNOSTIC_NOT_MAIN",
        "driver_calls": 0,
        "old_live_state_restored": False,
        "identities": 1500,
        "states": {"BACKED_UP": 2, "PLANNED": 1498},
        "next": rows[2],
        "handover": result,
        "analysis_rows": analysis,
        "bundle_bytes": (root / "historical-evidence.tar.gz").stat().st_size,
        "source_hashes": {p.name: hash_file(p) for p in Path(__file__).parent.glob("*.py")},
    }
    Path("/tmp/native-packed-proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print("PASS: native Linux two-original import and packed recovery; zero driver calls")


if __name__ == "__main__":
    main()
