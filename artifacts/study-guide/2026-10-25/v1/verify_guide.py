"""Verify coverage, navigation and preserved evidence in the learning PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader
from references import REFERENCES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main() -> None:
    build = json.loads((HERE / "build-verification.json").read_bytes())
    pdf = ROOT / "output/pdf/commit-aware-agents-explained-v1/complete-study-guide.pdf"
    reader = PdfReader(pdf)
    body = PdfReader(ROOT / "tmp/pdfs/study-guide-v1/learning-body.pdf")
    original = PdfReader(
        ROOT / "output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf"
    )
    assert len(reader.pages) == build["total_pages"]
    assert len(body.pages) == build["guide_pages"]
    assert len(reader.pages) == len(body.pages) + 8
    for index in range(8):
        appendix = reader.pages[len(body.pages) + index]
        assert appendix.get_contents().get_data() == original.pages[index].get_contents().get_data()
        assert appendix.extract_text() == original.pages[index].extract_text()
    navigation_links = 0
    for first, second in zip(
        body.pages[1].get("/Annots", []),
        reader.pages[1].get("/Annots", []),
        strict=True,
    ):
        before, after = first.get_object(), second.get_object()
        if "/Dest" in before:
            assert "/Dest" in after
            assert body.get_page_number(before["/Dest"][0].get_object()) == reader.get_page_number(
                after["/Dest"][0].get_object()
            )
            navigation_links += 1
    coverage = json.loads((HERE / "original-block-coverage.json").read_bytes())
    text = (HERE / "guide.md").read_text(encoding="utf-8")
    assert len(coverage) == 52
    assert all("> " + entry["original_text"] in text for entry in coverage)
    assert sum(line.startswith("### Q") for line in text.splitlines()) == 50
    assert all("## " + entry[0] in text for entry in REFERENCES)
    assert all(len(page.extract_text() or "") > 100 for page in reader.pages)
    data = ROOT / "artifacts/phase-8-final-analysis/v1"
    inventory = json.loads((data / "final-inventory.json").read_bytes())
    for name, expected in inventory["files"].items():
        assert hashlib.sha256((data / name).read_bytes()).hexdigest() == expected, name
    source_pdf = ROOT / "output/pdf/commit-aware-agents-full-v1/commit-aware-agents-full.pdf"
    assert hashlib.sha256(source_pdf.read_bytes()).hexdigest() == build["source_paper_sha256"]
    for required in (
        "eight attempts",
        "30 passes",
        "600 seconds",
        "SCRIPTED_TONE_SEMANTIC_PROXY",
        "fixed phrase",
        "AI assistance",
        "not a confidence interval",
    ):
        assert required in text, required
    result = {
        "status": "PASS_CONTENT_NAVIGATION_AND_PRESERVATION",
        "pages": len(reader.pages),
        "original_prose_blocks_explained": len(coverage),
        "original_appendix_pages_stream_and_text_identical": 8,
        "contents_links_preserved_with_same_destination": navigation_links,
        "reference_explainers": len(REFERENCES),
        "questions": 50,
        "closeout_inventory_files_unchanged": len(inventory["files"]),
        "source_paper_unchanged": True,
        "new_research_executions": 0,
        "regrading": False,
        "analysis_reruns": 0,
        "aws_calls": 0,
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "visual_review": "Separate visual-review.json required",
    }
    (HERE / "content-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
