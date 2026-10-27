"""Typeset the final-study review manuscript; read saved results only."""

from __future__ import annotations

import hashlib
import json
import re
from html import escape
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESULTS = ROOT / "artifacts/phase-8-final-analysis/v1"
OUTPUT = ROOT / "output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf"


def inline(value: str) -> str:
    value = escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*(.+?)\*", r"<i>\1</i>", value)
    return re.sub(
        r"(https://[^\s<]+)",
        r'<link href="\1" color="#214e73">\1</link>',
        value,
    )


def contract_figure(width: float) -> Drawing:
    figure = Drawing(width, 116)
    labels = [
        ("Intent", "Accepted revision and target"),
        ("Effect", "Provider commit / cancellation / UNKNOWN"),
        ("Evidence", "Observation source, resource version, validity"),
        ("Claim", "Permission to publish a specific outcome statement"),
        ("Playback", "Start, decisive progress, completion, interruption"),
        ("Repair", "Persistent obligation and delivery record"),
    ]
    for index, (label, detail) in enumerate(labels):
        y = 98 - 18 * index
        figure.add(Rect(0, y, width, 17, strokeWidth=0, fillColor=colors.HexColor("#edf2f5")))
        figure.add(String(7, y + 5, label, fontName="TNR-Bold", fontSize=9))
        figure.add(String(82, y + 5, detail, fontName="TNR", fontSize=9))
    return figure


def communication_figure(width: float, summary: dict[str, Any]) -> Drawing:
    figure = Drawing(width, 110)
    entries = summary["values_by_arm"]
    segments = [("TRUE", "#16766d"), ("FALSE", "#5e6a75"), ("UNKNOWN", "#d8aa4e")]
    x0, bar_width = 40, width - 56
    for index, arm in enumerate(("B3", "P1", "P2")):
        y = 78 - 24 * index
        figure.add(String(2, y + 4, arm, fontName="TNR-Bold", fontSize=9))
        x = x0
        counts = entries[arm]["complete_corrective_communication"]
        for label, color in segments:
            count = counts.get(label, 0)
            if not count:
                continue
            size = bar_width * count / 33
            figure.add(Rect(x, y, size, 16, fillColor=colors.HexColor(color), strokeWidth=0))
            figure.add(
                String(
                    x + size / 2,
                    y + 4,
                    str(count),
                    textAnchor="middle",
                    fontName="TNR-Bold",
                    fontSize=9,
                    fillColor=colors.white if label != "UNKNOWN" else colors.black,
                )
            )
            x += size
    for index, (label, color) in enumerate(segments):
        x = 40 + index * 125
        figure.add(Rect(x, 5, 9, 9, fillColor=colors.HexColor(color), strokeWidth=0))
        figure.add(String(x + 14, 5, label, fontName="TNR", fontSize=8))
    return figure


