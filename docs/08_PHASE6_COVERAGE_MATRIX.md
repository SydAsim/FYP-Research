# Phase 6 implemented scenario coverage

The [closure manifest](../artifacts/phase-6-completion/completion-0ce13a086fe0.json)
indexes **43 paired fixtures, 256 verified executions including one auxiliary
Redis repair witness**. This is harness verification, not the Phase 7 pilot or
the Phase 8 confirmatory campaign. Arm executions and repetitions do not add
independent scenarios. Child manifests retain their actual source/image versions.

## Mandatory and boundary fixtures

| Family | Variation actually exercised | Arms | Independent evidence |
|---|---|---|---|
| P0 | Correction before first acceptance; one corrected CREATE | All six | No prior accepted revision or operation |
| P1–P5 | Accepted, precommit, hidden commit, postresponse, verified boundaries | All six | Explicit reach/release and isolated provider commits |
| P2 delay/refusal | Commit held until release; rejected write reconciled before corrected write | All six | Simulator fault configuration and raw request/status events |
| P2 partial effect | HELD is PARTIAL; budget exhaustion; no follow-up write or decisive claim | All six | One truth-log commit; eight strict-arm reconciliation reads; durable handoff |
| P3 Redis loss | Reserved cache database flushed and service restarted during hidden commit | All six | Equal PostgreSQL snapshots; absent cache hint; resumed reconciliation |
| Read | Readback preserves a previously created appointment | All six | Identical append-only truth before and after the actual read |
| P5 competing writer | Newer resource version blocks stale reschedule; known ABSENT and handoff | B3/P1/P2 | Actual concurrent commit, HTTP 409, authoritative reconciliation |
| P6/P7 | Generated/unpublished and published/unplayed stale audio | All six | Shared deterministic TTS port, named boundary, no stale playback acknowledgement |
| P8/P9 | Partial and completed stale audio; explicit repair ablation | All six | Client progress/completion spans and independent semantic/truth grading |
| Existing repair + cache loss | OPEN repair survives cache wipe and restart; becomes REPAIR_PLAYED | P2 witness | Nonempty repair/receipt/permit snapshots, actual Redis restart, corrected client acknowledgement |
| Clean control | One accepted intent, one CREATE, useful supported outcome | All six | Provider truth and client acknowledgement |
| Local acoustic inputs | Clean synthetic, noise, overlap, disfluency, uncertainty, recorded clean | All six | Actual Vosk → local Qwen → safe eSpeak output, input/model/prompt/output hashes |

The acoustic run shares one measured proposal per fixture across arms to isolate
protocol mechanisms. Recorded clean speech succeeds; the other five conditions
produce clarification and **failed task/outcome scores**, with no provider write
or decisive claim. Failed recognition is retained, not counted as success.

## Constrained secondary covering array

`research/scenario_dsl/covering.py` constructs 70 valid candidate rows and selects
20 deterministically. These 20 live rows cover all **150 feasible pairs within
the declared secondary domain**. They do not claim pairwise coverage of every
level in the entire project, and the Cartesian product is not executed.

| Dimension | Secondary domain |
|---|---|
| Revision | Parameter correction, retraction, additive compatible, replacement, conflicting instruction |
| Action semantics | Logical reschedule, cancel, reuse, replace; concrete compensation depends on provider/profile |
| Workflow | One ticket/resource; two workflows/tickets/resources with side booking preserved |
| Acoustic condition | Fixed scripted recognition; six actual acoustic levels are separate mandatory fixtures |
| Provider capability | Atomic reschedule; cancel then create with status/resource lookup |
| Visibility | Immediate, delayed two reads, stale two reads, permanently unavailable |
| Speech exposure | Fixed corrected-outcome-only; P6–P9 vary exposure separately |
| Fault | Fixed P3 hidden-commit response loss; other fault families have mandatory rows |

Constraint declared before execution: permanently unavailable evidence cannot
finish the independent side booking, so that multi-workflow combination is not
in the secondary feasible domain. No outcome-driven exclusion was added.

## Scope and limits

- B0–B2 use direct provider drivers; B3/P1/P2 use durable controller/worker paths.
  Their explicit profile differences are preserved. P5 for B0 is a tool-observation
  hook; B1/B2 use their status check, and proposed arms use verification receipts.
- Baseline audio is isolated synthetic counterfactual evidence. It is not routed
  to real callers. All arms use the same deterministic test TTS interface in the
  P6–P9 protocol checks. These tones do not measure natural speech quality.
- Physical hearing/comprehension is optional RQ9, not a required Phase 6 gate.
  Client acknowledgements are transport evidence only.
- The authoritative claim enum has no cancellation outcome template. Retraction
  verifies cancellation through provider truth and withholds decisive speech.
  Cancellation exposure has denominator zero, not an inferred perfect rate.
- Legacy safe-resolution rows remain immutable. Secondary definition v2 adds
  honest durable handoff safety without changing task success or outcome coverage.
- Logical turn and server/client timestamp latencies are recorded where available.
  Missing/noncomparable timestamps remain explicit; no physical end-of-turn or
  hearing latency is invented. Censored outcome observations remain censored.
- Non-inferiority margins, exclusions, statistical sample justification, global
  protocol freeze and population effect estimates belong to Phase 7 onward.
