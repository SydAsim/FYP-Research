# Phase 8.5 refusal amendment v1

**IMPLEMENTED; LOCAL LIVE QUALIFICATION BLOCKED. Not accepted, frozen or launchable.**

The main campaign remains paused with one retained original and 1,499 planned slots.
No AWS operation, provisioning, restart, clock reset, new spending authorization or main
driver command was performed. AWS stopped status refers to the preserved shutdown evidence;
this task did not poll AWS. Retained storage can continue its previously documented charges.

## Narrow change

The candidate collector recognizes only a B3 schedule refusal whose nested RFC 9457
problem is exactly `b3-evidence`, non-retryable, for revision 2. Recognition also requires
the normal request and wrapper to match, a current PRESENT operation, a matching authoritative
resource observation, and both linked CREATE/RESCHEDULE status observations returning
`501 / Operation status lookup is absent` during that refused request. Raw observation
hashes and workflow/operation/scenario bindings are checked. A 409 alone is insufficient.
Other refusals, transport failures, missing or inconsistent evidence and probe errors retain
the technical failure pause. No request retry was added.

The raw driver status stays FAILED. A separate hashed `driver_classification` records
EXPECTED_EVIDENCE_REFUSAL. The collector continues the original 600-second observation,
uses the unchanged independent v4 oracle, exports both old and amended instrument results,
and performs the existing verified-backup sequence before another admission. An interrupted
driver without a finished checkpoint also persists a failure pause; commands are never replayed.

`runner.py` explicitly rejects CAMPAIGN scope before initialization or use of an existing
campaign root. Test tokens are synthetic, CALIBRATION scoped, and labelled as not human
acceptance. They cannot authorize main execution. The application, migrations, research arms,
main inputs, saved order, endpoints and observation windows are unchanged.

## First original: proposed disposition

Read-only [sidecar](first-original-sidecar.json) binds execution
`01a11705-11f0-79f1-9293-78f7f8207f70`, input p8v4-0484/B3/attempt 1, to raw export SHA-256
`283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b`.
The original export, FAILED status, grades, analysis row, master pause and backups remain intact.
The copied export is byte identical; the sidecar is not another scientific execution.

| Endpoint | Original and proposed result |
|---|---|
| Correct final business state | TRUE |
| Business correction succeeded | TRUE, from independent simulator truth |
| Correct final spoken update | FALSE |
| Unsupported exposed claim | FALSE |
| Incompatible stale exposure | FALSE |

All twelve endpoint values match, including existing NOT_APPLICABLE values. Complete protocol
journals contain no published segment or playback for the refused confirmation. This supports
“business correction succeeded; confirmation was not delivered in this protocol execution.”
It makes no claim about intelligible speech, human understanding or general arm superiority.

## Explicit timing-analysis amendment

Only a fully collected, evidence-validated expected refusal receives instrument status
COMPLETED, meaning the research outcome was observed, **not** successful speech or business
completion. Raw driver FAILED remains visible. Missing anchors, collection errors, source drift
or a last poll before the original cutoff prevent this mapping. Tampering with the stored
classification is a protocol error rather than a fallback success.

The first original changes censor reason from INFRASTRUCTURE_FAILURE to
NO_SUPPORTED_COMPLETION. Its duration remains 600 seconds and event_observed remains false.
It is an administrative right-censor at the original final external request plus 600 seconds;
the refusal time does not become a completion event. Original and proposed grade/evidence
hashes are separately recorded. Numeric timing inputs and endpoint values are identical.
The existing paired restricted-latency and clustered AFT/bootstrap functions, sampling units,
seeds and analysis settings are unchanged. No new campaign comparison was calculated.
The rule must be applied consistently to every matching refusal, not selectively to a winner.

## Fixed qualification and current evidence

[Plan](calibration-plan.json) was written before any live driver admission: four serial
calibration executions, 600 seconds each, 3,000-second total live budget, US$0 cloud spending.
Separate calibration fixture IDs preserve the original bank. A fifth ID is a never-admitted
sentinel reservation to prove a planned next slot stays unexecuted after a defect; it is not
a fifth planned driver execution.

| Required live proof | Current status |
|---|---|
| Expected refusal → full window → oracle → verified backup → actual next driver | UNRESOLVED; not executed |
| Next normal driver → full window → verified backup | UNRESOLVED; not executed |
| Injected technical exception → durable pause → planned sentinel rejected | UNRESOLVED; not executed |
| Checkpoint exit → same-boot collection attach, same ID/deadline, no POST replay | UNRESOLVED; not executed |

The harness uses the cached frozen Linux image, fresh per-slot PostgreSQL/Redis resources,
a dedicated internal network and no host ports or paid provider services. Backups use real
database dumps and two versioned local roots on E:. They share one physical disk and do not
qualify physical disaster recovery or repeat S3 qualification. Recovery here is collector
restart with application services alive on the same boot, not full-host recovery.

Completed checks:

