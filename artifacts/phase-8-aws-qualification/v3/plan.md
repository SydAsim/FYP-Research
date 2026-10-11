# Executing-adapter integrity boundary v3

Review found that v2 seals copied adapter files in evidence but its preserved
capsule inventory does not cover the executing files outside that capsule.
This separate version adds integrity checks at parent/collector entry, before
each admission and during each minute of active collection. A durable pause and
event stop new admissions; active collection retains its original deadline and
records source drift using the existing collector failure/missingness path.

Files: `integrity.py` verifies the SQL-registered manifest and exact executing
adapter paths; `runner_v3.py` carries this boundary into spawned collectors;
`test_integrity.py` checks actual changed/missing files and manifest damage.
Their invariant is rejection of executing-source drift without outcome replacement.
No application, schema, fixture, oracle, grading, timeout or window changes.

V2 finite execution evidence remains immutable and is labelled as v2. V3 inherits
its exact final-read semantics; qualify the new integrity boundary using isolated
regression fixtures and an init/verify-only host check. Admit zero business slots
in that check. Do not represent init-only evidence as another full-window run.
The main 500-input campaign remains blocked, unreviewed and unfrozen.
