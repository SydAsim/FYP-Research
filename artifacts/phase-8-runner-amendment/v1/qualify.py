"""Four fixed serial, local PostgreSQL executions. No AWS or main capability."""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from controls import (
    Journal,
    Policy,
    canonical,
    hash_file,
    policy_commitment,
    read,
    utc,
    write_new,
)
from runner import HERE, REPO, authority_for, cloud_for, initialize, meter, run, verify_run

from research.execution_setup.core import Ledger
from research.study.models import StudyCase


def prepare(base: Path, ids: list[str]) -> Path:
    base.mkdir(parents=True)
    bank = read(HERE / "calibration-inputs.json")["calibration_inputs"]
    cases = {c["case_id"]: c for c in bank}
    sentinel = read(HERE / "calibration-inputs.json")["admission_sentinel"]
    cases[sentinel["case_id"]] = sentinel
    rows = [
        {
            "sequence": i + 1,
            "case_id": name,
            "arm": "B3",
            "fixture_hash": StudyCase.model_validate(cases[name]).fixture_hash,
        }
        for i, name in enumerate(ids)
    ]
    schedule = base / "schedule.json"
    write_new(schedule, {"scope": "CALIBRATION", "rows": rows})
    # Reuse the frozen executable source in the cached image plus the explicit overlay.
    files = dict(read(REPO / "artifacts/phase-8-review-freeze/v2/review-inventory.json")["files"])
    for path in list(HERE.glob("*.py")) + [
        HERE / "calibration-plan.json",
        HERE / "calibration-inputs.json",
    ]:
        files[path.relative_to(REPO).as_posix()] = hash_file(path)
    package_hash = hashlib.sha256(canonical(files)).hexdigest()
    manifest = base / "calibration-inventory.json"
    write_new(
        manifest,
        {
            "kind": "REVIEW_INVENTORY",
            "scope": "CALIBRATION",
            "files": files,
            "package_hash": package_hash,
            "closed_source_roots": [
                "apps",
                "packages",
                "research",
                "tests",
                "database",
                "contracts",
                "docs",
            ],
        },
    )
    # Synthetic scoped test tokens, never an actual acceptance/freeze/launch.
    key = base / "synthetic-test-key"
    key.write_bytes(b"CALIBRATION_ONLY_NOT_HUMAN_ACCEPTANCE" * 2)
    policy = Policy(scope="CALIBRATION", run_id="cal-p85a-" + base.name, host_started_at=utc())
    capabilities = base / "synthetic-calibration-capabilities"
    prior = None
    for kind in ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH"):
        body: dict[str, Any] = {
            "kind": kind,
            "scope": "CALIBRATION",
            "package_hash": package_hash,
            "policy_hash": policy_commitment(policy, kind),
            "schedule_hash": hash_file(schedule),
            "predecessor_hash": prior,
            "expires_at": policy.stop_at.isoformat(),
            "signer": "SYNTHETIC_LOCAL_TEST_NOT_USER_ACCEPTANCE",
        }
        body["signature"] = hmac.new(key.read_bytes(), canonical(body), "sha256").hexdigest()
        write_new(capabilities / f"{kind}.json", body)
        prior = hashlib.sha256(canonical(body)).hexdigest()
    root = base / "execution"
    initialize(root, REPO, manifest, policy, capabilities, key, schedule, base / "backup")
    write_new(root / "cloud.json", {"offline_root": str(base / "offline-backup")})
    return root


def notices(root: Path) -> list[dict[str, Any]]:
    with Journal(root).connect() as db:
        return [json.loads(r[0]) for r in db.execute("SELECT body FROM notices ORDER BY n")]


def result(root: Path, expected: str) -> list[dict[str, Any]]:
    verify_run(root)
    rows = Journal(root).rows()
    reports = []
    for slot in rows:
        if slot["case_id"] == "cal-v4-p85a-never-admit-05":
            assert slot["state"] == "PLANNED"
            assert not (root / "slots" / f"{slot['sequence']:04d}").exists()
            continue
        assert slot["state"] == "BACKED_UP", slot
        folder = root / "slots" / f"{slot['sequence']:04d}"
        trace_path = folder / "executions" / slot["execution_id"] / "export.json"
        trace = read(trace_path)
        assert "oracle_failure" not in trace and not trace.get("collection_errors"), trace_path
        assert trace["missing_final_anchor"] is False
        from datetime import datetime

        cutoff = datetime.fromisoformat(trace["original_deadline"])
        assert (
            cutoff - datetime.fromisoformat(trace["external_requests"][-1]["issued_at"])
        ).total_seconds() == 600
        assert datetime.fromisoformat(trace["polls"][-1]["at"]) >= cutoff
        assert (
            trace["analysis_row"]["values"] == trace["original_instrument_analysis_row"]["values"]
        )
        proof = read(root / "backups" / f"{slot['execution_id']}.json")
        from storage import ObjectProof, verify_local

        verify_local(Path(proof["local"]), proof["sha256"])
        cloud_for(root).verify(ObjectProof.model_validate(proof["cloud"]))
        assert read(folder / "retired.json")["raw_evidence_local_and_cloud_retained"]
        Ledger(folder).verify()
        if "refusal" in slot["case_id"] or "recovery" in slot["case_id"]:
            assert trace["status"] == "FAILED"
            assert trace["driver_classification"]["classification"] == "EXPECTED_EVIDENCE_REFUSAL"
            assert trace["analysis_row"]["censor_reason"] == "NO_SUPPORTED_COMPLETION"
            assert trace["analysis_row"]["values"]["correction_success"] == "TRUE"
            assert trace["analysis_row"]["values"]["correct_final_update"] == "FALSE"
            assert (
                len(
                    [
                        c
                        for c in trace["http"]
                        if c["method"] == "POST" and c["path"] == "/internal/phase6/b3/schedule"
                    ]
                )
                == 1
            )
        reports.append(
            {
                "case_id": slot["case_id"],
                "execution_id": slot["execution_id"],
                "state": slot["state"],
                "raw_status": trace["status"],
                "outcome_values": trace["analysis_row"]["values"],
                "censor_reason": trace["analysis_row"]["censor_reason"],
                "deadline": trace["original_deadline"],
                "polls": len(trace["polls"]),
                "trace": str(trace_path),
                "export_sha256": hash_file(trace_path),
                "backup": proof,
                "expected": expected,
            }
        )
    return reports


