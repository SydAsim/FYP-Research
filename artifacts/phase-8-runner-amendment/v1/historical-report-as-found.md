# Phase 8.5 deployment and guarded Inspect the retained first execution only. Show the request that received 409, its exact response body and error code, the attempted confirmation, and the provider facts/evidence that caused rejection. Identify the precise backend check and source location. Explain the event sequence in simple English. Do not rerun anything or change code.launch report

## Verdict

**MAIN CAMPAIGN STARTED, THEN BLOCKED.** One original was collected through its full window, graded, independently backed up and retained. The frozen collector treats a normal-path HTTP 409 evidence refusal as a driver exception and permanently pauses admissions. The queue stopped with **1 BACKED_UP and 1,499 PLANNED**. The EC2 host is confirmed stopped. No original was replayed, no outcome replaced and no frozen code changed.

This is a newly demonstrated operational blocker in the accepted v2 setup. Its historical final-verification.json remains PASS and unchanged; that gate did not demonstrate unattended continuation after a live normal-path refusal. Its normal-return/refusal window tests qualified collection, not continued campaign admission. Do not interpret PASS as resolving this defect.

## Authorized scope and provenance

The user's Phase 8.5 instruction authorizes deployment and up to US$65 incremental campaign costs against the accepted Phase 8.4 v2 freeze. A separate owner-signed LAUNCH capability binds the actual run, original operational clock, policy and freeze. Owner key material remains outside the project and frozen source.

| Item | Value |
|---|---|
| Run | p85-01a116f7-3b82-7a79-8653-3aee62dc99e9 |
| Accepted package hash | c76fc54018ce6b9e9f77eeb2946cea253271ad4a8573f8fe047961d7b6f6dc6b |
| Archive SHA-256 | 0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62 |
| Freeze receipt SHA-256 | 0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2 |
| Launch receipt SHA-256 | 35b9d06c9676baadffd4561bf2489b2bc1b08afce28fca5f1e259657f841bcd9 |
| Study | 500 v4 inputs, B3/P1/P2, 1,500 serial original identities |
| Order and endpoints | Accepted saved order; unchanged v4 outcomes and analysis |
| Observation | Original final externally issued request + 600 seconds |
| Changes to application / migrations / frozen runner | 0 / 0 / 0 |

[Launch statement](phase-8-launch/v1/launch-authorization-statement.json), [signed launch](phase-8-launch/v1/LAUNCH.json), [preprovision verification](phase-8-launch/v1/preprovision-verification.json), [after-stop preservation and oracle checks](phase-8-launch/v1/after-stop-verification.json).

After shutdown, all 1,678 accepted source files, 5,597 historical files and 144 verification artifacts match their stored hashes. All 17 files listed by the freeze checksums match (18 freeze files including the checksums file itself were checked before provisioning). Archive and inventory remain unchanged. The old unstarted template and historical acceptance/freeze documents were not rewritten to imply a new state.

## Exact timeline (UTC)

| Event | Time |
|---|---|
| Launch-bound operational clock began before provisioning | 2026-10-07 15:24:23.810674 |
| EC2 launch | 2026-10-07 15:29:05 |
| Standalone systemd campaign service started | 2026-10-07 15:43:07 |
| First original admitted | 2026-10-07 15:43:08.643790 |
| Final externally issued request, revision 2 | 2026-10-07 15:43:16.732035 |
| Driver returned HTTP 409 / FAILED | 2026-10-07 15:43:17.556977 |
| Immutable original cutoff | 2026-10-07 15:53:16.732035 |
| Final poll started | 2026-10-07 15:53:16.732207 |
| Export finished | 2026-10-07 15:53:17.012137 |
| DRIVER_FAILURE propagated to master pause | 2026-10-07 15:53:23.699615 |
| Original BACKED_UP transition | 2026-10-07 15:53:24.675126 |
| New admissions stopped | 2026-10-07 15:53:26.482436 |
| Stop evidence and final master metadata verified in S3 | 2026-10-07 15:57:02–03 |
| EC2 stop transition | 2026-10-07 15:57:46 |
| Original admission cutoff, unchanged | 2026-10-22 14:54:23.810674 |
| Original operational deadline, unchanged | 2026-10-22 15:24:23.810674 |

