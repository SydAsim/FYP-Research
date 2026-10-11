# Phase 8.3 postflight status — 6 October 2026, 23:03 Pakistan time

The cloud pilot runner has ended. Its 95,449,610-byte evidence archive was uploaded with a verified S3 checksum and versioned receipt at 17:32:27 UTC. EC2 was independently confirmed STOPPED. The final 24-slot accounting and comparisons await local archive verification; runner completion is not a claim that all endpoints passed.

Archive SHA-256: `b863ee5eec8a409373f67a09c55571e96746b05b4e5c6bc09218c7e1b02a03b7`.
S3 version: `nbJrmG0vT96bOYiMMsnggMYLfgKhFVaK`.

## Recovery

The original storage-list connection error, original 90-second download timeout and partial archive, a stopped stalled download, aborted larger-range attempt, and SDK connection-closure failure are retained in separate artifact directories. A separate direct download attempt has a finite deadline. No experimental driver was rerun and no observation window or endpoint was changed.

The new `recovery-v6/recover.py` helper runs independently from a normal terminal using the existing fyp-research credential provider and Sydney bucket. It reuses only prior verified pieces, downloads remaining ranges from the pinned version with bounded network retries, journals transport failures, and verifies the entire archive hash. Its eight simultaneous reads are evidence downloads, not additional experimental executions or research parallelism.

At this snapshot 73 of 1457 pieces were verified; the helper was running. This is a snapshot, not a completion claim. Download dependencies are isolated under recovery-v5/sdk; application dependencies, migrations, fixtures and historical artifacts are unchanged. Ruff and strict mypy checks passed with untyped SDK imports isolated.

Only after two local copies and the S3 version verify does the existing exact-owner postflight remove instance `i-021200fbdba05bb8e` and root disk. The helper then writes a new recovered-outcomes report. Earlier failed reports and files are not overwritten. If recovery fails, the disk and evidence remain and the failure is recorded. Keep the computer awake and connected.

Two local copies are partitions of the same SSD; versioned S3 is a separate storage location. The stopped server has no ongoing compute charge; its retained disk and S3 storage still cost money. Cleanup has not yet been confirmed.

All 1939 protected historical/source hashes remain identical. Main study: UNSTARTED and UNFROZEN; all 500 inputs across B3/P1/P2 remain. No main admissions, optional study extensions, or application behaviour changes.
