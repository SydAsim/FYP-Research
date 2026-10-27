"""Retain the exact blocked attempt and conservative refreshed planning values."""
import json
import hashlib
from datetime import UTC,datetime,timedelta
from ops import HERE,record

def read(name):return json.loads((HERE/name).read_text())

def main():
    assert read('verify-stopped1-result.json')['result']['Reservations'][0]['Instances'][0]['State']['Name']=='stopped'
    assert read('verify-preparation-retired-result.json')['result']['State']=='DISABLED'
    raw=read('export-layout-status1-result.json')['result'];assert raw['Status']=='Success' and raw['ResponseCode']==0
    layout=json.loads(raw['StandardOutputContent']);assert layout['backed_up']==145 and layout['planned']==1355
    assert layout['root_source']=='/opt/fyp-phase8-continuation-v9' and not layout['original_clock_renamed'] and not layout['metadata_stage_wrote_history']
    historical='/var/lib/p8-continuation-v9/run/historical/first-slot/executions/01a11705-11f0-79f1-9293-78f7f8207f70/export.json'
    assert layout['paths'][historical]['sha256']=='283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b'
    now=datetime.now(UTC);anchor=datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00');stop=anchor+timedelta(hours=432)
    remaining=290*1355/1498;rate=.1197+.005+160*.096/730;reserves=48*160*.096/730+80*.025+5+1.25
    forecast=lambda at:(at-anchor).total_seconds()/3600*rate+reserves
    finish=now+timedelta(hours=remaining+2.5);uncertain=finish+timedelta(hours=24)
    record('final-status.json',{'status':'BLOCKED_CLOSED145_EXPORT_LAYOUT_SAFE_STOP_VERIFIED','at':now.isoformat(),
        'host_id':'i-057344e5372faf62f','host_state':'stopped','verified_stopped_at':read('verify-stopped1-result.json')['at'],
        'root_volume_id':'vol-09dbb42bbf607f5de','root_and_evidence_retained':True,
        'service_state':'Owned old campaign/watchdog verified inactive before source deployment; EC2 stopped, no compute execution',
        'backed_up':145,'planned':1355,'active':0,'next_sequence':146,'next_arm':'P2','next_attempt':1,
        'next_execution_id':'01a11705-11f1-772d-8190-c43552871801','actual_admission':None,
        'source_deployed':True,'source_and_public_authority_verified':True,'inventoried_files_verified':3441,
        'package_hash':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c',
        'archive_sha256':'212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37',
        'source_version':'QmAcYmVhFW5GHo08qBB01sD.laBJlcyo','new_source_uploads':0,'source_downloads':1,'refreeze':False,
        'precise_failed_gate':'closed145.verify_retained_root:95 -> read(root/exports/0001/export.json), FileNotFoundError',
        'missing_directory':'/var/lib/p8-continuation-v9/run/exports','original_first_export_present':historical,
        'verified_first_export_hash':layout['paths'][historical]['sha256'],'first_archive_present':True,
        'evidence_loss_not_demonstrated':True,'all145_exports_individually_verified':False,
        'root_run_configuration_changed':False,'clock_anchor_changed':False,'pause_released':False,
        'pause_sha256':layout['pause_sha256'],'readiness_issued':False,'launch_binding_issued':False,
        'new_prelaunch_backup':None,'new_complete_backup':None,
        'historical_backups':json.loads((HERE.parent/'final-status.json').read_text())['existing_research_backups'],
        'completed_qualification_reused':True,'new_checks':'Finite external Bash/Python syntax and current AWS/root/source reads only',
        'driver_calls':0,'scenarios_run':0,'grades_changed':0,'historical_timing_sidecar':False,
        'preparation_guard':'DISABLED_AND_READ_BACK_AFTER_STOP','absolute_aws_guard':'ENABLED_READ_BACK_BEFORE_BOOT_UNMODIFIED',
        'absolute_stop':stop.isoformat(),'elapsed_host_hours':432,'original_clock_anchor':anchor.isoformat(),
        'retention_decision_deadline':'2026-10-27T15:24:23.810674Z','deletion_authorized_or_performed':False,
        'admission_guard_usd':70,'total_ceiling_usd':75,'cloud_and_backup_caps_gib':80,
        'planning':{'remaining_allowance_hours':remaining,'preparation_shutdown_hours':2.5,'uncertainty_hours':24,
            'completion_utc':finish.isoformat(),'uncertainty_utc':uncertain.isoformat(),'completion_usd':forecast(finish),
            'uncertainty_usd':forecast(uncertain),'full_deadline_usd':forecast(stop),'actual_billing_not_substituted':True,
            'future_storage_with_reservation_gib':read('feasibility.json')['with_reservation_gib'],'fresh_metadata_size_and_actual_capacity_not_reached':True},
        'minimum_next_procedure':'Qualify external exact-record metadata materialization from existing verified retained exports/archives; leave frozen validator unchanged; reuse installed source, do not repeat exclusive bootstrap; new guard/live gates/readbacks before any admission'})
    print(json.dumps(read('final-status.json'),indent=2))

if __name__=='__main__':main()
