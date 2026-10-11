# Phase 8.2 — finite AWS execution qualification

**Status: finite AWS qualification complete and ready for review. Main-campaign launch readiness remains UNRESOLVED.**

Five calibration traces were executed: one original rejected by the collection-window gate, one separately labelled diagnostic rerun, and three other completed calibrations. Four meet the revised full-window gate. No main inputs ran. All **1,500 main slots remain NOT_STARTED**, representing the unchanged **500-input B3/P1/P2** study. No protocol freeze or launch authorization was created.

## Scope, files and invariants

Only the separate `artifacts/phase-8-aws-qualification/` package and this report were created/updated. Application behaviour, migrations, original fixture banks, research arms, endpoints and observation windows are unchanged. Existing schema head `0013_readiness_capability` was applied only to dedicated research PostgreSQL instances; **migrations added: none**.

| Files/package | Invariant or purpose |
| --- | --- |
| `v1/{plan,preflight,provision,qualify}` and AWS journals | Separate calibration resources, explicit US$2 approval, Sydney regional deployment, retained original attempts |
| `v2/{worker_v2,runner_v2,qualify,test_window}` and seals | Collection through the original cutoff after returns/refusals; unchanged 600-second observation and application |
| `v2/parallel-v2/{plan,lane,parallel}` and seal | Exactly two declared isolated P2 executions; named admission barrier; cache/restart interference checks |
| `v3/{integrity,runner_v3,test_integrity}` and seal | Detect drift in executing research adapters and source capsule; durable pause, no replacement outcomes |
| `v3.1/` and decision/seal | Future diagnostics use attempt=2; historical v2 attempt=1 remains immutable |
| `postprocess-v1/{measure,verify_backups,selection,test_selection}` | Independent oracle replay, resource measurements, backup integrity, diagnostic exclusion by label/linkage |
| Original and revised finish/finalize scripts | Background export, checksum/version checks, bounded shutdown; retained failed finalizers |
| `OPERATING.md`, validation records, this report | Normal-terminal controls, explicit limits and review gates |

PostgreSQL remains the durable correctness authority; Redis loss is a cache fault. No ambiguous external write was retried, no model/API provider was added, and no paid voice service was invoked. B3 safeguards and ordinary corrective statements were preserved. The oracle reads independent simulator truth; repair telemetry remains separate from observable outcomes.

All **1,662 protected historical/source files** and v1/v2/v3/v3.1 seals verified unchanged after the work: [preservation record](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/v1/final-preservation.json>). The 8.1 capsule remains SHA-256 `2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5` (1,642 files, 300 read-only compatibility aliases). These integrity seals are not a reviewed study freeze.

## Recorded execution outcomes

All rows are **CALIBRATION ONLY**. Driver status is COMPLETED in all five; qualification status is separate. The diagnostic never replaces the failed original.

| Version / arm / case | Collection qualification | Outcome and limitations | Trace |
| --- | --- | --- | --- |
| v1 B3 clean, original | **FAIL**: final snapshot began 0.106181s before cutoff | Raw final business state TRUE; raw unsupported/stale exposure FALSE. Driver completed but the full-window gate rejected collection. Its unadmitted second slot stays PLANNED. | [original](<E:/fyp-phase82-evidence/completed/fyp-p82/native-original/executions/8e07da51-1185-413c-aac3-80640caada4c/export.json>) |
| v2 B3 clean, diagnostic linked to original | PASS | Business state and clean success TRUE; unsupported/stale exposure FALSE. Excluded from original-attempt estimates; legacy attempt=1 preserved. | [diagnostic](<E:/fyp-phase82-evidence/completed/fyp-p82-v2/native-original/executions/d95e0d92-782c-468b-a237-77a25f214dec/export.json>) |
| v2 P1 buffered stale start | PASS after normal-path 409 refusal | Business state, correction and final update TRUE. **Unsupported exposed claim and incompatible stale exposure UNKNOWN**; refusal alone does not establish silence. | [expected refusal](<E:/fyp-phase82-evidence/completed/fyp-p82-v2/native-original/executions/2d0f672f-c64e-4c6e-80ce-89db5aeb11a6/export.json>) |
| v2 P2 restart before repair, lane A | PASS, isolation PASS | Business state, final update, explicit retraction and corrective delivery TRUE in the scripted protocol. One persisted obligation reached REPAIR_PLAYED with protocol acknowledgement. | [restart trace](<E:/fyp-phase82-evidence/completed/fyp-p82-v2/parallel-v2/A/run/executions/7961402c-c72a-4ee5-9e82-94b0ecb553e8/export.json>) |
| v2 P2 Redis loss, lane B | PASS, isolation PASS | Business state, correction and final update TRUE; unsupported/stale exposure FALSE; zero repair obligations. | [cache trace](<E:/fyp-phase82-evidence/completed/fyp-p82-v2/parallel-v2/B/run/executions/40b34359-61e8-4dd4-b7aa-5dcd472b9c51/export.json>) |