The independent calendar timers were active before the first original, set to 2026-10-22 15:24:23 UTC (rounded down by 0.810674 seconds), with the independent watchdog also active. The campaign unit uses Restart=no. These host timers do not limit charges for a stopped disk or retained S3 evidence. The host was stopped early after the failure and verified backups; it is not continuing in the background.

## Deployment and financial checks

All project resources are in ap-southeast-2, using fyp-research. Global pricing reads do not deploy resources elsewhere.

| Resource | Configuration |
|---|---|
| EC2 | i-0a6196aff6f8098ac, m7i-flex.large, 2 vCPU / 8 GiB, on-demand |
| OS | Canonical Ubuntu 24.04 amd64, ami-090b1140798d2d006 |
| Root disk | vol-07baf9132bce08e77, encrypted 160-GiB gp3, 3,000 IOPS / 125 MB/s, DeleteOnTermination=false |
| Human access | SSM, no SSH or other inbound rules |
| IAM role/profile | FYP-p85-01a116f7-3b82-7a79-8653-3aee62dc99e9; SSM plus dedicated evidence-prefix read/write, no evidence delete |
| Evidence bucket | Existing versioned fyp-p82-20261005-018da1d6-803656589923, private, SSE AES256 |
| Dedicated prefix | exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/ |
| Runtime | uv 0.9.24; CPython 3.12.13; locked application, analysis and transport environments |
| Database images | Frozen digest-pinned PostgreSQL 16.9 and Redis 7.4.5-alpine |
| Host shutdown action | Stop, preserve disk; no automatic restart |

AWS Free plan was ACTIVE with US$119.37 remaining credits before provisioning. The after-stop credit API still reports US$119.37; billing is delayed and this is not evidence of zero spend. No upgrade, model API, paid speech API or subscription was added.

AWS Price List reads matched the accepted rates: compute US$.1197/hour; public IPv4 US$.005/hour; gp3 US$.096/GiB-month; first-tier S3 US$.025/GiB-month. The previously accepted 312-hour estimate is US$52.23 and 360-hour estimate US$59.23, including the specified reserves. These are planning amounts, not bills.

The instance ran approximately 28 minutes 41 seconds. Compute plus public IPv4 for that interval is approximately US$.060; running disk adds approximately US$.010. Forty-eight hours of stopped 160-GiB disk adds approximately US$1.01 using a 730-hour planning month. Request charges, retained object versions and billing rounding are additional. Actual invoice amounts remain unconfirmed. No US$55 guard or US$65 policy increase occurred.

[Current pricing evidence](phase-8-launch/v1/pricing-preflight.json), [configuration and credits](phase-8-launch/v1/config-preflight.json), [verified stopped instance](phase-8-launch/v1/stopped-instance-state.json), [retained resource/version inventory](phase-8-launch/v1/retained-aws-inventory.json).

## Readiness evidence before admission

The real host passed:
- Source closure and acceptance/freeze/launch signature chain, including original receipt byte hashes.
- Owner directory/key permissions 0700/0600.
- Instance health and encrypted disk configuration.
- Available RAM 7,360,872,448 bytes; actual free disk 160,577,970,176 bytes. Working and backup paths share that physical device; these numbers are not additive.
- Qualified loopback ports available and dedicated slot resources configured.
- Versioned S3 permission probe with immutable PUT, checksum/version verification.
- Master ledger SQLite integrity and a real verified prelaunch cloud backup.
- Exact 1,500 slot/input/arm/attempt/execution bindings.
- Independent hard-stop timers and watchdog active before starting the unit.

The standalone systemd process, host ledger and S3 client do not require a Codex conversation. Its observed stop was caused by the frozen failure guard, not chat disconnection. [Readiness response](phase-8-launch/v1/readiness-final-result.json), [real start response](phase-8-launch/v1/main-start-result.json).

## Original 1: retained result, not a successful driver

