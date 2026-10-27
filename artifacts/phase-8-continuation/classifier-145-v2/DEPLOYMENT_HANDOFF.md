# Future retained-host readiness handoff — NOT authorization

No command below was executed against the stopped host in this task. Current
time/cost gates fail. Acceptance/freeze and deployment authority are unstarted.

The future reviewed route retains the master ledger at
`/var/lib/p8-continuation-v9/run` and all original exports/backups in place.
Before boot: verify accepted policy/receipt hashes, feasibility and independent
preparation-stop guard/readback; preserve superseded owned schedules safely.
After boot: preserve old unit state, verify ownership, stop owned campaign and
watchdog units, verify inactivity and preserve the original durable pause.

Then verify the newly accepted source/dependency closure, actual 145-original
root and pinned backups. The added read-only gate is to be invoked from the
verified source's runner directory using the existing pinned interpreter:

```bash
# Run only after separately authorized preparation and exact source verification.
# SOURCE_DIR must be the actual verified source root recorded by that deployment.
cd "$SOURCE_DIR/artifacts/phase-8-runner-amendment/v4-complete"
timeout --signal=TERM --kill-after=5s 120s "$SOURCE_DIR/.venv/bin/python" -B - <<'PY'
import json
from pathlib import Path
from closed145 import verify_retained_root
proof = verify_retained_root(Path('/var/lib/p8-continuation-v9/run'))
print(json.dumps(proof, sort_keys=True))
PY
```

This is an additional external readiness requirement. It does not replace the
existing source authority, signed receipts, full pinned master/archive verification,
resource/capacity/permission checks or backup readback. Successful output is
`READ_ONLY_CLOSED145_GATE_NOT_AUTHORIZATION`, 145 BACKED_UP, 1,355 PLANNED and
sequence 146/P2/attempt 1. Any failure stops preparation; preserve output and
follow the existing bounded shutdown procedure. Do not reset rows or replay slots.

Retain the prior freeze/acceptance/launch receipts as historical records. Any
new source binding must use this package's exact hash and its frozen-v9 parent;
old receipts cannot authorize a changed source. Host/runtime provenance must
record the actual new inventory, refusal hash and closed145 gate hash even where
inherited module labels still say v9.

Only after every future gate passes: verified prelaunch backup → genuine readiness
and separate launch records → complete backup/readback → reviewed durable pause
release → standalone service. Next must be saved sequence 146, execution
`01a11705-11f1-772d-8190-c43552871801`. Existing shutdown policy is unchanged here.
