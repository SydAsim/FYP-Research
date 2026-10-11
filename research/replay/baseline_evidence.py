"""Check baseline mechanism evidence without assigning it proposed-arm behavior."""

from typing import Any

from research.replay.recovery_evidence import verify_cache
from research.scenario_dsl.models import FaultFamily, ProviderVisibility, ScenarioCase


def verify_baseline(execution: dict[str, Any], case: ScenarioCase) -> None:
    if case.fault_family is FaultFamily.REDIS_LOSS:
        verify_cache(execution["redis_loss_evidence"])
    if case.action_semantics == "CREATE_READ_REUSE":
        read = execution["read_only_evidence"]
        if (
            read["truth_before"] != read["truth_after"]
            or read["truth_after"] != execution["simulator_truth"]
        ):
            raise ValueError("Baseline read changed provider truth")
    ambiguous = False
    writes = 0
    status_reads: list[dict[str, Any]] = []
    for event in execution["baseline_events"]:
        kind = event["event_kind"]
        raw = event["raw_json"]
        normalized = event["normalized_json"]
        if kind == "REQUEST_SENT":
            if ambiguous:
                raise ValueError("Baseline wrote before reconciling an ambiguous outcome")
            writes += 1
        elif kind == "PROVIDER_RESPONSE":
            ambiguous = (
                bool(raw.get("transport_error"))
                or raw.get("status", 500) >= 500
                or normalized.get("outcome") == "PARTIAL"
            )
        elif kind == "STATUS_LOOKUP":
            status_reads.append(event)
            if normalized.get("authoritative") and normalized.get("outcome") in (
                "PRESENT",
                "ABSENT",
            ):
                ambiguous = False
    if execution["permit_id"] is not None or execution["receipt_id"] is not None:
        raise ValueError("Baseline unexpectedly acquired a proposed claim mechanism")
    if (
        case.fault_family is FaultFamily.PARTIAL_EFFECT
        or case.visibility is ProviderVisibility.UNAVAILABLE
    ):
        if writes != 1 or execution["playback_ack"] is not None:
            raise ValueError("Unresolved baseline effect was retried or announced")
    if (
        case.visibility
        in (ProviderVisibility.STALE_TWO_READS, ProviderVisibility.DELAYED_TWO_READS)
        and execution["arm"] != "B0"
    ):
        if len(status_reads) < 3 or any(
            row["normalized_json"]["outcome"] != "UNKNOWN" for row in status_reads[:2]
        ):
            raise ValueError("Baseline lost inconclusive read evidence")
