# AWS collector qualification v2 — diagnostic amendment

The v1 original B3 result, refusal slot left unadmitted, SQL ledger, snapshots,
raw tone/ACK evidence and failure notice remain unchanged. v1 was exported to S3
with checksum verification and the server automatically stopped. No main inputs
ran. Its final snapshot started 0.106181 s before the cutoff and ended 0.038593 s
afterward. This does not pass the strict snapshot-start gate.

Files added: `worker_v2.py` is the exact preserved research collector with one
stop-condition change; `runner_v2.py` binds that collector in the research process
and seals the additional code; `qualify.py` runs separately labelled diagnostics;
`parallel-v2/*` retains the finite ownership-isolation plan with numeric host
operator UID/GID; `finish-v2.sh` retains export/shutdown after both finite gates.
Their invariants are complete-window collection, source integrity, no replacement
of original outcomes, and exclusive resource ownership. Application behaviour,
migrations, fixture contents, oracle and analysis pipeline remain unchanged.

The final read must now **start** at or after the original cutoff. No shortening
or extending the 600-second estimand window: this read establishes coverage at
the original cutoff; event-time grading continues using recorded timestamps and
the existing cutoff. Its small acquisition overshoot is reported.

Use `/srv/fyp-p82-v2` and separate backups. Clean B3 is DIAGNOSTIC_RERUN linked to
the original execution. P1 is a first execution of the previously unadmitted
refusal recipe in a new queue. Retain all records, including unsuccessful ones.
No automatic replay of either original driver after a host restart.

The conditional parallel gate still consists of exactly two calibration-only
recipes, P2 restart-before-repair and P2 cache-loss, under separate network/PID
namespaces. Their source dependencies are read-only. Run as the host operator
UID/GID so the proctor can inspect retained output. Probe `/work` disk capacity
only after verifying host Docker and output directories occupy the same device.
The sealed v1 parallel draft was never admitted; retain it unchanged.

The approved US$2 ceiling and original four-hour powered-session envelope remain.
Replace the reboot-relative stop timer with the original absolute UTC deadline
2026-10-05 21:11:53, not four further hours. Main admission, freeze and launch
remain disabled. Every failure stops new admissions and triggers evidence
retention; no further performance optimization exercise is included.
