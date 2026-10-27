# Phase 8 final results and closeout

Date: 2026-10-25. **All planned originals and computational analyses complete; scientific limitations retained.** Phase 9 is unstarted. No scenario was replayed, no original was replaced/regraded, and no AWS compute was started during closeout.

## 1. What the study found

Across the fixed synthetic study frame, **B3, P1 and P2 each achieved 455/500 correct final business states (91%)**, including **300/300 clean tasks**. Their correction-success outcomes matched input by input. The co-primary comparisons do not demonstrate an improvement from P2 over B3.

A narrower secondary distinction appears in corrective communication. All three arms delivered an ordinary supported update in the **33 predeclared recovery inputs**. P2 also received complete corrective-communication credit in **33/33**. B3 and P1 each had **26 FALSE and 7 UNKNOWN** for that endpoint. UNKNOWN is preserved. This supports a specific protocol/template-level observation about explicit withdrawal of earlier information; it does not demonstrate better human understanding or general superiority.

[Frozen-method outcome results](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/outcomes.json>) · [Exact counts](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/summary.json>) · [Final technical validation](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/final-validation.json>)

## 2. Exact accounting

| Item | Final count |
|---|---:|
| Unique input configurations | 500 |
| Original executions | 1,500: 500 B3, 500 P1, 500 P2 |
| Complete paired three-arm input sets | 500 |
| Saved ledger state BACKED_UP | 1,500 |
| Unique admission notices | 1,500; no repeated original admission |
| EXPORTED/BACKED_UP transitions | 1,500 each |
| Exports after each saved observation deadline | 1,500 |
| Verified chained notices | 196,037 |
| Raw driver status COMPLETED / FAILED | 1,359 / 141 |
| Original rows with missing or zero timing values | 0 / 0 |
| New research executions, regrades or AWS calls in local analysis | 0 |

The 141 raw FAILED records remain FAILED. All 141 nevertheless have TRUE final-business-state grades; none has a supported final update recorded. Another 135 records have raw COMPLETED status but FALSE final-business-state grades. Driver completion and business/speech outcomes therefore require separate reporting. These labels are not silently reconciled or replaced.

The current study is **500 inputs × three arms**, with 300 CLEAN, 100 HIDDEN_COMMIT, 60 PLAYOUT and 40 OTHER_BOUNDARY inputs. The earlier `artifacts/phase-8-report.md` describes a historical, superseded candidate with 2,700 proposed slots; it is preserved and is not the final campaign report.

Post-deadline export notices support full-window accounting. They do not prove that every client event was observed, or that an absent acknowledgement establishes silence. The 600-second observation windows are unchanged.

## 3. Arms, units and methods

B3 is the competent baseline: durable idempotency, reconciliation before retry, revision invalidation, transaction staging, compensation and playback tracking. P1 additionally enables claim permits and orthogonal product-state invariants. P2 additionally enables durable repair of previously played content. Ordinary baseline corrective updates are creditable. These profiles remain explicit in the frozen `research/arms.py`.

The sampling/analysis unit is an **input draw**, with all three arm results paired. The frame comprises 50 fixed recipe families and synthetic contexts. It is not 1,500 independent scenarios, a random population of speakers, or a random sample of production providers. Intervals condition on the accepted fixed-frame/input-independence assumptions; shared host, time and operational interruptions limit those assumptions.

Methods are the accepted frozen pure functions: saturated arm-by-stratum marginal means; correction weights 0.5/0.3/0.2; paired exact component bounds; two co-primary comparisons with 0.025 allocated to each bound; the ten-comparison Holm diagnostic family; the 5-percentage-point clean-case tolerance; planned-denominator missingness bounds; and 20 fixed temporal-block omission summaries. Timing uses 2,000 stratified paired input bootstrap draws (seed 8042051), a right-censored lognormal arm+stratum AFT fit, and 1,000 input-cluster bootstrap fits (seed 8042052). All three arm rows stay together when an input is resampled. No new endpoint, covariate model or outcome-selected exclusion was introduced.

## 4. Business outcomes and co-primary comparisons

| Endpoint | B3 | P1 | P2 |
|---|---:|---:|---:|
| Correct final business state, all inputs | 455/500 | 455/500 | 455/500 |
| Clean task success | 300/300 | 300/300 | 300/300 |
| Correction success, all non-clean inputs | 155/200 | 155/200 | 155/200 |
| Correct supported final update recorded | 408/500 | 408/500 | 408/500 |
| Recorded forbidden effect | 0/500 | 0/500 | 0/500 |

Correction success by stratum is **73/100 HIDDEN_COMMIT**, **56/60 PLAYOUT**, and **26/40 OTHER_BOUNDARY**, identically for each arm. Equal observed outcomes are not proof of universal equivalence.

