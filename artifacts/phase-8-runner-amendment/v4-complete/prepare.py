"""Prepare a separate review candidate; never run a driver or AWS mutation."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OLD = HERE.parent / "v2"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name: str, value: object) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def main() -> None:
    protected = json.loads((OLD / "preservation-before.json").read_text())
    for p in OLD.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            protected[str(p)] = digest(p)
    protected[str(HERE.parent / "v2-review-candidate.tar.gz")] = digest(
        HERE.parent / "v2-review-candidate.tar.gz"
    )
    for p, expected in protected.items():
        if digest(Path(p)) != expected:
            raise ValueError("HISTORICAL_DRIFT: " + p)
    write("preservation-before.json", protected)
    for name in (
        "collector",
        "controls",
        "runner",
        "storage",
        "transport",
        "postflight",
        "window",
        "instrument",
        "handover",
        "refusal",
        "legacy_refusal",
        "test_controls",
        "test_storage",
        "test_transport",
        "test_collector",
        "test_preflight",
    ):
        shutil.copyfile(OLD / (name + ".py"), HERE / (name + ".py"))
    for name in (
        "retained-first-original.json",
        "retained-second-original.json",
        "first-original-proposed-sidecar.json",
        "second-original-proposed-sidecar.json",
        "mypy-sdk-boundary.ini",
    ):
        shutil.copyfile(OLD / name, HERE / name)
    write(
        "qualification-plan.json",
        {
            "scope": "LOCAL_OFFLINE_ONLY_NOT_MAIN",
            "cloud_spending_usd": 0,
            "new_live_executions": 0,
            "reused_full_window_pg_checks": 9,
            "maximum_wall_seconds": 1800,
            "maximum_focused_checks": 120,
            "checks": [
                "All eight literal permissive call sites and forwarding ack path",
                "Six B3/P1/P2 unexpected 409/500 controls",
                "Recorded expected stale refusals and declared barrier polling",
                "Unexpected response persists despite later success; "
                "observation/recovery/backup/admission controls",
                "Exactly two BACKED_UP plus 1498 PLANNED real metadata import",
                "Reject altered order, identities, attempts, active slots, "
                "incomplete backups and sidecars",
                "Existing 68 offline controls and 61 instrument/application "
                "regressions reused/run unchanged",
            ],
            "stopping_rule": "Stop on failed verification or 1800 seconds; retain attempts; "
            "never admit main or provision AWS",
            "application_changes": False,
            "window_seconds": 600,
        },
    )
    records: list[dict[str, Any]] = []
    sources = list((REPO / "artifacts/phase-8-study-design/v4/calibration").rglob("*.json"))
    sources += list((REPO / "artifacts/research-remedies-v2").rglob("*.json"))
    sources += list((OLD / "qualification").rglob("*export*.json"))
    for p in sources:
        try:
            row = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(row, dict) or "http" not in row:
            continue
        for n, c in enumerate(row["http"]):
            path = c.get("path", "")
            if (c.get("status", 0) or 0) >= 400 and (
                path.endswith("/playback-events")
                or path.endswith("/release")
                or path.endswith("/claims")
                or path.endswith("/b3/schedule")
                or "/barriers/" in path
            ):
                records.append(
                    {
                        "source": str(p),
                        "source_sha256": digest(p),
                        "call_index": n,
                        "call": c,
                        "arm": row.get("arm"),
                        "family": row.get("input", {}).get("generator_family"),
                        "row": row,
                    }
                )
    write("recorded-response-inventory.json", records)
    print(
        "Prepared separate candidate, protected files:",
        len(protected),
        "recorded rejected calls:",
        len(records),
    )
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for r in records:
        c = r["call"]
        # Collapse variable trace IDs to useful response examples below.
        b = c.get("response", {})
        k = (
            r["arm"],
            r["family"],
            c["path"].split("/")[-1],
            c["status"],
            b.get("type"),
            b.get("detail"),
        )
        unique[k] = {"request": c.get("request"), "response": b}
    write("response-examples.json", [{"context": k, **v} for k, v in unique.items()])


if __name__ == "__main__":
    main()
