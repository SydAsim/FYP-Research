# Phase 8.4 — review preparation report

## Scope and status

Prepared a separate v1 review overlay over the unchanged v4 scientific candidate.
**Design review ready. Operational freeze and main launch remain blocked.**
No review acceptance or freeze receipt has been created, no AWS resources were
provisioned, and all 1,500 main slots remain NOT_STARTED. The 24 calibration
executions are not drawn from or subtracted from the 500 main inputs.

Read [the concrete review package](phase-8-review-freeze/v1/REVIEW.md) and
[terminal instructions](phase-8-review-freeze/v1/OPERATING.md).

## Files and invariants

All additions are under `artifacts/phase-8-review-freeze/v1`, plus this report.
No application, migration, contract, fixture or historical evidence file was edited.

| File group | Invariant |
|---|---|
| REVIEW.md, OPERATING.md, checklist.json | Explicit scope, spend/recovery decisions, review before freeze, launch separately authorized |
| schedule.json/csv, build_review.py, test_schedule.py | Exactly 500 inputs × B3/P1/P2; saved input/arm/block order; original attempts untouched |
| budget.json, measurements.json, pricing request/response records, local-resource records | Measured runtime basis, current price source, explicit assumptions/headroom |
| transport.py, requirements.txt, test_transport.py | Version-pinned evidence reads, finite retries, retained partials/failures, safe short-path extraction |
| qualify.py, qualification.json, pilot-receipt.json, expected-failure.json | Real saved evidence replay and real S3 read; synthetic drift control clearly separated |
| preserved-before.json, preservation-after.json, review-fingerprints.json, verify_review.py | Historical preservation and review integrity; fingerprints are not a freeze receipt |
| regression/static-check logs, validation-initial-attempts.json, linux-overlay-source-proof.json | Failures retained, dependency/platform distinctions, qualified source identity |

**Migrations added: none.** Main scientific drivers, oracle and analysis implementation
remain unchanged. The only new implementation is research evidence transport,
review scheduling and read-only verification.

## Schedule and resources

Recommended serial schedule: 1,500 slots in the saved order, twenty blocks of
25 inputs. There are zero adjacent same-arm restart/cache pairs eligible for
the narrow 8.3 qualification. No ordinary recipe is silently declared safe to overlap.
The exact file rows include each input/arm/fixture hash; no calendar launch date.

Median calibration reference is 255.58 hours (10.65 days); plan 12–13 continuous
days, maximum running allowance 360 hours. Fresh rate reads support a 13-day
estimate of **US$52.23**, a maximum-allowance estimate of **US$59.23**, and a
**proposed US$65 ceiling**, not yet approved. Those estimates include 48 stopped
disk hours, 30 GiB S3 for one month and a US$5 request/transfer/monitoring allowance.
The admission stop at estimated committed US$55 preserves a US$10 reserve;
alerts alone are not a hard billing lock. Long retention or unresolved backup
failures require explicit review; evidence is not deleted to conceal a failure.

Proposed host: the measured Sydney m7i-flex.large class, 2 vCPU/8 GiB, encrypted
160 GiB gp3. It replaces the pilot's 40 GiB disk allocation for evidence capacity.
Pilot paired peak CPU reached 97.03%; memory headroom is not permission for
whole-bank concurrency. A full-bank storage maximum was not measured. Pilot
projections and reserve/stop rules are explicit in the review.

## Commands and validation

Commands and exact environments are in OPERATING.md. Executed here:

- `build_review.py`: generated the 1,500-row proposal without initializing any
  execution ledger, accepting, freezing or launching.
- Five read-only AWS CLI queries: Sydney compute/gp3/IPv4/S3 pricing and current
  Free Tier plan state; retained request/response JSON. FREE/ACTIVE, US$119.37
  credits at the read. No AWS write was performed.
- Windows targeted pytest suite with the preserved analysis dependency overlay:
  **76 passed**, `windows-regression-attempt3.txt`.
- Linux process/platform regression in the retained container with a read-only
  protected Linux module overlay: **16 passed**, `linux-regression-attempt2.txt`.
  No Docker socket, AWS credentials, network or live business driver was provided.
- Ruff: PASS. Strict mypy: **four production scripts passed**; boto3/JSON boundary
  types are isolated and missing external SDK stubs are explicitly allowed.
- `qualify.py`: extracted the actual retained archive, regraded every saved pilot
  export using the revised independent oracle, and read one pinned S3 range.
  **24/24 identical** grades; original archive hash unchanged.
