# Independent research review handoff — 8 October 2026

**Disposition: review evidence, not a continuation approval.** Run `p85-01a116f7-3b82-7a79-8653-3aee62dc99e9` has **38 BACKED_UP, 1,462 PLANNED and zero active originals**. AWS was last verified STOPPED at 17:15:29 UTC on 8 October; no AWS query or action was made for this report. Root disk remains retained. No scenario, regrading, freeze or launch occurred.

Throughout: **D** = documented design; **I** = implementation inspected; **T** = existing retained test/execution evidence; **U** = unresolved or not verified. Historical documents saying “unstarted” or “draft” describe their creation dates; the later acceptance/freeze/deployment receipts establish the campaign's subsequent history.

## Evidence map

- [38 original executions](38-executions.csv): identities, raw status, every endpoint, recorded runner/driver versions, full-window timestamps, export hashes and pinned backup versions.
- [500 input catalogue](500-input-catalogue.csv), [counts](catalogue-summary.json): all cases, recipes, faults, phases, seeds and arm order. Input-file SHA-256: `eda9d3b10845fce6b5149ea49bcbf2370911603c7deedef5e08cc8117a96a3c1`.
- [Complete resource-only matched triple](matched-triple-0484.json): exact requests/responses, independent provider truth, ordinary observations and original analysis rows.
- [Planned repair fixture, UNEXECUTED](planned-repair-fixture-UNEXECUTED.json).
- [Offline feasibility](offline-feasibility.json), [read-only verification](read-only-verification.json).
- Raw retained snapshot: `E:/FYP Project/p8-observation-20261008-1/x/inspection/`; archive SHA-256 `257cdc762459f07c67f132ed0141021dd38430a9f5cb2040cd3479e3e7d37905`, S3 version `eal8yi_Nd_ELncozskW0Si5f5ELTr.b9`. All 93 inventoried members and 38 original export hashes were checked before and after appendix extraction. Backup verification here reuses retained pinned-version proofs; it is not a new cloud read.

## 1. Objective, hypotheses and contribution

**D:** Current guiding question: **“When do the proposed mechanisms provide additional protection beyond a competent baseline's existing checks?”** Contract RQs are in `docs/04_TEST_EVALUATION_AND_TRACEABILITY.md:87–94`: correction under ambiguity; UNKNOWN/reconcile-before-retry; revision-bound receipts; supported speech; durable playback repair; named-barrier evaluation. Optional human-belief and other extensions are outside this campaign.

Pre-result comparison rules appear in `docs/09_PHASE7_PROTOCOL.md`, `docs/12_PHASE8_CANDIDATE_V4.md` and frozen copies: P2 versus B3 on two co-primary endpoints; P1 comparisons explain mechanisms. The primary directions are more correct correction outcomes and fewer unsupported decisive exposures, subject to clean usefulness loss less than 5 percentage points. Improvement requires the prespecified uncertainty criteria, not a mechanism record or a passing test. Ties or intervals that include no benefit mean **no demonstrated incremental benefit**. Worse corrections, unsupported exposure, or failed clean tolerance indicate harm; added latency, unresolved outcomes and costs must also be disclosed.

**I:** Revision/resource-bound speech permits and PostgreSQL repair discovery are implemented. **T:** Selected local mechanism traces and tests support those boundaries. The first 12 complete main triples tie; no main superiority result exists. **U:** General superiority, novelty priority, human-confusion reduction and publication acceptance are not verified. “FYP” is established; intended degree level, institutional thesis rubric, required publication venue and supervisor acceptance criteria are **not verified**.

### Closest literature and precise overlap

Primary records rechecked on 8 October; these five are **verified preprints**, not verified peer-reviewed publications. Full-text novelty exclusion was not performed for this handoff. The earlier source-grounded comparison and verification-depth notes are in `output/pdf/research-proposal-v1/research-proposal.md` and `bibliography.md`.

