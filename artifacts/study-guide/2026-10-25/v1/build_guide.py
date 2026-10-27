"""Build one learning PDF from preserved results and authored teaching notes."""

from __future__ import annotations

import hashlib
import json
import re
from html import escape
from pathlib import Path
from typing import Any

from annotations import NOTES
from glossary import GLOSSARY
from pypdf import PdfReader, PdfWriter
from questions import QUESTIONS
from references import REFERENCES
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PAPER = ROOT / "artifacts/paper-final-study/2026-10-25/v1/paper.md"
PAPER_PDF = ROOT / "output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf"
RESULTS = ROOT / "artifacts/phase-8-final-analysis/v1"
OUTPUT = ROOT / "output/pdf/commit-aware-agents-explained-v1/complete-study-guide.pdf"
WORK = ROOT / "tmp/pdfs/study-guide-v1"
WIDTH = A4[0] - 38 * mm
NAVY = colors.HexColor("#15324a")
TEAL = colors.HexColor("#137b76")
GRAY = colors.HexColor("#516371")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https://[^\s)]+)\)",
        r'<link href="\2" color="#126d79">\1</link>',
        text,
    )
    return re.sub(
        r"(?<![\"=])(https://[^\s<]+)(?![^<]*</link>)",
        r'<link href="\1" color="#126d79">\1</link>',
        text,
    )


