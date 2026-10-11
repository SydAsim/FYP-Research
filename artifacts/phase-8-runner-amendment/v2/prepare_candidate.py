"""Local candidate preparation. Does not freeze, authorize or contact AWS."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(name: str, body: object) -> None:
    with (HERE / name).open("x", encoding="utf-8") as stream:
        json.dump(body, stream, indent=2, default=str)


def prepare() -> None:
    # Capture the actual source, frozen receipts/packages and retained originals.
    paths: list[Path] = []
    inventory = json.loads(
        (REPO / "artifacts/phase-8-review-freeze/v2/review-inventory.json").read_text()
    )
    paths.extend(REPO / p for p in inventory["files"])
    for directory in (
        "phase-7-pilot",
        "phase-8-review-freeze/v2",
        "phase-8-continuation/v1",
        "phase-8-continuation-freeze/v1",
        "phase-8-continuation-deployment/v1",
        "phase-8-runner-amendment/v1",
    ):
        root = REPO / "artifacts" / directory
        paths.extend(
            p
            for p in root.rglob("*")
            if p.is_file()
            and not {"__pycache__", "node_modules", ".next", ".venv"}.intersection(p.parts)
        )
    paths.extend(p for p in Path("C:/p8c1/m/x/slot").rglob("*") if p.is_file())
    paths.extend(p for p in Path("C:/p8c1/s/x/slot").rglob("*") if p.is_file())
    save("preservation-before.json", {str(p.resolve()): digest(p) for p in paths})
    base = REPO / "artifacts/phase-8-continuation/v1"
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
    ):
        shutil.copyfile(base / f"{name}.py", HERE / f"{name}.py")
    shutil.copyfile(
        REPO / "artifacts/phase-8-runner-amendment/v1/refusal.py", HERE / "legacy_refusal.py"
    )
    for name in ("test_controls.py", "test_storage.py", "test_transport.py", "test_collector.py"):
        shutil.copyfile(REPO / "artifacts/phase-8-runner-amendment/v1" / name, HERE / name)
    first = REPO / "artifacts/phase-8-runner-amendment/v1/retained-first-original.json"
    shutil.copyfile(first, HERE / "retained-first-original.json")
    second = next(Path("C:/p8c1/s/x/slot").glob("executions/*/export.json"))
    shutil.copyfile(second, HERE / "retained-second-original.json")
    prepare_bank()


def prepare_bank() -> None:
    from research.study_v4.design import materialize

    cases = materialize(calibration=True)
    refusal = next(c for c in cases if c.generator_family == "resource-only")
    clean = next(c for c in cases if c.stratum == "CLEAN")
    bank = []
    plan = []
    for kind in ("refusal", "defect", "recovery"):
        for arm in ("B3", "P1", "P2"):
            name = f"cal-v4-preflight-v2-{kind}-{arm.lower()}"
            case = (clean if kind == "defect" else refusal).model_copy(update={"case_id": name})
            bank.append(case.model_dump(mode="json"))
            plan.append({"id": name, "arm": arm, "kind": kind, "recipe": case.generator_family})
    sentinel = clean.model_copy(update={"case_id": "cal-v4-preflight-v2-never-admit"})
    save(
        "calibration-inputs.json",
        {"calibration_inputs": bank, "admission_sentinel": sentinel.model_dump(mode="json")},
    )
    save(
        "calibration-plan.json",
        {
            "version": "phase85-preflight-amendment-v2",
            "status": "DECLARED_NOT_ACCEPTED_NOT_FROZEN",
            "scope": "LOCAL_CALIBRATION_ONLY",
            "main_campaign": "PAUSED",
            "cloud_budget_usd": 0,
            "planned_live_executions": 9,
            "concurrency": 1,
            "observation_seconds_per_execution": 600,
            "live_wall_budget_seconds": 6600,
            "cases": plan,
            "checks": [
                "three arms exact evidenced refusals; no retry; full window; independent grades",
                "verified dual local backups before permitted next admission",
                "three arm technical-defect durable pauses and rejected sentinel admission",
                "three same-execution/deadline interrupted resumes with unchanged POST count",
                "negative recognition and corrupted-evidence checks; failed-backup admission stop",
                "main admission blocked; historical hashes and remaining identity order unchanged",
            ],
            "stop": (
                "No new local admission after 110 minutes or unexpected failure. "
                "Retain every attempt. "
                "An admitted collector finishes its original window and backup; never truncate it."
            ),
            "evidence": "Scripted tone/client protocol acknowledgements, not human comprehension.",
            "backup": (
                "Existing qualified OfflineCloud; two retained local roots; "
                "not fresh S3 qualification"
            ),
        },
    )


if __name__ == "__main__":
    prepare()
