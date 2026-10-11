"""Context-specific permissive-response checks. No application calls or retries."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from research.scenario_dsl.models import stable_hash

VERSION = "phase85-combined-amendment-v3"
STALE = {"verified-stale-attempt", "queued-stale", "buffered-stale"}


def version_change_supported(
    row: dict[str, Any], call: dict[str, Any], scenario: str, item: dict[str, Any]
) -> list[str]:
    """Only ordinary successful source observations establish the named version fault.

    Provider-unavailable UNKNOWN evidence does not qualify for this exemption.
    No oracle truth or assumption of successful fault injection is used.
    """
    snapshot = row.get("response_context_snapshot", row.get("snapshot", {}))
    start, end = (datetime.fromisoformat(call[k]) for k in ("sent_at", "received_at"))
    observations = snapshot.get("observations", [])
    before, after = [], []
    for observation in observations:
        raw = observation["raw"]
        if (
            observation["source_type"] != "SIMULATOR_RESOURCE"
            or observation["raw_hash"] != stable_hash(raw)
            or observation["query"].get("scenario_id") != scenario
            or observation["query"].get("resource_key") != item.get("resource_key")
            or raw.get("status") != 200
            or raw.get("body", {}).get("authoritative") is not True
        ):
            continue
        at = datetime.fromisoformat(observation["available_at"])
        if at < start:
            before.append(observation)
        elif start <= at <= end:
            after.append(observation)
    for old in reversed(before):
        for fresh in after:
            if old["query"].get("operation_id") != fresh["query"].get("operation_id"):
                continue
            old_rows = old["raw"]["body"].get("appointments", [])
            new_rows = fresh["raw"]["body"].get("appointments", [])
            if len(old_rows) != 1 or len(new_rows) != 1:
                continue
            a, b = old_rows[0], new_rows[0]
            if a.get("version") != b.get("version") and {
                k: v for k, v in a.items() if k != "version"
            } == {k: v for k, v in b.items() if k != "version"}:
                return [old["raw_hash"], fresh["raw_hash"]]
    return []


def problem(body: dict[str, Any], path: str, code: str, title: str, detail: str) -> bool:
    try:
        UUID(body["trace_id"])
        return (
            body.get("type") == "https://example.invalid/problems/" + code
            and body.get("title") == title
            and body.get("detail") == detail
            and body.get("instance") == path
            and body.get("status") == 409
            and body.get("retryable") is False
        )
    except (ValueError, KeyError, TypeError):
        return False


def evaluate(
    row: dict[str, Any],
    call: dict[str, Any],
    *,
    scenario: str,
    item: dict[str, Any],
    services: dict[str, str],
) -> dict[str, Any]:
    """Classify this exact call from pre-call recorded context and actual response.

    Accepted unsafe attempts stay observable outcomes. Unexpected replies remain
    defects even if the driver subsequently completes a correct update.
    """
    family = row["input"]["generator_family"]
    arm = row["arm"]
    path, method, base = call["path"], call["method"], call["base"]
    request, response = call.get("request") or {}, call.get("response") or {}
    status = call.get("status")
    prior = [
        c for c in row["http"] if c is not call and c.get("received_at", "") <= call["sent_at"]
    ]
    accepted = [
        c
        for c in prior
        if c.get("method") == "POST"
        and c.get("path") == f"/v1/workflows/{item.get('workflow_id')}/revisions"
        and c.get("status") == 201
    ]
    revision = max((c["response"]["revision"] for c in accepted), default=0)
    names = {b["name"] for b in row.get("barriers", []) if b.get("at", "") <= call["sent_at"]}
    segments = [
        c["response"]
        for c in prior
        if c.get("status") == 200
        and c.get("method") == "GET"
        and c.get("path", "").startswith("/v1/audio-segments/")
    ]
    segment_id = request.get("segment_id") or (
        path.split("/")[-2] if path.endswith("/release") else None
    )
    segment = next(
        (
            s
            for s in reversed(segments)
            if s.get("id") == segment_id
            and s.get("call_id") == item.get("call_id")
            and s.get("workflow_id") == item.get("workflow_id")
        ),
        None,
    )
    outcome, reason = (
        "UNEXPECTED_RESPONSE",
        "No declared endpoint/request/scenario response matches",
    )
    held = row["input"]["provider"]["held_barriers"]
    for barrier in held:
        if (
            method == "GET"
            and base == services["simulator"]
            and path == f"/internal/scenarios/{scenario}/barriers/{barrier}"
            and not request
        ):
            if status == 404 and response == {"detail": "Unknown barrier"}:
                outcome, reason = (
                    "EXPECTED_BARRIER_POLL",
                    "Declared held barrier has not been reached",
                )
            elif (
                status == 200
                and response.get("barrier_name") == barrier
                and "reached_at" in response
            ):
                outcome, reason = "EXPECTED_BARRIER_POLL", "Declared barrier state observed"
    stale = family in STALE and revision > 1 and request.get("expected_intent_revision") == 1
    if (
        family in {"verified-stale-attempt", "queued-stale"}
        and stale
        and arm == "B3"
        and base == services["voice"]
        and method == "POST"
        and path == "/internal/phase6/b3/schedule"
        and request.get("workflow_id") == item.get("workflow_id")
    ):
        prefix = (
            f"Controller rejected GET /internal/phase6/b3/workflows/{item['workflow_id']}"
            "/synthesis-input?revision=1: 409 "
        )
        if (
            status == 409
            and response.get("type") == "https://example.invalid/problems/voice-command-rejected"
            and response.get("title") == "Voice Command Rejected"
            and response.get("instance") == path
            and response.get("status") == 409
        ):
            try:
                UUID(response["trace_id"])
                detail = response["detail"]
                nested = json.loads(detail[len(prefix) :]) if detail.startswith(prefix) else {}
                if problem(
                    nested,
                    f"/internal/phase6/b3/workflows/{item['workflow_id']}/synthesis-input",
                    "b3-scope",
                    "B3 scope mismatch",
                    "No current B3 research revision",
                ):
                    outcome, reason = (
                        "EXPECTED_STALE_REFUSAL",
                        "Accepted correction precedes old B3 scheduling",
                    )
            except (ValueError, TypeError, KeyError):
                pass
        elif status == 200 and isinstance(response.get("segment_id"), str):
            outcome, reason = (
                "OBSERVABLE_ACCEPTANCE",
                "Record actual stale scheduling; oracle judges safety",
            )
    if (
        family == "verified-stale-attempt"
        and stale
        and arm in {"P1", "P2"}
        and method == "POST"
        and base == services["api"]
        and path == "/internal/phase3/claims"
    ):
        receipt = next(
            (
                c["response"]
                for c in reversed(prior)
                if c.get("path") == "/internal/phase3/verifications"
                and c.get("status") == 201
                and c["response"].get("receipt_id") == request.get("receipt_id")
            ),
            None,
        )
        if receipt and receipt.get("intent_revision") == 1:
            if status == 409 and problem(
                response,
                path,
                "stale-intent-revision",
                "Stale intent revision",
                "Claim revision is no longer current",
            ):
                outcome, reason = (
                    "EXPECTED_STALE_REFUSAL",
                    "Bound old receipt after accepted revision",
                )
            elif status == 201 and isinstance(response.get("permit_id"), str):
                outcome, reason = "OBSERVABLE_ACCEPTANCE", "Record actual stale authorization"
    if (
        family == "queued-stale"
        and stale
        and arm in {"P1", "P2"}
        and segment
        and segment.get("intent_revision") == 1
        and method == "POST"
        and base == services["api"]
        and path == f"/internal/phase4/audio-segments/{segment['id']}/release"
    ):
        if status == 409 and any(
            problem(response, path, *p)
            for p in (
                ("segment-state", "Audio state conflict", "Segment is not queued"),
                (
                    "stale-intent-revision",
                    "Stale intent revision",
                    "Permit belongs to an earlier revision",
                ),
                ("stale-audio", "Stale audio", "Audio release lost its current claim"),
            )
        ):
            outcome, reason = (
                "EXPECTED_STALE_REFUSAL",
                "Bound queued old segment after accepted correction",
            )
        elif (
            status == 200
            and response.get("segment_id") == segment["id"]
            and response.get("state") == "PUBLISHED"
        ):
            outcome, reason = "OBSERVABLE_ACCEPTANCE", "Record actual stale publication"
    playback = (
        method == "POST"
        and base == services["api"]
        and segment
        and path == f"/v1/calls/{item.get('call_id')}/playback-events"
        and request.get("event_type") == "STARTED"
        and segment.get("intent_revision") == 1
    )
    changed = (
        family == "version-change-before-start" and "VERSION_ONLY_CHANGE" in names and revision == 1
    )
    version_proof = version_change_supported(row, call, scenario, item) if changed else []
    buffered = family == "buffered-stale" and revision > 1
    if playback and (changed or buffered):
        if (
            status == 202
            and response.get("event_id") == request.get("event_id")
            and response.get("segment_id") == segment_id
            and response.get("state") == "STARTED"
        ):
            outcome, reason = (
                "OBSERVABLE_ACCEPTANCE",
                "Actual STARTED proxy retained; no inference of human understanding",
            )
        elif (
            status == 409
            and buffered
            and problem(response, path, "stale-audio", "Stale audio", "Segment cannot start")
        ):
            outcome, reason = "EXPECTED_STALE_REFUSAL", "Bound old segment after durable correction"
        elif (
            status == 409
            and changed
            and version_proof
            and arm in {"P1", "P2"}
            and problem(
                response,
                path,
                "fresh-evidence-required",
                "Fresh evidence required",
                "Current source facts do not support audio playback",
            )
        ):
            outcome, reason = (
                "EXPECTED_VERSION_REFUSAL",
                "Named version-change fault precedes bound STARTED attempt",
            )
    # No timeout/provider send is converted to an application failure here.
    return {
        "version": VERSION,
        "classification": outcome,
        "reason": reason,
        "call_hash": stable_hash(call),
        "family": family,
        "arm": arm,
        "accepted_revision": revision,
        "request": request,
        "response": response,
        "trace_id": response.get("trace_id") or call.get("trace_id"),
        "at": call.get("received_at"),
        "context_hash": stable_hash(
            {
                "prior_calls": prior,
                "barriers": row.get("barriers", []),
                "scenario": scenario,
                "item": item,
            }
        ),
        "version_observation_hashes": version_proof,
    }


def retain(trial: Any, proof: dict[str, Any]) -> None:
    trial.row.setdefault("permissive_response_checks", []).append(proof)
    if proof["classification"] == "UNEXPECTED_RESPONSE":
        from research.execution_setup.core import atomic, now

        trial.row.setdefault("permissive_response_errors", []).append(proof)
        trial.save()  # transactional checkpoint before returning to caller
        trial.ledger.event("UNEXPECTED_PERMISSIVE_RESPONSE", execution_id=trial.id, proof=proof)
        pause = {
            "reason": "UNEXPECTED_PERMISSIVE_RESPONSE",
            "execution_id": trial.id,
            "trace_id": proof["trace_id"],
            "at": now(),
        }
        atomic(trial.ledger.root / "pause.json", pause)
        # Pause the admission authority immediately; collector still finishes its window.
        from controls import Journal

        Journal(trial.ledger.root.parent.parent).pause("UNEXPECTED_PERMISSIVE_RESPONSE")
    trial.save()


def finish_driver(trial: Any) -> None:
    if trial.row.get("permissive_response_errors"):
        trial.row["status"] = "FAILED"
        trial.row["failure"] = {
            "type": "UNEXPECTED_PERMISSIVE_RESPONSE",
            "detail": "Earlier unexpected response retained despite later driver completion",
            "proofs": trial.row["permissive_response_errors"],
        }
        # Never allow semantic evidence-refusal classification to mask a prior defect.
        trial.row.pop("driver_classification", None)
        trial.save()
