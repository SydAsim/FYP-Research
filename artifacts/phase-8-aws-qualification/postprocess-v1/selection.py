"""Retain failures; exclude labelled diagnostics even with legacy numbering errors."""

from typing import Any


def original_attempts(traces: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    originals, diagnostics = [], []
    for trace in traces:
        label = trace.get("attempt_label")
        if label == "DIAGNOSTIC_RERUN":
            if not trace.get("original_id"):
                raise ValueError("ORPHAN_DIAGNOSTIC: preserve and review")
            diagnostics.append(trace["execution_id"])
        elif label == "ORIGINAL_PLANNED" and trace.get("attempt") == 1:
            if trace.get("original_id"):
                raise ValueError("CONTRADICTORY_ORIGINAL_LINK")
            originals.append(trace)  # Includes every original failure, timeout and missing result.
        else:
            raise ValueError("AMBIGUOUS_ATTEMPT_METADATA: do not assume an original")
    return originals, diagnostics
