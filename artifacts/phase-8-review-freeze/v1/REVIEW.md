# Phase 8.4 — proposed execution package for review

**Status: REVIEW ONLY. No acceptance, frozen protocol, launch authorization,
main execution, or new AWS resource has been created.**

Review applies to this v1 overlay together with the unchanged v4 candidate.
The earlier US$2 authorization covered the completed pilot and its cleanup.
It does not authorize this campaign or its proposed US$65 ceiling.

## Decisions to accept

| Decision | Recommended choice | Consequence |
|---|---|---|
| Schedule | All 1,500 original slots serial, lane A, saved order | Preserves the timing comparison and requires about 12–13 continuous days. No whole-bank parallel speedup is claimed. |
| Infrastructure | One Sydney m7i-flex.large, 2 vCPU/8 GiB, encrypted 160 GiB gp3, no inbound access, SSM | Uses the measured host class; adds disk capacity rather than changing application behaviour. No paid speech/model API. |
| Money | US$65 proposed incremental study ceiling; estimated committed-cost admission stop at US$55 | Current on-demand estimate is about US$52 for 13 days, including two stopped-disk days and a US$5 request/transfer allowance. Credits are not treated as a discount. |
| Time/recovery | Absolute maximum 360 running hours; stop admitting 30 minutes before that deadline; at most 48 hours of stopped-disk recovery before escalation | Pauses do not restart the host cost clock. An unfinished campaign remains unfinished. No outcome replacement. |
| Storage | Retain immutable versioned S3 evidence up to 30 GiB for the first month; local working and backup capacity gates | Two local partitions are one physical SSD, not independent hardware. S3 supplies a separate storage location. Growth beyond the cap stops new admissions; no evidence is silently deleted. |
| Analysis | Unchanged v4 binary endpoints plus the explicit clustered timing amendment | Retains required latency intervals and censored timing analysis; no descriptive-only waiver. |

These are choices for review, not claims that every launch control is implemented.
The launch prerequisites at the end must be completed before operational freezing.

## Exact order and observation schedule

`schedule.csv` and `schedule.json` list every original slot, its input, arm,
recipe, stratum, block and fixture hash. The order is exactly v4
`execution-order.json`, seed 8042043: 20 fixed temporal blocks of 25 inputs.
Execute all three arms of an input in its saved arm order before moving on.
Every slot has attempt 1, status NOT_STARTED and no execution ID. Calendar start
time is deliberately unset until separate launch authorization.

For each slot: verify frozen dependencies and resource/cost gates; allocate fresh
isolated services, application and simulator PostgreSQL databases, network,
cache and synthetic resource binding; issue the normal arm driver; collect
through the **actual externally issued final request + 600 seconds**, including
normal returns, refusals and driver faults. Take a snapshot whose collection
**starts at or after** the original cutoff. Export uncapped raw observations,
cutoff-filtered outcome evidence, ledger and database dumps; independently
replay the revised oracle; verify and back up the original before the next slot.
Retain a defect and stop new admissions if this sequence cannot complete.

600 seconds is an observation horizon, not a completion promise. The issued
request timestamp is recorded before HTTP; accepted revision is a separate
durable server timestamp. A crash between recording issuance and transmission
is uncertain. If the final-request anchor is missing, collect a fallback 600
seconds from the last recorded issuance or execution start, flag the missing
anchor, and do not pretend the intended window was observed. Driver refusal
or timeout does not shorten collection or restart the deadline.

Retain the existing provider HTTP 30s, scheduler 15s, driver 40s, barrier 120s,
operation lease 180s, repair lease 30s, reconciliation 8s, drain 30s, permit TTL
30s and recovery-watch 40s settings. No observation window or scientific fault
is shortened for cost. Host hard-stop and pause controls govern admissions,
not those application settings.

### Why there are no overlapping main slots

The completed 8.3 pilot qualified only a same-arm restart-before-repair/cache-loss
pair, using separate services, databases, bindings, faults, networks and queries.
It ran one such pair under each arm. It did not qualify ordinary clean, hidden
commit, stale-playout or cross-arm overlapping workloads. Peak paired CPU was
97.03%, despite ample RAM. Different execution IDs alone do not establish isolation.

