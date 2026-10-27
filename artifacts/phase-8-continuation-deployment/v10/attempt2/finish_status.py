"""Retain this bounded stopped-host attempt; no further AWS requests."""
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from read_control import HERE, record

def load(name: str) -> dict:
    return json.loads((HERE/name).read_text())

def main() -> None:
    now=datetime.now(UTC)
    start=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')
    stop=start+timedelta(hours=432)
    allowance=290*1355/1498
    rate=.1197+.005+160*.096/730
    reserves=48*160*.096/730+80*.025+5+1.25
    completion=now+timedelta(hours=allowance+2.5)
    uncertain=completion+timedelta(hours=24)
    def forecast(at: datetime) -> float:
        return (at-start).total_seconds()/3600*rate+reserves
    old=json.loads((HERE.parent/'feasibility.json').read_text())
    lower=old['storage_projection_bytes']+292118202
    record('feasibility.json', {
        'status':'TIME_COST_PLANNING_FITS_STORAGE_AND_LIVE_GATES_UNVERIFIED',
        'at':now.isoformat(),'remaining_allowance_hours':allowance,'preparation_shutdown_hours':2.5,
        'uncertainty_reserve_hours':24,'planning_allowances_unchanged':True,
        'expected_shutdown':completion.isoformat(),'uncertainty_shutdown':uncertain.isoformat(),
        'completion_forecast_usd':forecast(completion),'uncertainty_forecast_usd':forecast(uncertain),
        'full_deadline_forecast_usd':forecast(stop),'admission_guard_usd':70,'total_ceiling_usd':75,
        'uncertain_plan_headroom_before_admission_guard_hours':(70-forecast(uncertain))/rate,
        'absolute_stop':stop.isoformat(),'elapsed_host_hours':432,'original_anchor':start.isoformat(),
        'credits_latest':load('plan-result.json')['result']['accountPlanRemainingCredits'],
        'actual_billed_spending':'No fresh Cost Explorer request; prior estimated project-wide gross snapshot 11.3540656882 USD not substituted for conservative campaign forecast',
        'previous_boot_upload_stopped_history_accounting':'All original elapsed hours retained, full 80GiB S3 month, 48h EBS and unchanged reserves; verified successful upload added to last projection',
        'previous_storage_measurement_bytes':old['cloud_all_versions_bytes'],
        'known_added_source_version_bytes':292118202,
        'current_storage_inventory':'UNVERIFIED_PROCESS_TIMEOUT_NO_ZERO_ASSUMPTION',
        'minimum_known_projected_storage_with_reservation_gib':lower/1024**3+1,
        'storage_limit_gib':80,'not_a_live_admission_pass':True,
    })
    host=load('host-result.json')['result']['Reservations'][0]['Instances'][0]
    assert host['State']['Name']=='stopped'
    assert load('absolute-result.json')['result']['State']=='ENABLED'
    record('final-status.json',{
        'status':'BLOCKED_CONTROL_PLANE_NO_BOOT_NO_ADMISSION', 'at':now.isoformat(),
        'host_id':host['InstanceId'],'host_state':'stopped','host_state_verified_at':load('host-result.json')['at'],
        'service_state':'No execution while EC2 stopped; internal systemd unit state not inspected',
        'original_ambiguous_request':'2026-10-12T16:27:20.228195Z',
        'reconciliation':'SSM commands, invocations and CloudTrail broad-window lists empty with no continuation token; historical execution remains UNKNOWN, not nonexecution',
        'blocking_gates':['Local identity and pinned-source HEAD request timeout','Unfiltered SSM and all-version inventory process deadlines','Historical quiescence execution not established; guarded root inspection still required'],
        'aws_mutations_this_attempt':0,'command_resends':0,'archive_uploads':0,'refreezes':0,
        'qualified_tests_repeated':0,'launch_receipt_issued':False,'readiness_issued':False,
        'new_prelaunch_backup':None,'new_complete_backup':None,
        'preserved_backups':json.loads((HERE.parent/'final-status.json').read_text())['existing_research_backups'],
        'retained_boundary':{'BACKED_UP':145,'PLANNED':1355,'active':0,'basis':'Last verified retained boundary; no main or driver request issued during this attempt'},
        'next_sequence':146,'next_arm':'P2','next_attempt':1,'next_execution_id':'01a11705-11f1-772d-8190-c43552871801',
        'freeze':load('existing-freeze-verification.json'),
        'absolute_aws_guard':'ENABLED_READ_BACK_2026-10-12T17:48:21.131604Z',
        'fresh_preparation_guard':'NOT_CREATED_GATE_FAILED_BEFORE_BOOT',
        'absolute_stop':stop.isoformat(),'retention_decision_deadline':'2026-10-27T15:24:23.810674Z',
        'root_retained':'vol-09dbb42bbf607f5de','evidence_deleted':False,
        'manual_handoff':'cloudshell-control-preflight.py; read-only, no credentials or signing keys',
        'manual_handoff_sha256':hashlib.sha256((HERE/'cloudshell-control-preflight.py').read_bytes()).hexdigest(),
    })
    print(json.dumps(load('feasibility.json'),indent=2))

if __name__=='__main__':
    main()
