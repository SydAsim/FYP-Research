"""Apply narrow edits only to newly copied candidate files."""
# ruff: noqa: E501 -- retained literal source fragments in this one-time assembly helper

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def replace_function(text: str, name: str, replacement: str) -> str:
    start = text.index("def " + name + "(")
    end = text.find("\n\ndef ", start + 4)
    if end < 0:
        raise ValueError(name)
    return text[:start] + replacement + text[end:]


def main() -> None:
    h = HERE / "handover.py"
    text = h.read_text()
    text = replace_function(
        text,
        "closed_boundary",
        """def closed_boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    from two_originals import boundary
    pinned = read(HERE / "saved-identities.json")["rows"]
    # Verify frozen schedule columns as well as every existing execution identity.
    if len(saved) != 1500 or any(any(a[k] != b[k] for k in ("sequence", "case_id", "arm", "attempt", "fixture_hash")) for a, b in zip(rows, saved, strict=True)):
        raise ValueError("SAVED_ORDER_OR_BINDING_DRIFT")
    boundary(rows, pinned)
""",
    )
    text = replace_function(
        text,
        "stage",
        """def stage(master: Path, first: Path, destination: Path, *, second: Path,
          first_archive: Path, second_archive: Path) -> dict[str, Any]:
    from two_originals import stage as import_two
    return import_two(master, first, second, first_archive, second_archive, destination)
""",
    )
    text = replace_function(
        text,
        "verify_imported_first",
        '''def verify_imported_first(root: Path) -> None:
    """Compatibility entry point now verifies BOTH immutable originals."""
    from two_originals import verify
    verify(root)
''',
    )
    text = text.replace("phase85-continuation-v1", "phase85-combined-amendment-v3").replace(
        "phase85-refusal-amendment-v1", "phase85-preflight-amendment-v2"
    )
    text = text.replace(
        'prefix = "artifacts/phase-8-continuation/v1/"',
        'prefix = "artifacts/phase-8-runner-amendment/v3/"',
    )
    text = text.replace(
        '"refusal_sha256": hash_file(HERE / "refusal.py"),',
        '"refusal_sha256": hash_file(HERE / "refusal.py"),\n        "response_guard_sha256": hash_file(HERE / "response_guard.py"),\n        "two_originals_sha256": hash_file(HERE / "two_originals.py"),',
    )
    text = text.replace(
        'parser.add_argument("--first", type=Path)',
        """parser.add_argument("--first", type=Path)
    parser.add_argument("--second", type=Path)
    parser.add_argument("--first-archive", type=Path)
    parser.add_argument("--second-archive", type=Path)""",
    )
    text = text.replace(
        "if args.master is None or args.first is None:",
        "if any(p is None for p in (args.master, args.first, args.second, args.first_archive, args.second_archive)):",
    )
    text = text.replace(
        "stage(args.master.resolve(), args.first.resolve(), args.root.resolve())",
        "stage(args.master.resolve(), args.first.resolve(), args.root.resolve(), second=args.second.resolve(), first_archive=args.first_archive.resolve(), second_archive=args.second_archive.resolve())",
    )
    h.write_text(text, encoding="utf-8")
    # Keep main launch hard blocked in this unaccepted candidate. Stage is metadata only.
    r = HERE / "runner.py"
    text = r.read_text().replace(
        'closed["execution_id"] == FIRST',
        'closed["execution_id"] in (FIRST, "01a11705-11f0-7826-bd9d-9066d82c4452")',
    )
    r.write_text(text, encoding="utf-8")
    s = HERE / "storage.py"
    text = s.read_text().replace(
        '    config = read(source / "run.json")\n    for label,',
        '    if (source / "historical").exists():\n        shutil.copytree(source / "historical", destination / "historical")\n    config = read(source / "run.json")\n    for label,',
    )
    s.write_text(text, encoding="utf-8")
    from handover import ro_rows

    (HERE / "saved-identities.json").write_text(
        json.dumps(
            {
                "rows": ro_rows(Path("C:/p8c1/m/x/slot")),
                "kind": "EXISTING_IDENTITIES_NO_GENERATION",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    shutil.copyfile(HERE.parent / "v2/calibration-inputs.json", HERE / "calibration-inputs.json")
    for path in (Path("C:/fyp-p85/stopped-attempt1/slot1"),):
        protected = json.loads((HERE / "preservation-before.json").read_text())
        from prepare import digest

        for p in path.rglob("*"):
            if p.is_file():
                protected[str(p)] = digest(p)
        (HERE / "preservation-before.json").write_text(
            json.dumps(protected, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