All five exports independently regraded **identically** using the preserved revised instrument: [measurements/oracle replay](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/postprocess-v1/completed-measurements.json>). Selection retains original failures/timeouts and excludes diagnostics by label and original linkage, including the legacy numbering anomaly. Four original records and one excluded diagnostic are documented; main inferential N is **0**.

For P1 the first recorded blocking mechanism was stale-segment START validation returning 409. For P2 restart, the existing workflow-scoped recovery path discovered the persisted obligation and published repair after the worker restart. A named automatic-publication barrier was observed before scripted client acknowledgement. Worker PID changed 194 to 198, while peer B stayed at PID 185. This exercises documented recovery, not a replay manually delivering repair. It does not prove recovery after arbitrary whole-host loss.

The cache test left A's sentinel intact while B's own sentinel was erased. Each lane had separate application/truth PostgreSQL, cache, resource bindings, faults, queries, outputs and backups; distinct network/PID namespaces; and no published database ports. No foreign workflow appeared in the peer snapshot. [Isolation evidence](<E:/fyp-phase82-evidence/completed/fyp-p82-v2/parallel-v2/success.json>).

These recipes/arms were not paired comparative samples. They cannot establish a winner, a tie across arms, novelty or additional protection beyond a competent baseline. The future paired study must answer that research question.

## Collector remedies and validation

The historical loop checked the clock after acquiring a snapshot. A query could begin before cutoff, finish afterward and end collection. V2 requires the final query's **recorded start** to reach the original cutoff. A deterministic straddling-query test reproduces the defect and checks the correction. Acquisition overshoot does not extend grading beyond final script issuance +600 seconds. Server acceptance remains a separate durable timestamp.

V3 checks executing adapters outside the capsule at entry/admission and during collection; changed/missing files or manifest drift produce a durable pause. V3.1 adds future diagnostic numbering. Their real Linux init/verify checks admitted **zero business slots**, and integrity regressions passed. **Neither v3 nor v3.1 has a full-window business execution**: actual window evidence is v2, component/init evidence is v3/v3.1. A later reviewed finite pilot must use one explicit combined candidate identity.

| Validation | Result / retained evidence |
| --- | --- |
| Preserved Linux regressions plus cutoff tests | **56 passed**, no skips; `E:/fyp-phase82-evidence/completed/fyp-p82-v2/linux-tests.txt` (includes earlier 54) |
| Executing-file/manifest integrity tests | **3 passed locally and on Linux**; `v3/tests.txt` and cloud integrity archive; one cache-write warning, no skips |
| Archive/export qualification unit checks | **7 passed**; `v1/qualification-tests.txt` |
| Original/diagnostic selection checks | **3 passed**; `postprocess-v1/selection-tests.txt` |
| Strict typing of final research adapters/postprocessor | PASS; versioned mypy outputs retained |
| Same-ID/deadline checkpoint and parent SIGTERM reattach | PASS; detached collector continued; native checkpoint, safe-parent-stop and reattach records |
| Completed-slot pause and saved-order resume | PASS; second slot resumed without replacing first |
| Offline grade and analysis-row replay | All five IDENTICAL; no inferential campaign analysis |
| Final archives, backups and historical hashes | PASS; no restore/PITR claim |
| Latest v3.1 initializer on AWS | PASS: diagnostic attempt=2, original attempt=1, both execution IDs NULL |

Counts overlap across reruns/platforms; they are checks, not independent inputs. Missing-anchor, fixed-deadline, lost-service/reboot refusal, failed-export retention and main-ID guards remain covered by the preserved Linux regressions. These actual full-window traces used recorded anchors. Resource-stop/file-drift tests are not separate 600-second live runs.

Retained failures include first preflight import failure; actual t3.large Free-plan eligibility rejection; bootstrap adapter ownership denial; original collection rejection; first local cutoff fixture failure; intermediate strict-typing failures; long Windows-path extraction failure; and two unsuccessful export finalizers. Parallel-v1 was never admitted; output ownership was corrected in a new version before its finite test. No failed outcome was overwritten.

## Standalone operation and interruption rules

SSM starts systemd units and returns. Python collectors, checkpoints, export and shutdown run on the server without a Codex client or callback. Parent SIGTERM/reattach retained the same deadline; completed-slot pause/resume was exercised. Export and automatic stop completed independently. The absolute four-hour cost-stop deadline was not renewed on restart. Whole-host interruption of active observation remains incomplete, not automatic replay.

