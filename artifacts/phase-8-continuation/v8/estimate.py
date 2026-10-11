"""Unchanged planning allowance and limits, refreshed retained evidence only."""
from __future__ import annotations
import json
import sqlite3
import tarfile
import zlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from prepare import HERE, PREFIX, SOURCE, write

def ledger(path: Path) -> dict[str,int]:
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.execute('BEGIN');n=db.execute('SELECT count(*) FROM notices').fetchone()[0]
    return {'sqlite_bytes':path.stat().st_size,'zlib9_bytes':len(zlib.compress(path.read_bytes(),9)),'notices':n}

def main() -> None:
    runtime=SOURCE/PREFIX
    results=[json.loads((Path('E:/p8v8/closure-remaining-evidence')/name).read_text())
             for name in ('prelaunch-roundtrip.json','complete-roundtrip.json')]
    assert {r['phase'] for r in results}=={'PRELAUNCH','COMPLETE'}
    base=max(r['bytes'] for r in results)
    earlier=ledger(runtime/'closed-82/campaign.sqlite3')
    recent=ledger(runtime/'closed-120/campaign.sqlite3')
    previous=ledger(runtime/'boundary/campaign.sqlite3')
    # Never reduce the previously reviewed slope to manufacture feasibility.
    growth=max((recent['zlib9_bytes']-earlier['zlib9_bytes'])/38,(earlier['zlib9_bytes']-previous['zlib9_bytes'])/44)
    old=json.loads((HERE.parent/'v6/feasibility-final.json').read_text())
    # The old full archive max remains an EXTRA payload allowance above the new
    # measured metadata base. Do not charge the new metadata twice by using a
    # current full archive that itself contains that same historical metadata.
    extra=old['observed_backup_max_bytes']
    aws=json.loads((HERE/'aws-stopped-readonly.json').read_text())
    count=1380; cap=60*1024**3
    growth_bytes=2*growth*(count*(count+1)/2)
    index=count*256*1024
    planned=aws['all_version_evidence_bytes']+(count+2)*base+count*extra+growth_bytes+index
    now=datetime.now(UTC)
    start=datetime(2026,10,7,15,24,23,810674,tzinfo=UTC)
    deadline=start+timedelta(hours=360)
    allowance=290*count/1498
    finish=now+timedelta(hours=allowance+2)
    shutdown=finish+timedelta(minutes=30)
    rate=.1197+.005+160*.096/730
    reserves=48*160*.096/730+60*.025+5+1.25
    cost=(shutdown-start).total_seconds()/3600*rate+reserves
    guard_time=start+timedelta(hours=(60-reserves)/rate)
    latest=min(deadline,guard_time)-timedelta(hours=allowance+2.5)
    credits=float(aws['plan']['accountPlanRemainingCredits']['amount'])
    checks={'time':shutdown<deadline,'cost':cost<60 and cost<65,'credits':credits>=65,'cloud_and_local_projection':planned+1024**3<cap,'stopped':aws['State']=='stopped'}
    write(HERE/'estimates.json',{'status':'PROPOSED_FITS' if all(checks.values()) else 'BLOCKED_DO_NOT_DEPLOY','checks':checks,'at_utc':now.isoformat(),'remaining_originals':count,'planning_allowance_hours':allowance,'original_290_hours_per_1498_basis_unchanged':True,'preparation_hours':2,'shutdown_hours':.5,'projected_finish_utc':finish.isoformat(),'projected_shutdown_utc':shutdown.isoformat(),'original_deadline':deadline.isoformat(),'latest_preparation_start_utc':latest.isoformat(),'cost_guard_time_utc':guard_time.isoformat(),'projected_conservative_usd':cost,'conservative_elapsed_cost_now_usd':(now-start).total_seconds()/3600*rate+reserves,'cost_at_absolute_deadline_usd':360*rate+reserves,'admission_guard_usd':60,'total_campaign_ceiling_usd':65,'reserve_usd':reserves,'handover_reserve_usd':1.25,'prior_paused_time_spending_retained_storage_included':True,'rates_unchanged_and_refreshed':aws['rates'],'available_credits_usd':credits,'cloud_and_local_limit_bytes':cap,'capacity_planning_bytes':planned,'capacity_planning_gib':planned/1024**3,'headroom_gib':(cap-planned)/1024**3,'slot_reservation_gib':1,'current_cloud_all_versions_bytes':aws['all_version_evidence_bytes'],'measured_new_metadata_archive_bytes':base,'existing_extra_payload_allowance_bytes_per_slot':extra,'ledger_82':earlier,'ledger_120':recent,'compressed_growth_per_slot_bytes':growth,'doubled_future_ledger_growth_bytes':growth_bytes,'backup_index_allowance_bytes':index,'qualification_backups':results,'retained_root_decision_deadline':'2026-10-11T09:33:51.252814Z','limitations':['Not an invoice cap; billing and credit reporting can lag. No Cost Explorer calls were added.','Elapsed-clock accounting conservatively charges paused hours; old duplicate-root costs remain within prior operational/handover reserves.','No guarantee of recipe durations or archive bounds: largest old full archive remains extra payload, measured metadata base plus twice maximum retained ledger slope.','Successful clock samples use service journals, not per-slot ledger growth; reserve local operational logs up to existing working/disk guards. Rejected samples are durable notices and can cause pause.','All S3 versions/reservations count. Failed live capacity/cost gates stop admissions; no limit grows.','48-hour retained-root disposition remains separate; continuation beyond that reviewed decision deadline needs explicit retention disposition before boot.','Fresh real host/permission/timer/source/backup/readiness gates remain unexecuted.'],'authorization':False,'freeze':False,'AWS_start':False})
    print(json.dumps(json.loads((HERE/'estimates.json').read_text()),indent=2))

if __name__=='__main__':main()
