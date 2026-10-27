"""Concrete operational review proposal; never authorizes AWS writes or launch."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "recovery"


def main() -> None:
    retained = json.loads((EVIDENCE / "verified-preservation-summary.json").read_bytes())
    stopped = json.loads((EVIDENCE / "stopped-read1-result.json").read_bytes())
    assert retained["counts"] == {"BACKED_UP": 1297, "PLANNED": 203}
    assert stopped["result"]["State"]["Name"] == "stopped"
    now = datetime.now(UTC)
    original_anchor = datetime.fromisoformat("2026-10-07T15:24:23.810674+00:00")
    old_stop = datetime(2026, 10, 26, tzinfo=UTC)
    proposed_stop = datetime(2026, 10, 26, 12, tzinfo=UTC)
    extra_root = 0.629884584534137
    added_retention = 16 * 0.096 / 730 * (proposed_stop-old_stop).total_seconds()/3600
    rate = 0.1197 + 0.005 + 160*0.096/730
    reserves = 48*160*0.096/730 + 80*0.025 + 5 + 1.25

    def forecast(at: datetime) -> float:
        return (at-original_anchor).total_seconds()/3600*rate+reserves+extra_root+added_retention

    completion = now + timedelta(hours=203*262.31642189586114/1355+2.5)
    uncertainty = completion+timedelta(hours=24)
    lookahead = uncertainty+timedelta(minutes=30)
    proposal = {
        "kind": "PROPOSED_OPERATIONAL_AMENDMENT_REQUIRES_EXPLICIT_ACCEPTANCE",
        "prepared_at": now.isoformat(),
        "parent_frozen_package": "e89ca0fbb9c9e7333a18af23014d0d00d4ffbc6dbe1298f0546620523626e348",
        "parent_archive_sha256": "3dc00ac7b60018c7fa0357d54d5fac96f22c6e84deba39e9037575b8a93b0579",
        "instance_id": "i-057344e5372faf62f",
        "old": {"stop": old_stop.isoformat(), "admission_usd": 74, "total_ceiling_usd": 75},
        "proposed": {
            "stop": proposed_stop.isoformat(), "admission_usd": 76, "total_ceiling_usd": 77,
            "elapsed_host_hours": (proposed_stop-original_anchor).total_seconds()/3600,
            "original_anchor": original_anchor.isoformat(),
            "cloud_and_local_backup_cap_bytes": 80*1024**3,
            "owned_root_retention_hours_after_actual_shutdown": 48,
            "retention_decision_absolute_outer_bound": (proposed_stop+timedelta(hours=48)).isoformat(),
            "root_or_evidence_deletion_authorized": False,
        },
        "planning": {
            "remaining_original_executions": 203, "hours_per_execution": 262.31642189586114/1355,
            "preparation_shutdown_hours": 2.5, "uncertainty_hours": 24, "margin_hours": 0.5,
            "completion": completion.isoformat(), "uncertainty_completion": uncertainty.isoformat(),
            "admission_projection_time": lookahead.isoformat(),
            "admission_projection_usd": forecast(lookahead), "full_deadline_forecast_usd": forecast(proposed_stop),
            "extended_extra_root_retention_reserve_usd": added_retention,
            "time_headroom_hours": (proposed_stop-lookahead).total_seconds()/3600,
            "time_gate": lookahead<proposed_stop, "admission_gate": forecast(lookahead)<76,
            "ceiling_gate": forecast(proposed_stop)<77,
            "accounting": "Unchanged accepted original elapsed-clock forecast, including prior stopped time, all original reservations and extra-root reserve; not actual billed spending",
        },
        "retained_boundary": {"BACKED_UP": 1297, "PLANNED": 203, "active": 0, "next": retained["next"]},
        "verified_backups": {"master": retained["master_backup"], "diagnostic": retained["diagnostic_backup"],
                             "master_readback_sha256": retained["master_readback_sha256"],
                             "diagnostic_readback_sha256": retained["diagnostic_readback_sha256"]},
        "installed_os_correction_sha256": retained["correction"]["sha256"],
        "safeguards": [
            "Preserve all originals, raw failures, grades, archives, pinned versions, notices, saved identities/order and observation deadlines",
            "No application, arm, claim selection, fixture, oracle, analysis or 600-second-window change",
            "Prepare a separately inventoried operational overlay only after explicit acceptance of the new limits; preserve frozen v11",
            "Verify final source/archive/authority bindings and focused policy/timer controls before conditional freeze",
            "Verify fresh feasibility and independent preparation stop before boot, then owned-unit quiescence, fresh paired boot anchor preserving original elapsed history",
            "Reuse successful backups without repeating their original transfers; verify current closed boundary, capacity, timers, readiness and authorized pause-release bindings",
            "Fresh required prelaunch/complete evidence must be genuine; do not fabricate readiness or bypass ordering",
            "Resume only sequence1298/B3/attempt1; no replay, regrading, deletion or automatic limit increases",
            "Fail closed and preserve evidence on any failed gate; bounded safe shutdown",
        ],
        "authorization": "NOT_ACCEPTED_NOT_FROZEN_NOT_DEPLOYED; generic continuation request not recorded as numeric-policy acceptance",
    }
    assert all(proposal["planning"][k] for k in ("time_gate", "admission_gate", "ceiling_gate"))
    payload = json.dumps(proposal, indent=2).encode()+b"\n"
    with (HERE/"operational-proposal.json").open("xb") as f:
        f.write(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with (HERE/"proposal-sha256.txt").open("x") as f:
        f.write(digest+"\n")
    print(json.dumps({"proposal_sha256": digest, "planning": proposal["planning"], "changes": proposal["proposed"]}, indent=2))


if __name__ == "__main__":
    main()
