"""12 focused offline checks for approved policy/clock/timer/boundary integration."""

import copy, hashlib, json, sys
from pathlib import Path
from datetime import timedelta, datetime, UTC

source = Path(sys.argv[1])
sys.path.insert(0, str(source))
runtime = source / "artifacts/phase-8-runner-amendment/v4-complete"
sys.path.insert(0, str(runtime))
from controls import Policy, canonical, guard, clock_check
from operational_limits import effective_policy, verified_limits
from closed616 import check_rows
from pydantic import ValidationError

raw = json.loads((runtime / "original-launch-policy.json").read_text())
policy = effective_policy(raw)
tests = []


def check(name, value):
    assert value, name
    tests.append(name)
    print("PASS " + name, flush=True)


def rejected(name, fn):
    try:
        fn()
    except (ValueError, ValidationError):
        check(name, True)
    else:
        raise AssertionError(name)


check(
    "exact-approved-deadline-and-guard",
    policy.stop_at == datetime(2026, 10, 26, tzinfo=UTC)
    and policy.admission_committed_usd == 74
    and policy.budget_usd == 75,
)
check(
    "original-policy-serialization-preserved",
    canonical(Policy.model_validate(raw).model_dump(mode="json")) == canonical(raw),
)
check(
    "exact-original-elapsed-history",
    policy.host_started_at == datetime.fromisoformat("2026-10-07T15:24:23.810674+00:00")
    and policy.host_hours * 3600 == (policy.stop_at - policy.host_started_at).total_seconds(),
)
rejected(
    "unapproved-elapsed-limit-rejected", lambda: Policy.model_validate({**raw, "host_hours": 433.5})
)
clock_at = datetime(2026, 10, 17, tzinfo=UTC)
rejected(
    "five-second-clock-rollback-preserved",
    lambda: clock_check(
        policy,
        {"boot_id": "cal-boot", "wall": clock_at.isoformat(), "monotonic": 100},
        clock_at + timedelta(seconds=10),
        116,
        "cal-boot",
    ),
)
from runner import unit_text

service, timer = unit_text(Path("/var/lib/cal-only"), policy)
check(
    "exact-absolute-timer-binding",
    "OnCalendar=2026-10-26 00:00:00 UTC" in timer
    and "432h" not in timer
    and policy.cloud_limit_bytes == 80 * 1024**3
    and policy.backup_archive_limit_bytes == 80 * 1024**3,
)

rows = []
for i in range(1500):
    rows.append(
        {
            "sequence": i + 1,
            "case_id": "cal-offline-" + str(i),
            "arm": ("B3", "P1", "P2")[i % 3],
            "attempt": 1,
            "execution_id": "cal-" + str(i),
            "fixture_hash": "a" * 64,
            "state": "BACKED_UP" if i < 616 else "PLANNED",
            "deadline": clock_at.isoformat() if i < 616 else None,
            "backup_hash": "b" * 64 if i < 616 else None,
            "error": None,
        }
    )
rows[616]["execution_id"] = "01a11705-11f2-7276-8d5f-0277ced1a5f5"
rows[616]["arm"] = "P2"
check_rows(rows, rows)
check("closed616-normal-boundary", True)
for change in ["backup", "identity", "active", "attempt", "incomplete"]:
    changed = copy.deepcopy(rows)
    if change == "backup":
        changed[615]["backup_hash"] = "0" * 64
    elif change == "identity":
        changed[616]["execution_id"] = "replacement"
    elif change == "active":
        changed[616]["state"] = "RUNNING"
    elif change == "attempt":
        changed[616]["attempt"] = 2
    else:
        changed.pop()
    rejected("closed616-reject-" + change, lambda: check_rows(changed, rows))
assert len(tests) == 12
print(
    json.dumps(
        {
            "status": "PASS",
            "checks": 12,
            "research_executions": 0,
            "python": sys.version,
            "policy_sha256": hashlib.sha256(canonical(policy.model_dump(mode="json"))).hexdigest(),
            "limits": verified_limits().model_dump(mode="json"),
        }
    )
)
