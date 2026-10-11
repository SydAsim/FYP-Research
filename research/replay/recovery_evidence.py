"""Independent replay checks for additional fault and cache mechanism evidence."""

from typing import Any

from research.scenario_dsl.models import FaultFamily, ProviderVisibility, ScenarioCase, stable_hash


def verify_cache(cache: dict[str, Any]) -> None:
    if (
        cache["database"] != 15
        or cache["flush_result"] != "OK"
        or cache["keys_after_flush"] != 0
        or cache["restart_ping"] != "PONG"
        or cache["hint_after_restart"]
        or cache["before"] != cache["after"]
        or cache["hint_hash"] != stable_hash(cache["before"])
        or cache["durable_hash"] != stable_hash(cache["after"])
    ):
        raise ValueError("Redis loss changed durable correctness facts")


def verify_recovery(execution: dict[str, Any], case: ScenarioCase) -> None:
    if case.action_semantics == "CREATE_READ_REUSE":
        read = execution["read_only_evidence"]
        if (
            read["truth_before"] != read["truth_after"]
            or read["truth_after"] != execution["simulator_truth"]
            or read["raw"].get("status") != 200
            or not read["raw"]["body"].get("authoritative")
            or len(read["truth_after"]) != 1
        ):
            raise ValueError("Read-only case changed provider truth or lacked authority")
    if case.revision_type == "ADDITIVE_COMPATIBLE" and execution["current_operation_id"]:
        if execution["current_operation_id"] != execution["first_operation_id"]:
            raise ValueError("Compatible revision failed to reuse the reconciled effect")
        operation = execution["provider_evidence"][0]["operation"]
        if operation["applicability"] != "REUSABLE" or operation["intent_revision"] != 1:
            raise ValueError("Reused effect lacks explicit applicability")
    if case.revision_type == "RETRACTION" and (execution["playback_ack"] or execution["permit_id"]):
        raise ValueError("Retraction published an unsupported cancellation claim")
    if case.fault_family is FaultFamily.REDIS_LOSS:
        cache = execution["redis_loss_evidence"]
        verify_cache(cache)
        if (
            cache["database"] != 15
            or cache["flush_result"] != "OK"
            or cache["keys_after_flush"] != 0
            or cache["restart_ping"] != "PONG"
            or cache["hint_after_restart"]
            or cache["before"] != cache["after"]
            or cache["hint_hash"] != stable_hash(cache["before"])
            or cache["durable_hash"] != stable_hash(cache["after"])
        ):
            raise ValueError("Redis loss changed durable correctness facts")
        if [row["action"] for row in execution["simulator_truth"]] != ["CREATE", "RESCHEDULE"]:
            raise ValueError("Redis loss caused a duplicate or lost effect")
    if case.visibility is ProviderVisibility.STALE_TWO_READS:
        first = next(
            item
            for item in execution["provider_evidence"]
            if item["operation"]["id"] == execution["first_operation_id"]
        )
        reads = [item for item in first["attempts"] if item["attempt_type"] == "STATUS_LOOKUP"]
        if (
            len(reads) < 3
            or any(
                item["normalized_result_json"] != {"outcome": "UNKNOWN", "authoritative": False}
                or not item["raw_response_json"]["status"]["body"].get("stale")
                or not item["raw_response_json"]["resource"]["body"].get("stale")
                for item in reads[:2]
            )
            or reads[2]["normalized_result_json"]["outcome"] != "PRESENT"
        ):
            raise ValueError("Stale evidence was treated as current authority")
    if case.fault_family is not FaultFamily.PARTIAL_EFFECT:
        return
    evidence = execution["partial_effect_evidence"]
    snapshot = evidence["handoff_snapshot"]
    first = next(
        item
        for item in execution["provider_evidence"]
        if item["operation"]["id"] == execution["first_operation_id"]
    )
    reads = [item for item in first["attempts"] if item["attempt_type"] == "STATUS_LOOKUP"]
    writes = [item for item in first["attempts"] if item["attempt_type"] == "WRITE"]
    truth = execution["simulator_truth"]
    handoffs = snapshot["handoffs"]
    if (
        evidence["simulator_config"]["faults"]
        != [{"request_index": 1, "stage": "BEFORE_COMMIT", "kind": "PARTIAL_EFFECT"}]
        or len(truth) != 1
        or truth[0]["result_code"] != "PARTIAL"
        or truth[0]["after_facts"]["status"] != "HELD"
        or first["operation"]["effect_knowledge"] != "PARTIAL"
        or len(writes) != 1
        or len(reads) != 8
        or any(item["normalized_result_json"]["outcome"] != "PARTIAL" for item in reads)
        or len(handoffs) != 1
        or handoffs[0]["known_facts"].get("effect_outcome") != "PARTIAL"
        or handoffs[0]["unknown_facts"] != {"final_intent_resolution": "UNRESOLVED"}
        or snapshot["workflow"]["resolution_status"] != "HANDOFF"
        or snapshot["counts"] != {"claims": 0, "claim_permits": 0, "audio_segments": 0}
        or execution["current_operation_id"] is not None
        or execution["playback_ack"] is not None
        or evidence["claim_denial"]["status"] != 409
        or evidence["unknown_receipt"]["result"] != "VIOLATED"
    ):
        raise ValueError("Partial effect was retried, erased, or claimed as complete")