| Prespecified P2−B3 quantity | Estimate | Frozen uncertainty output |
|---|---:|---|
| Weighted correction-success difference | 0.00 percentage points | Conservative 97.5% interval: −8.79 to +8.79 pp |
| Unsupported exposed claims in HIDDEN_COMMIT | 0/100 in each arm; difference 0 | Conservative 97.5% difference interval: −4.95 to +4.95 pp |
| Clean-task success difference | 0.00 pp | One-sided 95% lower bound: −1.22 pp, above accepted −5 pp tolerance |

All primary pairs are known. The clean criterion is met under the frozen descriptive/conditional rule. The structured outputs retain their original `confirmatory_claim_permitted: false` and draft-conclusion fields; this closeout does not rewrite those flags into a blanket inferential endorsement. Every temporal-block omission estimate for the primary correction difference is zero. This does not establish stationarity for other endpoints or timing.

## 5. Corrective communication and the P1/P2 ablation

| Endpoint within the 33 designated recovery inputs | B3: TRUE / FALSE / UNKNOWN | P1 | P2 |
|---|---:|---:|---:|
| Supported corrected update after challenge | 33 / 0 / 0 | 33 / 0 / 0 | 33 / 0 / 0 |
| Complete corrective communication | 0 / 26 / 7 | 0 / 26 / 7 | 33 / 0 / 0 |

Complete corrective communication requires a supported update plus explicit withdrawal when earlier incompatible content requires it. A claim that the baseline never corrects the appointment would contradict the first row.

| Predeclared family | Inputs | B3 and P1 complete communication | P2 |
|---|---:|---|---|
| Full playback before correction | 9 | 9 FALSE each | 9 TRUE |
| Delayed decisive acknowledgement | 7 | 7 FALSE each | 7 TRUE |
| Partial decisive-time playback | 7 | 7 UNKNOWN each | 7 TRUE |
| Reconnect and another revision | 7 | 7 FALSE each | 7 TRUE |
| Restart before repair | 3 | 3 FALSE each | 3 TRUE |

For P2−B3 and P2−P1, the complete-pair diagnostic test has 26 P2-only successes, no opposite discordance, and seven missing pairs. The frozen exact McNemar diagnostic p-value is 2.9802e−8; its ten-family Holm diagnostic value is 2.9802e−7. These are **complete-pair diagnostics**, not missingness-free confirmatory claims. Over all 33 planned inputs, assigning the seven baseline UNKNOWNs every possible value gives an **empirical difference range of +78.79 to +100 pp**. This is a missingness/identification range, not a confidence interval.

P2's retained mechanism telemetry records **40 repair obligations in the 33 inputs**, all REPAIR_PLAYED, including multiple obligations after another revision. That is internal persistence/playback evidence. It alone does not prove unattended discovery, service uptime or end-to-end recovery without experiment orchestration. Existing scenario/calibration qualifications remain separate. The sampled P2 trace includes explicitly invoked repair-worker processes; it must not be described as independent proof of an always-running autonomous consumer.

The withdrawal grader recognizes the frozen prefix **“Correction: my earlier confirmation was outdated.”** on a supported, fully acknowledged update. It is arm-label neutral, but it is a fixed-template measure, not a general semantic-equivalence or human-belief test. This limitation is material to the positive secondary finding.

[Descriptive communication figure](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/presentation/corrective-communication.svg>) · [Every endpoint count](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/presentation/endpoint-counts.csv>) · [Figure and descriptive data](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/presentation/descriptive-facts.json>)

## 6. Unsupported claims and UNKNOWN exposure

The hidden-commit co-primary endpoint has no observed unsupported exposed claims in any arm: 0/100 each. Across **all 500 inputs**, the original grades are:

| Unsupported exposed claim | B3 | P1 | P2 |
|---|---:|---:|---:|
| TRUE | 4 | 0 | 0 |
| FALSE | 481 | 481 | 481 |
| UNKNOWN | 15 | 19 | 19 |

All four B3 TRUEs are `version-change-before-start` PLAYOUT inputs (sequences 59, 507, 849 and 931; cases p8v4-0425, -0411, -0413 and -0424). Their corresponding P1/P2 outcomes are UNKNOWN. This is not evidence that the other arms definitively eliminated those exposures. None of these four is part of the hidden-commit co-primary denominator.

The stale-exposure endpoint has no TRUEs, but 15 UNKNOWNs in B3 and 19 each in P1/P2. Earlier content can become outdated after a later accepted request even if it was not stale at its original playback time. Explicit corrective withdrawal and prevention of an already-stale playback are different endpoints.

## 7. Timing: computed, with restricted interpretation

There are 1,224 supported-completion events and 276 right-censored arm records. The frozen paired timing helper reports no missing input pairs and uses the 600-second horizon. Its intervals are conditional on independent input draws.