The main bank has three restart inputs and two cache-loss inputs: 15 arm slots.
There are **zero adjacent matching same-arm pairs** in the saved order. This
package therefore uses none of that narrow parallel qualification. Reordering
or extending it would require a new reviewed operational design and measured
timing/dependence justification. Neither is included here. Parallel S3 range
reads are evidence transport, not parallel research executions.

## Runtime, prices and storage

`measurements.json` records the pilot basis: serial median 613.386 seconds,
paired block median 621.246 seconds. Multiplying the serial median by 1,500
gives 255.58 hours / 10.65 days. This is a calibration projection, not a full
bank measurement. Provisioning, backups, checks and slower fault recipes justify
planning **12–13 days continuously**, with a maximum 15-day running allowance.
Pausing overnight adds calendar time and can exhaust that fixed allowance.

Fresh AWS Price List reads are retained in this directory. Sydney Linux shared
m7i-flex.large is US$0.1197/hour; one public IPv4 is US$0.005/hour; gp3 is
US$0.096/GiB-month; S3 Standard first-tier storage is US$0.025/GiB-month.
Global pricing queries use us-east-1; all project resources remain in Sydney.

| Schedule | Compute + IP | 160 GiB disk, including 48h stopped retention | S3 30 GiB for one month + US$5 allowance | Estimated total |
|---|---:|---:|---:|---:|
| Median reference, 10.65 days | $31.87 | $6.39 | $5.75 | $44.01 |
| Planning, 13 days | $38.91 | $7.57 | $5.75 | $52.23 |
| Maximum running allowance, 15 days | $44.89 | $8.58 | $5.75 | $59.23 |

US$65 is proposed, not approved. Taxes, exchange rates and other project resources
are excluded. Actual billing can lag. The project is currently FREE/ACTIVE,
with US$119.37 credit remaining at the recorded read; recheck before launch.
No plan upgrade or new paid service is proposed. The US$5 allowance covers
requests, transfer and lightweight monitoring; it is an assumption, not a quote
for a measured full campaign. Recheck rates and projected committed charges
before deployment. Budgets alerts do not enforce an instantaneous spending cap.
The estimate covers the first storage month. Continuing to retain 30 GiB costs
about US$0.75 per additional month at this rate and requires a retention/budget
decision before that period expires. Do not automatically delete research evidence.

Pilot retained raw, backup and archive sizes project to approximately 23.35,
8.66 and 5.56 GiB respectively across 1,500 slots. The pilot mix is not a maximum
for all recipes; WAL preallocation is not a per-case write rate. Reserve 50 GiB
for raw working evidence, 50 GiB for backups, 25 GiB for OS/images and 35 GiB
headroom within the 160 GiB disk. These are admission accounting reservations
on one disk, not claims of separate physical disks. Versioned cloud exports,
attempt logs, chunk journals and failure files all count against the S3 cap.

Require at least 2 GiB available host RAM and 20 GiB actual disk free before
admission, plus enough capacity for the next working/export/backup estimate.
No new slot if sampled available RAM drops below 1 GiB, disk below 10 GiB,
projected retained evidence exceeds its reserved capacity, or estimated committed
cost including shutdown/backup retention would exceed US$55. Continue collecting
the active original where resources permit; any forced loss is recorded as an
infrastructure interruption with missingness. Do not shrink buffers or windows.
CPU/load and collection gaps remain recorded; a >10s poll-start gap flags a
collector warning, a >30s gap stops future admissions for review. Neither proves
the interval between snapshots was observed, nor erases later durable ACK times.

Local measurements are saved in `local-memory.json` and `local-disk.json`:
16.98 GB visible RAM, about 3.21 GB available; C: about 21.99 GB free,
D: 107.70 GB and E: 193.64 GB at the measurement. They are transient measurements,
not a launch reservation. Require 50 GiB free on E: and 50 GiB on D: before full
evidence download/extraction, and remeasure. Both are on physical Disk 0.

## Recovery and late effects

1. Pause normally **between completed, exported and backed-up slots**. The saved
   next sequence and original attempts remain unchanged. Resume the same order
   only within the fixed host deadline and after hash/resource checks.
2. If only the collector exits while the same boot, service processes and databases
   survive, reconcile their identities and attach read-only to the **same execution**.
   Keep its original request anchor, cutoff and execution ID. Do not replay the driver,
   send a replacement request or restart the observation clock.