| Verified work | Existing overlap | FYP's additional question; not an established omission in that work |
|---|---|---|
| [Revisable by Design](https://arxiv.org/abs/2604.23283v1) | Revision/reversibility and preserving work under changed instructions | Applicable authority for a statement after an uncertain external commit |
| [REVISE](https://arxiv.org/abs/2609.00643v1) | Invalid-work recovery, provenance and revalidation before commit | Current evidence at publication/playback and responsibility after an exposed old statement |
| [Atomix](https://arxiv.org/abs/2602.14849v2) | Transactional staging and compensation | Independently scored business, supported speech and corrective-delivery outcomes |
| [PACE](https://arxiv.org/abs/2608.07631v1) | Generated-versus-played context and playback alignment | Persisted correction tied to revision and business-resource evidence |
| [Tool Receipts](https://arxiv.org/abs/2603.10060v1) | Trace-grounded validation of tool assertions | Expiring revision/resource authority plus playback-relative recovery |

The defensible current contribution is an inspectable protocol implementation and controlled comparative instrument joining these boundaries. Its incremental scientific benefit remains a hypothesis. Remaining bibliography entries retain the earlier report's verification status; their full-text scope and peer-review status are not reverified here. Private faculty/discussion references in the supplied background are **not verified** and cannot establish novelty. Absence from an abstract does not prove absence from a paper.

## 2. What actually runs

**D/I:** A typed accepted intent becomes a durable `intent_revisions` row and current workflow revision. `apps/api_controller/phase2_service.py` stages an operation; `apps/durable_worker/phase2.py` dispatches with a stable request/idempotency identity. Lost acknowledgement leaves effect knowledge UNKNOWN. Reconciliation consults ordinary provider operation/resource reads before another write or compensation. Verification (`phase3_verification_service.issue_verification`, `_evaluate`) records raw observations and a three-valued, revision-bound receipt. P1/P2 `phase3_claim_service.authorize` requires an applicable SATISFIED receipt and renders fixed text; audio release and STARTED perform further checks. B3 evaluates the same relevant facts through `_b3_text`, without a permit object. Playback events persist; P2 persists an incompatible-played-span repair and its worker discovers and delivers it after restart.

| Durable store | Actual ownership |
|---|---|
| Application PostgreSQL | `workflows`, `intent_revisions`, `operations`, `operation_attempts`, `effect_ledger`, `reconciliation_jobs`, `verification_receipts`, `evidence_items`, `claims`, `claim_permits`, `audio_segments`, `playback_events`, `repair_obligations`; migrations add research observations/ACKs and repair leases |
| Separate simulator PostgreSQL | Provider appointments/idempotency state and append-only truth commits; oracle access is distinct from application reads |
| SQLite | Master campaign slots/notices and collector checkpoints: research orchestration/evidence metadata, **not business truth** |
| Redis | Dedicated companion-cache control; no correctness fact depends solely on it; the tested flush is not an application-consumed Redis outage |

**T:** Main exports show typed scripted inputs, real provider/database actions and synthetic client ACKs. **No live LLM, microphone recognition or native-audio service runs in the main study.** Media is `SCRIPTED_TONE_PROTOCOL_PROXY`; speech uses fixed templates and `deterministic-tone-tts-v1` (`apps/voice_worker/cascade.py`). Word metadata is a proxy, not independently measured phonetic alignment.

**I, separate application path:** `offline_adapters.py` implements Vosk `vosk-model-small-en-us-0.15`, local `qwen2.5-0.5b-instruct-q4_k_m`, prompt `phase5-local-intent-v2`, temperature 0, max 120 tokens, and `espeak-ng-en-us` at 155 words/minute, PCM16/16 kHz. These are outside the 500-input execution path. **U:** Those live models' active deployment, exact current eSpeak binary version, and real-call performance in this campaign are not verified. Gemini/native audio remains an optional adapter, not evidence for this strict research arm.

## 3. B3 versus P1 versus P2

**I:** `research/arms.py:PROFILES`, `phase6_b3_audio.py`, `phase4_audio_service.py`, `phase4_playback_service.py` and `apps/durable_worker/repair.py` implement the distinctions:

| Capability | B3 | P1 | P2 |
|---|---|---|---|
| Durable idempotency, reconcile-before-retry | Yes | Yes | Yes |
| Revision invalidation, staging, compensation | Yes | Yes | Yes |
| Current provider verification for outcome wording | Yes, ordinary observations | Yes, receipt | Yes, receipt |
| Persisted playback/old-segment rejection | Yes | Yes | Yes |
| Explicit receipt/claim/content binding, permit and product-state rules | No | Yes | Yes |
| Resource/evidence revalidation at permitted release/STARTED | Ordinary synthesis/staging verification and revision STARTED check | Permit freshness plus evidence | Same as P1 |
| Durable played-span repair discovery/completion | No | No | Yes |
| Supported ordinary corrected statement | Yes | Yes | Yes, plus explicit repair wording when applicable |

B3 retains current revisions, operation/effect/reconciliation work, generated/published segments and ACK history across process crashes. It does **not** retain a P2 repair-obligation queue. `research/remedies/runner.py:recover` gives it an ordinary response opportunity from the current PRESENT operation. P1 adds speech authority but no P2 repair capability. P2's `repair.discover` uses PostgreSQL leases/`SKIP LOCKED`; completion requires current-revision completed playback, not merely obligation creation.

**D/T fairness:** Same input, empty initial state, fresh isolated property/workflow/provider databases, same simulator faults, host allocation and 600-second horizon; random saved arm order; no model/prompt variability in these executions. Qualification preserved B3 ordinary safeguards. **Known differences beyond the permit boolean:** P1/P2 use more verification/authorization requests and repair text has extra words; P2 recovery can be discovered by a native consumer, while B3/P1 ordinary update opportunities are supplied by the scripted responder. Recovery process opportunities are therefore not an identical unattended production responder comparison. ACK completion times incorporate template duration. Single held-response “reorder” and unused-cache flush have the limited scopes described above. **U:** No proof of unrestricted parallel isolation, real caller parity, or population generalization; main schedule is serial.

## 4. Guarantees and assumptions

**I:** `packages/domain/phase3_verification.py:receipt_applicable` requires SATISFIED, matching claim type/current intent revision, non-invalidated receipt, validity interval and matching observed resource version. `phase3_claim_service._check_receipt` additionally checks workflow, permit expiry, predicates/content/template. `phase4_audio_service.check_fresh` and playback STARTED recheck fresh observations. Accepted revision invalidates older authorities and stops obsolete queued/published segments. Late PROGRESS/COMPLETED creates repair only for repair-capable P2; delayed/duplicate ACK safety was addressed in the revised instrument.

UNKNOWN is distinct from VIOLATED or proven absence. Stable provider idempotency and reconciliation avoid a blind new write after timeout. Current resource visibility alone cannot certify a historical reschedule effect; unavailable status can cause honest refusal even when the final resource is right. Retry limits are **eight reconciliation attempts**, **30 drain passes**, not seconds.

**T:** PostgreSQL tests include `test_unavailable_provider_handoffs_unknown_without_retry`, `test_delayed_visibility_reconciles_unknown_without_duplicate_write`, `test_reused_effect_requires_fresh_receipt_and_is_invalidated_by_later_change`, and `test_readiness_v2_postgres.test_late_ack_capability_duplicate_and_reordering`. Prior qualification records, not new executions, are cited.

Exposure means accepted client telemetry reaches decisive semantic content according to the fixed word timeline. “Your maintenance” alone is not decisive; reaching confirmation/time predicates is. Delivered correction needs a supported final statement with accepted full COMPLETED telemetry. Retraction additionally needs recognized withdrawal wording after incompatible content. **U/limits:** These are protocol proxies, not hearing or comprehension. Safety relies on truthful provider authoritative reads/idempotency, clock/order assumptions and honest ACKs. A check followed by later provider change cannot retroactively prevent already played content. Repair needs execution opportunity, applicable evidence and reconnection before the horizon; bounded retries/deadlines can leave escalation or UNKNOWN. No unconditional exactly-once external-effect or eventual-human-delivery theorem is established.

## 5. Frozen 500 inputs

**D/I:** `research/study_v4/design.py` seed **8042041**, 50 fixed recipes, independent conditional context draws, 500 distinct generated requests. Ten clean recipes contribute 300 inputs; twenty hidden-commit recipes contribute 100; ten playout recipes 60; ten other-boundary recipes 40. Recipe counts and nonexclusive fault memberships are in the appendices; 66 DROP_RESPONSE-after-commit, 41 held REORDER-after-commit, 4 duplicate-before-commit, 5 precommit-5xx, 3 partial-effect and 5 precommit-delay memberships include boundary overlaps and are not a disjoint allocation.

| Target | Planned inputs, not demonstrated main outcomes |
|---|---:|
| Direct old-claim/evidence release attempt (`verified-stale-attempt`) | 8 |
| Resource version change before STARTED | 4 |
| Queued/buffered old segment release/start checks | 6 + 5 |
| Playout stratum, including before-decisive control | 60, including 4 introductory controls |
| Fixed recovery-challenge denominator | 33 |
| Full-before-correction / partial-time / late decisive ACK | 9 / 7 / 7 |
| Persisted correction followed by worker restart | 3 |
| Logical disconnect/reconnect, missing ACK, another revision | 7 |

All 200 correction inputs exercise changed instructions; all P1/P2 updates use their authority chain, but those 200 are not 200 isolated permit experiments. The 33 recovery cases test supported corrective delivery; only ten explicitly target restart/disconnect. These counts overlap other targets.

Named provider/playout barriers establish causal placement. An arm preventing exposure still stays in the predeclared challenge denominator; do not drop it or force unsafe exposure to make arms resemble each other. Failed hook preconditions must be reported, not relabelled as successful fault activation. `calibration.Driver.run` and `qualification.py` retain actual effects and causal evidence.

Order seed **8042043**, twenty fixed blocks of 25 inputs, saved in `execution-order.json` and the 1,500-identity schedule. Arm order was drawn and saved per input. Original attempt is always 1; no replacement. Dedicated services/databases/resources and scoped collection isolate each serial slot. Real wall-clock **600 seconds after the final externally scripted request**, not simulated time; interrupted collection resumes the same deadline without replay. Raw late evidence is retained, but oracle grading is capped to the administrative horizon. **T:** All 38 collected windows completed. **U:** Recovery outcomes for the unstarted inputs remain unobserved.

## 6. Independent oracle

**I:** `research/study/oracle.py:business`, `evaluate`, `validate_records`; `research/oracle/readiness_v2.py:grade_observable`, `support`; `research/study_v4/oracle.py:delivery`, `administrative_cap`, `revised_evaluate`.

| Endpoint | Definition and planned denominator per arm |
|---|---|
| Correction success, co-primary | Correct single final appointment matching external final intent, with no forbidden effects; 200 correction inputs, stratum weights .5/.3/.2 |
| Unsupported decisive exposure, co-primary | Recorded decisive claim with FALSE truth/evidence at release/play; UNKNOWN support remains UNKNOWN rather than counted safe or automatically counted false; 100 hidden-commit inputs |
| Business correctness / forbidden effects | Independent final state / duplicate operation effects, duplicate creates, wrong resource or unrequested action/time; all 500 |
| Correct final update | Supported correct final statement with full accepted playback; applicable inputs, reported separately from business state |
| Stale exposure | Decisive incompatible content relative to the intent accepted at playback; adverse telemetry survives other missing evidence |
| Explicit retraction | Recognized withdrawal after previously exposed incompatible content; conditional denominator, otherwise N/A |
| Corrective delivery / complete corrective communication | Supported delivered final update after scheduled recovery challenge / update plus withdrawal when required; fixed 33-input denominator |
| Clean usefulness | Correct business state, no forbidden effect and supported completed update; 300 clean inputs |

Truth comes from separate simulator append-only commits; available observations from raw provider journals; script/accepted-revision anchors and client telemetry supply timing. Receipt verdicts, permit IDs and internal repair state **do not determine observable scores**. `support` checks authoritative resource version and 30-second observation applicability; “has been moved” also requires operation evidence. Persisted/discovered/retried/played obligations are separate mechanism telemetry.

An ordinary supported B3 correction gets equal update/delivery credit: `delivery` reads observable claims/COMPLETED events, not arm names. Tests `test_label_and_internal_representation_do_not_change_outcomes`, `test_external_equivalence_not_arm_label`, and `test_ordinary_update_delivery_is_label_invariant` enforce that separation. Bad-outcome/missingness controls include explicit retraction versus ordinary update, unsupported true claim without observations, missing completion, malformed evidence, decisive versus introductory exposure, and stale ACKs.

**U:** “Truthful uncertainty” and safe-resolution/handoff are contract concepts but **not separately identifiable endpoint fields in these retained main analysis rows**. Refusal does not earn booking/update credit. Cancellation reporting is not demonstrated by this booking/reschedule campaign. Do not silently substitute communication completion for truthful uncertainty or claim full coverage of every original research deliverable. Missing observations/ACKs/anchors/incomplete windows give UNKNOWN; lack of ACK is not proof of silence, and obligation state is not proof of delivery.

## 7. Frozen analysis and amendments

**D/T:** Original package freeze verified **7 October 2026, 14:02:59.106188 UTC**, before original admission. `artifacts/phase-8-freeze/v1/freeze-verification.json` records package `c76fc54018ce6b9e9f77eeb2946cea253271ad4a8573f8fe047961d7b6f6dc6b`; freeze receipt `0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2`. Analysis is in its frozen source (`research/study_v4/analysis.py`, execution timing/statistical modules), with accepted continuation provenance below. This is a local timestamped freeze, not verified registration in a public registry.

P2−B3 is primary; Bonferroni .025 per co-primary bound. Correction uses saturated arm×eligible-stratum marginal cell means and simultaneous component binomial bounds, standardized .5/.3/.2; hidden exposure uses paired win/loss bounds. P1−B3/P2−P1 and two delivery outcomes form ten secondary diagnostic comparisons with Holm. Structural N/A is excluded appropriately; missing data stays in planned denominators via best/worst paired bounds. No confirmatory complete-case noninferiority if missingness undermines it. Clean margin 5pp, n=300; design power about 80.39% assumes equal risks and 5% discordance, not estimated from this prefix.

Input draw is the dependence/resampling unit; all arms remain paired. Recipe labels and legacy `member`/`cluster_representative` fields are not independently sampled clusters. No repeats increase n. Stratified paired input bootstrap (2,000 draws, seed 8042051) estimates capped 600-second supported-ACK latency; identifiable censored lognormal AFT uses input-cluster bootstrap (1,000, seed 8042052). Fixed time-block omission/order diagnostics address shared-host dependence without asserting independent blocks. `v3/instrument.py:analysis` wires these into authorized analysis; older draft `outcome_report` flags remain historical safeguards, not final campaign status.

**U:** No accepted universal maximum latency increase or per-task cost-effectiveness threshold was found; report effects/intervals and operational costs, not an invented acceptable cutoff. Recovery n=33 is imprecise (design illustration ±10.8pp at 10% discordance); restart n=3 cannot substantiate broad unattended advantage. 100 hidden-commit inputs cannot establish zero population risk from zero events. Synthetic draws do not estimate real callers or speech distributions.

**Post-view changes, explicitly separated:** Earlier audits revised arm-dependent grading and decisive-exposure measurement before main freeze. Descriptive-only timing was superseded by clustered latency/AFT during prelaunch setup. After first B3/P1 failures, accepted v1/v3 refusal handling preserved raw FAILED/grades but added separately traceable NO_SUPPORTED_COMPLETION administrative-censor sidecars (`artifacts/phase-8-runner-amendment/v3/first-original-proposed-sidecar.json` and `second-original-proposed-sidecar.json`, accepted despite their historical filenames). Main P2 expected refusal retains raw FAILED with revised instrument classification. V3 permissive-response guard prevents later success masking unexpected errors. V4 changes only watchdog consistency; no endpoint/analysis change. These boundaries must appear in the final methods and timing sensitivity; historical outcomes must never be overwritten.

## 8. Preserved 38 executions

**T:** 13 inputs started; 12 complete triples; one extra clean input has only P1/P2, and its B3 is next untouched. **38 correct business states; 35 correct final updates; zero recorded unsupported or stale exposures.** Unequal arm n is B3=12, P1=13, P2=13; aggregate rates must not rank arms. In the 12 triples every endpoint agrees: business 12/12, update 11/12, exposure 0/12 per arm; nine matched clean inputs pass usefulness. Retraction and all three corrective-delivery fields are N/A across the prefix.

### Decisive example: `p8v4-0484`, all three original attempts

Provider commits CREATE, response is lost, revision 2 requests 12:00–12:45 Australia/Sydney on 20 August 2037, reconciliation/correction completes one RESCHEDULE. Independent truth says CONFIRMED, version 1, 02:00–02:45 UTC. Resource observation returns authoritative PRESENT at that corrected time. Operation observations return **501: `{"detail":"Operation status lookup is absent"}`**. A current resource proves current state but not the historical “moved” predicate.

| Arm / original | First speech-blocking check and retained result |
|---|---|
| B3 / seq1 `01a11705-11f0-79f1-9293-78f7f8207f70` | POST `/internal/phase6/b3/schedule`, expected revision 2; outer `voice-command-rejected` 409 contains inner `b3-evidence`, “Current provider facts do not support speech”, retryable false. `_b3_text` (`phase6_b3_audio.py:46–67`) rejects non-SATISFIED evaluation before synthesis |
| P1 / seq2 `01a11705-11f0-7826-bd9d-9066d82c4452` | Verification creates revision-2 RESCHEDULED_APPOINTMENT receipt **UNKNOWN**, observed version “1”; POST `/internal/phase3/claims` returns `receipt-not-applicable`, 409, “A current SATISFIED receipt is required”, retryable false |
| P2 / seq3 `01a11705-11f0-7a68-8c68-4da5c8126c84` | Same UNKNOWN receipt/check; backend trace `654e4b39-f115-4aed-a432-7a88108e22e8`; accepted v3 records EXPECTED_EVIDENCE_REFUSAL without retry |

P1/P2 block in `phase3_claim_service.authorize`/`receipt_applicable`. P2 receipt `d259770a-fddc-4396-953a-e4742bc3a13c` was created 07:34:37 UTC on 8 October, before the refusal. Exact P1 receipt ID, HTTP bodies and timestamps are preserved in the triple appendix; the original row is not rewritten.

**Communication evidence:** all three exports contain **zero outcome segments and zero client playback records**. Thus no final confirmation was delivered; there is no recorded spoken uncertainty statement either. This is recorded protocol behavior, not proof of physical silence. Independent business state TRUE, correction TRUE, final update FALSE; recorded adverse exposure FALSE after full collection. Each has raw FAILED. First two original INFRASTRUCTURE_FAILURE timing rows remain intact; accepted sidecars provide the distinct corrected administrative censor. All three windows completed; retained failures are not replaced.

**Unexecuted repair example:** `p8v4-0438`, `restart-before-repair`, in the appendix. Script completes old playback, accepts correction, persists or ablates repair, restarts worker; P2 waits up to 40 seconds for native discovery/publication, B3/P1 get ordinary response opportunities; all then collect the full 600-second window. This main fixture has **not run**. There is no observed main crash-repair comparison in the 38 prefix.

## 9. Watchdog incident and v4

**T:** At 13:46:02 UTC on 8 October, watchdog reported `LEDGER_TRANSITION_DRIFT` near seq38 backup. Runner completed its verified backup/retirement, then paused; seq39 never admitted. Current consistent snapshot has SQLite integrity `ok`, valid notice hash chain and zero transition mismatches. Frozen v3 `Journal.verify` read notices and slots in separate snapshots: a valid atomic writer could commit between those SELECTs. The deployed master is **SQLite, journal_mode DELETE**, separate from application PostgreSQL.

**I:** Candidate `artifacts/phase-8-runner-amendment/v4/controls.py` adds exactly:

```diff
 with self.connect() as db:
+    db.execute("BEGIN")
     if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
```

The explicit read transaction makes integrity/chain/slot comparison consistent. No exception swallowing, writer rule, classifier or admission limit changed. Context manager alone does not start this legacy read transaction; see [Python SQLite documentation](https://docs.python.org/3.12/library/sqlite3.html#how-to-use-the-connection-context-manager) and [SQLite isolation](https://www.sqlite.org/isolation.html).

**T:** Fifteen distinct controls, named query barriers, two real connections: two reproduce legacy false drift; WAL snapshot and actual DELETE locking controls pass; genuine state/deadline/backup/notice/missing-notice/physical corruption is rejected; uncommitted writes are excluded; later committed corruption is caught on next verification; disposable master copy retains all identities/38 export hashes. Final 15 passed in 1.33s, lint/format/strict typing PASS, total 16.75s. Local runtime Python 3.12.14, SQLite 3.53.1. Failed LF/CRLF assembly and an initial typing-command failure remain retained; both test invocations had 15 passing tests, not 30 independent controls.

**Limits:** Exact historical reader interleaving was not captured. Tests reproduce the vulnerability and a matching cause, not historical memory. Linux deployment used Python 3.12.13; integrated Linux amendment, its SQLite/dependency versions, writer contention/timeout interaction and full packaged recovery are **not verified**. Hash-preservation evidence establishes unchanged originals, not a proof the entire instrument is defect-free. Existing oracle grades have no identified dependency on this master-reader false alarm.

Version boundary: accepted v3 package `2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736`, archive `0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf`, freeze manifest `49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86`. V4 local candidate `c6023e2591375b377c49a4a2a13b797dba0a673deabce3b08d6e42414c48f8c6`, archive `241d4a53d3673d01d7d1d70a723d85ff98293275b0c10d836ec493c0add801d9`; controls SHA changes `2adc2595…` → `0b62290a…` (full hashes in v4 report). V4 is **not an integrated frozen deployable package**. The only candidate runtime delta is BEGIN; any future assembly/host/dependency/handover changes need explicit provenance rather than an assertion that absolutely nothing else changed. Both earlier original attempts already have separate runner/timing provenance.

## 10. Feasibility and concrete remaining decisions

**Existing measurements / offline projection at 8 October 18:46 UTC (23:46 PKT):**

| Quantity | Evidence-based value and limit |
|---|---|
| Remaining observation minimum | 1,462 × 600s = **243.67 hours**, before setup/backups |
| Observed cadence | 35 continued start-to-start intervals: mean **619.386s**, median 619.260s; prefix is clean-heavy |
| Remaining at that cadence | **251.54h**, approximately 10.48 days; immediate-start projection 19 October 06:18 UTC, **81.10h** before deadline |
| Conservative projected guard accounting | **US$49.25**, including original elapsed clock, prior documented cost allowances, 48h disk retention, 30-GiB S3 allowance, US$5 transfer/request allowance and US$1.25 handover reserve; less than US$55/US$65, conditional on cadence and no additional unaccounted resources |
| Cost-limited latest start under that projection | Approximately **10 October 10:14 UTC / 15:14 PKT**; this is arithmetic, not launch authority or a guaranteed safe-start date |
| Spending to date | **Actual billed campaign total not verified.** Deployment records prior compute/IP estimate US$0.1417 and prior/retained disk upper estimate US$0.3759. New host ran about 10.16h (~US$1.27 compute/IP), plus disk/versioned evidence; these partial estimates are not a reconciled project bill |
| Last credit read | US$119.08, FREE/ACTIVE, 8 October deployment; not refreshed and not a budget increase |
| Retained root | 160-GiB gp3 at recorded US$0.096/GiB-month; ~**US$0.505/day**, ~US$1.01 per 48h using policy's 730h convention; keep/remove decision due **10 October 22:14:53 PKT** |
| Evidence growth | Retained per-slot compressed backup mean 1.940MB, max 2.479MB; remaining ~2.84GB at prefix mean, excluding duplicate versions/diagnostics. 30-GiB cloud cap remains; old all-version preprovision measurement 202.6MB is not current occupancy |
| Resources | Prelaunch available RAM 6.86GiB, free disk 149.41GiB. Last slot start ~6.65GiB available and ~148.5GiB free. Per-slot DB/WAL/log/audio sizes are in exports; these samples are not peak resource certification |

Recorded prices: compute US$0.1197/h + IPv4 US$0.005/h; Sydney S3 US$0.025/GiB-month. No new price/billing query was made. Slower recovery, new preparation, failed transfers, retained disks, versioned backups and billing lag can consume the margin. Policy's cost estimate deliberately charges original elapsed time including downtime; real billing differs. Actual resumption must recompute both feasibility and enforceable guards without clock/limit reset. Absolute deadline remains **22 October 2026 15:24:23.810674 UTC / 20:24:23.810674 PKT**; last admission is at least 30 minutes earlier.

### Remaining review table

| Issue | Available evidence | Missing evidence / concrete decision | Affects |
|---|---|---|---|
| Consistent watchdog read | One-line v4, 15 local PASS controls, DELETE master verified | Complete versioned Linux integration and focused runtime/dependency verification | Resumption |
| Exact 38-prefix handover | All original IDs/grades/export hashes and 38 pinned backups; next seq39 B3 `01a11705-11f0-73c0-af15-dd9f1d590b08` | Verified integrated import of 38 BACKED_UP + 1,462 PLANNED; preserve sidecars/history; reject active/altered/incomplete import | Resumption, analysis |
| New authority/provenance | Prior accepted chain and local v4 candidate | Review concrete integrated inventory, accept/freeze exact version, then separate launch authorization and readiness gates | Resumption |
| Billing/time/storage | Recorded prices, prefix cadence, offline estimate, original absolute clock | Current authorized price/credit/cost/resource reconciliation before any launch; root disposition by stated retention deadline | Resumption |
| Comparative delivery | 33 planned challenges; native P2 discovery and ordinary baseline opportunities | Main recovery results; no production-equivalent unattended baseline comparison | Analysis, publication |
| Outcome/timing amendments | Raw failures unchanged; accepted separate sidecars and exact v3 classifications | Explicit final-methods amendment history and timing sensitivity; uncertainty/handoff/cancellation coverage limits | Analysis, publication |
| Speech and human claims | Scripted tone/ACK evidence with semantic controls | Actual intelligible playback/alignment/speaker evidence is not verified; outside accepted campaign scope | Publication |
| Novelty/thesis fit | Verified overlapping preprints and protocol implementation | Full-text priority analysis, institution/supervisor/degree requirements not verified | Publication |

**Review verdict:** sufficient retained evidence for an independent review of the design, implemented mechanisms, early ties and reproduced watchdog vulnerability. **Not ready to resume from the local v4 patch alone.** No research superiority, real-speech effectiveness or error-free campaign claim is supported. Keep AWS stopped while the concrete integration, handover, review/freeze and time/cost gates remain unresolved.
