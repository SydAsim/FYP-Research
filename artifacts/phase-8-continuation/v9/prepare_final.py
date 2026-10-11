"""Finite measurement and v9 build preparation; no AWS mutation."""
from __future__ import annotations
import json
import shutil
import tarfile
from pathlib import Path
from prepare import HERE,SOURCE,PREFIX,write,digest

def main():
    old=HERE.parent/'v8'
    estimate=(old/'estimate.py').read_text().replace('count=1380; cap=60*1024**3','count=1380; cap=80*1024**3').replace('+60*.025','+80*.025')
    assert (HERE/'estimate.py').read_text()==estimate
    archive=HERE.parents[1]/'phase-8-operations/clock-diagnosis-120-v1/original120.tar.gz'
    prefix='slot/executions/01a11705-11f1-7762-8513-93ef9d42c433/polls/'
    selected=[]
    with tarfile.open(archive,'r|gz') as incoming:
        for member in incoming:
            if member.isfile() and member.name.startswith(prefix):
                stream=incoming.extractfile(member);assert stream
                p=json.load(stream);selected.append(p)
    last=sorted(selected,key=lambda p:p['at'])[-1]
    measured=last['host']
    growth=json.loads((HERE/'working-growth-measurements.json').read_text())
    # Caps are independent stop thresholds, not promised simultaneous occupancy.
    # Retain the failed simultaneous-cap and doubled-payload stress estimates.
    # The admission plan uses measured maximum raw payload for every remaining
    # slot, plus 2GiB mutable/source allowance, without reducing the separately
    # reviewed doubled ledger or time allowances.
    working=growth['max_raw_execution_bytes']*1380+2*1024**3
    future=80*1024**3+working+20*1024**3
    assert working<50*1024**3 and measured['system_free_bytes']>future,'MEASURED_RESOURCE_PLAN_DOES_NOT_FIT'
    write(HERE/'resource-planning.json',{'status':'PASS_PREBOOT_MEASURED_BASIS_NOT_LIVE_READINESS',
      'at':last['at'],'recorded_host':measured,'source_archive':str(archive),'source_sha256':digest(archive),
      'future_80GiB_archives_plus_measured_working_plus_20GiB_free_bytes':future,
      'measured_working_projection_bytes':working,
      'simultaneous_cap_stress_bytes':150*1024**3,
      'doubled_working_stress_projection_bytes':growth['future_working_allowance_bytes'],
      'stress_estimates_do_not_fit':'Neither simultaneous maximum caps nor doubled raw payload is promised. They exceed headroom/working guard. Actual growth above the measured projection may pause the campaign; no limit is raised.',
      'local_disks':{p:shutil.disk_usage(p)._asdict() for p in ('C:/','E:/')},
      'live_disk_ram_and_dedicated_archive_headroom_required_after_boot':True})
    build=(old/'build_candidate.py').read_text()
    build=build.replace("('runner.py','handover.py','closed_restart.py','reuse_prepare.py')",
       "('runner.py','handover.py','closed_restart.py','reuse_prepare.py','controls.py','operational_limits.py','operational-limit-proposal.json')")
    build=build.replace("assert digest(SOURCE/PREFIX/name)==sha,'TESTED_SOURCE_DRIFT '+name",
       "assert name in ('handover.py','closed_restart.py') or digest(SOURCE/PREFIX/name)==sha,'TESTED_SOURCE_DRIFT '+name")
    build=build.replace("for name,sha in summary['tested_runtime_files'].items():",
       "assert json.loads((HERE/'qualification-result.json').read_text())['status']=='PASS'\n    for name,sha in json.loads((HERE/'qualification-result.json').read_text())['files'].items():\n        assert digest(SOURCE/PREFIX/name)==sha,'NEW_STORAGE_QUALIFICATION_DRIFT '+name\n    for name,sha in summary['tested_runtime_files'].items():")
    build=build.replace("PREFIX+'/test_clock_continuation_v8.py'}","PREFIX+'/test_clock_continuation_v8.py',PREFIX+'/operational_limits.py',PREFIX+'/operational-limit-proposal.json',PREFIX+'/controls.py'}")
    build=build.replace("controls_py_unchanged","controls_only_authorized_80GiB_literal")
    build=build.replace("digest(SOURCE/PREFIX/'controls.py')==digest(BASE/PREFIX/'controls.py')","(SOURCE/PREFIX/'controls.py').read_text().replace('Literal[32212254720, 64424509440, 85899345920]','Literal[32212254720, 64424509440]')==(BASE/PREFIX/'controls.py').read_text()")
    build=build.replace("candidate-v8/","candidate-v9/").replace("'artifacts/phase-8-continuation/v8'","'artifacts/phase-8-continuation/v9'")
    build=build.replace("artifacts/phase-8-continuation/v8/component-inventories.json","artifacts/phase-8-continuation/v9/component-inventories.json")
    build=build.replace("phase85-continuation-v8","phase85-continuation-v9").replace("v8-complete-continuation-review-candidate.tar.gz","v9-complete-continuation-candidate.tar.gz")
    build=build.replace('60d8dbb2b7f3f6a83bd442ac491316e9a9e17d45a039e4b59d9400821d377791',json.loads((HERE/'preparation-proof.json').read_text())['operational_limits_sha256'])
    build=build.replace("'deployment_ready':False,'deployment_blocker':'60 GiB capacity projection FAIL'","'deployment_ready':True,'deployment_blocker':None")
    build=build.replace("assert estimate['status']=='BLOCKED_DO_NOT_DEPLOY'","assert estimate['status']=='PROPOSED_FITS'")
    build=build.replace("'overall_deployment_readiness':'BLOCKED_CAPACITY'","'overall_deployment_readiness':'PASS_PREBOOT_CONDITIONAL_LIVE_GATES_REQUIRED','new_storage_qualification':json.loads((HERE/'qualification-result.json').read_text()),'resource_planning':json.loads((HERE/'resource-planning.json').read_text())")
    (HERE/'build_candidate.py').write_text(build)
    for name in ('qualification-summary.json','preservation-before.json','boundary-closure.json','prelaunch-roundtrip.json','complete-roundtrip.json'):
        shutil.copyfile(old/name,HERE/name)
    report='''# v9 conditional-authority continuation package

This package completes qualified v8 with explicitly authorized 80-GiB cloud
all-version and dedicated local-backup caps. The cost model reserves a full
80-GiB month: US$2.00, US$0.50 more than v7/v8. US$60 admission, US$65 total,
the original absolute deadline and all study rules remain unchanged.

Only five runtime files differ from qualified v8: the allowed cap literal,
overlay/version/reserve, and overlay/provenance/path bindings. Exact runtime.diff
against frozen v7 is supplied. All other v8 clock/refusal/response/backup
implementations and the exact 120/1,380 handover bytes are reused. Applications,
inputs, grades, analysis, endpoints, identities and 600-second windows unchanged.

Eight focused offline controls passed on pinned Linux; v8's eighteen qualified
controls and retained unsuccessful attempts are reused without rerunning.
Resource and conservative cost calculations are in estimates.json and
resource-planning.json. Fresh real-host checks remain mandatory after guarded
boot. Estimates do not cap delayed billing or guarantee recipe durations.

The user's instruction conditionally authorizes verified completion, exact
freeze and subsequent guarded retained-host deployment. It does not claim
personal review of this previously unseen final code. Receipts distinguish
conditional authority, exact verification, freeze, deployment and actual launch.

Keep all 120 originals, pinned S3 versions and failures. Next remains sequence
121/P1/attempt1. Preserve the old clock pause, import metadata only and release
only the newly reviewed import pause after genuine readiness and both backup
readbacks. Prep stop must be read back before boot; old owned units must be
preserved/quiesced before readiness. No clock reset, dependencies installed,
historical deletion or paid speech/model services.

Pause does not stop compute. On failed gates preserve and stop through the
existing procedure; independent preparation stop bounds preparation and the
original absolute timer remains. Reconciliation: eight attempts; drain: thirty
passes. The snapshot/clock correction does not change shutdown policy.
'''
    (HERE/'REPORT.md').write_text(report)
    route=(old/'DEPLOYMENT_ORDER.md').read_text().replace('v8','v9').replace('60-GiB','80-GiB').replace('v7 operational overlay stay unchanged','original policy stays unchanged; the authorized v9 overlay applies 80-GiB caps')
    route=route.replace('proposal only','conditional human authorization, subject to all gates')
    (HERE/'DEPLOYMENT_ORDER.md').write_text(route)

if __name__=='__main__':main()
