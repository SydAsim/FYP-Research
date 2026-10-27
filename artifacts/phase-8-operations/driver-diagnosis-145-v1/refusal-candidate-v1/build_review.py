"""Read-only evidence report assembly; no AWS, driver, oracle or campaign import."""
from __future__ import annotations

import collections
import difflib
import hashlib
import importlib.util
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SOURCE = Path("E:/p8v9/source")
OVERLAY = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete"
ROOT = Path("D:/FYP-ResearchBackups/slot145-diagnosis/verified-cloud-v2/required")
REPO = HERE.parents[3]


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    path = path.resolve()
    if sys.platform == "win32":
        path = Path("\\\\?\\" + str(path))
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def save(name: str, data: Any) -> None:
    with (HERE / name).open("x", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def main() -> None:
    export = ROOT / "executions/01a11705-11f1-7386-a804-76b957c218d5/export.json"
    row = read(export)
    sys.path[:0] = [str(SOURCE), str(OVERLAY)]
    spec = importlib.util.spec_from_file_location(
        "candidate_diagnostic_refusal", HERE / "refusal.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    proof = module.recognize(row)
    assert proof
    with sqlite3.connect(
        (ROOT / "ledger.sqlite3").resolve().as_uri() + "?mode=ro&immutable=1", uri=True
    ) as db:
        events = [
            {"at": at, **json.loads(body)}
            for at, body in db.execute("SELECT at,body FROM events ORDER BY n")
            if json.loads(body).get("kind") == "DRIVER_FAILURE"
        ]
    freeze = REPO / "artifacts/phase-8-continuation-freeze/v9"
    manifest = read(freeze / "freeze-manifest.json")
    drift = [name for name, digest in manifest["files"].items() if sha(freeze / name) != digest]
    assert not drift, drift
    before = read(HERE / "preservation-before.json")
    assert all(sha(Path(path)) == digest for path, digest in before.items())
    save("preservation-after.json", {
        "status": "PASS", "unchanged_before_hashes": before,
        "frozen_manifest_sha256": sha(freeze / "freeze-manifest.json"),
        "frozen_inventory_files_checked": len(manifest["files"]), "drift": drift,
    })
    inspection = Path("E:/p8driver145v1/provisional2/inspection")
    inspection_manifest = read(inspection / "manifest.json")["files"]
    assert sha(inspection / "read-only-ledger.json") == inspection_manifest["read-only-ledger.json"]
    rows = read(inspection / "read-only-ledger.json")["rows"]
    bindings = read(OVERLAY / "closed-120/bindings.json")
    assert [{key: item[key] for key in bindings[0]} for item in rows] == bindings
    assert collections.Counter(item["state"] for item in rows) == {
        "BACKED_UP": 145, "PLANNED": 1355,
    }
    assert rows[145]["execution_id"] == "01a11705-11f1-772d-8190-c43552871801"
    save("boundary-verification.json", {
        "status": "PASS_RETAINED_METADATA", "counts": {"BACKED_UP": 145, "PLANNED": 1355},
        "identities_checked": 1500, "replay": False, "next": rows[145],
        "ledger_export_sha256": sha(inspection / "read-only-ledger.json"),
        "bindings_sha256": sha(OVERLAY / "closed-120/bindings.json"),
        "original145_receipt_sha256": sha(HERE.parent / "original145-receipt.json"),
    })
    save("evidence.json", {
        "bundle_sha256": "f9d639added6872c5679e931b4f07e1027643d00a28f9bb4cbbc0e5601c4cb48",
        "local_verification": str(ROOT.parent / "local-verification.json"),
        "verification_scope": "User-described verified bundle; internal member hashes and ledger "
        "chain locally verified. Independent CloudShell bundle digest not supplied separately. "
        "Full pinned original archive hash is cloud-extractor proof, not locally re-downloaded.",
        "export_sha256": sha(export), "execution_id": row["execution_id"],
        "case_id": row["input"]["case_id"], "raw_status": row["status"],
        "failure": row["failure"],
        "refused_call": next(c for c in row["http"] if c["status"] == 409),
        "operations": row["snapshot"]["history"]["operations"],
        "effects": row["snapshot"]["history"]["effects"],
        "observations": row["snapshot"]["observations"], "driver_failure_notices": events,
        "driver_finished_at": row["driver_finished_at"],
        "original_deadline": row["original_deadline"], "final_poll": row["polls"][-1]["at"],
        "existing_values_copied_no_oracle_run": row["revised_grade"]["values"],
        "original_analysis_censor_reason": row["analysis_row"]["censor_reason"],
        "candidate_classification_diagnostic_only": proof,
        "historical_status_or_grades_written": False,
    })
    at = datetime.now(UTC)
    deadline = datetime.fromisoformat("2026-10-22T15:24:23.810674+00:00")
    start = datetime.fromisoformat("2026-10-07T15:24:23.810674+00:00")
    available = (deadline - at).total_seconds() / 3600
    remaining = 290 * 1355 / 1498
    preparation = 2.5
    rate = .1197 + .005 + 160 * .096 / 730
    reserve = 48 * 160 * .096 / 730 + 80 * .025 + 5 + 1.25
    projection = ((at - start).total_seconds() / 3600 + remaining + preparation) * rate + reserve
    save("feasibility.json", {
        "at": at.isoformat(), "available_hours": available,
        "unchanged_remaining_allowance_hours": remaining,
        "preparation_shutdown_hours": preparation, "required_hours": remaining + preparation,
        "shortfall_hours": remaining + preparation - available,
        "window_floor_excluding_overhead_hours": 1355 / 6,
        "time_fits": remaining + preparation <= available,
        "cost_conservative_projection_usd": projection,
        "admission_guard_usd": 60, "total_ceiling_usd": 65,
        "admission_fits": projection <= 60, "total_fits": projection <= 65,
        "rate_per_hour_usd": rate, "reserve_usd": reserve,
        "rates_last_verified": "2026-10-10", "actual_current_bill_or_credits": "Not retrieved",
        "accounting": "Unchanged reviewed elapsed-clock conservative model, includes elapsed "
        "stopped hours; forecast is not actual spend. Allowances not reduced.",
        "deadline": deadline.isoformat(), "caps_gib": 80,
    })
    (HERE / "refusal.diff").write_text("".join(difflib.unified_diff(
        (OVERLAY / "refusal.py").read_text().splitlines(True),
        (HERE / "refusal.py").read_text().splitlines(True),
        fromfile="frozen-v9/refusal.py", tofile="candidate-v1/refusal.py",
    )), encoding="utf-8")
    save("verification-results.json", {
        "status": "PASS_FOCUSED_OFFLINE_CANDIDATE_NOT_DEPLOYMENT_QUALIFIED",
        "pytest": {"passed": 24, "failed": 0, "reported_seconds": 1.96,
                   "attempt": "offline-attempt1.txt"},
        "mypy": "PASS: 2 source files",
        "ruff": "PASS after test-only line wrapping; failure retained",
        "runtime": sys.version, "platform": sys.platform,
        "pinned_linux_runtime_checks": "NOT_RUN; existing Windows Python; no Docker/AWS started",
        "new_research_executions": 0, "historical_oracle_runs": 0,
        "freeze": False, "launch": False, "application_files_changed": 0,
        "raw_failure_preserved": True,
    })
    print(json.dumps({"time_shortfall_hours": remaining + preparation - available,
                      "cost_projection": projection, "frozen_files_checked": len(manifest["files"]),
                      "next": rows[145]}, indent=2))


if __name__ == "__main__":
    main()
