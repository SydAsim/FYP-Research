# Retained document-production attempts

- First build: 76 pages; pypdf reported an annotation-cloning warning. Exact original appendix content remained intact. The final build clones the learning document before appending the original, preserving TOC destinations without that warning.
- Second build: 77 pages. A first content-QA assertion incorrectly counted only reference headings containing a hyphen and found 10 rather than 12. This was a verification heuristic defect, not missing references. Verification now checks all twelve exact source titles.
- Initial lint/type checks found formatting/unused-import issues, an untyped ReportLab subclass boundary, a drawing-coordinate type, and an invalid Windows shell glob passed to mypy. Those document-helper issues were corrected; initial outputs remain beside final checks.
- Visual review found tight quotation-label spacing and an unnecessary small-table split. The third build changes only layout: quotation spacing, widow/orphan controls, section-heading grouping and keeping tables together. Research text, grades and analysis remain unchanged.
- No research scenario, oracle regrade, statistical reanalysis, AWS operation, paid speech API or dependency installation was performed.

- Final localized layout pass keeps reading card52 whole. Only page streams44/45 differ from the reviewed79-page build; both were re-rendered/inspected. All other77 page streams are unchanged.
