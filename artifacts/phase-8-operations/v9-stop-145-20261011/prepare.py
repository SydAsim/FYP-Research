"""Prepare the existing authorized closed-boundary preservation procedure."""
from pathlib import Path

here = Path(__file__).resolve().parent
artifacts = here.parents[1]
previous = artifacts / "phase-8-operations/v7-stop-120-20261010"
deployment = artifacts / "phase-8-continuation-deployment/v9"
for name in ("ops.py", "actual-deployment-binding.json"):
    with (here / name).open("xb") as target:
        target.write((deployment / name).read_bytes())
body = (previous / "preserve-stop-boundary.sh").read_text(encoding="utf-8")
body = body.replace("continuation-v7", "continuation-v9")
body = body.replace("'BACKED_UP':120,'PLANNED':1380", "'BACKED_UP':145,'PLANNED':1355")
body = body.replace("WALL_CLOCK_BACKWARD_STOP_ADMISSIONS", "DRIVER_FAILURE")
body = body.replace("stop-120", "stop-145").replace("stopped-120", "stopped-145")
body = body.replace("rows[:120]", "rows[:145]").replace("rows[120]", "rows[145]")
body = body.replace("CLOSED_120", "CLOSED_145").replace("all_120", "all_145")
body = body.replace("2026-10-09 23:05:00 UTC", "2026-10-10 13:10:00 UTC")
body = body.replace("2026-10-09 16:00:00 UTC", "2026-10-10 13:10:00 UTC")
body = body.replace("import json,collections,subprocess,sys,shutil,tarfile,time", "import json,collections,subprocess,sys,shutil,tarfile,time,sqlite3")
body = body.replace("write_new(out/'read-only-ledger.json',{'rows':rows})", """write_new(out/'read-only-ledger.json',{'rows':rows})
with sqlite3.connect((root/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.execute('BEGIN')
    notices=[json.loads(r[0]) for r in db.execute('SELECT body FROM notices ORDER BY n')]
write_new(out/'historical-notices.json',{'notices':notices})
write_new(out/'last-original.json',rows[144])""")
with (here / "preserve-stop-boundary.sh").open("x", encoding="utf-8", newline="\n") as target:
    target.write(body)
print("Prepared v9/145 closed-boundary preservation; no application/source changes")
