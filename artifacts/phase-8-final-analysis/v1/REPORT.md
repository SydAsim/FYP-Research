# Phase 8 closeout — evidence validation in progress

Status: IN_PROGRESS_AWAITING_RETURNED_CLOUDSHELL_BUNDLE. All1500 original campaign slots are BACKED_UP; this is not yet a completed statistical analysis. AWS campaign host remains stopped. No Phase9, scenario execution, replay, regrading, new freeze/launch, application/fixture/endpoint change, or evidence deletion.

## Verified evidence and authority

- Final master archive4239bb8dbfc5596749344c2ba71676f5bc38220a3b90bbc229b6ea2feadfcfe4, pinned versionBOQu6CMmpLlmpTif0TMHLnGkSURD7puE, reused in place on D:. Ledger and binding members match archive manifest;1500 exact identities,500 per arm.
- All1500 backup receipt members match manifest and master backup hashes. Read-only S3 all-version inventory independently confirms all1500 pinned versions and sizes;1573 versions, zero delete markers in this campaign export prefix. Content re-download of all archives is not claimed.
- All196037 master notices verify their chained hashes; SQLite quick_check passed.
- Frozen v12 archive60218b4a7b7a9ac5862b1792e28cd93e1fc2ea7b6bc163da12ef4576b6955e0b and source packagecad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d verified.3450 local source inventory entries match final frozen inventory. Existing signed acceptance/freeze/launch and archived readiness/saved identities verify; no key was exported, printed or placed in a handoff.
- Existing735-result compact download SHA1a669f90ef6ceea07adca474249ed25d06baae99aac3bd800da5ceba3f2d01b7 matches its original verification. All735 identities/archive/version bindings match final master;735 rows pass frozen model validation.120 rows additionally match directly available original export bytes; remaining rows reuse prior sealed compact-extraction verification.
- All500 frozen cases match their1500 fixture bindings:300CLEAN/100HIDDEN_COMMIT/60PLAYOUT/40OTHER_BOUNDARY.

## Files and invariants

PLAN.md: bounded scope. extraction-control.json/receipts.json/frozen-cases.json: identity and evidence binding. cloud_extract_final_v1.py: read-only streamed pinned evidence extraction; no oracle. extract_core.py: separate readable maintenance template; the distributed script hash remains unchanged. prepare_dataset.py: fail-closed bundle/member/identity/grade validation and original row assembly. run_analysis.py: offline calls matching frozen instrument.analysis, fixed bootstrap counts/seeds, no application imports or network. Verification JSON files retain exact checks. No migrations. Historical phase reports are untouched.

## CloudShell handoff and current state

Uploaded script SHA4890790c30a48f3c7e243e5cf5c50ad3ced1a0fcae4b79065c83f1b7b40f8b50;728641bytes. User reported successful hash verification, eight offline Linux controls, and first verified missing records736–739. Treat this as reported progress, not an independently received completed bundle.

Extractor reads765 missing original pinned archives, once each,41943356497 compressed bytes in total. It streams archive/member hashes without retaining full tar files, bounds selected records, counts existing staging/logs, reserves failure space, caps stage at192MiB, compact memory at48MiB and bundle at32MiB. Process bound14400seconds plus external termination bound14415seconds/10-second kill grace. No automatic retries/restarts. Requests and completed records are preserved; any error stops. No campaign writes or S3 uploads. CloudShell checks expected project803656589923, Sydney region, and stopped host before reads.

Expected returned file: /home/cloudshell-user/fyp-phase8-final-evidence-v1/final-records.tar.gz plus its printed SHA256. Complete inferential analysis is unstarted until this bundle is verified locally.

## Validation and retained unsuccessful attempts

- Eight focused offline extractor controls passed locally; the same eight passed in CloudShell per the user's returned output. Verified retained first export also passes compact-record identity/grade agreement checks.
- Dataset and analysis adapters pass configured Ruff and mypy checks. Readable extraction template passes Ruff, Linux-target mypy and eight offline controls. Generated/distributed v1 bytes are preserved; maintenance-template formatting/type annotations do not silently update that executable.
- Source verification initially used an earlier prequalification inventory and flagged two files subsequently finalized before the accepted freeze. Failed comparison is retained. Final accepted inventory hash4e735251074949bcbe35f4e51aeb4a53cd3500a2f1b9dfe767ace1c50d672329 resolves this; frozen source was not changed.
- Two cached-row check attempts assumed all145 old raw exports were direct master members. Actual direct matching coverage is120. Failed assumptions are retained in cached-adapter-verification.json; no missing raw record is fabricated or replaced. All735 derivative rows retain their prior verification and current pinned receipt binding.
- One local pinned slot1500 retrieval reached its declared120-second limit at7995392bytes; partial copy and timeout record preserved. No retry or transport loop. It did not yield new verified research evidence. CloudShell streaming is the supported evidence-access route.
- First manual handoff command failed because upload had not happened; its hash gate prevented execution. Subsequent reported upload/hash/test/start succeeded.

## Accepted analysis and scientific limits

Use existing frozen outcome_report, paired_latency(2000draws,seed8042051), lognormal_aft and input-ID-cluster aft_cluster_bootstrap(1000draws,seed8042052). Retain500 paired inputs, fixed-stratum weights, co-primary Bonferroni, ten-comparison secondary Holm family,5pp clean-case tolerance, planned missingness bounds,20fixed-block omission sensitivity and600-second horizon. No outcome-selected exclusion, substitute attempt or new extension.

Raw original rows are preserved. Previously accepted first/second sidecars are separately manifest/retained-handover authenticated: they change only censor_reason and oracle_hash, with identical numeric times and outcome values. A separate accepted timing view reuses those exact old records; no new sidecar or oracle call is permitted. Historical raw infrastructure labels for any other originals remain unchanged. They cannot be assumed to establish independent administrative censoring; report timing limits rather than silently reclassifying.

Shared revision-only claim selection remains unchanged. SCRIPTED_TONE_SEMANTIC_PROXY supports protocol/evidence/ACK claims only; no intelligible-speech, hearing or human-comprehension conclusion. Fixed recipe support, shared host/time effects, operational interruptions and versions must be disclosed. Competent baseline ordinary updates receive credit. Ties or negative findings are reportable; neither passing controls nor1500backups establishes novelty/superiority/publication readiness.

## Remaining gates

1. Receive/hash-verify completed bundle; verify its committed records against all1500 frozen identities, pinned receipts and fixture hashes.
2. Assemble complete dataset and separate accepted timing view without changing raw records.
3. Run fixed offline analyses; retain missingness, failed fits and censor labels. Review timing assumptions and failure sensitivity before claims.
4. Produce final tables, mechanism/limitation interpretation, success/failure trace references, reproducible artifact inventory and final Phase8 report. Optional Phase9 remains unstarted.
5. Root retention remains a separate operational decision: up to48hours after actual shutdown, outer decision bound28October2026 12:00UTC. No deletion authorized or performed. Preserve S3/local evidence.
