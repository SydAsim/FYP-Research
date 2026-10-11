"""Verify historical bytes, stage metadata and assemble an unaccepted package."""

from __future__ import annotations

import ast
import hashlib
import json
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from controls import canonical, hash_file, read
from handover import ContinuationPolicy, stage, verify_imported_first

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def write(name: str, value: Any) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def analysis_source() -> None:
    text = (REPO / "artifacts/phase-8-continuation/v1/analyze.py").read_text()
    start = text.index("def imported_first_row(")
    end = text.index("\n\ndef analyze(", start)
    wrapper = """def imported_first_row(root: Path) -> tuple[AnalysisRow, dict[str, Any]]:
    from imported_analysis import imported_row
    return imported_row(root, FIRST)
"""
    text = text[:start] + wrapper + text[end:]
    text = text.replace(
        'slot["execution_id"] == FIRST',
        'slot["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")',
    )
    text = text.replace(
        "row, provenance = imported_first_row(root)",
        "from imported_analysis import imported_row\n"
        '            row, provenance = imported_row(root, slot["execution_id"])',
    )
    (HERE / "analyze.py").write_text(text, encoding="utf-8")


def pre_review() -> None:
    sites = []
    for name in ("research/study_v4/calibration.py", "research/remedies/runner.py"):
        path = REPO / name
        source = path.read_text()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call) and any(
                k.arg == "allow_failure"
                and isinstance(k.value, ast.Constant)
                and k.value.value is True
                for k in node.keywords
            ):
                sites.append(
                    {
                        "source": name,
                        "line": node.lineno,
                        "source_sha256": hash_file(path),
                        "call": ast.get_source_segment(source, node),
                    }
                )
    if len(sites) != 8:
        raise ValueError("PERMISSIVE_CALL_SITE_CLOSURE_DRIFT")
    write(
        "permissive-call-sites.json",
        {
            "sites": sites,
            "ack_forwarding_line": 294,
            "legacy_E2": "Not reachable from v4 dispatch; no generic E2 exemption added",
            "guard": "collector.Trial.request -> response_guard.evaluate/retain",
        },
    )
    root = Path("C:/p8v3/import-packed-final")
    root.parent.mkdir(exist_ok=True)
    result = stage(
        Path("C:/p8c1/m/x/slot"),
        Path("C:/fyp-p85/stopped-attempt1/slot1/x/slot"),
        root,
        second=Path("C:/p8c1/s/x/slot"),
        first_archive=Path("C:/fyp-p85/stopped-attempt1/slot1/t/e.tar.gz"),
        second_archive=Path("C:/p8c1/s/t/e.tar.gz"),
    )
    verify_imported_first(root)
    write(
        "handover-qualification.json",
        {"status": "PASS", "root": str(root), "proof": result, "pause": read(root / "pause.json")},
    )
    from imported_analysis import imported_row

    write(
        "original-analysis-verification.json",
        {
            "rows": [
                imported_row(root, p["execution_id"])[0].model_dump(mode="json")
                for p in result["originals"]
            ],
            "raw_exports_unchanged": True,
        },
    )
    protected = read(HERE / "preservation-before.json")
    after = {name: hash_file(Path(name)) for name in protected}
    if protected != after:
        raise ValueError("HISTORICAL_HASH_DRIFT")
    write("preservation-after.json", {"status": "PASS", "count": len(after), "hashes": after})
    baseline = read(REPO / "artifacts/phase-8-review-freeze/v2/review-inventory.json")["files"]
    if any(hash_file(REPO / name) != value for name, value in baseline.items()):
        raise ValueError("BASELINE_DRIFT")
    write("baseline-source-verification.json", {"status": "PASS", "count": len(baseline)})
    old = HERE.parent / "v2/qualification-summary.json"
    qualification = read(old)
    if qualification["status"] != "PASS_FIXED_NINE" or len(qualification["executions"]) != 9:
        raise ValueError("PG_QUALIFICATION_DRIFT")
    write(
        "reused-qualification.json",
        {
            "status": "PASS_REUSED_NOT_RERUN",
            "source_sha256": hash_file(old),
            "executions": qualification["executions"],
        },
    )


