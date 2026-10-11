# Phase 8.4 — concrete final campaign candidate v2

**Status: ready for acceptance review after the linked verification record passes.
Not accepted, not frozen, not authorized to launch. Phase 8.5 remains unstarted.**

The exact source archive is `campaign-source.tar.gz`; `bundle-receipt.json` gives
its SHA-256 and the review inventory fingerprint. `review-inventory.json` lists
every source file and separate executable, configuration, fixture, oracle and
analysis inventories. These are candidate fingerprints, not a freeze receipt.
`final-verification.json` verifies this concrete archive and historical evidence.

## Scope and exact schedule

500 unchanged new v4 inputs, B3/P1/P2 paired within each input, **1,500 original
executions**. `schedule.json` and `schedule.csv` are byte-identical copies of v1's
saved serial queue: seed 8042043; 20 blocks of 25 inputs; each input's saved arm
order. Allocation stays 300 CLEAN, 100 HIDDEN_COMMIT, 60 PLAYOUT and 40
OTHER_BOUNDARY. No pilot or control calibration counts toward 500.

Every original has attempt 1. After a valid accepted freeze and separate launch
capability, initialization reserves a UUIDv7 for each slot and seals its input,
fixture hash, arm, attempt, execution identity and queue sequence in the master
ledger. No main identities have been allocated by this work. Main initialization,
admission and workers check the three chained owner-signed receipts and source
closure. A calibration capability cannot authorize a main input. The old
calibration-only candidate entrypoints retain their guards.

No main executions overlap. The 8.3 qualification covers only three narrow
same-arm restart/cache pairs. There are zero eligible adjacent pairs in this saved
main order, and paired peak CPU was 97.03%. Parallel range downloads are transport,
not parallel research executions. Different input IDs do not establish isolation.

## Observation and outcome rules

Collect until the actual externally issued final request **plus 600 seconds**,
including returns, refusals and driver failures. Issuance is checkpointed before
HTTP; accepted-revision time is separate. The final snapshot must start at or
after the original cutoff. Keep raw later observations alongside capped outcome
evidence. A durable receipt arriving after cutoff is not backdated into success.

If the final anchor is missing, preserve that missingness and collect a fallback
600 seconds from the last recorded issuance, or execution start. This is not an
invented final-request anchor. Gaps and missing playback remain UNKNOWN where
required. A >10-second poll-start gap warns; >30 seconds or backward time stops
future admissions. Original failures, timeouts, missing records and unresolved
repair remain in the planned denominator. Diagnostic reruns would be separately
identified and excluded; this package does not schedule any.

Keep final business state, claim truth/evidence at publication/playback, incompatible
exposure, correct final update, explicit withdrawal and durable repair persistence,
discovery/completion separate. Supported ordinary B3 updates receive equal delivery
credit. All 24 saved pilot grades and analysis rows replay identically through the
new metadata adapter. No winning arm or novelty claim follows from passing controls.

The unchanged co-primary endpoints, weighting, Bonferroni allocation, 300-input
clean-case 5-percentage-point tolerance, secondary Holm family and 33 fixed delivery
challenges remain defined by v4. Accept the already proposed timing compatibility
amendment: paired input-cluster bootstrap (2,000 draws, seed 8042051), censored
lognormal AFT `1 + C(arm) + C(stratum)` and 1,000 input-cluster draws (8042052).
Retain fit failures and 20-block omission sensitivity. All three arm rows stay
together. Missing anchors/gaps are not ordinary administrative censoring. The new
read-only analysis controller binds exports to originals and emits explicit UNKNOWN
rows for missing/oracle-failed originals instead of dropping them.

**Unit correction:** reconciliation is bounded by **eight attempts**, confirmed in
`database/001_initial_schema.sql` and the worker's `attempt_count >= max_attempts`
check. Drain is bounded by **30 passes**, confirmed by `range(30)` in the recipe
runner. Neither is seconds. Preserve HTTP provider 30s, scheduler 15s, driver 40s,
barrier 120s, operation lease 180s, repair lease 30s, permit TTL 30s and recovery
watch 40s. Historical v1 prose remains unchanged and is superseded on these units.

## Implemented operational controls — proposals pending acceptance

