"""Read-only data/source checks for a new manuscript; no statistical reanalysis."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = ROOT / "artifacts/phase-8-final-analysis/v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_bytes())


def main() -> None:
    fingerprints: dict[str, str] = {}
    analysis_receipt = load(DATA / "analysis/verification.json")
    for name, expected in analysis_receipt["files"].items():
        path = DATA / "analysis" / name
        assert digest(path) == expected, f"Analysis drift: {name}"
        fingerprints[str(path.relative_to(ROOT))] = expected
    inventory = load(DATA / "final-inventory.json")
    for name, expected in inventory["files"].items():
        assert digest(DATA / name) == expected, f"Closeout drift: {name}"
    old_receipt = load(
        ROOT / "artifacts/paper-draft-agsu/2026-10-24/v1/edits/comment1/verification.json"
    )
    for name, expected in old_receipt["after_sha256"].items():
        assert digest(ROOT / name) == expected, f"Historical paper drift: {name}"
        fingerprints[name] = expected
    summary = load(DATA / "analysis/summary.json")
    outcomes = load(DATA / "analysis/outcomes.json")
    latency = load(DATA / "analysis/latency.json")
    bootstrap = load(DATA / "analysis/aft-bootstrap.json")
    closeout = load(DATA / "final-validation.json")
    assert summary["inputs"] == 500 and summary["originals"] == 1500
    assert summary["raw_status"] == {"COMPLETED": 1359, "FAILED": 141}
    assert summary["strata"] == {
        "CLEAN": 300,
        "HIDDEN_COMMIT": 100,
        "PLAYOUT": 60,
        "OTHER_BOUNDARY": 40,
    }
    for arm in ("B3", "P1", "P2"):
        values = summary["values_by_arm"][arm]
        assert values["final_business_state_correct"] == {"TRUE": 455, "FALSE": 45}
        assert values["correction_success"] == {"TRUE": 155, "FALSE": 45, "NOT_APPLICABLE": 300}
        assert values["clean_task_success"] == {"TRUE": 300, "NOT_APPLICABLE": 200}
        assert values["correct_final_update"]["TRUE"] == 408
        assert values["corrective_delivery_after_challenge"] == {"TRUE": 33, "NOT_APPLICABLE": 467}
        expected = (
            {"TRUE": 33, "NOT_APPLICABLE": 467}
            if arm == "P2"
            else {"FALSE": 26, "UNKNOWN": 7, "NOT_APPLICABLE": 467}
        )
        assert values["complete_corrective_communication"] == expected
    primary = outcomes["primary_bounds"]
    assert primary["confirmatory_claim_permitted"] is False
    assert [round(100 * x, 2) for x in primary["correction"]["conservative_interval"]] == [
        -8.79,
        8.79,
    ]
    assert [round(100 * x, 2) for x in primary["hidden_exposure"]["conservative_interval"]] == [
        -4.95,
        4.95,
    ]
    assert round(100 * outcomes["clean_noninferiority"]["one_sided_95_lower_bound"], 2) == -1.22
    for row in outcomes["secondary_family"]["comparisons"]:
        if row["endpoint"] == "complete_corrective_communication" and row["comparison_arm"] == "P2":
            assert row["comparison_only"] == 26 and row["missing_pairs"] == 7
            assert f"{row['exact_mcnemar_p']:.4e}" == "2.9802e-08"
            assert f"{row['holm_diagnostic_p']:.4e}" == "2.9802e-07"
    assert [round(row["restricted_mean_difference_seconds"], 4) for row in latency] == [
        0.2593,
        0.2251,
        0.0342,
    ]
    assert bootstrap["completed_draws"] == 1000 and bootstrap["failed_draws"] == []
    assert bootstrap["claim_permitted"] is False
    assert closeout["exports_after_saved_deadlines"] == 1500
    assert closeout["verified_backup_transitions"] == 1500
    assert closeout["notice_chain_entries"] == 196037
    assert summary["historical_infrastructure_censor_sequences"] == [1, 2, 145, 616]
    paper = (HERE / "paper.md").read_text(encoding="utf-8")
    assert paper.isascii() and len(paper.split("<!-- PAGE_BREAK -->")) == 8
    references = re.findall(r"^\[(\d+)\] ", paper, re.MULTILINE)
    assert references == [str(x) for x in range(1, 13)]
    for required in (
        "exact-prefix",
        "revision-only claim-selection",
        "UNKNOWN",
        "does not independently prove unattended discovery",
        "claim guards as false",
        "SCRIPTED_TONE_SEMANTIC_PROXY",
        "No new sidecar",
    ):
        assert required in paper, f"Missing interpretation constraint: {required}"
    pdf = ROOT / "output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf"
    reader = PdfReader(pdf)
    assert len(reader.pages) == 8
    assert all(len(page.extract_text() or "") > 1500 for page in reader.pages)
    for path in (
        DATA / "final-validation.json",
        DATA / "examples/verification.json",
        DATA / "presentation/descriptive-facts.json",
        DATA / "final-inventory.json",
        ROOT / "artifacts/phase-8-continuation/classifier-145-v2/REPORT.md",
        Path("E:/p8v12/source/research/arms.py"),
        Path("E:/p8v12/source/research/oracle/readiness_v2.py"),
        HERE / "paper.md",
        HERE / "EVIDENCE_MAP.md",
        HERE / "REVIEW_READINESS.md",
        pdf,
    ):
        fingerprints[str(path)] = digest(path)
    result = {
        "status": "PASS_MANUSCRIPT_DATA_CHECKS_AUTHOR_REVIEW_REQUIRED",
        "pdf_pages": 8,
        "verified_references": 12,
        "original_analysis_hashes_unchanged": True,
        "closeout_inventory_files_verified": len(inventory["files"]),
        "historical_wip_unchanged": True,
        "data_assertions": "Counts, primary bounds, clean bound, secondary diagnostics and timing",
        "new_scenarios": 0,
        "regrading": False,
        "analysis_reruns": 0,
        "aws_calls": 0,
        "publication_or_author_approval_recorded": False,
        "fingerprints": fingerprints,
    }
    (HERE / "manuscript-verification.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "fingerprints"}))


if __name__ == "__main__":
    main()
