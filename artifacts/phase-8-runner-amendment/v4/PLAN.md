# V4 local ledger-read correction plan

Scope: inspect and reproduce the watchdog reader's inconsistent SQLite snapshot, then add only an explicit read transaction in a separate controls version. No research scenarios, application processes, Docker actions, AWS calls, pilot, full-window calibration, replay, regrade, acceptance, freeze or launch.

Files:

- `controls.py`: byte-preserving copy of v3 plus `db.execute("BEGIN")` inside `Journal.verify`; read all integrity/notice/slot queries from one snapshot. Existing rejection checks and writers unchanged.
- `controls.diff`: exact source difference for review.
- `test_ledger_snapshot.py`: deterministic temporary SQLite controls using named query boundaries and two connections. No timing sleeps or scientific fixtures executed.
- `prepare.py`, `qualify.py`: candidate assembly, fixed local check budget and preservation verification; no deployment capability.
- `qualification-plan.json`, result/log files, `REPORT.md`, inventories: scope, evidence, retained failures, limitations and non-launch provenance.

Fixed qualification set: **15 tests**, maximum **five minutes** for the local qualification invocation; each tool subprocess bounded. No test expansion to a pilot. Cases:

1–2. Legacy verifier falsely rejects a valid concurrent deadline or backup commit between notice and slot reads (WAL).
3–4. Revised verifier sees one consistent old snapshot under the same two WAL schedules; a subsequent verification sees the new committed transition and releases its transaction.
5. Rollback-journal reader defers the writer's commit until the reader finishes; valid writer succeeds afterward.
6. Uncontended valid ledger passes.
7–12. Genuine state mismatch, deadline mismatch, backup-hash mismatch, notice hash corruption, missing transition and damaged SQLite file remain rejected.
13. An uncommitted WAL write does not leak into the read snapshot.
14. Corruption committed during a read becomes visible and rejected on the next verification; consistent reads do not waive corruption checks.
15. A disposable copy of the independently retained master verifies exactly 38 BACKED_UP, 1,462 PLANNED, unchanged 1,500 saved identity tuples/attempts/order and sequence-39 B3 next identity. All 38 original export hashes remain unchanged.

Validation: focused pytest; Ruff lint; configured formatting; strict type checking of the candidate controls and tests; exact one-line semantic diff; protected source/freeze/historical/retained snapshot hashes before and after. No broad regression suite or application integration tests: this change affects research metadata read isolation only, and executable SQLite is the relevant integration boundary.

Stop on an unexpected control failure or preservation drift. Retain all unsuccessful invocations. The existing production pause remains; a passing candidate is not authorized to resume or deploy.