| Control | Implementation and consequence |
|---|---|
| Host maximum | Absolute launch-bound 360h deadline, persisted same-boot monotonic anchor, independent systemd calendar timer and `OnBootSec=360h`. Clock rollback stops admissions; reboot is unqualified. Active observation may be interrupted at the hard limit and remains recorded. |
| Admission cutoff | No new original in the final 30 minutes. Pauses never reset the clock. This tail allowance cannot guarantee every faulted slot finishes before shutdown. |
| Estimated committed cost | Refuse admission at projected US$55, including 30 minutes more running, 48h stopped-disk retention, a full first storage month and US$5 allowance. Rates and policy are signed; no automatic budget increase. |
| Proposed budget | US$65 incremental ceiling. This is not an instantaneous AWS billing lock; alerts/credit reporting may lag. Taxes and unrelated resources are excluded. |
| RAM and disk | Admission requires 2 GiB available RAM and 20 GiB actual free across working, backup and Docker/system paths. Active pressure below 1 GiB or 10 GiB records a stop notice while collecting where possible. |
| Capacity reservation | Add a conservative 1 GiB next-slot reserve to each 50 GiB working/backup allowance and actual disk admission check. This is an operational reservation, not a measured maximum for every recipe. Exceeding it stops admission. |
| Cloud evidence | Dedicated Sydney bucket/run prefix, versioning required; all retained object versions plus outstanding PUT reservations count toward 30 GiB. Single PUTs only, <5 GiB each; larger archives stop for review. |
| Backup | Each slot needs verified members, gzip trailer, immutable archive receipt, master/slot SQLite snapshots, raw evidence and both real PG dumps, plus a pinned checksum/size/version cloud receipt before the next slot. |
| Ambiguous PUT | Preserve reservation, archive and failure. No repeated/new PUT while unresolved. Explicit read-only version reconciliation can recover a unique matching object; it never clears the failure pause. |
| Service/DB retirement | Quiesce surviving owned service processes before dumps. Remove only this slot's exact owned containers/volumes after verified local and cloud copies and both dumps. Raw traces, archives and version receipts remain. Wrong volume bindings are rejected. |
| Completion | Back up final master metadata and all per-slot receipts before requesting host shutdown. Independent hard stop remains armed if finalization fails. No evidence disk or S3 deletion is performed by the runner. |

The final ledger contains transactional admission/transition events; state, identity,
source, immutable exports and clock-seal drift are rejected. Failure pauses cannot
be hidden by an ordinary pause or automatically cleared. A normal terminal/systemd
service owns execution; no active Codex conversation is needed. `OPERATING.md` gives
the exact future commands. This work has not installed a campaign systemd service
on AWS or activated a real host shutdown.

## Runtime, money and storage

Reuse 8.2/8.3 measurements and the 2026-10-07 v1 price reads, rather than making new
AWS queries: serial median 613.386s gives 255.58h / 10.65 days as a reference.
Plan **12–13 continuous days**, subject to slower recipes and new backup/check
overhead; this is not a measurement of the complete bank. The maximum host
allowance is 15 days; the US$55 admission guard can stop the queue sooner, around
332h at these rates. Completion is never guaranteed by extending a budget or window.

One proposed Sydney m7i-flex.large (2 vCPU, 8 GiB), encrypted 160 GiB gp3,
no inbound access, SSM and an instance role. No paid model/speech API.

| Running time | Estimated total, including 48h stopped disk and first storage month |
|---|---:|
| Median reference, 255.58h | US$44.01 |
| Planning, 312h | US$52.23 |
| Maximum, 360h | US$59.23 |

Rates: compute .1197/hour; public IPv4 .005/hour; gp3 .096/GiB-month;
S3 .025/GiB-month; 730h/month accounting; US$5 request/transfer/monitoring allowance.
Credit is not a discount. The completed pilot's US$2 approval does not authorize
this budget. Recheck rates, plan, credits and actual deployment configuration at
separately authorized deployment. A hard compute timer does not stop EBS/S3 costs.

Pilot growth projections are 23.35 GiB raw, 8.66 GiB backups and 5.56 GiB archives
for 1,500 slots. They are not whole-bank upper bounds. New master snapshots,
failures, transfer pieces and retention add overhead. Reserve 50 GiB working,
50 GiB backups, 25 GiB OS/images and 35 GiB headroom on the same 160 GiB disk.
Two local partitions share physical hardware. S3 is the independent storage copy.

Stopped disk retention is proposed at 48h; 160 GiB costs about US$.51/day.
Escalate before that limit if postflight is incomplete: seek an explicit storage
and budget decision while retaining evidence. Never delete the only copy to meet
a ceiling. First-month 30 GiB S3 is US$.75; continued retention needs a decision
before the next month. An exact US$65 hard cap and indefinite evidence retention
cannot both be guaranteed.