- Observe the unchanged **600 seconds** after recorded final script issuance, even after return/refusal/failure. Missing anchors use start+600 only to bound collection; timing stays unknown.
- Preserve actual event and query times. Maximum poll-start gap was **5.512424s** versus nominal 5s. Successful final query start overshoots were **0.000122–0.000306s**. Gaps are not silence; missing acknowledgements do not prove completion.
- Resume the same execution ID, original deadline and saved order. Source drift, protocol defects and resource pressure stop new admissions and record the reason. Do not clear a safety pause as an ordinary user pause.
- Retain originals and immutable exports. Diagnostics use new IDs/labels/linkage; no successful replacement. Hard losses retain gaps and missingness.
- Verify S3 checksum/version and local backups before disposal. Failed exports retain disk and failure notices; the powered-time stop still applies.

[Normal-terminal commands and failure/stop/resume instructions](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/OPERATING.md>) are supplied. Do not rerun old finite queues or restart this stopped server under its completed finite-session authorization.

## Resources and practical schedule

Dedicated Sydney host: **m7i-flex.large**, 2 vCPUs, nominal 8 GiB RAM (guest 7.59 GiB), encrypted **40 GiB gp3**, Ubuntu 24.04 amd64, Python **3.12.3**, Docker **29.1.3**. Local 8.1 validation used Python 3.12.13: native regressions establish compatibility for these checks, not binary equivalence or prolonged endurance.

| Measurement | Actual observation |
| --- | --- |
| Successful serial sampled memory | Peak used **0.979 GiB**; minimum available **6.615 GiB** |
| Two-lane host, 123 samples | Peak used **1.597 GiB**; minimum available **5.997 GiB** |
| Two-lane maximum sampled CPU load | **91.05%**, host aggregate including surrounding workload; no arm-specific attribution |
| Successful serial maximum sampled CPU load | **28.53%**; not a sustained-throughput limit |
| Lane limits | Each service namespace 2 GiB /1 CPU; each PostgreSQL 256 MiB /1 CPU; cache 64 MiB |
| Root disk free after qualification | **32.66 GiB** |
| Final app / truth database sizes | Approximately **10.1–10.47 MiB /7.68 MiB** |
| WAL directories | App **32 MiB**, truth **16 MiB** per server; preallocation/rotation, not linear per-case growth |
| Logs / tone audio per execution | **0.029–0.033 MiB /0.060–0.159 MiB** |
| Polls / execution folders / exports | **2.68–10.31 MiB /4.58–16.11 MiB /0.90–2.80 MiB** |
| Final retained archive | **27,144,021 bytes (25.89 MiB)**; extracted approximately **106.98 MiB**, including repeated backups |
| Windows available RAM during qualification | **2.93 GiB** of 15.81 GiB detected nominal 16 GB |
| Final local disk free | C: **20.20 GiB**, D: **100.48 GiB**, E: **181.56 GiB**; all physical Disk 0 |

These are sampled peaks/minima and short observations, not continuous maxima or proof of campaign capacity. Calibration admission requires >=1.5 GiB available RAM serial, >=4 GiB for the finite parallel check, >=5 GiB system/Docker disk and >=2 GiB output/backup reserve. Below 1 GiB available RAM stops new admissions. Campaign capacity/backup limits still need acceptance; **40 GiB is a calibration disk, not qualified campaign storage**.

Successful two-slot serial control took about **20m29s**, including checkpoint/resume/backups. The separate parallel pair took **10m25.79s**, including admission/preparation. Successful individual traces lasted **602.7–604.8s**. Different recipes were used: no paired causal speedup or latency equivalence is established.

**Recommend serial campaign planning.** Only these two P2 restart/cache recipes are qualified for overlap. Other recipes and B3/P1 remain serial/exclusive until isolation is demonstrated; differing IDs alone are insufficient. Do not halve the entire forecast.

For 1,500 executions, 600-second windows alone require **250 hours** serial. Retain the previous **12.6–13.1 continuous-day** planning range with preparation/backup/interruptions; these few AWS traces do not establish a representative all-recipe runtime distribution. A reviewed finite representative pilot must validate runtime and storage. Windows are unchanged. A complete two-lane campaign forecast is unresolved.

## Analysis compatibility and voice limits

Allocation and arms remain unchanged. Independent input is the resampling unit; B3/P1/P2 stay paired within declared scenario strata. Recipe labels, repetitions, execution slots and scheduling blocks do not become independent inputs. Required clustered latency intervals remain in scope; descriptive-only timing does not replace them. Retain the candidate's identifiable timing model and missingness/censoring rules. Future concurrency needs lane/overlap records and reviewed shared-host dependence assumptions. This unpaired qualification set supports no inferential arm comparison.