3. Record every collection gap and later snapshot. A reconnect snapshot may recover
   durable timestamps but cannot prove unrecorded client playback. Grade unsupported
   evidence/ACK claims UNKNOWN. Receipt arrival must be within the outcome cutoff;
   a late ACK is stored raw, not backdated into a success.
4. Collect after normal returns and refusals through the full window. Keep raw late
   effects observed by final snapshots beside the capped analysis view. At cutoff,
   save pending operations and durable repair obligations in exports/dumps. Do not
   mark pending repair completed or failed solely because observation ended.
5. This finite study cannot promise observation of effects arbitrarily far after
   cutoff. Export/dump before retiring an isolated slot's services; recorded post-cutoff
   effects do not alter capped outcomes. Future effects after retirement are unobserved,
   rather than assumed absent. Report that limit explicitly.
6. A host reboot, lost database or unrecoverable service identity is **not qualified
   transparent recovery**. Retain the original interruption, trace, original denominator
   and unresolved endpoints. Stop admissions and obtain review before continuing
   untouched slots. A logical dump integrity check is not a host restore/PITR test.
7. A diagnostic rerun, if later authorized, receives a new execution/attempt ID and
   an original-ID link; its evidence lives separately. It never replaces an original
   failed, timed-out, missing or UNKNOWN observation or increases independent N.
8. On protocol defect, source drift or failed backup verification, stop new admissions,
   retain all originals and print/save a failure notice. No silent patch, auto-unpause,
   result substitution or source resealing. Revisions require a new reviewed package.
9. At the running hard deadline, stop the host and retain its disk if verified backups
   are unavailable. Ambiguous AWS stop/delete responses require read-only reconciliation
   of exact tagged IDs before any repeated write. Never delete the only evidence copy.
10. Allow at most 48 hours for stopped-disk postflight under this proposal. Clean up
    exact owned compute/disk only after verified versioned S3 and two hash-matching
    local archives, replay/accounting and dump checks. If verification still fails,
    **escalate before 48 hours for an explicit storage/budget extension**; preserve
    evidence meanwhile. A retained 160 GiB disk costs about $0.51/day. Do not claim
    a guaranteed hard US$65 cap while promising indefinite evidence retention.

These limits preserve uncertain outcomes, not a claim of lossless recovery from
every outage. No manual delivery of repair counts as unattended recovery.

## Integrated postflight fix

`transport.py` replaces the pilot's 90-second whole-file AWS CLI download and
long hash-named extraction folder in a **new** versioned evidence-only component.
It uses the recorded S3 version, receipt hash/size/checksum, 64 KiB ranges,
one shared client and at most eight range readers. The bounded SDK has 10s connect
and 30s read timeouts, three header attempts, and at most three body attempts.
Authorization/version failures stop immediately. Network failures are retained.
Every completed range has a durable hash/version/range proof. Resume validates
those proofs and the same receipt; mismatches or unproven partials stop rather
than redownload over them. Unique interrupted assembly files remain on disk.

The transport admission deadline is 1,800 seconds and persists in its checkpoint;
it does **not** modify the study's observation deadline. Already active bounded
reads can finish after it. If it expires, create a separately labelled transport
attempt and explicitly retain/link prior pieces and logs; never alter the original
checkpoint. That is a read recovery, not a scientific rerun. A stale process lock
requires identity reconciliation and a retained renamed lock before resuming.

Extraction uses a new short root (for example `E:/P84Q1/x`), full archive SHA-256,
path length <240, all-member path/collision/type checks and a capacity check before
creating the extraction tree. No traversal, links, Windows device/stream names,
case collisions or overwrite of a partial extraction. An interrupted extraction
gets a separately named root; its partial tree and failure record remain.
The component does **not** delete AWS resources or bypass postflight verification.

Qualification: finite offline interruption/drift/path tests; extraction of the
actual retained 95,449,610-byte pilot archive; all 24 saved independent oracle
replays; and one real pinned 64 KiB S3 read. The full network download was not
repeated: recovery-v6 already retained its successful 427.219-second measurement.
This is not a claim that the revised complete multi-day postflight ran unattended.

## Unchanged study and analysis

500 new independent context draws, not 1,500 independent cases. B3/P1/P2 are
paired within an input. Allocation is 300 CLEAN, 100 HIDDEN_COMMIT, 60 PLAYOUT,
40 OTHER_BOUNDARY over v4's fixed 50-recipe support. Repetitions/calibrations,
including the 24 pilot slots, do not enter this denominator.