| Field | Value |
|---|---|
| Input / arm / attempt | p8v4-0484 / B3 / 1 |
| Recipe | resource-only; hidden commit / dropped response |
| Execution | 01a11705-11f0-79f1-9293-78f7f8207f70 |
| Raw status | FAILED; RuntimeError from normal-path HTTP 409 |
| Window / snapshots | Full 600 seconds, 116 polls, final poll after cutoff |
| Maximum poll-start gap | 5.565513 seconds |
| Missing final anchor / oracle failure | false / absent |
| Final business state / correction success | TRUE / TRUE |
| Correct final spoken update | FALSE |
| Unsupported exposed claim / incompatible stale exposure | FALSE / FALSE |
| Timing censor reason | INFRASTRUCTURE_FAILURE, retained exactly as frozen |
| Voice evidence | SCRIPTED_TONE_SEMANTIC_PROXY / SCRIPTED_TONE_ACK_PROTOCOL_ONLY |
| Export SHA-256 | 283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b |

[Retained original export](C:/fyp-p85/stopped-attempt1/slot1/x/slot/executions/01a11705-11f0-79f1-9293-78f7f8207f70/export.json). Local postflight verifies archive, gzip trailer, every manifest member, exact version and short-path extraction. The revised oracle and analysis row recompute identically from this original. They were not rewritten.

B3 rejected publication because current provider facts did not support the speech. Voice trace 37ca68fd-99ab-4f68-aa0f-b123d02346ad; controller trace 65db2483-69f1-48af-9800-387c419d19b9; workflow 2187b4c4-60af-4245-b04f-d81df24d25ed.

This is an expected safeguard response to a research fault. The permanent campaign stop is the operational problem. Historical v4 qualification retained 36 normal-path HTTP 409 refusals. The frozen collector raises these as RuntimeError, writes DRIVER_FAILURE, then continues collection correctly. Frozen runner.py propagates that pause after export, completes the backup, retires verified owned resources and refuses the next admission. Its failure pause cannot be cleared by ordinary resume. The frozen timing adapter also classifies FAILED as INFRASTRUCTURE_FAILURE; that semantic classification must be addressed explicitly in any reviewed amendment, not silently recoded here.

No arm comparison, statistical study conclusion or novelty claim follows from this one B3 result. No paired input is complete.

## Evidence preservation and shutdown

The original backup includes both logical PostgreSQL dumps before verified-resource retirement:
- Original archive: cc38346ff273b2f04ef8022345654708991fd40ff8ab3ffc9c8b8f4de5bfb8f1, 444,490 bytes, version SDh8fTiUZ60.u3OMiYr_bVKjEpxL19SA.
- Stop operational evidence: be7c9d1c0aaea1095608b6aae86905a75e18afcf0b3b7db37d3a8e3fa0211e5a, 9,674 bytes, version DO_xFsB1hlLb3Qc7_C0K4f0RP4rBrCcw.
- Master metadata: eff99d3a331ff59a309f4d50b5ade469558524dde46cd9f00324497deed7fd4c, 178,735 bytes, version FTfJUeHOoTS1j6C.Qss2dX95wObE7y4n.

All three have verified S3 versions and verified local archives/extractions at C:/fyp-p85/stopped-attempt1. The stopped encrypted EBS copy is retained. Master metadata preservation does not mark the incomplete queue completed.

The latest run-prefix inventory has 20 retained versions totaling 30,907,243 bytes, below 30 GiB. It includes the source and deployment records as well as scientific evidence. No only evidence copy was deleted. Main backups were obtained through the frozen bounded range downloader and short-path extractor, using version-pinned MCP-signed URLs and independently checked S3 heads. Parallel reads are evidence transport only.

[Preservation receipts](phase-8-launch/v1/stop-preserved.json), [cloud version checks](phase-8-launch/v1/backup-object-heads.json), [local postflight](phase-8-launch/v1/local-postflight.json), [saved failure state](phase-8-launch/v1/launch-stopped.json).