def register_fonts() -> None:
    for name, filename in (
        ("Guide", "segoeui.ttf"),
        ("Guide-Bold", "segoeuib.ttf"),
        ("Guide-Italic", "segoeuii.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / filename)))
    pdfmetrics.registerFontFamily(
        "Guide",
        normal="Guide",
        bold="Guide-Bold",
        italic="Guide-Italic",
        boldItalic="Guide-Bold",
    )


def make_styles() -> dict[str, ParagraphStyle]:
    return {
        "body": ParagraphStyle(
            "body",
            fontName="Guide",
            fontSize=10.5,
            leading=15.2,
            spaceAfter=9,
            alignment=TA_LEFT,
            allowWidows=0,
            allowOrphans=0,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Guide-Bold",
            fontSize=29,
            leading=34,
            textColor=NAVY,
            spaceAfter=16,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Guide",
            fontSize=14,
            leading=20,
            textColor=GRAY,
            spaceAfter=16,
        ),
        "part": ParagraphStyle(
            "part",
            fontName="Guide-Bold",
            fontSize=20,
            leading=25,
            textColor=NAVY,
            spaceBefore=5,
            spaceAfter=18,
            keepWithNext=True,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Guide-Bold",
            fontSize=14.5,
            leading=19,
            textColor=TEAL,
            spaceBefore=14,
            spaceAfter=9,
            keepWithNext=True,
        ),
        "smallhead": ParagraphStyle(
            "smallhead",
            fontName="Guide-Bold",
            fontSize=11.5,
            leading=16,
            textColor=NAVY,
            spaceBefore=11,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "original": ParagraphStyle(
            "original",
            fontName="Guide",
            fontSize=9.2,
            leading=13.2,
            alignment=TA_JUSTIFY,
            backColor=colors.HexColor("#f0f3f6"),
            borderPadding=9,
            borderColor=colors.HexColor("#d9e1e7"),
            borderWidth=0.45,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=14,
            spaceAfter=14,
            allowWidows=0,
            allowOrphans=0,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Guide-Bold",
            fontSize=8.5,
            leading=12,
            textColor=GRAY,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Guide-Italic",
            fontSize=8.7,
            leading=12.4,
            textColor=GRAY,
            spaceBefore=5,
            spaceAfter=12,
        ),
        "table": ParagraphStyle(
            "table",
            fontName="Guide",
            fontSize=9.1,
            leading=12.7,
        ),
        "tablehead": ParagraphStyle(
            "tablehead",
            fontName="Guide-Bold",
            fontSize=9.1,
            leading=12.7,
            textColor=NAVY,
        ),
        "toc": ParagraphStyle(
            "toc",
            fontName="Guide",
            fontSize=11,
            leading=17,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=7,
        ),
    }


class GuideDocument(BaseDocTemplate):  # type: ignore[misc]
    """Headings supply navigation and a generated contents page."""

    def __init__(self, path: Path, styles: dict[str, ParagraphStyle]) -> None:
        super().__init__(
            str(path),
            pagesize=A4,
            leftMargin=19 * mm,
            rightMargin=19 * mm,
            topMargin=18 * mm,
            bottomMargin=19 * mm,
            title="Commit-Aware Agents - Complete Plain-English Study Guide",
            author="Learning companion prepared for Syed Asim Bacha",
            subject="Annotated full manuscript, methods, reference guide and meeting practice",
        )
        self.styles = styles
        self.heading_records: list[dict[str, Any]] = []
        self.addPageTemplates(
            PageTemplate(
                "guide",
                frames=[
                    Frame(
                        self.leftMargin,
                        self.bottomMargin,
                        self.width,
                        self.height,
                        leftPadding=0,
                        rightPadding=0,
                        topPadding=0,
                        bottomPadding=0,
                    )
                ],
                onPage=self.chrome,
            )
        )

    def beforeDocument(self) -> None:
        self.heading_records = []

    def afterFlowable(self, flowable: Any) -> None:
        if not hasattr(flowable, "guide_key"):
            return
        key, title, level = flowable.guide_key, flowable.guide_title, flowable.guide_level
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=True)
        if level == 0:
            self.notify("TOCEntry", (0, title, self.page, key))
        self.heading_records.append({"key": key, "title": title, "page": self.page})

    def chrome(self, canvas: Any, document: Any) -> None:
        canvas.saveState()
        if document.page > 1:
            canvas.setFont("Guide", 8)
            canvas.setFillColor(GRAY)
            canvas.drawString(
                self.leftMargin, A4[1] - 10 * mm, "COMMIT-AWARE AGENTS / LEARNING COMPANION"
            )
            canvas.setStrokeColor(colors.HexColor("#d6e1e6"))
            canvas.line(self.leftMargin, A4[1] - 12 * mm, A4[0] - self.rightMargin, A4[1] - 12 * mm)
        canvas.setFont("Guide", 8)
        canvas.setFillColor(GRAY)
        canvas.drawString(
            self.leftMargin,
            10 * mm,
            "25 October 2026 | Teaching examples are not research observations",
        )
        canvas.drawRightString(A4[0] - self.rightMargin, 10 * mm, str(document.page))
        canvas.restoreState()


def architecture(width: float) -> Drawing:
    figure = Drawing(width, 202)
    boxes = [
        (0, 137, 145, "Input / browser", "Typed intents in main study"),
        (170, 137, width - 170, "API + domain rules", "Validate and accept a revision"),
        (0, 73, 145, "Durable PostgreSQL", "Intent, effects, evidence, repair"),
        (
            170,
            73,
            width - 170,
            "Worker / verifier / scheduler",
            "Dispatch, reconcile, authorize output",
        ),
        (0, 9, 145, "Provider simulator", "Separate append-only truth"),
        (170, 9, width - 170, "Independent research layer", "Runner, oracle, ledger, backups"),
    ]
    for x, y, w, title, detail in boxes:
        figure.add(
            Rect(
                x,
                y,
                w,
                52,
                fillColor=colors.HexColor("#ecf3f5"),
                strokeColor=colors.HexColor("#aec4cc"),
                strokeWidth=0.6,
            )
        )
        figure.add(
            String(x + 9, y + 31, title, fontName="Guide-Bold", fontSize=9.3, fillColor=NAVY)
        )
        figure.add(String(x + 9, y + 13, detail, fontName="Guide", fontSize=8.1, fillColor=GRAY))
    figure.add(Line(146, 164, 168, 164, strokeColor=TEAL, strokeWidth=1.5))
    figure.add(Line(257, 136, 257, 127, strokeColor=TEAL, strokeWidth=1.5))
    figure.add(Line(146, 100, 168, 100, strokeColor=TEAL, strokeWidth=1.5))
    return figure


def dimensions(width: float) -> Drawing:
    figure = Drawing(width, 155)
    rows = [
        ("INTENT", "Which request was accepted?"),
        ("EFFECT", "What did the provider actually do?"),
        ("EVIDENCE", "What can current observations establish?"),
        ("CLAIM", "Which specific statement may be released?"),
        ("PLAYBACK", "What progress did the client report?"),
        ("REPAIR", "What correction remains owed?"),
    ]
    for index, (label, question) in enumerate(rows):
        y = 130 - 25 * index
        figure.add(
            Rect(
                0,
                y,
                width,
                22,
                strokeColor=colors.HexColor("#d1dee4"),
                fillColor=colors.HexColor("#f1f5f7"),
                strokeWidth=0.4,
            )
        )
        figure.add(String(8, y + 7, label, fontName="Guide-Bold", fontSize=8.7, fillColor=TEAL))
        figure.add(String(96, y + 7, question, fontName="Guide", fontSize=9.1, fillColor=NAVY))
    return figure


def comparison_chart(width: float, communication: bool) -> Drawing:
    figure = Drawing(width, 136)
    segments = (
        [("TRUE", "#137b76"), ("FALSE", "#657786"), ("UNKNOWN", "#c79836")]
        if communication
        else [("Correct", "#137b76"), ("Incorrect", "#657786")]
    )
    summary = json.loads((RESULTS / "analysis/summary.json").read_bytes())
    total = 33 if communication else 500
    x0, bar_width = 40.0, width - 54
    for index, arm in enumerate(("B3", "P1", "P2")):
        y = 100 - index * 27
        figure.add(String(1, y + 5, arm, fontName="Guide-Bold", fontSize=10, fillColor=NAVY))
        counts = (
            summary["values_by_arm"][arm]["complete_corrective_communication"]
            if communication
            else {"Correct": 455, "Incorrect": 45}
        )
        x = x0
        for label, color in segments:
            count = counts.get(label, 0)
            if not count:
                continue
            size = bar_width * count / total
            figure.add(Rect(x, y, size, 19, fillColor=colors.HexColor(color), strokeWidth=0))
            figure.add(
                String(
                    x + size / 2,
                    y + 5,
                    str(count),
                    textAnchor="middle",
                    fontName="Guide-Bold",
                    fontSize=9,
                    fillColor=colors.white if label != "UNKNOWN" else colors.black,
                )
            )
            x += size
    for index, (label, color) in enumerate(segments):
        x = 40 + index * 125
        figure.add(Rect(x, 8, 9, 9, fillColor=colors.HexColor(color), strokeWidth=0))
        figure.add(String(x + 14, 8, label, fontName="Guide", fontSize=8.3, fillColor=NAVY))
    return figure


def original_blocks() -> list[tuple[int, str, str]]:
    blocks: list[tuple[int, str, str]] = []
    for page, content in enumerate(
        PAPER.read_text(encoding="utf-8").split("<!-- PAGE_BREAK -->"), 1
    ):
        for block in re.split(r"\n\s*\n", content.strip()):
            block = block.strip()
            if block.startswith(
                (
                    "##",
                    "# ",
                    "|",
                    "<!--",
                    "[",
                    "**Syed",
                    "Department",
                    "syedasim",
                    "*Full",
                    "**Keywords",
                )
            ):
                kind = "other"
            else:
                kind = "prose"
            blocks.append((page, kind, block))
    return blocks


def assemble_markdown() -> tuple[str, list[dict[str, Any]]]:
    parts = [(HERE / "lessons.md").read_text(encoding="utf-8")]
    parts.append(
        "# PART V - Read the full manuscript closely\n\nEvery original prose block "
        "appears below in gray. Read it, then read the explanation. The separate "
        "appendix reproduces all eight original pages. Table values remain the "
        "original values.\n"
    )
    block_index, last_page = 0, 0
    coverage: list[dict[str, Any]] = []
    for page, kind, block in original_blocks():
        if page != last_page:
            parts.append(f"## Original manuscript page {page}\n")
            last_page = page
        if kind == "prose":
            title, explanation, terms, example, caution = NOTES[block_index]
            block_index += 1
            parts.extend(
                [
                    f"### {block_index:02d}. {title}\n",
                    f"> {block}\n",
                    f"**Plain-English reading:** {explanation}\n",
                    f"**Difficult words:** {terms}\n",
                    f"**A teaching example:** {example}\n",
                    f"**Keep the claim accurate:** {caution}\n",
                ]
            )
            coverage.append(
                {
                    "block": block_index,
                    "manuscript_page": page,
                    "original_text": block,
                    "sha256": hashlib.sha256(block.encode()).hexdigest(),
                    "explanation_title": title,
                }
            )
        elif block.startswith("|"):
            parts.append(block + "\n")
        elif block.startswith("## ") and block != "## References":
            parts.append("**Original heading: " + block[3:] + "**\n")
        elif block == "<!-- CONTRACT_FIGURE -->":
            parts.append("<!-- DIMENSIONS -->\n")
        elif block == "<!-- COMMUNICATION_FIGURE -->":
            parts.append("<!-- COMMUNICATION_CHART -->\n")
    assert block_index == len(NOTES) == 52
    parts.append(
        "# PART VI - The twelve referenced works explained\n\nThese works are not "
        "twelve language models installed in our system. Some are algorithms, "
        "runtimes, theories or benchmarks; one is an engineering article. The "
        "following concise summaries explain their role. They do not reproduce "
        "the papers, claim their code was run, or compare their rates with ours. "
        "The close-reading chapter and the appendix retain the manuscript's "
        "references.\n"
    )
    for title, kind, url, summary, connection in REFERENCES:
        parts.extend(
            [
                f"## {title}\n",
                f"**What kind of work is it?** {kind}.\n",
                f"**Simple explanation:** {summary}\n",
                f"**Connection to our paper:** {connection}\n",
                f"**Read the primary source:** {url}\n",
            ]
        )
    parts.append(
        "# PART VII - Difficult professor questions and defensible answers\n\nThese"
        " are practice answers, not permission to claim expertise or work you did"
        " not perform. Read the short answer first. The follow-up explains the "
        "boundary a professor may test. Adapt personal-contribution statements to"
        " your actual work.\n"
    )
    category = ""
    for index, (group, question, answer, followup) in enumerate(QUESTIONS, 1):
        if group != category:
            parts.append(f"## {group}\n")
            category = group
        parts.extend(
            [
                f"### Q{index:02d}. {question}\n",
                f"**Answer:** {answer}\n",
                f"**If challenged further:** {followup}\n",
            ]
        )
    parts.append((HERE / "meeting.md").read_text(encoding="utf-8"))
    parts.append(
        "# PART IX - Technical words in everyday English\n\nUse this dictionary "
        "when a word interrupts your reading. Definitions explain this project's "
        "usage. Exact executable constraints remain in the frozen "
        "contracts/source.\n"
    )
    for term, meaning in GLOSSARY:
        parts.append(f"**{term}.** {meaning}\n")
    parts.append(
        "# APPENDIX - The preserved original manuscript\n\nThe following eight "
        "pages reproduce the complete original research manuscript, including its"
        " tables, figures and references. Its original printed page numbers "
        "restart at 1. Use the PDF's Appendix bookmark to return here. This book "
        "does not change the original file, its grades, or its source "
        "commitments.\n\nBefore you present: explain the main result in your own "
        "words, identify one verified trace, name the strongest measurement "
        "limitation, and state what your evidence cannot answer. The goal is "
        "understanding and accurate scientific discussion.\n"
    )
    return "\n".join(parts), coverage


def make_table(block: str, styles: dict[str, ParagraphStyle]) -> Table:
    rows = []
    for line in block.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    columns = len(rows[0])
    if columns == 2:
        widths = [95, WIDTH - 95]
    elif rows[0][0] == "Endpoint":
        widths = [WIDTH - 177, 59, 59, 59]
    elif rows[0][0] == "Stored grade":
        widths = [WIDTH - 177, 59, 59, 59]
    elif rows[0][0] == "Stratum":
        widths = [WIDTH - 245, 55, 100, 90]
    elif rows[0][0] == "Comparison":
        widths = [95, 145, WIDTH - 240]
    elif columns == 3:
        widths = [120, (WIDTH - 120) / 2, (WIDTH - 120) / 2]
    else:
        widths = [WIDTH / columns] * columns
    table = Table(
        [
            [
                Paragraph(inline(cell), styles["tablehead"] if index == 0 else styles["table"])
                for cell in row
            ]
            for index, row in enumerate(rows)
        ],
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f0f2")),
                ("LINEABOVE", (0, 0), (-1, 0), 0.7, TEAL),
                ("LINEBELOW", (0, 0), (-1, 0), 0.4, TEAL),
                ("LINEBELOW", (0, -1), (-1, -1), 0.7, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def main() -> None:
    assert sha(PAPER_PDF) == "5cfc960e8e69fa3de3196746cbfc839437769bafbe7300839640a7e083dbfe39"
    assert sha(PAPER) == "ea3b8cc652d52be8468104961c63ef33f5e3bb70222a9ce1edd087f8a59c289d"
    assert len(REFERENCES) == 12 and len(QUESTIONS) == 50
    original_result_receipt = json.loads((RESULTS / "analysis/verification.json").read_bytes())
    for name, expected in original_result_receipt["files"].items():
        assert sha(RESULTS / "analysis" / name) == expected
    register_fonts()
    styles = make_styles()
    text, coverage = assemble_markdown()
    assert text.isascii(), "Use simple ASCII punctuation for dependable rendering"
    (HERE / "guide.md").write_text(text, encoding="utf-8")
    (HERE / "original-block-coverage.json").write_text(
        json.dumps(coverage, indent=2) + "\n", encoding="utf-8"
    )
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    body_pdf = WORK / "learning-body.pdf"
    doc = GuideDocument(body_pdf, styles)
    story: list[Any] = [
        Spacer(1, 22),
        Paragraph("Commit-Aware Agents", styles["title"]),
        Paragraph("The complete plain-English study guide", styles["subtitle"]),
        Paragraph(
            "Understand the paper. Follow the story. Explain the method. Defend the limits.",
            styles["section"],
        ),
        Spacer(1, 8),
        Image(str(HERE / "assets/fictional-booking-story.png"), width=WIDTH, height=WIDTH * 2 / 3),
        Paragraph(
            (
                "AI-generated fictional teaching scenes, not research photographs or "
                "participant evidence."
            ),
            styles["caption"],
        ),
        Paragraph(
            (
                "Prepared for Syed Asim Bacha\nDepartment of Computer Science, Islamia "
                "College Peshawar, Pakistan"
            ),
            styles["body"],
        ),
        Paragraph(
            (
                "Includes the complete annotated manuscript, twelve reference explainers,"
                " fifty professor questions, a technical dictionary and the original "
                "eight-page paper."
            ),
            styles["body"],
        ),
        Paragraph(
            "Learning companion | 25 October 2026 | Original study and grades preserved",
            styles["caption"],
        ),
        PageBreak(),
        Paragraph("Contents and reading routes", styles["part"]),
        Paragraph(
            (
                "Beginner route: Parts I-II, then Part IV. Paper-reading route: Part V "
                "and the appendix. Meeting route: Parts VII-VIII, then revisit the "
                "evidence and glossary. The contents links and PDF bookmarks provide "
                "navigation."
            ),
            styles["body"],
        ),
    ]
    toc = TableOfContents()
    toc.levelStyles = [styles["toc"]]
    toc.dotsMinLevel = 0
    story.append(toc)
    counter = 0
    last_card_start: int | None = None
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### 52."):
            last_card_start = len(story)
        if block.startswith("# PART VI ") and last_card_start is not None:
            # Keep the last reading card whole instead of leaving its final
            # two-line caution alone on a page before the next part.
            story[last_card_start:] = [KeepTogether(story[last_card_start:])]
        if block.startswith("# "):
            story.append(PageBreak())
            title, style, level = block[2:], "part", 0
        elif block.startswith("## "):
            title, style, level = block[3:], "section", 1
        elif block.startswith("### "):
            title, style, level = block[4:], "smallhead", 2
        else:
            title, style, level = "", "body", -1
        if level >= 0:
            counter += 1
            heading = Paragraph(inline(title), styles[style])
            heading.guide_key = f"guide-heading-{counter}"
            heading.guide_title = title
            heading.guide_level = level
            story.append(heading)
            continue
        if block.startswith("> "):
            story.append(Paragraph("ORIGINAL MANUSCRIPT", styles["label"]))
            story.append(Paragraph(inline(block[2:]), styles["original"]))
        elif block.startswith("|"):
            story.append(KeepTogether([make_table(block, styles), Spacer(1, 11)]))
        elif block.startswith("**Original heading:"):
            story.append(Paragraph(inline(block), styles["smallhead"]))
        elif block in ("<!-- STORY_IMAGE -->", "<!-- INFRA_IMAGE -->"):
            name = (
                "fictional-booking-story.png"
                if "STORY" in block
                else "fictional-research-infrastructure.png"
            )
            story.append(Image(str(HERE / "assets" / name), width=WIDTH, height=WIDTH * 2 / 3))
            story.append(
                Paragraph(
                    (
                        "Fictional AI-generated illustration for learning. It is not an actual "
                        "experiment, author, participant, interface or AWS facility."
                    ),
                    styles["caption"],
                )
            )
        elif block == "<!-- ARCHITECTURE -->":
            story.extend(
                [
                    architecture(WIDTH),
                    Paragraph(
                        (
                            "Simplified component map. The independent research layer "
                            "grades external"
                            " observations; this drawing does not replace the exact executable "
                            "transition rules."
                        ),
                        styles["caption"],
                    ),
                ]
            )
        elif block == "<!-- DIMENSIONS -->":
            story.append(dimensions(WIDTH))
            story.append(
                Paragraph(
                    "Independent questions that can coexist, not a single linear state sequence.",
                    styles["caption"],
                )
            )
        elif block == "<!-- COMMUNICATION_CHART -->":
            story.append(comparison_chart(WIDTH, True))
            story.append(
                Paragraph(
                    (
                        "Planned n=33 per arm. Complete corrective communication: TRUE, FALSE and"
                        " UNKNOWN kept distinct. Ordinary supported updates succeed 33/33 in "
                        "every arm."
                    ),
                    styles["caption"],
                )
            )
        elif block == "<!-- BUSINESS_CHART -->":
            story.append(comparison_chart(WIDTH, False))
            story.append(
                Paragraph(
                    (
                        "Correct final business state: 455 TRUE and 45 FALSE in each arm, planned"
                        " n=500 per arm. This is the observed business tie, not an AWS command "
                        "success rate."
                    ),
                    styles["caption"],
                )
            )
        else:
            story.append(Paragraph(inline(" ".join(block.splitlines())), styles["body"]))
    doc.multiBuild(story)
    body_reader = PdfReader(body_pdf)
    original_reader = PdfReader(PAPER_PDF)
    assert len(original_reader.pages) == 8
    # Preserve internal TOC bindings before appending the original manuscript.
    writer = PdfWriter(clone_from=body_reader)
    appendix = writer.add_outline_item(
        "Original eight-page manuscript (preserved)", len(body_reader.pages)
    )
    writer.append(original_reader, import_outline=False)
    for index in range(8):
        writer.add_outline_item(
            f"Original manuscript page {index + 1}", len(body_reader.pages) + index, parent=appendix
        )
    writer.add_metadata(
        {
            "/Title": "Commit-Aware Agents - Complete Plain-English Study Guide",
            "/Author": "Learning companion prepared for Syed Asim Bacha",
            ("/Subject"): (
                "Annotated paper, story, system, AWS, methods, references and professor Q&A"
            ),
        }
    )
    with OUTPUT.open("wb") as stream:
        writer.write(stream)
    final_reader = PdfReader(OUTPUT)
    report = {
        "status": "BUILT_CONTENT_AND_VISUAL_REVIEW_REQUIRED",
        "guide_pages": len(body_reader.pages),
        "original_appendix_pages": 8,
        "total_pages": len(final_reader.pages),
        "words_in_learning_source": len(text.split()),
        "original_prose_blocks_explained": len(coverage),
        "original_tables": 5,
        "original_figures_explained": 2,
        "reference_explainers": len(REFERENCES),
        "professor_questions": len(QUESTIONS),
        "glossary_entries": len(GLOSSARY),
        "realistic_generated_composites": 2,
        "source_paper_sha256": sha(PAPER_PDF),
        "final_pdf_sha256": sha(OUTPUT),
        "final_pdf_bytes": OUTPUT.stat().st_size,
        "research_executions": 0,
        "analysis_reruns": 0,
        "aws_calls": 0,
        "headings": doc.heading_records,
    }
    (HERE / "build-verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "headings"}))


if __name__ == "__main__":
    main()