| Comparison | Restricted mean difference, seconds | Conditional paired bootstrap 95% interval |
|---|---:|---:|
| P2−B3 | +0.2593 | +0.2241 to +0.2996 |
| P1−B3 | +0.2251 | +0.2041 to +0.2472 |
| P2−P1 | +0.0342 | +0.000073 to +0.07192 |

Positive differences mean a longer recorded time. This is time to a supported **scripted-ACK completion**, not measured human call latency or time to corrected user belief. It is not the same endpoint as full corrective communication.

The lognormal AFT fit converged on all 1,500 positive timing rows. All **1,000/1,000** input-cluster bootstrap fits converged; failed fits were not dropped (none occurred). Conditional time ratios against B3 are P1 **1.2258** (bootstrap interval 1.2044–1.2451) and P2 **1.2265** (1.2034–1.2506). The lognormal form and independent censoring are unproven; the fit's `claim_permitted` remains false.

Raw timing labels retain four INFRASTRUCTURE_FAILURE entries at sequences **1, 2, 145 and 616**. The separate timing view reuses only the previously accepted first/second sidecars, changing their historical labels to NO_SUPPORTED_COMPLETION without changing any numeric duration or outcome. Two raw infrastructure labels therefore remain in that view (145 and 616). No new sidecar, retrospective timing correction or regrading was applied. These labels do not establish independent administrative censoring. All timing/model results must retain this qualification; their computation does not resolve the scientific assumption.

[Full latency output](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/latency.json>) · [AFT fit](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/aft.json>) · [All bootstrap results](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/aft-bootstrap.json>)

## 8. Verified trace examples, without new downloads

Three exact original exports were reused from the already verified local final master. Each matches both its master-manifest commitment and its original export SHA-256. Their backup versions and archive hashes are indexed in [example provenance](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/examples/verification.json>).

- **Successful corrective delivery: sequence 82, P2, p8v4-0401.** Another accepted revision arrives during repair and a delayed old completion is retained. The trace ends with a correct final state, a supported corrected update, explicit withdrawal, and two REPAIR_PLAYED obligations. [Original trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/examples/0082-P2.export.json>).
- **Expected fault outcome: sequence 59, B3, p8v4-0425.** The provider resource changes before playback. The grade records truth at publication/playback as TRUE but evidence at playback as FALSE. The unsupported-claim endpoint is TRUE and final business state FALSE. A statement can therefore have a true appointment-time component while its evidence/version binding is invalid. [Original trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/examples/0059-B3.export.json>).
- **Appropriate refusal with an unsuccessful speech outcome: sequence 1, B3, p8v4-0484.** The saved HTTP409 wraps `b3-evidence`: current provider facts do not support speech. Raw status remains FAILED; independent final business state is TRUE; no supported final update is recorded. [Original trace](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/examples/0001-B3.export.json>).

The example-retention attempt stopped at its 8-MiB bound before a fourth trace could be retained. The three verified examples total 8,185,456 bytes. No evidence was deleted or downloaded again. Examples illustrate mechanisms; they do not select or alter the 1,500-row analysis denominator.

## 9. Evidence, source and operational provenance

Returned bundle SHA-256: `1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341` (823,115 bytes). Its four member hashes, 765 modern record commitments, exact 735-cache reuse, all identities/fixtures/archive/version bindings and explicit recovery provenance passed local verification. Recovery's one additional pinned read of1129 is retained as a separately labelled evidence read, not a research replay.

The final source package is `cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d`. All **3,450** frozen inventory entries still match after analysis. Existing authority/sidecar receipts were verified; no acceptance, freeze or launch was created during closeout. The retained frozen v12 archive is `60218b4a7b7a9ac5862b1792e28cd93e1fc2ea7b6bc163da12ef4576b6955e0b`.

The ledger retains nine admission-controller binding segments: sequences **1; 2; 3–38; 39–82; 83–120; 121–145; 146–616; 617–1297; 1298–1500**. Every result is joined to its actual admission notice, controller-run binding, saved deadline, export/backup timestamp, original export hash and pinned backup version in [the 1,500-row provenance index](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/operational-provenance.csv>). Controller binding is a historical reference, not per-process binary attestation. Earlier originals must not be described as all having run the final v12 binary. Their full original archives retain further process/source information.

The compact derivative is intentionally not a replacement for full raw traces. In modern compact rows, diagnostic fields such as `observations_count` or `collection_errors` can reflect absent top-level fields while observations exist under the snapshot. Do not interpret these defaults as proof of no provider observations or no collection gaps. Substantive endpoints retain their original independent grades.

## 10. Validation, runtime and retained failures

