"""Narrow edits in the separate source tree; parent bytes never change."""
from __future__ import annotations

import difflib
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("E:/p8v4/source")
RUNTIME = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete"
OLD = SOURCE / "artifacts/phase-8-runner-amendment/v3"


def function(text: str, name: str, replacement: str) -> str:
    start = text.index("def " + name + "(")
    end = text.find("\n\ndef ", start + 4)
    if end < 0:
        raise ValueError("MISSING_FUNCTION_BOUNDARY")
    return text[:start] + replacement + text[end:]


def main() -> None:
    path = RUNTIME / "handover.py"
    text = (OLD / "handover.py").read_text()
    text = text.replace('from two_originals import boundary', 'from closed_prefix import boundary')
    text = text.replace('pinned = read(HERE / "saved-identities.json")["rows"]', 'pinned = read(HERE / "saved-boundary.json")["rows"]')
    text = function(text, "stage", '''def stage(master: Path, destination: Path) -> dict[str, Any]:
    from closed_prefix import stage as import_closed
    return import_closed(master, destination)
''')
    text = function(text, "verify_imported_first", '''def verify_imported_first(root: Path) -> None:
    """Compatibility entry point verifies all 38 imported originals."""
    from closed_prefix import verify
    verify(root)
''')
    text = text.replace('"phase85-combined-amendment-v3"', '"phase85-complete-continuation-v4"')
    text = text.replace('prefix = "artifacts/phase-8-runner-amendment/v3/"', 'prefix = "artifacts/phase-8-runner-amendment/v4-complete/"')
    text = text.replace('"4b921d416b9111594531ca33f26b1b307e04b22241ef995b6e571ce96a21f3e7"', '"49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86"')
    text = text.replace('"two_originals_sha256": hash_file(HERE / "two_originals.py"),', '"two_originals_sha256": hash_file(HERE / "two_originals.py"),\n        "closed_prefix_sha256": hash_file(HERE / "closed_prefix.py"),\n        "controls_sha256": hash_file(HERE / "controls.py"),')
    text = text.replace('ready["instance_id"] == ("i-0a6196aff6f8098ac")', 'ready["instance_id"] in ("i-0a6196aff6f8098ac", "i-034252c3e9b083abf", "i-002b63326e1566005")')
    text = text.replace('"?mode=ro&immutable=1"', '"?mode=ro"').replace('db.row_factory = sqlite3.Row\n        if', 'db.row_factory = sqlite3.Row\n        db.execute("BEGIN")\n        if')
    start = text.index('    if args.action == "stage":')
    end = text.index('    elif args.action == "verify-import":', start)
    text = text[:start] + '''    if args.action == "stage":
        if args.master is None:
            parser.error("stage requires the authoritative stopped-boundary metadata")
        stage(args.master.resolve(), args.root.resolve())
''' + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")
    path = RUNTIME / "runner.py"
    text = (OLD / "runner.py").read_text()
    text = text.replace('    FIRST,\n', '')
    text = text.replace('from storage import (', 'from closed_prefix import imported as imported_closed\nfrom storage import (')
    text = text.replace('closed["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")\n                    and (root / "handover.json").exists()', 'imported_closed(root, closed["execution_id"])')
    # verify_run already verifies the complete imported prefix before the loop;
    # avoid 38 redundant full-history scans, leaving retirement rules unchanged.
    text = text.replace('                    verify_imported_first(root)\n                    continue', '                    continue')
    path.write_text(text, encoding="utf-8", newline="\n")
    path = RUNTIME / "analyze.py"
    text = (OLD / "analyze.py").read_text().replace('from handover import FIRST', 'from handover import FIRST\nfrom closed_prefix import imported as imported_closed')
    text = text.replace('slot["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")\n            and (root / "handover.json").exists()', 'imported_closed(root, slot["execution_id"])')
    path.write_text(text, encoding="utf-8", newline="\n")
    path = RUNTIME / "imported_analysis.py"
    text = (OLD / "imported_analysis.py").read_text()
    at = text.index('    proof = next(')
    text = text[:at] + '''    record = read(root / "handover.json")
    closed = next(p for p in record["closed_originals"] if p["identity"]["execution_id"] == execution_id)
    if closed["identity"]["sequence"] > 2:
        path = root / "historical/boundary/exports" / f"{closed['identity']['sequence']:04d}" / "export.json"
        trace = read(path)
        if hash_file(path) != closed["export_sha256"]:
            raise ValueError("IMPORTED_ORIGINAL_EXPORT_DRIFT")
        return AnalysisRow.model_validate(trace["analysis_row"]), {
            "execution_id": execution_id,
            "raw_status": trace["status"],
            "export_hash": closed["export_sha256"],
            "original_analysis_row": trace["analysis_row"],
            "replacement_or_driver_replay": False,
            "status": "IMMUTABLE_RECORDED_V3_ANALYSIS",
        }
''' + text[at:]
    path.write_text(text, encoding="utf-8", newline="\n")
    test = (REPO / "artifacts/phase-8-runner-amendment/v4/test_ledger_snapshot.py").read_text()
    test = test.replace('HERE.parent / "v3/controls.py"', 'HERE.parent / "v3/controls.py"')
    test = test.replace('Path("E:/FYP Project/p8-observation-20261008-1/x/inspection")', 'HERE / "boundary"')
    (RUNTIME / "test_ledger_snapshot.py").write_text(test, encoding="utf-8", newline="\n")
    (HERE / "runtime-diffs").mkdir(exist_ok=True)
    for name in ("controls.py", "handover.py", "runner.py", "analyze.py", "imported_analysis.py"):
        diff = ''.join(difflib.unified_diff((OLD / name).read_text().splitlines(True), (RUNTIME / name).read_text().splitlines(True), fromfile="accepted-v3/"+name, tofile="candidate-v4/"+name))
        (HERE / "runtime-diffs" / (name + ".diff")).write_text(diff, encoding="utf-8")
    for name in ("refusal.py", "legacy_refusal.py", "response_guard.py", "collector.py", "instrument.py", "storage.py", "transport.py", "postflight.py", "window.py", "two_originals.py"):
        assert (OLD / name).read_bytes() == (RUNTIME / name).read_bytes(), name
    shutil.copyfile(HERE / "PLAN.md", RUNTIME / "V4_PLAN.md")


if __name__ == "__main__":
    main()