- Finite retained drift control: a changed completed piece was rejected before
  redownload; the original archive and failure journal remain in `E:/P84Drift01`.
- Review/historical fingerprint verifier: outcome is recorded in
  `phase-8-review-freeze/v1/final-verification.json`.

No new PostgreSQL write/integration case was needed: application/transaction
behaviour and migrations were unchanged. The 24 replays consume the retained
real-PostgreSQL simulator truth evidence independently, not mocked controller
state. This does not constitute a new live fault execution or restore qualification.

### Unsuccessful validation attempts, retained

The first Windows suite passed 72 and failed one AFT check because base `.venv`
lacked SciPy. The corrected command uses the existing separate analysis overlay.
A subsequent combined invocation incorrectly included Linux platform tests on
Windows: 85 passed, seven failed for platform/procfs requirements; retained in
`regression-attempt2.txt`. It did not exercise the Linux paths correctly.

The first native-Linux container check passed 15 and failed one missing-container
message test because that retained image predates the already qualified source
fix. The final source archive's runtime member matches the current protected
runtime byte-for-byte. A read-only mount of that same module gave 16/16 passing
checks; neither image nor historical source was rewritten. Initial Ruff import
ordering and three new-script typing findings were fixed; a later line-length
finding was fixed. Initial results and final logs remain separately labelled.

These are validation/dependency mistakes, not discarded business outcomes.
There were no new business calibration attempts or main attempts in this phase.

## Success and expected failure evidence

- Success: `qualification.json`, ID `cal-p84-postflight-v1-01`, actual
  95,449,610-byte archive, 18,715 tar members, 580,117,072 uncompressed bytes,
  maximum extracted path length 170 characters; 24 identical independent replays;
  65,536-byte version-pinned real S3 range identical to local archive bytes.
- Expected failure: `expected-failure.json`, ID `cal-p84-drift-v1-01`, points
  to the retained transport failure and unchanged original archive.

The source pilot archive SHA-256 remains
`b863ee5eec8a409373f67a09c55571e96746b05b4e5c6bc09218c7e1b02a03b7`.
S3 version remains `nbJrmG0vT96bOYiMMsnggMYLfgKhFVaK`.
This phase's read/extraction does not replace any original grade or failed download.

## Analysis and claims

The unchanged study keeps the two co-primary endpoints, paired input sampling,
300/100/60/40 allocation, clean 5pp tolerance, fixed corrective-delivery challenges,
planned-denominator missingness bounds and multiplicity rules. Review explicitly
accepts the prior execution-setup timing amendment: paired input-cluster latency
intervals and censored AFT with retained failed draws. Descriptive-only timing
would not satisfy the research contract.

Pilot business final-state outcomes tied across B3/P1/P2. Pilot communication
and mechanism findings remain their original results, not a study effect estimate.
Synthetic tone/client-ACK evidence does not establish actual spoken-word exposure,
hearing, understanding, human-call performance, novelty or arm superiority.

## Remaining limits, decisions and next gates

1. Human acceptance of schedule, budget/storage/recovery limits, unchanged v4
   endpoints and the explicit timing amendment is pending.
2. Qualified entrypoints still admit calibration IDs only; the v4 candidate pipeline
   correctly blocks CAMPAIGN analysis. A reviewed-freeze-bound main admission/analysis
   adapter is a launch prerequisite, not implemented or enabled here.
3. Multi-day watchdog and new cost/storage thresholds plus per-slot cloud backup
   handling require finite separate control qualification before a launchable
   executable inventory can be frozen. No paid API is needed for those checks.
4. Full host reboot/disk-loss restoration is unqualified and explicitly excluded;
   originals become interrupted/UNKNOWN where evidence is missing. Logical dump
   integrity is not proof of restored unattended application recovery.
5. Integrated transport has finite tests, actual extraction/replays and a real
   range read. The entire 95 MB network download was not repeated; its preserved
   recovery-v6 result is the timing basis. A multi-day unattended postflight is
   not claimed from this evidence-only check.
6. Before freezing, include the exact executable controls and their validation
   fingerprints in a concrete revised inventory. Acceptance is bound to that
   inventory; later code changes require a new review/version. Then freeze hashes;
   only a subsequent separate instruction may authorize main launch.

**Verdict: REVIEW READY; FREEZE/LAUNCH NOT YET READY. The 500-input campaign
remains entirely unstarted and guarded.**
