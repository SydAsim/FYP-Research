"""Finite read-only descriptive report after standalone postflight, no new runs."""

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUTPUT = REPO / "artifacts/phase-8.3-outcomes.md"


def render(proof: dict[str, Any], accounting: dict[str, Any]) -> str:
    measurements = {
        r["execution_id"]: r for r in proof["independent_regrades"] if "execution_id" in r
    }
    blocks = accounting["blocks"]
    pairs = [b for b in blocks if len(b["slots"]) == 2]
    slots = accounting["slots"]
    complete = all(s["state"] == "EXPORTED" for s in slots)
    regrades_ok = len(measurements) == 24 and all(
        r["oracle_replay"] == "IDENTICAL"
        and r["post_cutoff_snapshot_start"]
        and not r["missing_final_anchor"]
        and r["driver_status"] == "COMPLETED"
        for r in measurements.values()
    )
    qualified = (
        complete
        and regrades_ok
        and len(pairs) == 3
        and not any(b["pressure_recorded"] for b in blocks)
    )
    exported = sum(s["state"] == "EXPORTED" for s in slots)
    verdict = "PASS for observed pairs" if qualified else "FAIL/UNRESOLVED; inspect saved statuses"
    text = [
        "# Phase 8.3 — retained calibration outcomes",
        "",
        "Main study: **UNSTARTED / UNFROZEN**. All 500 inputs remain; no main execution.",
        "",
        f"Planned executions: **24**; exported slots: **{exported}**.",
        "Six original contexts across three arms, plus six repeats. Repeats do not enlarge N.",
        "",
        f"Finite pilot qualification: **{verdict}**.",
        "No superiority or novelty follows from this bookkeeping. Tone/ACK protocol evidence only.",
        "",
        "## All planned outcomes",
        "",
        "| Slot | Arm | Label | State | Endpoints | Recorded mechanisms | Trace |",
        "|---|---|---|---|---|---|---|",
    ]
    for slot in slots:
        row = measurements.get(slot.get("execution_id"), {})
        values = json.dumps(row.get("grade_values", "UNKNOWN_NO_VALID_EXPORT"), sort_keys=True)
        mechanism = json.dumps(
            {
                "unsafe_attempt": row.get("unsafe_attempt", "UNKNOWN"),
                "repair": row.get("repair_mechanism", "UNKNOWN"),
            },
            sort_keys=True,
        )
        link = (
            f"[trace](<{row['trace']}>)"
            if row.get("trace")
            else "No valid export; original retained"
        )
        text.append(
            f"| {slot['slot_id']} | {slot['arm']} | {slot['label']} | {slot['state']} | "
            f"{values.replace('|', '/')} | {mechanism.replace('|', '/')} | {link} |"
        )
    text += [
        "",
        "## Schedule evidence",
        "",
        f"Median serial release-to-result seconds: {accounting['serial_block_median_seconds']}",
        f"Median paired release-to-result seconds: {accounting['paired_block_median_seconds']}",
        "",
        "| Block | Slots | Wall seconds | Peak used GiB | Min available GiB | Max sampled CPU |",
        "|---|---|---|---|---|---|",
    ]
    for block in blocks:
        cpu = block.get("maximum_cpu_fraction")
        text.append(
            f"| {','.join(block['slots'])} | {len(block['slots'])} | "
            f"{block['released_wall_seconds']:.3f} | "
            f"{block['peak_used_memory_bytes'] / 1024**3:.3f} | "
            f"{block['minimum_available_memory_bytes'] / 1024**3:.3f} | "
            f"{cpu if cpu is not None else 'UNKNOWN'} |"
        )
    gaps = [r["maximum_start_gap_seconds"] for r in measurements.values()]
    text += [
        "",
        "## Storage and projection",
        "",
        f"Retained raw directory bytes: {accounting['raw_directory_bytes']}",
        f"Retained backup directory bytes: {accounting['backup_directory_bytes']}",
        f"Verified archive bytes: {proof['receipt']['bytes']}; two local copies plus S3.",
        f"Maximum recorded poll-start gap seconds: {max(gaps) if gaps else 'UNKNOWN'}.",
        f"1500 × median serial block, hours: {accounting['serial_1500_reference_hours']}.",
        "This excludes setup/export/maintenance and is not a whole-bank runtime qualification.",
        "WAL allocation is not per-minute growth. Inspect per-trace start/end resources.",
        "",
        "## Recommendation and remaining gates",
        "",
        (
            "At most two lanes for observed restart/cache pairs; other recipes remain serial. "
            "Review case eligibility, host dependence and sustained disk capacity before freezing."
            if qualified
            else "Keep the main schedule serial; no two-lane launch qualification is established."
        ),
        "Untested variants, prolonged load and host-loss recovery remain unqualified.",
        "Review traces for the first blocking step. Baseline updates count.",
        "Tone/ACK establishes no intelligible speech exposure or human understanding.",
        "Local copies share one physical SSD. S3 is a separate location.",
        "Main readiness: **review required; no freeze or 500-input launch authorized**.",
        "",
    ]
    return "\n".join(text)


def main() -> None:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    until = datetime.fromisoformat(config["deadline"]) + timedelta(hours=2)
    while datetime.now(UTC) < until:
        failures = sorted(HERE.glob("failure-*.json"))
        if failures:
            content = (
                "# Phase 8.3 — postflight stopped\n\n"
                "Evidence and original attempts are retained. Main study remains unstarted.\n\n"
                f"Failure: [{failures[-1].name}](<{failures[-1]}>). "
                "Reconcile saved IDs and files; do not replay drivers or replace outcomes.\n"
            )
            break
        if (HERE / "complete.json").exists():
            proof = json.loads((HERE / "verified-backups.json").read_text(encoding="utf-8"))
            root = Path(proof["primary"]).parent / ("extracted-" + proof["receipt"]["sha256"])
            accounting_path = root / "fyp-p83-v1/accounting.json"
            content = (
                render(proof, json.loads(accounting_path.read_text(encoding="utf-8")))
                if accounting_path.exists()
                else "# Phase 8.3 — retained evidence, missing accounting\n\n"
                "UNRESOLVED: archived source/polls and backups retained; reconstruct accounting "
                "without replacing observations. Main study remains unstarted.\n"
            )
            break
        time.sleep(60)
    else:
        content = (
            "# Phase 8.3 — postflight unresolved\n\n"
            "No completion notice within the finite postflight deadline. "
            "Inspect preserved controller/host state. Do not replay cases. Main study unstarted.\n"
        )
    with OUTPUT.open("x", encoding="utf-8") as output:
        output.write(content)


if __name__ == "__main__":
    main()
