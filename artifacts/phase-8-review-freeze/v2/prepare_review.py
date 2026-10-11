"""Write finite review metadata only; no receipt signing or study admission."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime

from controls import Policy, read, write_new
from runner import HERE, REPO


def prepare() -> None:
    previous = REPO / "artifacts/phase-8-review-freeze/v1"
    for name in ("schedule.json", "schedule.csv", "measurements.json", "budget.json"):
        with (previous / name).open("rb") as source, (HERE / name).open("xb") as target:
            shutil.copyfileobj(source, target)
    policy = Policy(
        scope="CAMPAIGN",
        run_id="proposal-not-a-launch",
        host_started_at=datetime(2026, 10, 7, tzinfo=UTC),
    )
    write_new(
        HERE / "policy-proposal.json",
        {
            "status": "PROPOSED_NOT_ACCEPTED_NOT_FROZEN_NOT_AUTHORIZED",
            "static_policy": policy.model_dump(mode="json", exclude={"host_started_at", "run_id"}),
            "launch_fields_unset": ["host_started_at", "run_id"],
            "attempts": 8,
            "drain_passes": 30,
            "independent_inputs": 500,
            "original_slots": 1500,
            "parallel_main_slots": 0,
        },
    )
    checks = [
        {
            "check": "authorization and fixed original identity/source closure",
            "status": "PASS",
            "evidence": "linux-final.txt",
        },
        {
            "check": "resource, cost, cloud reservation, clock and cutoff guards",
            "status": "PASS",
            "evidence": "linux-final.txt",
        },
        {
            "check": "backup, pause, same-execution recovery and no driver replay",
            "status": "PASS",
            "evidence": "linux-final.txt",
        },
        {
            "check": "bounded pinned downloads/short extraction and owned retirement",
            "status": "PASS",
            "evidence": "linux-final.txt",
        },
        {
            "check": "real existing isolated PostgreSQL dumps",
            "status": "PASS",
            "evidence": "local-postgres-qualification/result.json",
        },
        {
            "check": "24 saved pilot oracle and analysis-row parity",
            "status": "PASS",
            "evidence": "retained-pilot-replay-final/replay.json",
        },
        {
            "check": "matching active systemd host controls, actual role/bucket rights/headroom",
            "status": "UNRESOLVED_UNTIL_AUTHORIZED_DEPLOYMENT",
            "action": "verify before first admission; runner fails closed",
        },
        {
            "check": "360h endurance/full-host restore/actual human speech",
            "status": "NOT_CLAIMED",
            "action": "retain documented limitations; no optional extension",
        },
        {
            "check": "actual billing hard cap and indefinite evidence retention",
            "status": "UNRESOLVED_LIMITATION",
            "action": "accept delayed billing and storage escalation limits",
        },
    ]
    write_new(
        HERE / "checklist.json",
        {
            "implementation_checks": checks,
            "decisions": [
                {"decision": value, "status": "PENDING_USER_ACCEPTANCE"}
                for value in (
                    "exact v2 inventory and unchanged saved serial schedule",
                    "USD65 proposal/USD55 guard/360h/30min/160GiB/1GiB slot reserve",
                    "48h stopped disk and first-month S3 retention/escalation",
                    "UNKNOWN/recovery limits/clustered timing/synthetic evidence",
                )
            ],
            "accepted": False,
            "frozen": False,
            "launch_authorized": False,
            "main_started": False,
        },
    )
    linux = (HERE / "linux-final.txt").read_text()
    windows = (HERE / "windows-final.txt").read_text()
    replay = read(HERE / "retained-pilot-replay-final/replay.json")
    sdk = read(HERE / "sdk-qualification-attempt1/result.json")
    if (
        "failed" in linux.lower()
        or "passed" not in linux
        or "failed" in windows.lower()
        or replay["count"] != 24
        or sdk["status"] != "PASS"
    ):
        raise ValueError("REQUIRED_VERIFICATION_NOT_PASSED")
    write_new(
        HERE / "validation.json",
        {
            "status": "PASS_LOCAL_INTEGRATION_REUSED_LIVE_EVIDENCE",
            "windows_summary": windows.strip().splitlines()[-1],
            "linux_summary": linux.strip().splitlines()[-1],
            "oracle_parity": 24,
            "sdk_model_stub": sdk,
            "original_outcomes_replaced": 0,
            "new_scientific_executions": 0,
            "cloud_calls": 0,
            "cloud_spending_usd": 0,
            "main_executions": 0,
            "scope": "SEPARATE_LOCAL_CONTROLS_AND_READ_ONLY_REPLAYS",
            "failed_attempts_retained": True,
            "checks": checks,
            "measurement_basis": (
                "unchanged completed 8.2/8.3; new backup overhead is not "
                "a whole-bank runtime measurement"
            ),
        },
    )


if __name__ == "__main__":
    prepare()
