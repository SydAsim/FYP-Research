"""Descriptive six-family accounting; no inferential or superiority verdict."""

import csv
import json
from pathlib import Path
from typing import Any

from research.remedies.preserve import OUTPUT

ENDPOINTS = (
    "final_business_state_correct", "correct_final_update", "explicit_retraction",
    "incompatible_stale_exposure", "unsupported_exposed_claim",
)


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    families = {row["fixture"]["family"] for row in rows}
    arms = ("B3", "P1", "P2")
    counts = {
        arm: {
            endpoint: {
                status: sum(
                    str(r.get("grade", {}).get(endpoint, "MISSING")).upper() == status
                    for r in rows if r["arm"] == arm
                )
                for status in ("TRUE", "FALSE", "UNKNOWN", "NOT_APPLICABLE", "MISSING")
            }
            for endpoint in ENDPOINTS
        }
        for arm in arms
    }
    paired = []
    for family in sorted(families):
        selected = {r["arm"]: r for r in rows if r["fixture"]["family"] == family}
        paired.append({
            "generator_family": family,
            "speaker_id": None,
            "audio_type": "SCRIPTED_TONE",
            "arms_observed": sorted(selected),
            "endpoints": {
                endpoint: {a: selected[a].get("grade", {}).get(endpoint, "MISSING")
                           for a in arms if a in selected}
                for endpoint in ENDPOINTS
            },
        })
    return {
        "classification": "EXPLORATORY_DESCRIPTIVE_ONLY",
        "specified_fixture_families": len(families), "planned_slots": 18,
        "retained_executions": len(rows), "by_arm": counts, "paired": paired,
        "inference": "NONE; family/speaker population independence not established",
        "phase8_started": False,
    }


def main() -> None:
    manifest = json.loads((OUTPUT / "planned/manifest.json").read_text(encoding="utf-8"))
    rows = [json.loads(Path(e["path"]).read_text(encoding="utf-8"))
            for e in manifest["executions"]]
    (OUTPUT / "exploratory-summary.json").write_text(
        json.dumps(summary(rows), indent=2) + "\n", encoding="utf-8"
    )
    with (OUTPUT / "exploratory-outcomes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "fixture", "generator_family", "arm", "status", *ENDPOINTS,
            "repair_persisted", "repair_completed", "repair_pending", "trace_path",
        ])
        writer.writeheader()
        for execution, row in zip(manifest["executions"], rows, strict=True):
            writer.writerow({
                "fixture": row["fixture"]["id"], "generator_family": row["fixture"]["family"],
                "arm": row["arm"], "status": row["status"],
                **{e: row.get("grade", {}).get(e, "MISSING") for e in ENDPOINTS},
                **{f"repair_{e}": row.get("repair_telemetry", {}).get(e, "UNKNOWN")
                   for e in ("persisted", "completed", "pending")},
                "trace_path": execution["path"],
            })
    print(json.dumps(summary(rows), indent=2))


if __name__ == "__main__":
    main()
