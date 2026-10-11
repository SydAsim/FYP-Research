# V4 ledger snapshot correction — local review candidate

**Result: PASS for the bounded local correction.** AWS was stopped before this work; zero AWS actions were performed. No campaign restart, freeze or launch occurred. No research scenario, application stack, pilot or full-window calibration was run.

## Cause and smallest correction

Frozen v3 `Journal.verify()` reads the notice chain and then the slot rows using separate SELECTs. Under the connection's legacy transaction settings, `with connection` does not itself open a read transaction. A valid writer can atomically commit a slot transition and its matching notice after the reader has finished reading notices but before it reads slot rows. The verifier compares the earlier notices with later slot rows and raises `LEDGER_TRANSITION_DRIFT` even though the writer committed consistent data. The current consistent stopped snapshot and slot-38 backup timing fit this explanation.

The code defect is reproduced, including the production master's DELETE journal mode. The exact historical watchdog interleaving was not captured, so these controls confirm the vulnerability and a matching failure mechanism, rather than recovering the original reader's memory state.

The candidate is a byte-preserving copy of v3 `controls.py`, with exactly one executable line inserted:

```diff
 def verify(self) -> None:
     with self.connect() as db:
+        db.execute("BEGIN")
         if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
```

All integrity, notice-chain and row-transition queries now share one read snapshot. The existing context manager commits or rolls back that transaction, releasing it on both success and rejection. No writer, error check, pause rule, state transition, classification or recovery policy was changed. No retry or exception suppression was added.

This behaviour agrees with [Python 3.12's connection context manager documentation](https://docs.python.org/3.12/library/sqlite3.html#how-to-use-the-connection-context-manager) and [SQLite's isolation documentation](https://www.sqlite.org/isolation.html). WAL readers retain one snapshot while a writer commits; rollback-journal writers must wait for a reader to finish before committing. The tests exercise both behaviours with actual separate SQLite connections.

## Fixed qualification results

Plan recorded before checks: 15 distinct controls, five-minute invocation limit, no timing sleeps. Named trace-callback query boundaries force the precise commit opportunity. The second invocation refined the legacy backup control to the actual retained master's DELETE mode; the deadline control retains WAL. Count and scope stayed at 15.

| Control | Checks | Result |
|---|---:|---|
| Legacy deadline/backup commit between notice and slot queries | 2 | Reproduced false drift; subsequent uncontended legacy verification succeeds |
| Revised WAL deadline/backup interleavings | 2 | Consistent read succeeds; next read sees committed transition; transaction released |
| Revised DELETE reader/writer interaction | 1 | Writer commit is blocked during read, then succeeds after read; valid ledger passes |
| Valid ledger | 1 | PASS |
| Real state, deadline, backup-hash, notice-hash, missing-notice and physical-file corruption | 6 | All rejected; failure releases read transaction |
| Uncommitted WAL corruption | 1 | Invisible to reader; rolled-back writer leaves valid data |
| Corruption committed during the reader snapshot | 1 | Current snapshot is consistent; next verification rejects the newly committed corruption |
| Disposable copy of retained master and export hashes | 1 | Exact 38 BACKED_UP / 1,462 PLANNED boundary and all 1,500 identity tuples preserved |

Final pytest: **15 passed in 1.33 seconds** (subprocess wall 2.141 seconds). Ruff lint and formatting PASS. Strict mypy PASS for the candidate controls and test module, with normal dependency type information. Full final qualification, including before/after preservation hashing, took **16.75 seconds**.

The passing attempt is `qualification-1791481410661852100/`. Each command, exit code, measured wall time and stdout/stderr is retained there. The controlled legacy exceptions and genuine-corruption exceptions are asserted successful test observations, not ignored failures.

## Retained unsuccessful attempts

- Assembly attempt 1 stopped before candidate creation because an LF literal did not match the parent's CRLF bytes. `prepare-attempt1.txt` records it. Assembly now preserves the parent's newline bytes.
- Qualification `qualification-1791481274390847600/`: 15 tests passed in 1.31 seconds; lint and format passed; six type errors occurred because the validation command used global `--follow-imports=skip`, treating Pydantic/pytest as untyped. That validation configuration was corrected without weakening strict checking. The failed invocation is retained (61.359 seconds); it was not overwritten or called PASS.

These are local assembly/validation attempts. They are not scientific executions, new inputs or replacements for original campaign outcomes.

## Preservation and exact boundary

Both before and after the passing qualification verified:

- 4,489 protected historical file hashes.
- 1,788 accepted v3 source members and the accepted archive hash.
- 1,796 immutable v3 freeze members and its exact parent-bound manifest fingerprint.
- 93 independently retained stop-snapshot members, the version-specific archive hash, and all 38 original export hashes.

These are overlapping preservation groups, not independent sample counts. Both historical raw FAILED originals, their grades and separately accepted timing sidecars remain unchanged. The disposable copy test checks the immutable identity fields `(sequence, case_id, arm, attempt, execution_id, fixture_hash)` against the saved 1,500 rows, retaining attempt 1 and saved order throughout.

Next untouched original remains sequence **39**, B3, `p8v4-0240`, execution **01a11705-11f0-73c0-af15-dd9f1d590b08**. It remains PLANNED. No command was replayed, no deadline reset, no grade recomputed and no campaign outcome replaced. The original 22 October 2026 15:24:23.810674 UTC deadline and US$55/US$65 limits are unchanged.

## Files and provenance

- `controls.py`: sole runtime delta; base SHA-256 `2adc25953cb0bc5b04b6afba46ed8fae9aed3af22838cf5fff9b76dd9d34d966`, candidate SHA-256 `0b62290a17840f10eb2353c10af5a1b54d472f95faaad26899b7ef4cf1f885ec`.
- `controls.diff`: complete executable diff against preserved v3.
- `test_ledger_snapshot.py`: 15 SQLite-only controls.
- `prepare.py`, `qualify.py`: local assembly and bounded validation only.
- `PLAN.md`, `qualification-plan.json`, `qualification-refinement.md`, command logs/results: predeclared scope, measured checks and retained attempts.
- `candidate-inventory.json`, `candidate-package.json`, `final-verification.json`: separate review fingerprints and qualification summary. These are not acceptance, freeze or launch receipts.

Parent package remains `2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736`; parent archive `0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf`; immutable freeze manifest `49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86`.

## Limits and disposition

This is a qualified **local patch candidate**, not an amended deployable campaign archive. Frozen v3 was not edited in place. The one-line replacement must be integrated into a separately inventoried campaign package with its parent provenance before any future acceptance/freeze/launch decision. No approval or launch authority is inferred from the existing v3 receipts.

The controls qualify SQLite consistency on this local runtime, including both journal modes. They do not constitute a fresh Linux-host deployment qualification or guarantee that no other runner defect exists. A read snapshot is consistent as of its start; later corruption is rejected on a subsequent verification rather than magically becoming visible inside the earlier snapshot. The existing independent watchdog checks and corruption rejection remain necessary. No automatic-host-shutdown behaviour was changed by this narrow correction.

**Stop point: reviewable v4 delta with focused PASS evidence; AWS remains unstarted, 38 originals retained and 1,462 untouched. No freeze or launch.** The separately documented retained-root decision deadline remains 10 October 2026, 22:14:53 Pakistan time; this work does not extend retention or authorize deletion.
