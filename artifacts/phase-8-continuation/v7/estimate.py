"""One finite retained-evidence estimate; no experiments, AWS writes, or authorization."""
from __future__ import annotations

import json
import sqlite3
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = Path('E:/p8v6/source/artifacts/phase-8-runner-amendment/v4-complete')


def ledger(path: Path) -> dict[str, int]:
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.execute('BEGIN')
        n, body_bytes = db.execute('SELECT count(*), sum(length(CAST(body AS BLOB))) FROM notices').fetchone()
    return {'sqlite_bytes': path.stat().st_size, 'zlib9_bytes': len(zlib.compress(path.read_bytes(), 9)), 'notice_count': n, 'notice_body_bytes': body_bytes}


def main() -> None:
    original = json.loads((HERE.parent / 'v6/feasibility-final.json').read_text())
    recent = ledger(RUNTIME / 'closed-82/campaign.sqlite3')
    earlier = ledger(RUNTIME / 'boundary/campaign.sqlite3')
    growth = (recent['zlib9_bytes'] - earlier['zlib9_bytes']) / (82 - 38)
    # No claim that a linear projection bounds every unstarted recipe. Double the
    # observed compressed-ledger growth, plus every old archive's full maximum
    # above the new base metadata, then add explicit operational contingency.
    largest_archive = original['observed_backup_max_bytes']
    base = json.loads((HERE.parent / 'v6/storage-projection.json').read_text())['measured_metadata_archive_bytes']
    count = 1418
    raw = original['all_version_evidence_bytes'] + (count + 2) * base + count * largest_archive + 2 * growth * (count * (count + 1) / 2)
    backup_index_allowance = count * 256 * 1024  # compressed index/proof growth, conservatively charged every slot
    planned = raw + backup_index_allowance
    cap = 60 * 1024**3
    now = datetime.now(UTC)
    rate = .1197 + .005 + 160 * .096/730
    delta = (now - datetime.fromisoformat(original['at_utc'])).total_seconds()/3600
    cost = original['conservative_original_elapsed_clock_cost_usd'] + delta * rate + (60 - 30) * .025
    explicit = original['explicit_resources_cost_usd'] + delta * 160 * .096/730 + (60 - 30) * .025
    finish = now + timedelta(hours=original['reviewed_allowance_remaining_hours'] + 2)
    deadline = datetime.fromisoformat(original['original_deadline'])
    # Signed operational policy keeps original elapsed clock and existing reserves.
    start = datetime(2026,10,7,15,24,23,810674,tzinfo=UTC)
    fixed_reserves = 48*160*.096/730 + 60*.025 + 5 + 1.25
    guard_time = start + timedelta(hours=(60-fixed_reserves)/rate)
    latest_start = min(guard_time, deadline) - timedelta(hours=original['reviewed_allowance_remaining_hours'] + 2 + .5)
    result = {
        'status': 'PROPOSED_FITS' if cost < 60 and explicit < 60 and finish + timedelta(minutes=30) < deadline and planned + 1024**3 < cap else 'DO_NOT_PROPOSE_DEPLOYMENT',
        'at_utc': now.isoformat(), 'evidence_reused': 'v6 qualification + retained 38/82 metadata; no completed tests repeated',
        'remaining': count, 'original_deadline': deadline.isoformat(), 'reviewed_remaining_hours': original['reviewed_allowance_remaining_hours'], 'preparation_hours':2, 'shutdown_hours':.5,
        'projected_finish_utc':finish.isoformat(), 'projected_shutdown_utc':(finish+timedelta(minutes=30)).isoformat(), 'latest_preparation_start_utc':latest_start.isoformat(),
        'admission_guard_usd':60, 'total_campaign_ceiling_usd':65, 'unadmitted_ceiling_margin_usd':5,
        'projected_conservative_usd':cost, 'projected_explicit_resources_usd':explicit, 'cost_at_original_absolute_deadline_usd':360*rate+fixed_reserves,
        'cloud_limit_gib':60, 'cloud_limit_bytes':cap, 'capacity_planning_bytes':planned, 'capacity_planning_gib':planned/1024**3, 'remaining_headroom_bytes':cap-planned, 'remaining_headroom_gib':(cap-planned)/1024**3,
        'existing_cloud_all_versions_bytes': original['all_version_evidence_bytes'], 'new_metadata_base_bytes':base, 'old_full_archive_max_bytes':largest_archive,
        '38_slot_ledger':earlier, '82_slot_ledger':recent, 'measured_compressed_growth_bytes_per_slot':growth, 'projected_extra_ledger_bytes_with_2x_growth':2*growth*(count*(count+1)/2), 'backup_index_allowance_bytes':backup_index_allowance,
        'full_month_s3_reserve_usd':60*.025, 'increase_over_30gib_full_month_reserve_usd':30*.025, 'prior_spending_and_root_retention_included':True,
        'limits': ['Largest observed archive is not a maximum guaranteed for all recipes', '2x observed ledger slope and 256KiB/slot index allowance are planning assumptions, not qualified bounds', 'All versions and reserved uploads count; inventory failure or cap exhaustion still pauses', 'No limit automatically grows', 'Billing lag and retention beyond reserved duration require escalation within $65', '160GiB root and 50GiB working guard remain; local archive cap becomes 60GiB with verified redundant future staging removal', 'Fresh live prices/credits/storage/gates required after acceptance; latest cached prices measured 2026-10-09T12:35Z'],
        'authorization':False, 'freeze':False, 'AWS_start':False,
    }
    (HERE/'estimates.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__=='__main__':
    main()