## Recovery and integrated postflight

Pause between fully backed-up slots; resume saved order. If a same-boot collector
exits and services/DBs survive, recover the same SQL checkpoint and immutable
deadline. Reconcile PID creation identity; attach read-only to the original.
Do not rerun the driver or reissue a request. An interrupted driver stays failed.
Missing checkpoints, lost service/DB identity and host reboot stop automatic
recovery. Full-host restore/PITR is excluded; logical dump verification does not
qualify that claim. Continued snapshots cannot prove unrecorded client playback.

After cutoff, pending repair and operations remain pending in retained dumps.
Effects after isolated-resource retirement are unobserved, not assumed absent.
Every source drift, protocol defect, backup failure and collection interruption is
retained. Fixes would require another reviewed version; no silent resealing or
substitution of outcomes. The runtime never imports an LLM's asserted success as
decisive speech or changes application correctness ownership.

`postflight.py` integrates each backup receipt with the qualified range downloader:
version-specific 64 KiB reads, maximum eight readers, 10s connect/30s read timeouts,
three header/body attempts, original 1,800s transport admission deadline, per-piece
hash/version proofs and preserved interrupted assemblies. That transfer deadline
is separate from the research cutoff. Never overwrite unproven partial pieces.
Use a fresh short extraction root, <240-character paths, member/type/traversal/
collision checks, full SHA-256, trailer and member verification. Preserve partial
extractions/failure journals. Stale locks need identity reconciliation and retained
renaming. Expired transfers get separately linked diagnostic transfer attempts,
not a scientific rerun. The wrapper does not authorize AWS cleanup.

## Verification and limits

`qualification-plan.json` was written before tests. `validation.json` and
`final-verification.json` identify exact results and retained attempts. Verification
uses synthetic **CALIBRATION-only** capabilities in test directories; they are not
human acceptance, a main freeze or launch authorization.

Evidence includes Linux offline CLI/process checks, actual transactional SQLite
checkpoint recovery under a virtual 600-second clock, return/refusal collection,
resource/cost/deadline/drift/backup stop paths, pinned transport/extraction controls,
owned retirement checks and real read-only dumps of the two existing isolated
PostgreSQL databases. The original complete pilot windows, real S3 transfer,
short extraction and saved traces supply historical live evidence. No new
scientific executions or cloud calls were made, and unsuccessful attempts remain.

Historical hashes match the baseline copied before v2 editing. Full stream rereads
are recorded before and after final package assembly. The before-assembly check
is not represented as an earlier independent pre-edit reread; its chronology is
explicit in `preservation-before-assembly.json`. Original evidence bytes are unchanged.

These checks qualify the integrated local controls; they are not a 360h endurance
run, a new end-to-end cloud deployment or proof of recovery from host loss. Actual
systemd installation/activity, role/bucket permissions, prices, disk capacity and
resource headroom must be verified on the eventual authorized host **before its
first admission**. The runner fails closed without active matching independent
timers. No fresh AWS calibration is necessary to finish this review package.

All voice evidence remains scripted tone/client-ACK protocol evidence. It supports
simulator state and observable-proxy mechanism comparisons on the fixed input
frame. It cannot demonstrate human understanding, intelligible decisive-word
exposure, real-call usability or population superiority. No optional real-speech
extension is proposed. Conditional input independence, time dependence and AFT
assumptions remain analysis limitations.

## Remaining decisions — acceptance checklist

- [ ] Accept this exact v2 archive/inventory and unchanged 500-input, three-arm serial schedule.
- [ ] Accept the proposed US$65 ceiling, US$55 guard, 360h/30-minute limits, 160 GiB capacity and conservative slot reserve.
- [ ] Accept 48h stopped-disk/first-month S3 retention and escalation if evidence protection needs an extension.
- [ ] Accept original/UNKNOWN/recovery rules, clustered timing amendment and synthetic-evidence limits.

After explicit acceptance: create a separate immutable freeze receipt and verify
the accepted fingerprints. **Launch still needs separate authorization** tied to
that freeze and actual start/configuration. Deployment activation checks remain
mandatory. Creating this candidate records none of those decisions.

**Verdict: concrete package ready for acceptance review when final verification is
PASS; no current authorization to freeze, deploy, spend or start Phase 8.5.**