- **66 tests PASS on Linux** (`linux-regression-release.txt`), including 25 new classifier,
  evidence binding, timing parity, missingness, tamper and main-block tests; existing control,
  archive, transport and checkpoint tests were reused in this separate version. The same
  66 tests passed on Windows before the subsequent type-only test corrections.
- **Strict mypy PASS for 18 files** (`linux-mypy-release.txt`). The unchanged SDK boundaries
  lack third-party stubs; `import-untyped` was disabled, with all other strict checks enabled.
- **Ruff PASS** (`ruff-final.txt`).
- Frozen source closure and CALIBRATION capability verification PASS in the actual cached
  capsule (`pre-admission-control.txt`), with zero driver executions.
- Retained original oracle replay matches its original grade and analysis row exactly.
  Proposed classification preserves all outcome values and numeric timing.

These are instrument/control checks. Virtual-clock collection tests are clearly control-only:
they deliberately retain oracle failure for synthetic snapshots. They do not substitute for
the four outstanding real PostgreSQL/full-window executions.

### Resource stop and retained attempts

Attempt 1 was stopped before network creation or driver admission by the terminal preflight.
It measured C: 10,281,201,664 bytes (9.58 GiB), E: 193,130,446,848 bytes (179.86 GiB), and
available Windows RAM 1,732,591,616 bytes (1.61 GiB). Docker's data VHD is on C:.
The local C: minimum is 10 GiB; trace/backup admission on E: retains the existing 20-GiB
guard and Linux admission RAM retains 2 GiB. The earlier capsule measured about 2.27 GiB
available after its cgroup cap. No limit or window was reduced to obtain a pass.
Free at least 2 GB on C: before another attempt; remeasure RAM and disk at admission.

Every unsuccessful pre-check and test log is retained (`*-attempt*.txt/json`,
`attempt1-resource-stop.txt`). No failed calibration has been replaced or counted as a main
input. No live scientific driver has started in this amendment.

## Historical preservation discrepancy

The pre-check found an already changed title in `artifacts/phase-8.5-report.md`: the previous
inspection request had been inserted into its heading. That file was left untouched.
[As-found copy](historical-report-as-found.md) and
[sealed report recovered byte-identically](historical-report-sealed-recovered.md) are both retained.
The recovered version matches the sealed operational SHA-256
`acd2974b6c15bc1b37147d59db29fca3c2dcc7a929381cea4a8eae9ac4d65d3d`.
[Discrepancy record](preexisting-drift.json) distinguishes this from amendment-created changes;
there is no blanket claim that every operational document matched its old checksum.
All frozen source, frozen/historical scientific evidence and recovered raw first-execution
files passed the baseline check. The baseline includes 6,046 distinct paths and preserves the
as-found heading too. Before/after verification is recorded separately. No historical seal
was regenerated to conceal the discrepancy.

## Recommendation for review

**Retain the first original, with this separately approved classification sidecar if accepted.
Do not replace it or restart comparisons solely because of this classification defect.**
Its full window and independent endpoint evidence are already retained; all endpoint values
and numeric timing are unchanged. No complete three-arm input exists yet. A future approved
continuation must retain the 1,499 reserved original identities and saved serial order, using
the same application and inputs and the amendment uniformly. Changes are to observation
classification and admission handling, not treatment behaviour.

This recommendation is conditional on the four local qualification proofs, reviewed
disposition of the recovered report discrepancy, and a separately reviewed continuation
package. Full-host restart/restore remains unqualified. The current historical failure pause
must not be cleared as an ordinary pause; this candidate refuses main scope. Other 409
conditions can still stop admissions and are not qualified as harmless by this amendment.

The original operational clock remains 2026-10-07T15:24:23.810674Z and deadline remains
2026-10-22T15:24:23.810674Z. Paused time is not regained. Continuation feasibility must be
checked against that deadline and accepted cost/resource limits, without changing them.
Retained disk review remains due 2026-10-09T15:57:46Z; no disk deletion is scheduled here.

## Terminal continuation for local qualification only

After freeing space, from a normal PowerShell terminal in the repository:

```powershell
.\artifacts\phase-8-runner-amendment\v1\Qualify-Local.ps1 -Attempt attempt2
Get-Content 'E:\FYP Project\phase85-runner-amendment-v1\attempt2-console.log' -Tail 20
```

Use a new numbered attempt for an unsuccessful preflight or retained unsuccessful attempt.
Do not edit the versioned Python/fixture files while an admitted calibration is active:
its capability inventory rejects source drift. A detected defect preserves the attempt;
do not launch diagnostic repeats automatically. Qualification dispatch is detached and
does not require an active Codex chat. No command in this section launches the main campaign.

## Files and next gate

All changes are in this new version and its uniquely named amendment report. Candidate
collector, runner and instrument are changed; refusal classifier, read-only sidecar adapter,
finite tests/harness, fixture bank, plan and local dispatch script are new. Controls, storage,
transport, window, postflight and analysis are byte-identical copies of v2. No migration added.
The candidate inventory is a fingerprint inventory, not a freeze receipt.

**Next gate: finish the four local calibrations after the resource stop clears, then review
the amendment and continuation disposition. No new freeze or launch authorization is recorded.**
