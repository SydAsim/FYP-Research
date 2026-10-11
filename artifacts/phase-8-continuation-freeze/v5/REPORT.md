# Continuation v5 — read-only S3 inventory correction

**Ready for acceptance/freeze review; AWS remains stopped.** This task recorded no acceptance, freeze or deployment authorization and ran no research scenario, live application stack, pilot or observation-window calibration.

## Narrow correction and exact diff

`runtime.diff` contains every executable/runtime change against accepted v4. Only three existing files change: `storage.py` delegates inventory to a bounded read process; `runner.py` recognizes the 82 imported closed originals; `handover.py` binds the 82-original metadata boundary, v4 parent freeze and v5 provenance. New files implement inventory, metadata continuation, preparation and the focused tests. The runtime folder retains its historical `v4-complete` name to avoid unrelated import/path changes; the package/provenance version is v5.

The inventory-only reader permits **three complete attempts**, **1s then 2s backoff**, and a **120s total deadline**. Its dedicated S3 client has 5s connect / 10s read timeouts and one SDK attempt per request. A parent subprocess timeout kills a stalled read, including credential/DNS/pagination stalls. Retryable connection/timeouts and explicitly named transient S3 error codes are retried; authorization/schema/unknown errors are not. A failed later page discards that entire partial sum. Missing completion flags, missing/repeated markers, duplicate versions, out-of-scope records and expired deadlines fail closed. A verified explicitly complete empty response may correctly mean zero; missing evidence never does.

Exhaustion propagates through the existing durable PROTOCOL_STOP/pause path. The shared PUT/HEAD/find client configuration and appointment-write adapters are unchanged. This does not add automatic immediate host shutdown after a campaign pause; existing reviewed collection, backup and bounded operator shutdown rules remain.

## Focused qualification and retained failures

- Declared fixed set: **22 offline controls**, test limit 180s per attempt, at most three numbered attempts; zero scientific executions.
- Pinned Linux image: `sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8`; Python **3.12.13**, SQLite **3.46.1**, botocore **1.43.108**, network disabled.
- Attempt 1: retained **preparation timeout** at 245.813s; Windows bind-mounted copying did not reach tests. Its command/timeout/partial container remain recorded. The harness was changed to the already established archive-transfer route, with no runtime fix prompted by this attempt.
- Attempt 2: **22 passed in 73.52s**; complete container/transfer/test wall time **102.219s**. XML, stdout, commands and source archive retained. No third attempt was used.
- Demonstrated: connection failure then success; exhaustion; later-page restart/exhaustion; non-retryable errors even with HTTP 500; incomplete/cyclic pagination; budget exhaustion; an actual killed stalled child; no upload-client use; durable pause and forbidden next admission; invalid child results; exact 82/1,418 staging; identity, active-slot, backup and notice corruption rejection; original history/sidecar preservation.
- Strict mypy passes for all five modified/core inventory/handover modules and the preparation helper. Final lint passes. The preparation helper is statically checked; it has **not** been exercised on a live reboot and is not represented as a qualified live deployment.
- Prior nine full-window refusal/permissive-response controls and v4 ledger-snapshot qualification are reused with their original evidence. Neither set was rerun.

## Preserved campaign and continuation

All **82 BACKED_UP / 1,418 PLANNED / zero active** identities, order, attempt numbers, exports, grades, backup receipts and notice history remain unchanged. Next: **sequence 83, B3, attempt 1**, execution `01a11705-11f1-792b-ae1e-36bfc6773842`. The two original raw FAILED exports and separate timing sidecars remain retained. No original was replayed or replaced.

The accepted v4 parent has **2,107 source members** verified unchanged; its signed freeze and **2,115 frozen members** also verify unchanged. The supplemental master preservation archive remains pinned at SHA-256 `a51a9ee4274de714c73a338de6905e846021ecb65143b936af8ddad5f0178fd6`, S3 version `G5ADuMNUUko.W7UqyBFXtP1WIPJUOqBz`. All 82 complete archives remain external pinned evidence assets on retained root/S3, with the verified reference set included; they are not replaced by the new metadata bundle.