**Retention review deadline: 2026-10-09 15:57:46 UTC**, 48 hours after the recorded stop transition. The retained disk costs approximately US$.505/day. Disk deletion is not scheduled; protected-evidence retention needs an explicit cleanup/retention decision before that limit. S3 has no automatic deletion; first-month retention and further escalation remain as accepted. The hard compute timer does not solve either retention obligation.

Do not restart this instance to attempt main recovery. Host reboot/full-host restore is unqualified under the accepted package, and the failure pause is retained. Remaining 1,499 slots cannot be admitted by this version without a reviewed amendment.

## Commands and operating instructions

From a normal PowerShell terminal in the project:
```powershell
.\artifacts\phase-8-launch\v1\Check-Status.ps1
```

Prerequisites: AWS CLI v2 installed and fyp-research credentials valid. It reads EC2 state; if running, it asks the existing read-only SSM progress helper for the live ledger. If stopped, it displays the retained status and never starts a host, collector or driver. The older Check-Progress.ps1 requires a running SSM host; it cannot query the stopped host.

Executed operations are retained as MCP request/results: Price List/configuration/credit reads; CreateRole/scoped policy/profile/security group; version-pinned source upload; RunInstances; SSM bootstrap, readiness, start, progress and preservation; S3 backup HeadObject/ListObjectVersions; StopInstances and stopped-state verification. Local verification commands:
```powershell
.venv\Scripts\python.exe artifacts\phase-8-launch\v1\recover-stopped-evidence.py <private-signed-url-config> C:\fyp-p85\stopped-attempt1
.venv\Scripts\python.exe -B artifacts\phase-8-launch\v1\verify-after-stop.py
```
They already ran; write-new outputs intentionally prevent casual repetition into existing directories. Expired transfer credentials require a new evidence-only transfer attempt, never a scientific rerun.

## Files and failures

Created only Phase 8.5 operational files under artifacts/phase-8-launch/v1 and this report. Frozen application source, fixtures, migrations and earlier reports: unchanged. No migration added. No optional research extension added.

Retained deployment attempts:
1. uv 0.9.24 had no built-in CPython 3.12.13 catalog entry. Bootstrap failed before any original. A documented external catalog supplied that exact patch version; uv and frozen dependencies stayed pinned.
2. PowerShell JSON date coercion changed transported receipt timestamp strings. HMAC validation rejected the transfer before any original. Rejected copies and original envelope were retained; transfer was corrected to exact original bytes, not resealed.
3. First original's HTTP 409 refusal produced the frozen failure pause and stopped the queue. Full observation and grading continued; no suppression or retry occurred.

Successful operations trace: real prelaunch backup and independent-timer readiness PASS. Expected application failure trace: first original HTTP 409, above. There is no successful original driver trace in this run.

## Validation totals and remaining work

| Check | Result |
|---|---|
| Accepted final-verification / archive / inventory / freeze | PASS |
| Current prices / credits / permitted Region / deployment | PASS |
| Real readiness, S3 permissions, prelaunch backup, independent timers | PASS |
| Exact saved binding and first original admission | PASS |
| Full window after failed driver / immutable original and database dumps | PASS |
| Real per-slot S3 backup and stopped-master preservation | PASS |
| Three local evidence recoveries / oracle and analysis replay | PASS |
| 1,678 source / 5,597 historical / 144 verification artifacts unchanged | PASS |
| Normal-path refusal followed by unattended next-slot admission | FAIL: frozen permanent failure pause |
| All 1,500 originals / any complete three-arm input | NOT COMPLETED: 1/1,500 retained, 0 complete pairs |
| Actual final AWS bill / indefinite retention within US$65 | UNRESOLVED; billing delayed and retention bounded |

No broad regression suite or repeat pilot was executed because no application or frozen runner changes were made. This was a deployment and actual first-original run, not an additional calibration set.

**Next required decision:** review a narrowly scoped versioned runner/analysis amendment distinguishing expected research refusals from operational defects, with separate finite qualification and a reviewed continuation policy for the untouched 1,499 original slots. Preserve the first original and its original grades/status in all reporting. Nothing in this report authorizes a new freeze, code amendment, restart, clock reset, replacement run, higher spending limit or new launch.

Phase 8.5 remains incomplete and admissions are blocked.