def feasibility() -> None:
    policy = ContinuationPolicy.model_validate(
        read(REPO / "artifacts/phase-8-launch/v1/launch-policy.json")
    )
    at = datetime.now(UTC)
    rate = (
        policy.compute_usd_hour
        + policy.ipv4_usd_hour
        + policy.volume_gib * policy.disk_usd_gib_month / 730
    )
    cutoff = policy.host_started_at + timedelta(
        hours=(55 - policy.committed_cost(policy.host_started_at)) / rate
    )
    estimates = {}
    for name, hours in (
        ("full_window_lower_bound", 1498 * 600 / 3600),
        ("measured_median_reference", 1498 * 613.3855985 / 3600),
        ("planning_12_days", 288),
        ("planning_13_days", 312),
    ):
        finish = at + timedelta(hours=hours + 2)
        cost = policy.committed_cost(finish + timedelta(minutes=30))
        estimates[name] = {
            "execution_hours": hours,
            "setup_hours": 2,
            "finish_utc": finish,
            "committed_usd": cost,
            "fits_55": cost < 55,
            "fits_65": cost <= 65,
            "fits_deadline": finish <= policy.stop_at,
            "latest_setup_begin_utc": cutoff - timedelta(hours=hours + 2, minutes=30),
        }
    host = read(HERE / "aws-stopped-host.json")["Reservations"][0]["Instances"][0]
    if host["State"]["Name"] != "stopped":
        raise ValueError("AWS_NOT_STOPPED")
    write(
        "feasibility.json",
        {
            "as_of_utc": at,
            "original_deadline": policy.stop_at,
            "cost_guard_cutoff": cutoff,
            "estimates": estimates,
            "limits_unchanged": True,
            "clock_reset": False,
            "policy_usd": 65,
            "admission_guard_usd": 55,
            "reserve_included_usd": 1.25,
            "host": host["InstanceId"],
            "host_state": "stopped",
            "credits": read(HERE / "aws-plan-read.json"),
            "price_basis": "Accepted Sydney rates and retained v2 Price List evidence",
            "retention_decision_due": "2026-10-09T21:05:37.547530Z",
            "limitations": "12-day fit conditional; 13-day allowance fails $55. Median excludes "
            "main prep/backup variation. Billing delayed; retained disk/S3 charges continue.",
        },
    )


def package() -> None:
    protected = read(HERE / "preservation-before.json")
    if any(hash_file(Path(n)) != v for n, v in protected.items()):
        raise ValueError("FINAL_HISTORICAL_DRIFT")
    files = dict(read(REPO / "artifacts/phase-8-review-freeze/v2/review-inventory.json")["files"])
    # The original inventory cannot hash itself, but the continuation needs it
    # to verify the original source authority on a fresh host.
    authority_inventory = "artifacts/phase-8-review-freeze/v2/review-inventory.json"
    files[authority_inventory] = hash_file(REPO / authority_inventory)
    for p in HERE.rglob("*"):
        if (
            p.is_file()
            and "__pycache__" not in p.parts
            and p.name not in {"candidate-inventory.json", "candidate-package.json"}
        ):
            files[p.relative_to(REPO).as_posix()] = hash_file(p)
    inventory = {
        "kind": "CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE",
        "version": "phase85-combined-amendment-v3",
        "files": files,
        "package_hash": hashlib.sha256(canonical(files)).hexdigest(),
        "accepted": False,
        "frozen": False,
        "launch_authorized": False,
    }
    write("candidate-inventory.json", inventory)
    archive = HERE.parent / "v3-combined-review-candidate.tar.gz"
    with tarfile.open(archive, "x:gz") as output:
        for name in sorted(files):
            output.add(REPO / name, arcname=name, recursive=False)
        output.add(
            HERE / "candidate-inventory.json",
            arcname="artifacts/phase-8-runner-amendment/v3/candidate-inventory.json",
        )
    with tarfile.open(archive, "r:gz") as source:
        names = source.getnames()
        if len(names) != len(set(names)) or set(names) != set(files) | {
            "artifacts/phase-8-runner-amendment/v3/candidate-inventory.json"
        }:
            raise ValueError("ARCHIVE_MEMBER_CLOSURE_DRIFT")
        for name, expected in files.items():
            stream = source.extractfile(name)
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != expected:
                raise ValueError("ARCHIVE_HASH_DRIFT")
    write(
        "candidate-package.json",
        {
            "status": "VERIFIED_REVIEW_CANDIDATE_NOT_FREEZE",
            "archive": str(archive),
            "archive_sha256": hash_file(archive),
            "archive_bytes": archive.stat().st_size,
            "package_hash": inventory["package_hash"],
            "inventory_sha256": hash_file(HERE / "candidate-inventory.json"),
            "members_verified": len(files),
        },
    )


if __name__ == "__main__":
    import sys

    {
        "analysis": analysis_source,
        "pre-review": pre_review,
        "feasibility": feasibility,
        "package": package,
    }[sys.argv[1]]()