Application/migrations, evidence requirements, arms, inputs, endpoints, oracle/analysis and **600-second windows** are byte-unchanged. The snapshot correction, refusal classification and permissive-response safeguards are unchanged. No timing analysis rule is amended here. No comparison restart is recommended for this operational-only change; retain version provenance and disclose that changed collector/watchdog overhead can affect runtime/load. Tests do not guarantee an error-free campaign or actual spoken-content exposure.

## Retained host reuse: qualified boundary, gated live boot

Recommend reusing `i-057344e5372faf62f` / encrypted 160-GiB root `vol-09dbb42bbf607f5de`; no replacement server is necessary. Stage new source and metadata roots, keep the old roots and PROTOCOL_STOP intact, import metadata only, and bind a new monotonic boot anchor to the **unchanged original campaign clock**. The fixed checks qualify metadata handover, not an unconditional AWS restart.

**Concrete missing prestart requirement:** the original preparation timers were disabled after v4 launch. Before starting the instance, establish and independently verify a two-hour external preparation StopInstances guard and its service execution-role permission, scoped to this instance. Proposed route is a single Sydney Scheduler target; provision none until the combined authorization. If it is unsupported or its role/permissions cannot be verified, leave compute stopped. AWS Scheduler delivery is not a hard real-time guarantee; bounded operator shutdown remains required.

After authorization, live gates must verify: exact accepted freeze and v4 parent chain; same instance/root ownership; all source/dependency/image hashes; postboot closed ledger/notices; all 82 local full archives and pinned S3 versions; permissions; free ports and no surviving owned processes; RAM/disk/storage headroom; complete current inventory; versioned prelaunch backup and independent readback; active watchdog, preparation guard and original absolute stop timer; fresh readiness/launch signatures bound to the actual host. Only then release the **new reviewed import pause** and start the standalone service. The old failure pause stays preserved. See `REUSE_RUNBOOK.md` and `reuse-plan.json` for exact paths, procedure and stop rules.

## Time, cost and storage — unchanged limits

As of **2026-10-09T10:49:19.212040+00:00**; current official AWS price/plan reads retained in `read-only-aws`:

- FREE/ACTIVE; available credits **US$116.26**; credits do not override campaign limits.
- Remaining reviewed planning allowance **274.513h**, plus 2h preparation and 0.5h shutdown. It was scaled only by genuinely completed originals; not reduced to force feasibility.
- Continuous 78-interval mean **621.947s**, giving a descriptive **244.98h** throughput reference. All 79 intervals, including the documented stopped-host handover, remain reported; projecting repeated downtime at that rate gives **358.18h**, which does not fit. Continuation is conditional on avoiding similar repeated interruptions, not a guaranteed 12-day result.
- Allowance-based finish **2026-10-20T23:20:04.872921+00:00**; conservative original-elapsed-clock committed estimate **US$54.710**; explicit resource estimate including prior compute/disks, retained storage and reserves **US$52.432**.
- **US$55 admission guard / US$65 total limit / US$1.25 reserve** unchanged. Budget margin corresponds to only **1.993h** additional review/preparation delay under the unchanged allowance. Recalculate before boot/admission and stop if it no longer fits; do not shrink the allowance or increase limits.
- Original absolute deadline remains **22 October 2026, 15:24:23.810674 UTC**; cost guard is tighter than that deadline. Billing lags, unexpected failures and retained storage can consume margin.
- Current all-version evidence: **538559335 bytes** vs 30-GiB cap. Observed maximum slot archive **8335773 bytes**. These measurements do not guarantee future growth; original storage and resource gates remain mandatory.
- Root retention decision remains due **11 October 2026, 09:33:51.252814 UTC**. No root/evidence deletion or retention extension is authorized by this task.

## One combined decision requested

Accept the exact inventory/archive identified in `candidate-package.json`, freeze v5 immutably against verified v4, and separately authorize guarded reuse/deployment and continuation from sequence 83 in the same instruction, under unchanged limits. Authorization must cover the mandatory independent prestart preparation guard; it is not proof of actual readiness or launch. Failed gates stop the procedure and retain evidence. No acceptance/freeze/launch has been recorded here.
