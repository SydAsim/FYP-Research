# Post-acceptance deployment order (not authorization)

This supersedes only operational limit/path details of the retained v6
`REUSE_RUNBOOK.md`; all existing gates and shutdown bounds remain.

1. Obtain exact combined human acceptance, including US$60 admission/US$65 total,
   60-GiB cloud/local archive caps and verified redundant future staging retention.
   Record its verbatim statement outside the frozen source. Run prepared
   `freeze_accepted.py PACKAGE_SHA ARCHIVE_SHA ACCEPTANCE_JSON` only then.
   Acceptance JSON requires `explicit_human_acceptance: true`, package/archive
   hashes, `operational_limits_sha256` and `verbatim_user_instruction`.
   Verify freeze, parent v5 chain and preserved v6 qualification. No v6 freeze
   exists and none is invented. Save separate actual-run deployment authorization.
2. Recheck live pricing, credits/plan, all earlier costs/storage, original-clock
   planning allowance, deadlines and ownership of retained instance/root. If any
   estimate or gate fails, retain stopped resources and evidence, escalate within
   original retention bound; do not start merely to gather missing evidence.
3. Before host start, install/independently verify the reviewed preparation-stop
   guard for the actual start request. Preserve the original absolute stop.
   A schedule from a previous preparation attempt does not qualify this boot.
4. Verify complete deployment archive and each member at short path
   `/opt/fyp-phase8-continuation-v7`. Pin runtime/dependencies to prior records.
   Place new accepted/frozen receipts under
   `/var/lib/fyp-owner/continuation-v7-receipts` with restricted owner key.
5. Verify stopped boundary, quiescence/ports, all originals/backups/notice chains,
   network/IAM/S3 versioning, RAM/disk and timer evidence. Prepare external signed
   reuse gates bound to v7 package. Execute existing `reuse_prepare.py` with new
   root `/var/lib/p8-continuation-v7/run`; preserve old root/pause. New raw policy
   remains original 55/30; runtime authenticates the signed 60/60 overlay separately.
6. With genuine acceptance/freeze and prelaunch gates, run:

   ```sh
   python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py prelaunch \
     --root /var/lib/p8-continuation-v7/run --destination /var/lib/p8-continuation-v7/backup
   ```

   Verify versioned cloud copy, bounded independent readback and metadata closure.
   No readiness or launch placeholder. Build genuine readiness only afterwards,
   with all original `CHECKS`, original policy commitment, actual host/boot,
   prelaunch proof and `operational_limits_sha256` equal to
   `60d8dbb2b7f3f6a83bd442ac491316e9a9e17d45a039e4b59d9400821d377791`.
7. Sign separate CONTINUATION_LAUNCH only under explicit deployment authority.
   Its body has the same amendment hash, original policy hash, exact v7 package,
   identities, v5 immediate parent freeze, actual instance and readiness hash;
   expires at the original deadline. Then run the same backup command with
   `complete`. Verify both real backup proofs and readbacks before release.
8. Install/verify new service/watchdog units and original absolute timer. Recheck
   live effective US$60 cost guard, US$65 feasibility, 60-GiB all-version inventory,
   dedicated local archive cap, 50-GiB working cap, 1-GiB reservation and unchanged
   resource thresholds. Old unit text must not be reused without verifying its
   exact v7 source/root binding. Release only CONTINUATION_REVIEW_REQUIRED using
   the existing reviewed boundary function, then start the standalone service.
9. Report actual sequence-83 admission, ID, active timers/service/host, verified
   backups and remaining count. Retire preparation guard only according to the
   already reviewed successful-admission rule. Follow original bounded shutdown
   on any failed preparation/gate; do not bypass pause, reset clock or repeat writes.

Every future local archive and pinned S3 version remains. New redundant staging
removal applies only to sequence >82, after BACKED_UP, actual proof verification
and exact owned path checks. Missing/corrupted/partial staging is retained and
failure stops new admissions. No old original, root evidence or S3 version is
deleted. The retained root disposition deadline remains 11 October
09:33:51.252814 UTC; campaign hard stop remains 22 October 15:24:23.810674 UTC.