def qualify(output: Path) -> None:
    start = time.monotonic()
    output.mkdir(parents=True)  # fresh attempt only; unsuccessful outputs never overwritten
    write_new(
        output / "started.json",
        {
            "scope": "LOCAL_CALIBRATION_ONLY",
            "at": utc(),
            "plan_sha256": hash_file(HERE / "calibration-plan.json"),
            "main_executions": 0,
            "cloud_operations": 0,
            "wall_budget_seconds": 3000,
        },
    )
    reports = []
    for group, ids in [
        ("continuation", ["cal-v4-p85a-refusal-01", "cal-v4-p85a-next-02"]),
        ("defect", ["cal-v4-p85a-defect-03", "cal-v4-p85a-never-admit-05"]),
        ("recovery", ["cal-v4-p85a-recovery-04"]),
    ]:
        if time.monotonic() - start + 650 * len(ids) > 3000:
            raise TimeoutError("FIXED_CALIBRATION_BUDGET_NO_MORE_ADMISSIONS")
        root = prepare(output / group, ids)
        print(f"START {group}: {len(ids)} original local calibration slots", flush=True)
        if group == "recovery":
            run(root, checkpoint_once=True)
            slot = Journal(root).rows()[0]
            folder = root / "slots/0001"
            checkpoint = Ledger(folder).recover_checkpoint(slot["execution_id"])
            post_count = len([c for c in checkpoint["http"] if c["method"] == "POST"])
            assert slot["state"] == "RUNNING" and checkpoint["qualification_checkpoint_done"]
            write_new(
                output / "recovery-before.json",
                {
                    "execution_id": slot["execution_id"],
                    "deadline": slot["deadline"],
                    "post_count": post_count,
                    "checkpoint_hash": hash_file(
                        folder / "executions" / slot["execution_id"] / "checkpoint.json"
                    ),
                },
            )
            run(root)
            after = read(folder / "executions" / slot["execution_id"] / "export.json")
            assert after["execution_id"] == slot["execution_id"]
            assert after["original_deadline"] == slot["deadline"]
            assert len([c for c in after["http"] if c["method"] == "POST"]) == post_count
            assert len(after["collector_resumes"]) == 1
        elif group == "defect":
            try:
                run(root)
            except ValueError as error:
                assert str(error) == "PAUSED_ADMISSIONS", str(error)
            else:
                raise AssertionError("TECHNICAL_DEFECT_DID_NOT_PAUSE")
            assert read(root / "pause.json")["reason"] == "DRIVER_FAILURE"
            journal = Journal(root)
            try:
                journal.admit(authority_for(root), meter(root), utc(), cloud_for(root).inventory())
            except ValueError as error:
                assert str(error) == "PAUSED_ADMISSIONS"
            else:
                raise AssertionError("DEFECT_NEXT_ADMISSION_ALLOWED")
            try:
                journal.resume()
            except ValueError as error:
                assert "NO_AUTO_UNPAUSE" in str(error)
            else:
                raise AssertionError("DEFECT_AUTO_RESUME_ALLOWED")
            write_new(
                output / "defect-pause-proof.json",
                {
                    "reason": read(root / "pause.json"),
                    "next_admission": "REJECTED",
                    "resume": "REJECTED",
                    "notices": notices(root),
                },
            )
        else:
            run(root)
            events = notices(root)
            admissions = [e for e in events if e["kind"] == "ADMITTED"]
            backups = [e for e in events if e["kind"] == "TRANSITION" and e["state"] == "BACKED_UP"]
            assert len(admissions) == len(backups) == 2
            assert backups[0]["at"] < admissions[1]["at"]
            assert not (root / "pause.json").exists()
            write_new(
                output / "next-admission-proof.json",
                {"events": events, "verified_backup_precedes_next_admission": True},
            )
        group_reports = result(root, group)
        reports.extend(group_reports)
        write_new(output / f"{group}-PASS.json", {"status": "PASS", "results": group_reports})
    write_new(
        output / "result.json",
        {
            "status": "PASS",
            "executions": reports,
            "planned": 4,
            "elapsed_seconds": time.monotonic() - start,
            "main_executions": 0,
            "new_cloud_spending": 0,
            "window_seconds": 600,
            "synthetic_tone_only": True,
        },
    )


if __name__ == "__main__":
    target = Path(sys.argv[1])
    try:
        qualify(target)
    except Exception as error:
        write_new(
            target / f"failure-{time.time_ns()}.json",
            {
                "status": "FAIL",
                "type": type(error).__name__,
                "detail": str(error),
                "traceback": traceback.format_exc(),
                "retain_every_attempt": True,
            },
        )
        raise
