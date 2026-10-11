# DRIVER_FAILURE at the 145-original boundary — bounded diagnosis v1

## Verdict: exact driver cause unresolved; continuation remains blocked

AWS was confirmed **stopped** through a read-only EC2 request. No boot, pause
clearing, freeze, launch, scenario, application stack, dependency installation,
replay, replacement, regrading or evidence deletion occurred. Frozen v9's
3425 inventoried files passed their existing hashes.

The diagnostic could not retrieve the original exception/traceback because
read-only S3 transfers repeatedly encountered connection/body timeouts. Those
current retrieval errors are **not evidence of the original campaign cause**.
No code defect, resource cause, evidence-corruption cause, transient original
failure or safe unchanged-code recovery is established. No runtime diff or
correction candidate is justified; focused offline controls were not run.

## Supported sequence and identity

The retained closed-boundary snapshot is 145 BACKED_UP / 1,355 PLANNED / zero
active. All 1,500 identities and order match frozen bindings; the first 120 full
rows match frozen history. The original preservation procedure already verified
all 145 pinned backups and independently read back the full master on the host.
Retrieved diagnostic member hashes match their inspection manifest, but **the
complete inspection archive hash and SQLite master were not locally reverified**.
The local prefix is explicitly provisional; no stronger integrity claim is made.

The notices/journal prefix agree on this sequence:

- 17:56:31.611033Z: original sequence 145, **B3**, case p8v4-0361,
  execution **01a11705-11f1-7386-a804-76b957c218d5**, attempt 1 admitted.
- Original observation deadline: **18:06:47.750198Z**.
- 18:06:53.900124Z: master STOP_NEW_ADMISSIONS reason DRIVER_FAILURE.
  Durable master pause timestamp **18:06:53.908883Z**.
- 18:06:53.939767Z: sequence 145 EXPORTED; services quiesced at .949247Z.
- 18:07:21.797955Z: sequence 145 pinned cloud version verified.
- 18:07:21.811352Z: sequence 145 BACKED_UP.
- 18:07:31.210142Z: campaign journal prints VERIFIED BACKUP 145 / 1500.
- 18:07:39.739009Z: secondary PROTOCOL_STOP, ValueError **PAUSED_ADMISSIONS**;
  journal prints STOP at .759863Z. No sequence 146 ADMITTED notice.

Thus the DRIVER_FAILURE master pause was propagated **before** the verified
145 backup. After preserving 145, the next admission attempt was rejected by
the existing durable pause. It did not arise after that backup while running
sequence 146. The exact earlier driver exception time still needs its export.

Next is unchanged sequence **146, P2, attempt 1**,
**01a11705-11f1-772d-8190-c43552871801** (deadline null, state PLANNED).

## Source path explains propagation, not the underlying cause

Frozen collector.execute catches an unrecognized original driver exception,
stores type/detail/full traceback in trial.row.failure, writes DRIVER_FAILURE
in the slot ledger and a slot pause (`collector.py:442–484`). It continues
required collection/export. `runner.run_slot` copies that slot pause to the
master after collector exit (`runner.py:405–422`); `runner.run` backs up and
retires the closed slot, then journal.admit rejects a paused master.
The watchdog remained active and logged passing clock samples around the stop.
Nothing retrieved demonstrates it caused this DRIVER_FAILURE.

## Exactly missing

The preserved inspection has a master ledger/backup references, journals and
notices; it does **not** include slot 145's full execution export or slot ledger.
Those are retained in the verified original archive:

- SHA-256: `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`
- S3 version: `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`
- Bucket/key and size: `original145-receipt.json` (37,906,551 bytes).

Required members: `slot/executions/01a11705-11f1-7386-a804-76b957c218d5/export.json`
including failure.type/detail/traceback and recorded HTTP calls/observations;
`slot/ledger.sqlite3` DRIVER_FAILURE notice and checkpoints. Correlate those
with the archive's member manifest and independently verified export hash.
The campaign system journal only reports the propagated pause and final
PAUSED_ADMISSIONS; that secondary message is not the original traceback.

## Retained retrieval failures and checks

- Four pinned CLI ranges: response-body read timeouts; requests/results and
  partial files retained.
- Qualified small-range SDK transfer: raw urllib3 response-body timeout;
  original checkpoint/deadline, verified pieces and failure journals retained.
- Diagnostic read-only raw-timeout adapter and regional path-style attempt:
  partial verified ranges retained; no frozen transport code edited.
- Direct-body probe failed; path-style probe read 65,536 bytes successfully.
- Bounded signed-URL HTTPS attempt: connection timeout; URL never logged.
- First provisional reader hit its conservative 30-MiB member guard. A second
  separate reader retained the 40,796,760-byte campaign-journal member.
- Slot-145 pinned prefix SDK head and CLI retrieval: connection timeout; no
  export/traceback obtained. No authentication/evidence check was bypassed.
- Local stalled transfer processes were identified by their diagnostic command
  lines and stopped; their files/lock/checkpoint are retained, not erased.
- Existing qualification is reused; no pilot, full window or broad tests run.

## Minimum procedure before any resume

1. Complete version-pinned, bounded **read-only** retrieval of the inspection
   master and original 145 archive when connectivity permits; retain partials
   and original transfer checkpoints/deadlines. No AWS boot is needed.
2. Verify full hashes/members, the SQLite notice chain, export hash and failure
   traceback. Determine whether a correction is actually warranted. If so,
   version only the demonstrated path and run focused offline controls;
   otherwise justify unchanged-code recovery from the actual exception.
3. Qualify a 145-closed metadata boundary and the selected stopped-host recovery
   route, with exact 1,355 saved pending identities, original backups/grades,
   durable pause history, source/runtime provenance and prelaunch backups.
4. Recheck feasibility before proposing deployment, then reviewed authority,
   independent preparation guard, owned-unit quiescence, live gates, backup
   readback, genuine readiness/launch records and absolute timers. Do not clear
   this pause or admit 146 based on the secondary PAUSED_ADMISSIONS message.

At 2026-10-11T16:43:21.473752+00:00, the unchanged reviewed proportional allowance is
**262.316 hours + 2.5 hours preparation/shutdown**, against
**262.684 hours remaining** to the original deadline: currently
**does not fit**. This is
the prior planning allowance, not a runtime guarantee; it was not reduced to
obtain a pass. The 600-second-window floor alone is 225.833 hours and excludes
setup/backup/recovery. No new billing estimate or cost-feasibility pass is
claimed. US$60/US$65, 80-GiB caps and 22 October 2026 15:24:23.810674Z unchanged.

**Not ready to freeze or resume.** Exact root-cause evidence remains inaccessible
locally, and current unchanged planning allowance fails the remaining deadline.
All original evidence and pending identities remain retained.
