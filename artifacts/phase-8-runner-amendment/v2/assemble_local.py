"""Apply the explicit candidate overlay; never edit its frozen parents."""

from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise ValueError(f"EXPECTED_PARENT_FRAGMENT_MISSING:{path.name}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def assemble() -> None:
    replace(
        HERE / "runner.py",
        "return ContinuationAuthority(root, config)",
        'raise ValueError("PREFLIGHT_REVIEW_REQUIRED_MAIN_BLOCKED")',
    )
    replace(
        HERE / "runner.py",
        "CONTINUATION_IMPORT_REQUIRED_NO_NEW_IDENTITIES",
        "PREFLIGHT_REVIEW_REQUIRED_MAIN_BLOCKED",
    )
    replace(HERE / "runner.py", "    ContinuationAuthority,\n", "")
    replace(
        HERE / "collector.py",
        'case.case_id == "cal-v4-p85a-defect-03"',
        'case.case_id in {"cal-v4-preflight-v2-defect-b3", '
        '"cal-v4-preflight-v2-defect-p1", "cal-v4-preflight-v2-defect-p2"}',
    )
    parent = REPO / "artifacts/phase-8-runner-amendment/v1"
    qualify = (parent / "qualify.py").read_text(encoding="utf-8")
    qualify = qualify.replace(
        '"""Four fixed serial, local PostgreSQL executions. No AWS or main capability."""',
        '"""Nine fixed serial local executions, three arms; no main capability."""',
    )
    qualify = qualify.replace(
        '"arm": "B3",',
        '"arm": name.rsplit("-", 1)[-1].upper() '
        'if name != "cal-v4-preflight-v2-never-admit" else "B3",',
    )
    qualify = qualify.replace("cal-p85a-", "cal-p85b-")
    qualify = qualify.replace("cal-v4-p85a-never-admit-05", "cal-v4-preflight-v2-never-admit")
    qualify = qualify.replace("3000", "6600").replace('"planned": 4', '"planned": 9')
    start = qualify.index("    for group, ids in [")
    end = qualify.index("        if time.monotonic()", start)
    qualify = (
        qualify[:start]
        + """    groups = [("continuation", [f"cal-v4-preflight-v2-refusal-{a}"
                                for a in ("b3", "p1", "p2")])]
    groups += [("defect-" + a, [f"cal-v4-preflight-v2-defect-{a}",
                    "cal-v4-preflight-v2-never-admit"]) for a in ("b3", "p1", "p2")]
    groups += [("recovery-" + a, [f"cal-v4-preflight-v2-recovery-{a}"]) for a in ("b3", "p1", "p2")]
    for group, ids in groups:
"""
        + qualify[end:]
    )
    qualify = qualify.replace(
        "650 * len(ids)", '650 * sum(i != "cal-v4-preflight-v2-never-admit" for i in ids)'
    )
    qualify = qualify.replace('group == "recovery"', 'group.startswith("recovery")')
    qualify = qualify.replace('group == "defect"', 'group.startswith("defect")')
    qualify = qualify.replace('output / "recovery-before.json"', 'output / f"{group}-before.json"')
    qualify = qualify.replace(
        'output / "defect-pause-proof.json"', 'output / f"{group}-pause-proof.json"'
    )
    qualify = qualify.replace("== 2\n", "== 3\n")
    qualify = qualify.replace(
        'assert backups[0]["at"] < admissions[1]["at"]',
        'assert all(backups[i]["at"] < admissions[i + 1]["at"] for i in range(2))',
    )
    # Each arm makes one final synthesis/claim request; no non-retryable retry.
    qualify = qualify.replace(
        'c["path"] == "/internal/phase6/b3/schedule"',
        'c["path"] == ("/internal/phase6/b3/schedule" if trace["arm"] == "B3" '
        'else "/internal/phase3/claims")',
    )
    (HERE / "qualify.py").write_text(qualify, encoding="utf-8")
    launcher = (parent / "Qualify-Local.ps1").read_text(encoding="utf-8")
    launcher = launcher.replace("phase85-runner-amendment-v1", "phase85-runner-amendment-v2")
    launcher = launcher.replace("p85a-", "p85b-").replace(
        "phase-8-runner-amendment/v1", "phase-8-runner-amendment/v2"
    )
    launcher = launcher.replace("time.sleep(4000)", "time.sleep(8000)")
    (HERE / "Qualify-Local.ps1").write_text(launcher, encoding="utf-8")


if __name__ == "__main__":
    assemble()