All actual audio here is **scripted tone plus protocol acknowledgements and semantic proxy indices**, not intelligible speech. These records support protocol recovery/publication, event collection, truth and isolation under the fixtures. They do not establish human hearing/understanding, real speech alignment, ASR/native-audio performance, telephone transfer quality or actual customer exposure. Spoken-content conclusions require intelligible speech, alignment and appropriate playback evidence.

## Spending, exports and retention

User approved **US$2** for this finite stage. FREE/ACTIVE plan was verified; no paid upgrade. Actual t3.large launch failed eligibility despite a successful permission dry run. Eligible m7i-flex.large measured rate: **US$0.1197/hour**; IPv4 US$0.005/hour; gp3 US$0.096/GiB-month. Revised four-hour compute/IP/disk estimate: **US$0.51984**. With seven-day disk retention and US$0.50 export contingency: **US$1.90357**, within approval.

First launch to final automatic stop was approximately **75.3 minutes**, including an intermediate stopped interval. A conservative elapsed-time compute/IP bound is below **US$0.16**, before disk/export costs. This is a rate estimate, not an invoice. Displayed US$100 credits do not prove zero usage or complete billing.

Instance **i-0938c2aa962389253 is STOPPED**. Its 40 GiB disk persists at approximately **US$0.126/day**. Cleanup versus short retention requires the user's choice under AWS project instructions; S3 evidence stays independent of that choice.

Final immutable archive:

- Bucket `fyp-p82-20261005-018da1d6-803656589923`, Region `ap-southeast-2`.
- Key `exports/phase82-final-evidence-2f1793d840be7a8c407d2fdfe8814eec1d14f9ed972a628a2329f06f4e780175.tar.gz`.
- SHA-256 `2f1793d840be7a8c407d2fdfe8814eec1d14f9ed972a628a2329f06f4e780175`.
- S3 VersionId `jnIuc6WTAVirM0Cbihgrau.u_UJi5Bj9`.
- Project archive, E: short-path extraction and D:/P82 backup verified: [download record](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-aws-qualification/v1/download-completed-verification.json>).
- Backup checks: **50 manifest-file hashes, 690 compressed/raw pairs, eight SQLite integrity checks, 16 logical PostgreSQL dumps**. These include repeated snapshots; PostgreSQL restore/PITR is **not tested**.

S3 is private, encrypted, versioned and uses content-hash keys. Versioning is not Object Lock/WORM. C:/D:/E: share a physical disk; S3 adds an independent storage failure domain. Final evidence includes failures, partial attempts, source and adapter versions.

The v2 finisher lost a temporary source archive on reboot. An export-only replacement then failed on version-specific read permission. Automatic approval review rejected attempted permission expansion before execution, stating only “blocked by policy”; no expansion was applied. The successful replacement used existing current-object access, checked the returned original VersionId and SHA-256, retained persistent source, exported and stopped automatically. Version-specific GetObject requires GetObjectVersion permission: [AWS S3 API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html). No business driver was rerun for finalization.

## Readiness checklist

| Gate | Status | Remaining action |
| --- | --- | --- |
| Finite budget, dedicated Sydney resources, independent export/stop | PASS | Choose disk cleanup or bounded retention; keep S3 evidence |
| Full-window normal/refusal collection, checkpoint/reattach, pause/order | PASS for v2 | Next reviewed pilot uses one explicit combined candidate |
| Executing-source drift, diagnostic numbering/selection | PASS component/init | No latest v3.1 business-window run; retain this limitation |
| Parallel restart/cache isolation | PASS for two observed P2 recipes | Other overlaps unqualified; serial recommendation |
| Originals, oracle replay, preservation and backups | PASS | Continue hash checks and preserve UNKNOWN outcomes |
| First original full-window acquisition | FAIL, retained | Separate v2 correction; never replace original |
| Whole-host active recovery or database restore/PITR | UNRESOLVED / unqualified | Preserve incomplete attempts on loss; no transparent recovery claim |
| Representative campaign runtime/storage/continuous operation | UNRESOLVED | Review finite representative pilot and campaign resource/retention budget |
| Complete parallel schedule/latency dependence | UNRESOLVED | No global parallel launch; review assumptions and clustered analysis |
| Real spoken-content conclusions | UNRESOLVED | Restrict present conclusions to synthetic protocol mechanisms |
| Design acceptance, freeze and separate launch | UNAUTHORIZED / UNSTARTED | Review candidate, outcomes/windows/missingness, analysis, schedule, cost/storage and stop rules; accept then freeze; separate launch approval |

**Verdict:** Phase 8.2 provides finite standalone AWS qualification evidence ready for review and the next bounded pilot's planning. Full main-campaign launch readiness remains unresolved. The 500-input campaign is unstarted and launch-guarded.
