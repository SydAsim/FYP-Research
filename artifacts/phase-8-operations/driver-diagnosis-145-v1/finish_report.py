"""Record supported facts and exact missing evidence; never infer the driver cause."""
import collections
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[2]
INSPECT = Path("E:/p8driver145v1/provisional2/inspection")

def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()

def save(name: str, value: object) -> None:
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, indent=2)

def main() -> None:
    verified_members = {}
    for name, expected in read(INSPECT / "manifest.json")["files"].items():
        if name == "verified-master.tar.gz":
            continue
        assert sha(INSPECT / name) == expected
        verified_members[name] = expected
    rows = read(INSPECT / "read-only-ledger.json")["rows"]
    old = Path("E:/p8v9/source/artifacts/phase-8-runner-amendment/v4-complete/closed-120")
    bindings = read(old / "bindings.json")
    assert [{k: row[k] for k in bindings[0]} for row in rows] == bindings
    assert collections.Counter(row["state"] for row in rows) == {"BACKED_UP": 145, "PLANNED": 1355}
    assert rows[:120] == read(old / "ledger-read-only.json")["rows"][:120]
    assert rows[145]["execution_id"] == "01a11705-11f1-772d-8190-c43552871801"
    events = read(INSPECT / "historical-notices.json")["notices"]
    episode = [event for event in events if event.get("at", "") >= "2026-10-10T17:56:31" and
               (event.get("kind") != "TRANSITION" or event.get("state") in ("EXPORTED", "BACKED_UP"))]
    save("episode-notices.json", episode)
    journal = read(INSPECT / "campaign-journal.json")["stdout"]
    relevant = [line for line in journal.splitlines() if "python[1689]" in line and
                "2026-10-10T18:06:40" <= line[:19] <= "2026-10-10T18:07:45"]
    with (HERE / "campaign-excerpt.txt").open("x", encoding="utf-8") as output:
        output.write("\n".join(relevant) + "\n")
    freeze = REPO / "artifacts/phase-8-continuation-freeze/v9"
    manifest = read(freeze / "freeze-manifest.json")
    for name, expected in manifest["files"].items():
        assert sha(freeze / name) == expected, name
    save("frozen-v9-preservation.json", {"status": "PASS", "files": len(manifest["files"]),
         "freeze_manifest_sha256": sha(freeze / "freeze-manifest.json"),
         "package_hash": manifest["package_hash"], "frozen_changes": 0})
    at = datetime.now(UTC)
    stop = datetime.fromisoformat("2026-10-22T15:24:23.810674+00:00")
    remaining_hours = (stop - at).total_seconds() / 3600
    reviewed_hours = 290 * 1355 / 1498
    facts = {"status": "DIAGNOSIS_INCOMPLETE_RETRIEVAL_BLOCKED_NOT_READY_TO_RESUME",
       "at_utc": at.isoformat(), "counts": {"BACKED_UP": 145, "PLANNED": 1355},
       "all_1500_identity_order_match": True, "first_120_rows_exactly_preserved": True,
       "last_original": rows[144], "next": rows[145], "pause": read(INSPECT / "pause.json"),
       "frozen_v9_preservation": "PASS", "inspection_members_match_manifest": verified_members,
       "full_inspection_archive_hash": "NOT_COMPLETED_LOCALLY; PARTIALS_RETAINED",
       "complete_master_readback": "PASS_PREVIOUS_PRESERVATION_ON_HOST; NOT_REPEATED_LOCALLY",
       "driver_exception": "NOT_RETRIEVED", "underlying_cause": "UNDETERMINED",
       "original145": read(HERE / "original145-receipt.json"),
       "no_correction_candidate": "No code defect demonstrated; no unchanged-code recovery qualified",
       "offline_controls": "NOT_RUN_NO_DEMONSTRATED_DEFECT", "new_research_executions": 0,
       "host": "STOPPED_READ_ONLY_CONFIRMATION; NO_BOOT_OR_OTHER_HOST_MUTATION",
       "limits": {"admission_usd": 60, "total_usd": 65, "cloud_gib": 80, "local_backup_gib": 80,
                  "observation_seconds": 600, "stop_at": stop.isoformat()},
       "time_feasibility": {"available_hours_at_report": remaining_hours,
          "unchanged_reviewed_remaining_allowance_hours": reviewed_hours,
          "preparation_shutdown_hours": 2.5, "fits": reviewed_hours + 2.5 <= remaining_hours,
          "absolute_600_second_window_floor_hours": 1355 * 600 / 3600,
          "allowance_reduced": False, "deadline_reset": False}}
    save("diagnostic-facts.json", facts)
    report = f"""# DRIVER_FAILURE at the 145-original boundary — bounded diagnosis v1

## Verdict: exact driver cause unresolved; continuation remains blocked

AWS was confirmed **stopped** through a read-only EC2 request. No boot, pause
clearing, freeze, launch, scenario, application stack, dependency installation,
replay, replacement, regrading or evidence deletion occurred. Frozen v9's
{len(manifest['files'])} inventoried files passed their existing hashes.

The diagnostic could not retrieve the original exception/traceback because
read-only S3 transfers repeatedly encountered connection/body timeouts. Those
current retrieval errors are **not evidence of the original campaign cause**.
No code defect, resource cause, evidence-corruption cause, transient original
failure or safe unchanged-code recovery is established. No runtime diff or
correction candidate is justified; focused offline controls were not run.

## Supported sequence and identity

The retained closed-boundary snapshot is 145 BACKED_UP / 1,355 PLANNED / zero
active. All 1,500 identities and order match frozen bindings; the first 120 full
rows match frozen history. The original preservation procedure already verified
all 145 pinned backups and independently read back the full master on the host.
Retrieved diagnostic member hashes match their inspection manifest, but **the
complete inspection archive hash and SQLite master were not locally reverified**.
The local prefix is explicitly provisional; no stronger integrity claim is made.

The notices/journal prefix agree on this sequence:

- 17:56:31.611033Z: original sequence 145, **B3**, case p8v4-0361,
  execution **01a11705-11f1-7386-a804-76b957c218d5**, attempt 1 admitted.
- Original observation deadline: **18:06:47.750198Z**.
- 18:06:53.900124Z: master STOP_NEW_ADMISSIONS reason DRIVER_FAILURE.
  Durable master pause timestamp **18:06:53.908883Z**.
- 18:06:53.939767Z: sequence 145 EXPORTED; services quiesced at .949247Z.
- 18:07:21.797955Z: sequence 145 pinned cloud version verified.
- 18:07:21.811352Z: sequence 145 BACKED_UP.
- 18:07:31.210142Z: campaign journal prints VERIFIED BACKUP 145 / 1500.
- 18:07:39.739009Z: secondary PROTOCOL_STOP, ValueError **PAUSED_ADMISSIONS**;
  journal prints STOP at .759863Z. No sequence 146 ADMITTED notice.

Thus the DRIVER_FAILURE master pause was propagated **before** the verified
145 backup. After preserving 145, the next admission attempt was rejected by
the existing durable pause. It did not arise after that backup while running
sequence 146. The exact earlier driver exception time still needs its export.

Next is unchanged sequence **146, P2, attempt 1**,
**01a11705-11f1-772d-8190-c43552871801** (deadline null, state PLANNED).

## Source path explains propagation, not the underlying cause

Frozen collector.execute catches an unrecognized original driver exception,
stores type/detail/full traceback in trial.row.failure, writes DRIVER_FAILURE
in the slot ledger and a slot pause (`collector.py:442–484`). It continues
required collection/export. `runner.run_slot` copies that slot pause to the
master after collector exit (`runner.py:405–422`); `runner.run` backs up and
retires the closed slot, then journal.admit rejects a paused master.
The watchdog remained active and logged passing clock samples around the stop.
Nothing retrieved demonstrates it caused this DRIVER_FAILURE.

## Exactly missing

The preserved inspection has a master ledger/backup references, journals and
notices; it does **not** include slot 145's full execution export or slot ledger.
Those are retained in the verified original archive:

- SHA-256: `8abe7597a0e59154cf66e682fd08f3440fff815c458db0bdc8fe83666091ad24`
- S3 version: `RPSiYO12M2tM251ZCuLVOEK3IUn4NYHM`
- Bucket/key and size: `original145-receipt.json` (37,906,551 bytes).

Required members: `slot/executions/01a11705-11f1-7386-a804-76b957c218d5/export.json`
including failure.type/detail/traceback and recorded HTTP calls/observations;
`slot/ledger.sqlite3` DRIVER_FAILURE notice and checkpoints. Correlate those
with the archive's member manifest and independently verified export hash.
The campaign system journal only reports the propagated pause and final
PAUSED_ADMISSIONS; that secondary message is not the original traceback.

## Retained retrieval failures and checks

- Four pinned CLI ranges: response-body read timeouts; requests/results and
  partial files retained.
- Qualified small-range SDK transfer: raw urllib3 response-body timeout;
  original checkpoint/deadline, verified pieces and failure journals retained.
- Diagnostic read-only raw-timeout adapter and regional path-style attempt:
  partial verified ranges retained; no frozen transport code edited.
- Direct-body probe failed; path-style probe read 65,536 bytes successfully.
- Bounded signed-URL HTTPS attempt: connection timeout; URL never logged.
- First provisional reader hit its conservative 30-MiB member guard. A second
  separate reader retained the 40,796,760-byte campaign-journal member.
- Slot-145 pinned prefix SDK head and CLI retrieval: connection timeout; no
  export/traceback obtained. No authentication/evidence check was bypassed.
- Local stalled transfer processes were identified by their diagnostic command
  lines and stopped; their files/lock/checkpoint are retained, not erased.
- Existing qualification is reused; no pilot, full window or broad tests run.

## Minimum procedure before any resume

1. Complete version-pinned, bounded **read-only** retrieval of the inspection
   master and original 145 archive when connectivity permits; retain partials
   and original transfer checkpoints/deadlines. No AWS boot is needed.
2. Verify full hashes/members, the SQLite notice chain, export hash and failure
   traceback. Determine whether a correction is actually warranted. If so,
   version only the demonstrated path and run focused offline controls;
   otherwise justify unchanged-code recovery from the actual exception.
3. Qualify a 145-closed metadata boundary and the selected stopped-host recovery
   route, with exact 1,355 saved pending identities, original backups/grades,
   durable pause history, source/runtime provenance and prelaunch backups.
4. Recheck feasibility before proposing deployment, then reviewed authority,
   independent preparation guard, owned-unit quiescence, live gates, backup
   readback, genuine readiness/launch records and absolute timers. Do not clear
   this pause or admit 146 based on the secondary PAUSED_ADMISSIONS message.

At {at.isoformat()}, the unchanged reviewed proportional allowance is
**{reviewed_hours:.3f} hours + 2.5 hours preparation/shutdown**, against
**{remaining_hours:.3f} hours remaining** to the original deadline: currently
**{'fits' if facts['time_feasibility']['fits'] else 'does not fit'}**. This is
the prior planning allowance, not a runtime guarantee; it was not reduced to
obtain a pass. The 600-second-window floor alone is 225.833 hours and excludes
setup/backup/recovery. No new billing estimate or cost-feasibility pass is
claimed. US$60/US$65, 80-GiB caps and 22 October 2026 15:24:23.810674Z unchanged.

**Not ready to freeze or resume.** Exact root-cause evidence remains inaccessible
locally, and current unchanged planning allowance fails the remaining deadline.
All original evidence and pending identities remain retained.
"""
    with (HERE / "REPORT.md").open("x", encoding="utf-8", newline="\n") as output:
        output.write(report)
    save("diagnosis-inventory.json", {"files": {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}})
    print(json.dumps({"status": facts["status"], "frozen_files_verified": len(manifest["files"]),
                      "inspection_member_checks": len(verified_members), "counts": facts["counts"],
                      "time_feasibility": facts["time_feasibility"]}, indent=2))

if __name__ == "__main__":
    main()
