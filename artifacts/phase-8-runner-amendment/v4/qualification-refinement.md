# Fixed-set refinement before second qualification

The first invocation retained 15 passing SQLite controls and passing lint/format, then stopped on six type-check errors caused by the validation command's global `--follow-imports=skip`. That flag made Pydantic and pytest imports untyped; it is removed rather than weakening strict checking or changing the one-line controls correction.

Read-only inspection shows the retained production master uses rollback journal mode `DELETE`. The legacy backup-transition reproducer therefore uses DELETE mode; the deadline reproducer retains WAL. Revised WAL controls and the revised rollback reader/writer control remain. The same 15 controls are rerun, with no new research executions or extra pilot. Each invocation retains its own evidence and five-minute bound. The original predeclared plan and unsuccessful invocation remain unchanged.