def main() -> None:
    for name, filename in (
        ("TNR", "times.ttf"),
        ("TNR-Bold", "timesbd.ttf"),
        ("TNR-Italic", "timesi.ttf"),
        ("TNR-BoldItalic", "timesbi.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic"
    )
    summary = json.loads((RESULTS / "analysis/summary.json").read_bytes())
    assert summary["originals"] == 1500 and summary["inputs"] == 500
    assert summary["raw_status"] == {"COMPLETED": 1359, "FAILED": 141}
    for arm in ("B3", "P1", "P2"):
        values = summary["values_by_arm"][arm]
        assert values["final_business_state_correct"]["TRUE"] == 455
        assert values["corrective_delivery_after_challenge"]["TRUE"] == 33
    assert summary["values_by_arm"]["P2"]["complete_corrective_communication"]["TRUE"] == 33
    text = (HERE / "paper.md").read_text(encoding="utf-8")
    assert text.isascii(), "Use ASCII manuscript text for reliable typesetting"
    pages = text.split("<!-- PAGE_BREAK -->")
    assert len(pages) == 8
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = {
        "body": ParagraphStyle(
            "body", fontName="TNR", fontSize=10.25, leading=13.1, spaceAfter=6, alignment=TA_JUSTIFY
        ),
        "title": ParagraphStyle(
            "title",
            fontName="TNR-Bold",
            fontSize=18.5,
            leading=21,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "author": ParagraphStyle(
            "author", fontName="TNR", fontSize=10, leading=12, alignment=TA_CENTER, spaceAfter=4
        ),
        "note": ParagraphStyle(
            "note",
            fontName="TNR-Italic",
            fontSize=8.5,
            leading=10.3,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.HexColor("#555555"),
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName="TNR-Bold",
            fontSize=11.2,
            leading=13.2,
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="TNR-Italic",
            fontSize=9,
            leading=11,
            spaceAfter=5,
            spaceBefore=4,
            keepWithNext=True,
        ),
        "table": ParagraphStyle(
            "table", fontName="TNR", fontSize=9.4, leading=11.5, alignment=TA_LEFT
        ),
        "tablehead": ParagraphStyle("tablehead", fontName="TNR-Bold", fontSize=9.4, leading=11.5),
        "ref": ParagraphStyle("ref", fontName="TNR", fontSize=8.4, leading=10.4, spaceAfter=5),
    }
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=19 * mm,
        rightMargin=19 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title=(
            "Commit-Aware Agents: Separating Business Correctness, "
            "Evidence-Bound Claims, and Corrective Delivery"
        ),
        author="Syed Asim Bacha",
        subject=(
            "Completed synthetic protocol study: 500 paired inputs, "
            "1500 originals; manuscript for review"
        ),
        pageCompression=1,
    )
    story: list[Any] = []
    references = False
    for page_index, page in enumerate(pages):
        if page_index:
            story.append(PageBreak())
        for block in re.split(r"\n\s*\n", page.strip()):
            block = block.strip()
            if not block:
                continue
            if block == "<!-- CONTRACT_FIGURE -->":
                story.extend([contract_figure(doc.width), Spacer(1, 6)])
                continue
            if block == "<!-- COMMUNICATION_FIGURE -->":
                story.append(communication_figure(doc.width, summary))
                continue
            if block.startswith("# "):
                story.append(Paragraph(inline(block[2:]), styles["title"]))
                continue
            if block.startswith("## "):
                references = block[3:] == "References"
                story.append(Paragraph(inline(block[3:]), styles["heading"]))
                continue
            if block.startswith("|"):
                rows = []
                for line in block.splitlines():
                    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                    if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                        continue
                    rows.append(cells)
                columns = len(rows[0])
                if columns == 2:
                    widths = [42, doc.width - 42]
                elif rows[0][0] == "Endpoint":
                    widths = [doc.width - 174, 58, 58, 58]
                elif rows[0][0] == "Comparison":
                    widths = [98, 135, doc.width - 233]
                elif rows[0][0] == "Stored grade":
                    widths = [doc.width - 174, 58, 58, 58]
                else:
                    widths = [doc.width - 230, 55, 95, 80]
                content = [
                    [
                        Paragraph(
                            inline(cell), styles["tablehead"] if index == 0 else styles["table"]
                        )
                        for cell in row
                    ]
                    for index, row in enumerate(rows)
                ]
                table = Table(content, colWidths=widths[:columns], repeatRows=1, hAlign="LEFT")
                table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f5")),
                            ("LINEABOVE", (0, 0), (-1, 0), 0.65, colors.HexColor("#324858")),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor("#324858")),
                            ("LINEBELOW", (0, -1), (-1, -1), 0.65, colors.HexColor("#324858")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.extend([table, Spacer(1, 7)])
                continue
            if page_index == 0 and (
                block == "**Syed Asim Bacha**"
                or block.startswith("Department of Computer Science")
                or block == "syedasimbacha5@gmail.com"
            ):
                style = "author"
            elif block.startswith("*Full research"):
                style = "note"
            elif block.startswith(("Table ", "Figure ")):
                style = "caption"
            else:
                style = "ref" if references else "body"
            story.append(Paragraph(inline(" ".join(block.splitlines())), styles[style]))

    def chrome(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#52606b"))
        canvas.setFont("TNR", 8)
        if document.page > 1:
            canvas.drawString(doc.leftMargin, A4[1] - 10 * mm, "S. A. Bacha / Commit-Aware Agents")
        canvas.drawString(
            doc.leftMargin,
            10 * mm,
            "Full-study review manuscript - 25 October 2026 - not submitted",
        )
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    reader = PdfReader(OUTPUT)
    verification = {
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "pages": len(reader.pages),
        "intended_pages": len(pages),
        "source_words": len(re.findall(r"\b\S+\b", text)),
        "per_page_characters": [len(page.extract_text() or "") for page in reader.pages],
        "source_sha256": hashlib.sha256((HERE / "paper.md").read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "analysis_reruns": 0,
        "research_executions": 0,
        "aws_calls": 0,
    }
    (HERE / "build-verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(verification))
    if len(reader.pages) != len(pages):
        raise SystemExit("LAYOUT_OVERFLOW_REQUIRES_REVIEW")


if __name__ == "__main__":
    main()