The two co-primary outcomes remain correction success on 200 correction inputs
(weights .5/.3/.2) and unsupported decisive exposure on 100 hidden-commit inputs.
Primary P2–B3 claims use the existing two-comparison Bonferroni allocation.
Keep the identifiable saturated eligible arm/stratum cell means, paired input
covariance, weighted component bounds and planned-denominator best/worst missingness
bounds. Keep clean-case absolute 5 percentage-point noninferiority tolerance with
300 inputs and the existing conservative paired bound; no margin/sample change
after results. Keep the ten-comparison secondary Holm family and unresolved
adjustment when required p-values are missing.

The fixed 33 corrective-delivery challenges count ordinary supported baseline
updates equally. Explicit withdrawal when needed, correct final update, exposure,
claim support at publication/playback, repair persistence/discovery/completion and
final business state remain separate endpoints. Missing playback is UNKNOWN;
internal repair telemetry alone does not prove externally delivered correction.

**Explicit compatibility amendment:** accept the execution-setup v1
`analysis-compatibility.md`, superseding its older descriptive-only proposal.
Retain stratified paired **input-cluster** latency bootstrap, 2,000 draws, seed
8042051, and restricted mean time to recorded supported completion within 600s.
Keep the identifiable censored lognormal AFT `1 + C(arm) + C(stratum)` with
1,000 input-cluster bootstrap draws, seed 8042052; retain failed/nonconvergent fits
and fit-failure sensitivity. Missing anchors/gaps are not ordinary independent
administrative censoring. Completed-pair summaries stay descriptive. Keep all
three arm rows together per input and the fixed 20-block omission sensitivity;
blocks/recipe labels are not automatically independent sampling clusters.

Conditional input independence and the parametric/censoring assumptions remain
limitations; serial execution does not prove absence of host/time dependence.
Tone/scripted-ACK tests support protocol/state/exposure-proxy conclusions on the
fixed simulator frame. They do not support actual spoken-content exposure,
human understanding, real-call usability or population superiority. Actual speech
requires intelligible recordings, decisive-word alignment and playback evidence
under a separately reviewed study; none is added to this campaign.

## Acceptance, freeze and separate launch checklist

- [ ] Accept the unchanged 500-input, three-arm scope and exact serial saved schedule.
- [ ] Accept the infrastructure, US$65 proposed ceiling, US$55 admission guard and
      storage/retention limits; understand storage escalation if backups remain blocked.
- [ ] Accept interruption/UNKNOWN rules and the limited same-execution recovery claim.
- [ ] Accept the clustered timing amendment and synthetic-evidence limitations.
- [ ] Resolve launch-control implementation/qualification gaps listed below; record
      the exact executable package and successful checks in a revised review inventory.
- [ ] Record the user's review acceptance against that concrete package inventory.
- [ ] Then freeze its hashes in a new immutable freeze receipt; verify immediately.
- [ ] Separately request/record main launch authorization bound to that freeze and
      budget. Recheck credits, prices, headroom and guards; then and only then provision.

### Concrete remaining launch gaps

The currently qualified Linux entrypoints initialize **calibration IDs only**.
`research/study_v4/pipeline.py` intentionally rejects CAMPAIGN evidence until a
reviewed freeze. This overlay does not remove those safeguards. A guarded main
admission/analysis adapter must bind all 1,500 planned originals to the accepted
freeze and separate authorization before launch; simply running the pilot script
would repeat calibration, not execute this study.

The 360-hour multi-day host watchdog, US$55 committed-cost/30-GiB storage guards,
20/10-GiB thresholds and per-slot cloud backup receipt handling are specified
here but have not been exercised as an integrated main scheduler. Qualify their
failure/stop paths using separate finite synthetic calibration IDs, then include
the resulting executable hashes in the reviewed package **before operational
freezing**. No new scientific extension or main execution is authorized by this
requirement. Full host restore remains excluded rather than silently promised.

**Verdict: ready for design review; not yet ready to freeze a launchable runtime
or authorize the campaign.** Review may accept the decisions above, but remaining
runtime guards require verification and a concrete final inventory before freezing.
No acceptance is inferred from creating this document.