- Returned bundle and dataset checks: PASS; 500 complete input sets, no duplicate/replacement original.
- CSV rows match all original identity, raw-status, outcome and numeric duration values. Dataset hashes are unchanged after analysis.
- Master SQLite quick_check and all 196,037 notice hashes: PASS. Each original has one admission, post-deadline export and matching backup transition.
- Frozen source preservation: 3,450/3,450 hashes match. Historical reports, archives, raw grades, FAILED statuses and timing labels remain.
- Fixed statistical run: completed in approximately **347 seconds** on the existing local scientific environment. Python3.12.14; numpy2.3.5, scipy1.16.3, pandas2.3.3, statsmodels0.14.6, patsy1.0.2. No packages were installed.
- Reused qualification: v1's eight extractor controls; v2's eight recovery controls; v3's five package-only controls, including the actual mixed schema and complete staging roundtrip. The user-returned CloudShell run passed all five v3 controls in1.350seconds. No application/PostgreSQL/scenario suite was rerun because application behavior and database logic were not edited.
- Current adapter/verifier lint and type checks pass; visualization-library imports are treated as an isolated untyped dependency boundary. ReportLab only renders saved descriptive counts; it is not the statistical runtime.
- Failed attempts remain: the first local archive timeout/partial file; interrupted CloudShell v1 extraction; v2's demonstrated legacy-schema packaging KeyError; early adapter assumptions about direct raw-export coverage; a bounded example-retention stop; and descriptive-chart API/line-ending errors. They did not alter research outcomes. A telemetry summary also required recognizing baseline NOT_APPLICABLE schemas. Final data/analysis checks passed after corrections to helper handling. Original logs are retained.
- No migrations, application changes, new research trials, AWS compute start, evidence deletion, new historical sidecars or new grading occurred.

## 11. Supported conclusions and remaining limits

**Supported within this recorded synthetic frame:** competent B3 matched P1/P2 on final business state, clean success and primary correction success; all arms delivered ordinary recovery updates; P2 additionally produced the frozen explicit-withdrawal communication outcome in the 33 designated recovery inputs; P2 persistence/playback telemetry records40completed obligations. These are useful bounded findings, including the primary tie.

**Not established:** general superiority of P1/P2, broad equivalence, production reliability, improvement in human belief/understanding, natural speech exposure, autonomous unattended recovery from telemetry alone, correctness of every historical censor label, or external novelty/publication acceptance. The shared revision-only claim-selection limitation is unchanged. Missing playback evidence remains UNKNOWN. Operational source changes, a shared serial host, a fixed50-family frame and the exact-prefix retraction measure constrain interpretation. No result depends on relabeling an unknown as success/failure.

**Closeout verdict:** all 1,500 planned originals are accounted for and the accepted computations are complete and verified. The final dataset and findings are ready for research/manuscript review with these limitations. Confirmatory/model-assumption guard fields remain restricted. Phase9 optional transfer studies are unstarted; no extension is required merely to report the primary tie honestly.

The campaign host was last verified stopped; closeout made no AWS calls to change that state. Retained root/S3 evidence has not been deleted. Resource retention remains subject to the accepted bound (up to48hours after actual shutdown, with the separate outer decision limit28October2026 12:00UTC); this report does not authorize extending retention or deleting evidence. Billing was not refreshed and no new campaign cost figure is asserted.

## 12. Files, commands and reproduction

Main outputs: [all 1,500 original results (CSV)](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/original-results.csv>); [original analysis rows](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/dataset/analysis-rows.json>); [separate accepted timing view](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/dataset/accepted-timing-rows.json>); [retained compact records](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/dataset/recorded-results.json>); [controller history](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/analysis/operational-segments.json>); [validation record](<C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-final-analysis/v1/final-validation.json>).

Helpers created for closeout: `prepare_dataset.py` (integrity/model validation), `run_analysis.py` (exact frozen methods/settings), `verify_closeout.py` (source/ledger/CSV verification), `render_results.py` (descriptive output only), and separately versioned retrieval/recovery/packaging helpers. Their hashes are recorded in the final inventory. The earlier in-progress REPORT.md and all historical phase reports are preserved.

Commands actually executed from this workspace include:

```powershell
& '.venv-study-design/Scripts/python.exe' -B 'artifacts/phase-8-final-analysis/v1/prepare_dataset.py' --bundle 'C:/Users/syeda/Downloads/final-records.tar.gz' --sha256 '1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341'
& '.venv-study-design/Scripts/python.exe' -B 'artifacts/phase-8-final-analysis/v1/run_analysis.py' --run
& '.venv-study-design/Scripts/python.exe' -B 'artifacts/phase-8-final-analysis/v1/verify_closeout.py'
```

These preserve outputs with exclusive creation; do not rerun them into completed directories. Computational reproduction requires the pinned frozen source at E:/p8v12/source and the existing scientific environment above, and should use a separate output-directory copy. The results bundle does not claim to contain every original raw archive or a complete software runtime. The returned immutable evidence bundle and its original SHA-256 remain the input of record.
