# v6 candidate: backup closure and honest prelaunch order

Review candidate only. No acceptance, freeze, AWS start or launch is recorded.
The old v4 host/source/root and frozen v5 are retained. The new source route is
`/opt/fyp-phase8-continuation-v6`; new metadata is
`/var/lib/p8-continuation-v6/run`. Receipt directory is
`/var/lib/fyp-owner/continuation-v6-receipts`. Do not restart an old campaign
service or restore old application databases.

## Required order after separate authorization, if feasibility still passes

1. Verify exact v6 acceptance/freeze against signed frozen v5 and the historical
   parent chain. Record separate actual-run deployment authorization. Verify all
   original source/dependency/image hashes, owner permissions and unchanged
   policy. Recalculate time/cost with the original clock and reviewed allowance.
2. Before any host start, independently verify a two-hour preparation-stop guard
   bound to the actual start request and retained instance/root. Preserve the
   original absolute stop. Existing one-time schedules must not be assumed to
   cover a future boot. No new schedule is created by this candidate.
3. After an authorized boot, quiesce old operational services, preserve old pause
   and additional boot notices, verify the exact closed boundary and all 82
   full-archive and pinned-version backups. Verify source/runtime, permissions,
   capacity, complete storage inventory and absence of surviving owned services.
4. Run the unchanged external signed-gate checks and `reuse_prepare.py` with the
   new root. Its new import pause remains; binding a new monotonic boot anchor
   does not reset original campaign start/deadline. No research driver runs.
5. **Prelaunch backup:**

   ```sh
   python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py prelaunch \
     --root /var/lib/p8-continuation-v6/run --destination /var/lib/p8-continuation-v6/backup
   ```

   Requires valid accepted/frozen authority, original authorization and verified
   imported metadata. Copies all required restart history, original receipts,
   identities, ledger/notices and historical evidence. Readiness and the new
   launch receipt must be absent. Versioned upload and independent version-specific
   download, member hash checks and both continuation verifiers must succeed
   before `prelaunch-backup-proof.json` is written. This proof is not authorization.
6. Generate the new unit text without starting the campaign. Verify independent
   original-deadline and preparation timers and every existing readiness check
   from actual evidence. Only now issue genuine readiness with the prelaunch
   backup evidence, then the separately authorized signed CONTINUATION_LAUNCH
   bound to this candidate, run, host and readiness hash. No placeholder PASS
   record is permitted. A unit installer that needs full launch authority must
   wait until that authority exists; it cannot be used earlier to bypass it.
7. **Complete authorized backup:** run the same command with `complete` instead
   of `prelaunch`. Requires full existing launch/readiness checks, plus the
   prelaunch backup proof. Carries genuine readiness and launch receipt with the
   full metadata closure. A second versioned upload/readback produces
   `complete-backup-proof.json`, bound to run, restart boundary, freeze,
   readiness and launch receipt. The proof is stored after its archive is
   verified, avoiding a self-referential archive hash.
8. Install/start and verify watchdog and absolute timer using the already signed
   authority. Verify fresh RAM/disk/inventory/budget and next sequence 83. The
   existing boundary release now also verifies both pinned cloud/local backup
   proofs before releasing **only** CONTINUATION_REVIEW_REQUIRED. No later
   failure pause is cleared. Start the standalone campaign only after all gates.
9. Confirm actual sequence 83 B3 attempt 1 ID
   `01a11705-11f1-792b-ae1e-36bfc6773842`, watchdog/service/timer and backups.
   Follow the previously accepted retirement of the independent preparation guard
   only after successful actual admission. Keep the absolute deadline active.

## Failure and limits

On missing/corrupt metadata, unsuccessful readback, unavailable inventory,
authorization or resource failures: retain partial directories, archives,
receipts and logs; stop preparation/admissions under the existing bounded
shutdown procedure. An ambiguous upload is reconciled read-only; never blindly
repeat a PUT. No phase switch substitutes a readiness or launch signature.

Ordinary complete per-slot/master backups carry the restart boundary/history,
all retained receipts and pause/preparation records. The readback verifier checks
hashes and retained evidence; it does **not** claim authorization or that an old
readiness record applies to a new host. Live authorization remains independently
verified by ContinuationAuthority and the release/runner gates.

No change to pause shutdown policy: a paused service alone does not stop EC2.
The existing watchdog/deadline mechanisms and independent preparation timer
remain required; operator bounded shutdown applies on preparation failure.
Original root retention decision: **11 October 2026, 09:33:51.252814 UTC**.
Original campaign stop: **22 October 2026, 15:24:23.810674 UTC**.
US$55 admission guard / US$65 total / US$1.25 reserve remain unchanged.
