"""Render saved counts and a descriptive chart; no fitting, network or regrading.

ReportLab is used only for a standalone SVG in the existing document runtime.
The qualified statistical runtime and its saved outputs are unchanged.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reportlab.graphics import renderSVG
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.colors import HexColor

HERE = Path(__file__).resolve().parent


def read(name: str) -> Any:
    return json.loads((HERE / name).read_bytes())


def preserve_or_write(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("EXISTING_DERIVATIVE_DIFFERS:" + path.name)
        return
    with path.open("xb") as stream:
        stream.write(data)


def main() -> None:
    proof = read("analysis/verification.json")
    if proof["status"] != "PASS_ANALYSIS_EXECUTED_INTERPRETATION_REVIEW_REQUIRED":
        raise ValueError("VERIFIED_ANALYSIS_REQUIRED")
    for name, expected in proof["files"].items():
        if hashlib.sha256((HERE / "analysis" / name).read_bytes()).hexdigest() != expected:
            raise ValueError("ANALYSIS_OUTPUT_DRIFT:" + name)
    rows = read("dataset/analysis-rows.json")
    records = read("dataset/recorded-results.json")
    summary = read("analysis/summary.json")
    folder = HERE / "presentation"
    folder.mkdir(exist_ok=True)
    counts: list[dict[str, Any]] = []
    for arm in ("B3", "P1", "P2"):
        for endpoint, values in summary["values_by_arm"][arm].items():
            counts.append(
                {
                    "arm": arm,
                    "endpoint": endpoint,
                    "planned_arm": 500,
                    **{
                        status: values.get(status, 0)
                        for status in ("TRUE", "FALSE", "UNKNOWN", "NOT_APPLICABLE")
                    },
                }
            )
    csv_stream = io.StringIO(newline="")
    writer = csv.DictWriter(csv_stream, fieldnames=list(counts[0]))
    writer.writeheader()
    writer.writerows(counts)
    preserve_or_write(folder / "endpoint-counts.csv", csv_stream.getvalue().encode())
    recovery_families = (
        "full-before-correction",
        "late-decisive-ack",
        "partial-time",
        "reconnect-third-revision",
        "restart-before-repair",
    )
    by_family: dict[str, Any] = {}
    for family in recovery_families:
        by_family[family] = {
            arm: dict(
                Counter(
                    r["values"]["complete_corrective_communication"]
                    for r in records
                    if r["generator_family"] == family and r["arm"] == arm
                )
            )
            for arm in ("B3", "P1", "P2")
        }
    # Report only recorded P2 telemetry; NOT_APPLICABLE baseline fields are not missing successes.
    p2_telemetry: Counter[str] = Counter()
    for record in records:
        if (
            record["arm"] != "P2"
            or record["values"]["complete_corrective_communication"] == "NOT_APPLICABLE"
        ):
            continue
        if "revised_grade" in record:
            mechanism = record["revised_grade"]["repair_mechanism"]
            p2_telemetry.update(o["state"] for o in mechanism["obligations"])
        else:
            p2_telemetry.update(record["obligations"])
    unsupported = []
    index = {(r["case_id"], r["arm"]): r for r in records}
    for record in records:
        if record["values"]["unsupported_exposed_claim"] == "TRUE":
            unsupported.append(
                {
                    "sequence": record["sequence"],
                    "case_id": record["case_id"],
                    "arm": record["arm"],
                    "family": record["generator_family"],
                    "paired_values": {
                        arm: index[(record["case_id"], arm)]["values"]["unsupported_exposed_claim"]
                        for arm in ("B3", "P1", "P2")
                    },
                }
            )
    facts = {
        "kind": "DESCRIPTIVE_READOUT_OF_FROZEN_ANALYSIS_NO_NEW_TESTS",
        "input_count": 500,
        "original_count": 1500,
        "endpoint_counts": counts,
        "complete_communication_by_recovery_family": by_family,
        "recorded_P2_repair_states_in_33_opportunities": dict(p2_telemetry),
        "unsupported_claim_cases_all_strata": unsupported,
        "raw_status_business_cross": [
            {"raw_status": status, "final_business_state_correct": value, "count": n}
            for (status, value), n in Counter(
                (r["raw_status"], r["values"]["final_business_state_correct"]) for r in records
            ).items()
        ],
        "missing_timing": sum(r["duration_seconds"] is None for r in rows),
        "interpretation": (
            "UNKNOWN remains separate; the figure is descriptive, not an interval or human study"
        ),
    }
    facts_path = folder / "descriptive-facts.json"
    if facts_path.exists():
        if json.loads(facts_path.read_bytes()) != facts:
            raise ValueError("EXISTING_DESCRIPTIVE_FACTS_CHANGED")
    else:
        preserve_or_write(facts_path, json.dumps(facts, indent=2).encode())

    drawing = Drawing(1020, 340)
    drawing.add(
        String(
            26,
            312,
            "Ordinary corrected updates and complete corrective communication",
            fontName="Helvetica-Bold",
            fontSize=15,
        )
    )
    drawing.add(
        String(
            26,
            290,
            "33 predeclared recovery inputs per arm | Scripted tone + ACK protocol evidence only",
            fontName="Helvetica",
            fontSize=10,
        )
    )
    colors = [HexColor("#95d9c3"), HexColor("#efb3ab"), HexColor("#d4dae0")]
    for x, title, endpoint in (
        (76, "Supported update delivered after challenge", "corrective_delivery_after_challenge"),
        (566, "Update + explicit withdrawal when required", "complete_corrective_communication"),
    ):
        chart = HorizontalBarChart()
        chart.x, chart.y, chart.width, chart.height = x, 82, 380, 150
        chart.categoryAxis.style = "stacked"
        chart.categoryAxis.categoryNames = ["P2", "P1", "B3"]
        chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 33, 11
        chart.data = [
            tuple(
                summary["values_by_arm"][arm][endpoint].get(status, 0) for arm in ("P2", "P1", "B3")
            )
            for status in ("TRUE", "FALSE", "UNKNOWN")
        ]
        for i, color in enumerate(colors):
            chart.bars[i].fillColor = color
            chart.bars[i].strokeColor = HexColor("#ffffff")
        chart.barLabelFormat = lambda v: str(int(v)) if v else ""
        chart.barLabels.fontName, chart.barLabels.fontSize = "Helvetica-Bold", 10
        drawing.add(chart)
        drawing.add(String(x - 36, 253, title, fontName="Helvetica-Bold", fontSize=11))
        drawing.add(String(x + 110, 53, "Number of inputs (out of 33)", fontSize=9))
    for i, label in enumerate(("TRUE", "FALSE", "UNKNOWN")):
        x = 340 + i * 114
        drawing.add(Rect(x, 26, 12, 12, fillColor=colors[i], strokeColor=None))
        drawing.add(String(x + 18, 28, label, fontSize=10))
    drawing.add(
        String(
            26,
            8,
            "UNKNOWN is not failure. These counts do not establish human hearing "
            "or improved user beliefs.",
            fontSize=8,
        )
    )
    svg = renderSVG.drawToString(drawing)
    preserve_or_write(folder / "corrective-communication.svg", svg.encode())
    print(json.dumps({"status": "SAVED_DESCRIPTIVE_TABLES_AND_SVG", "folder": str(folder)}))


if __name__ == "__main__":
    main()
