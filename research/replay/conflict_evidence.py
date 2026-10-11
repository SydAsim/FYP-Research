"""Check conflict mechanism evidence without changing the independent oracle grade."""

from datetime import datetime
from typing import Any

from research.scenario_dsl.models import ScenarioCase


def verify_conflict(execution: dict[str, Any], case: ScenarioCase) -> None:
    evidence = execution["conflict_evidence"]
    config = evidence["simulator_config"]
    snapshot = evidence["handoff_snapshot"]
    handoffs = snapshot["handoffs"]
    details = {item["operation"]["id"]: item for item in execution["provider_evidence"]}
    current = details[execution["current_operation_id"]]
    writes = [item for item in current["attempts"] if item["attempt_type"] == "WRITE"]
    reads = [item for item in current["attempts"] if item["attempt_type"] == "STATUS_LOOKUP"]
    truth = execution["simulator_truth"]
    held = evidence["truth_while_held"]
    if (
        config["faults"]
        != [{"request_index": 2, "stage": "BEFORE_COMMIT", "kind": "CONFLICTING_CHANGE"}]
        or config["held_barriers"] != ["BEFORE_COMMIT:2"]
        or evidence["initial_receipt"]["result"] != "SATISFIED"
        or evidence["initial_receipt"]["intent_revision"] != 1
        or evidence["initial_receipt"]["observed_resource_version"] != "0"
        or len(held) != 1
        or held[0]["action"] != "CREATE"
        or held[0]["operation_id"] != execution["first_operation_id"]
        or len(truth) != 2
        or [item["action"] for item in truth] != ["CREATE", "CONCURRENT_CHANGE"]
        or truth[0] != held[0]
        or truth[1]["operation_id"] is not None
        or truth[1]["before_facts"] != truth[0]["after_facts"]
        or truth[1]["after_facts"] != {**truth[1]["before_facts"], "version": 1}
        or datetime.fromisoformat(truth[1]["after_facts"]["starts_at"]) != case.initial_start
        or current["operation"]["normalized_request_json"]["action"] != "RESCHEDULE"
        or current["operation"]["normalized_request_json"]["expected_resource_version"] != 0
        or current["operation"]["effect_knowledge"] != "ABSENT"
        or current["operation"]["processing_phase"] != "TERMINAL"
        or current["operation"]["reconciliation_required"]
        or len(writes) != 1
        or writes[0]["raw_response_json"].get("status") != 409
        or writes[0]["raw_response_json"]["body"].get("detail")
        != "Provider resource version changed"
        or len(reads) != 1
        or reads[0]["normalized_result_json"] != {"outcome": "ABSENT", "authoritative": True}
        or snapshot["workflow"] != {"current_revision": 2, "resolution_status": "HANDOFF"}
        or len(handoffs) != 1
        or handoffs[0]["reason_code"] != "PROVIDER_CONFLICT"
        or handoffs[0]["state"] != "OPEN"
        or handoffs[0]["known_facts"].get("effect_outcome") != "ABSENT"
        or handoffs[0]["unknown_facts"] != {"final_intent_resolution": "UNRESOLVED"}
        or handoffs[0]["linked_operation_ids"] != [execution["current_operation_id"]]
        or snapshot["counts"] != {"claims": 0, "claim_permits": 0, "audio_segments": 0}
        or evidence["violated_receipt"]["result"] != "VIOLATED"
        or evidence["claim_denial"]["status"] != 409
        or not evidence["claim_denial"]["problem"]["type"].endswith("receipt-not-applicable")
        or not evidence["claim_denial"]["problem"].get("trace_id")
        or execution["permit_id"] is not None
        or execution["playback_ack"] is not None
        or not execution["correction_to_outcome_latency"]["censored"]
    ):
        raise ValueError("Provider conflict did not preserve newer state and known absence")
