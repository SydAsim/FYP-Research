"""Single-use permits and deterministic text publication with fresh revalidation."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from apps.api_controller.phase1_service import (
    DomainProblem,
    _command_replay,
    _connection,
    _event,
    _execute,
    _hash,
    _one,
    _receipt,
    _workflow,
)
from apps.api_controller.phase3_models import AuthorizeClaimRequest, PermitCommand
from apps.api_controller.phase3_verification_service import (
    _evaluate,
    _external_observations,
    _local_effect_observation,
    _local_observation,
)
from packages.domain.phase3_verification import ClaimType, Result, receipt_applicable
from packages.speech_policy.phase3 import (
    POLICY_VERSION,
    PROGRESS,
    TEMPLATE_VERSION,
    UNKNOWN,
    render,
)


def _claim_type(value: str) -> ClaimType:
    return ClaimType(value)


def _permit_locator(conn: Any, permit_id: UUID) -> dict[str, Any]:
    locator = _one(
        conn,
        "SELECT p.workflow_id,c.operation_id FROM claim_permits p "
        "JOIN claims c ON c.id=p.claim_id WHERE p.id=%s",
        (permit_id,),
    )
    if locator is None:
        raise DomainProblem("permit-not-found", "Permit not found", "Unknown permit", 404)
    return locator


def _load_permit(
    conn: Any, permit_id: UUID
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    permit = _one(conn, "SELECT * FROM claim_permits WHERE id=%s FOR UPDATE", (permit_id,))
    assert permit is not None
    claim = _one(conn, "SELECT * FROM claims WHERE id=%s", (permit["claim_id"],))
    receipt = _one(conn, "SELECT * FROM verification_receipts WHERE id=%s", (permit["receipt_id"],))
    assert claim is not None and receipt is not None
    return permit, claim, receipt


def _check_receipt(
    workflow: dict[str, Any],
    permit: dict[str, Any],
    claim: dict[str, Any],
    receipt: dict[str, Any],
    now: datetime,
    current_resource_version: str | None,
) -> None:
    if permit["workflow_id"] != workflow["id"] or claim["workflow_id"] != workflow["id"]:
        raise DomainProblem("permit-scope", "Permit scope mismatch", "Workflow binding changed")
    if permit["intent_revision"] != workflow["current_revision"]:
        raise DomainProblem(
            "stale-intent-revision",
            "Stale intent revision",
            "Permit belongs to an earlier revision",
        )
    if now >= permit["expires_at"] or permit["invalidated_at"] is not None:
        raise DomainProblem("permit-expired", "Permit expired", "Permit is no longer valid")
    claim_type = _claim_type(claim["claim_type"])
    if not receipt_applicable(
        receipt, claim_type, workflow["current_revision"], now, current_resource_version
    ):
        raise DomainProblem(
            "receipt-not-applicable",
            "Receipt not applicable",
            "Receipt no longer supports this claim",
        )
    if (
        claim["semantic_predicates_json"] != receipt["predicates_json"]
        or claim["resource_version"] != receipt["observed_resource_version"]
    ):
        raise DomainProblem(
            "claim-not-entailed", "Claim not entailed", "Claim predicates exceed receipt evidence"
        )
    text = render(claim_type, claim["semantic_predicates_json"])
    if _hash(text) != claim["content_hash"] or claim["template_version"] != TEMPLATE_VERSION:
        raise DomainProblem(
            "template-mismatch",
            "Template mismatch",
            "Prepared text does not match the deterministic template",
        )


def authorize(request: AuthorizeClaimRequest, trace_id: str) -> dict[str, Any]:
    request_hash = _hash(request.model_dump(mode="json", exclude={"command_id"}))
    with _connection() as conn:
        locator = _one(
            conn, "SELECT workflow_id FROM verification_receipts WHERE id=%s", (request.receipt_id,)
        )
        if locator is None:
            raise DomainProblem("receipt-not-found", "Receipt not found", "Unknown receipt", 404)
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, request.command_id, "authorize_claim", request_hash)
        if replay is not None:
            return replay
        receipt = _one(
            conn, "SELECT * FROM verification_receipts WHERE id=%s", (request.receipt_id,)
        )
        assert receipt is not None
        operation = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (receipt["operation_id"],)
        )
        assert operation is not None
        if workflow["current_revision"] != request.expected_intent_revision:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                "Claim revision is no longer current",
            )
        now = datetime.now(UTC)
        claim_type = _claim_type(receipt["claim_type"])
        if not receipt_applicable(
            receipt,
            claim_type,
            workflow["current_revision"],
            now,
            receipt["observed_resource_version"],
        ):
            raise DomainProblem(
                "receipt-not-applicable",
                "Receipt not applicable",
                "A current SATISFIED receipt is required",
            )
        predicates = receipt["predicates_json"]
        try:
            text = render(claim_type, predicates)
        except (ValueError, KeyError, TypeError) as exc:
            raise DomainProblem(
                "invalid-evidence",
                "Invalid evidence",
                "Receipt predicates cannot render a safe claim",
            ) from exc
        claim_id, permit_id = uuid4(), uuid4()
        expires_at = min(receipt["valid_until"], now + timedelta(seconds=30))
        _execute(
            conn,
            "INSERT INTO claims (id,workflow_id,operation_id,intent_revision,claim_type,"
            "semantic_predicates_json,tense,resource_version,template_version,content_hash) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                claim_id,
                workflow["id"],
                operation["id"],
                workflow["current_revision"],
                claim_type.value,
                Jsonb(predicates),
                "HISTORICAL" if claim_type is ClaimType.HISTORICAL_EFFECT else "CURRENT",
                receipt["observed_resource_version"],
                TEMPLATE_VERSION,
                _hash(text),
            ),
        )
        _execute(
            conn,
            "INSERT INTO claim_permits (id,claim_id,receipt_id,workflow_id,intent_revision,"
            "policy_version,state,authorized_at,expires_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,'AUTHORIZED',%s,%s)",
            (
                permit_id,
                claim_id,
                receipt["id"],
                workflow["id"],
                workflow["current_revision"],
                POLICY_VERSION,
                now,
                expires_at,
            ),
        )
        if operation["intent_revision"] == workflow["current_revision"]:
            _execute(
                conn,
                "UPDATE operations SET speech_eligibility='CLAIM_PERMITTED',"
                "updated_at=now() WHERE id=%s",
                (operation["id"],),
            )
        _event(
            conn,
            workflow,
            "ClaimPrepared",
            workflow["current_revision"],
            operation["id"],
            request.command_id,
            {"claim_id": str(claim_id), "content_hash": _hash(text)},
            trace_id,
        )
        _event(
            conn,
            workflow,
            "ClaimAuthorized",
            workflow["current_revision"],
            operation["id"],
            request.command_id,
            {"permit_id": str(permit_id), "receipt_id": str(receipt["id"])},
            trace_id,
        )
        response = {
            "claim_id": str(claim_id),
            "permit_id": str(permit_id),
            "claim_type": claim_type.value,
            "content_hash": _hash(text),
            "expires_at": expires_at.isoformat(),
            "state": "AUTHORIZED",
        }
        _receipt(
            conn, request.command_id, "authorize_claim", workflow["id"], request_hash, response
        )
        return response


def queue(permit_id: UUID, request: PermitCommand, trace_id: str) -> dict[str, Any]:
    request_hash = _hash(
        {"permit_id": str(permit_id), "expected_intent_revision": request.expected_intent_revision}
    )
    with _connection() as conn:
        locator = _permit_locator(conn, permit_id)
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, request.command_id, "queue_claim", request_hash)
        if replay is not None:
            return replay
        operation = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (locator["operation_id"],)
        )
        assert operation is not None
        permit, claim, receipt = _load_permit(conn, permit_id)
        if request.expected_intent_revision != workflow["current_revision"]:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                "Queue request uses an old revision",
            )
        if permit["state"] != "AUTHORIZED":
            raise DomainProblem(
                "permit-state", "Permit state conflict", "Permit is not available to queue"
            )
        _check_receipt(
            workflow,
            permit,
            claim,
            receipt,
            datetime.now(UTC),
            receipt["observed_resource_version"],
        )
        _execute(
            conn,
            "UPDATE claim_permits SET state='QUEUED',version=version+1 WHERE id=%s",
            (permit_id,),
        )
        _event(
            conn,
            workflow,
            "ClaimQueued",
            workflow["current_revision"],
            operation["id"],
            request.command_id,
            {"permit_id": str(permit_id)},
            trace_id,
        )
        response = {
            "permit_id": str(permit_id),
            "state": "QUEUED",
            "content_hash": claim["content_hash"],
        }
        _receipt(conn, request.command_id, "queue_claim", workflow["id"], request_hash, response)
        return response


def publish(permit_id: UUID, request: PermitCommand, trace_id: str) -> dict[str, Any]:
    request_hash = _hash(
        {"permit_id": str(permit_id), "expected_intent_revision": request.expected_intent_revision}
    )
    with _connection() as conn:
        locator = _permit_locator(conn, permit_id)
        replay = _command_replay(conn, request.command_id, "publish_claim", request_hash)
        if replay is not None:
            return replay
        operation = _one(conn, "SELECT * FROM operations WHERE id=%s", (locator["operation_id"],))
        claim = _one(
            conn,
            "SELECT c.* FROM claims c JOIN claim_permits p ON p.claim_id=c.id WHERE p.id=%s",
            (permit_id,),
        )
        assert operation is not None and claim is not None
    claim_type = _claim_type(claim["claim_type"])
    observations = (
        _external_observations(operation, claim_type)
        if operation["provider_adapter"] == "simulator"
        else []
    )
    error: DomainProblem | None = None
    response: dict[str, Any] | None = None
    with _connection() as conn:
        workflow = _workflow(conn, locator["workflow_id"])
        replay = _command_replay(conn, request.command_id, "publish_claim", request_hash)
        if replay is not None:
            return replay
        current_op = _one(
            conn, "SELECT * FROM operations WHERE id=%s FOR UPDATE", (operation["id"],)
        )
        assert current_op is not None
        permit, current_claim, receipt = _load_permit(conn, permit_id)
        if workflow["current_revision"] != request.expected_intent_revision:
            raise DomainProblem(
                "stale-intent-revision",
                "Stale intent revision",
                "Publication revision is no longer current",
            )
        if permit["state"] != "QUEUED":
            raise DomainProblem(
                "permit-state", "Permit state conflict", "Permit is not queued for publication"
            )
        handoff = None
        if claim_type is ClaimType.HANDOFF_CREATED:
            handoff = _one(
                conn,
                "SELECT * FROM handoffs WHERE workflow_id=%s "
                "AND state IN ('OPEN','ACKNOWLEDGED') ORDER BY created_at DESC LIMIT 1",
                (workflow["id"],),
            )
        elif current_op["provider_adapter"] == "local_postgres":
            observations.append(_local_observation(conn, workflow))
            if claim_type is ClaimType.RESCHEDULED_APPOINTMENT:
                observations.append(_local_effect_observation(conn, current_op))
        fresh = _evaluate(claim_type, workflow, current_op, observations, handoff)
        now = datetime.now(UTC)
        if fresh.result is not Result.SATISFIED or fresh.predicates != receipt["predicates_json"]:
            if fresh.result is Result.VIOLATED or (
                fresh.resource_version is not None
                and fresh.resource_version != receipt["observed_resource_version"]
            ):
                event_id = _event(
                    conn,
                    workflow,
                    "ReceiptInvalidated",
                    workflow["current_revision"],
                    current_op["id"],
                    request.command_id,
                    {"receipt_id": str(receipt["id"]), "reason": "resource_changed"},
                    trace_id,
                )
                _execute(
                    conn,
                    "UPDATE verification_receipts SET invalidated_at=now(),"
                    "invalidating_event_id=%s WHERE id=%s AND invalidated_at IS NULL",
                    (event_id, receipt["id"]),
                )
                _execute(
                    conn,
                    "UPDATE claim_permits SET state='INVALIDATED',"
                    "invalidated_at=now(),invalidating_event_id=%s,version=version+1 "
                    "WHERE id=%s",
                    (event_id, permit_id),
                )
                _event(
                    conn,
                    workflow,
                    "ClaimPermitInvalidated",
                    workflow["current_revision"],
                    current_op["id"],
                    request.command_id,
                    {"permit_id": str(permit_id), "reason": "resource_changed"},
                    trace_id,
                )
            error = DomainProblem(
                "fresh-evidence-required",
                "Fresh evidence required",
                "Current source facts do not support publication",
            )
        else:
            _check_receipt(workflow, permit, current_claim, receipt, now, fresh.resource_version)
            text = render(claim_type, current_claim["semantic_predicates_json"])
            _execute(
                conn,
                "UPDATE claim_permits SET state='PUBLISHED',version=version+1 "
                "WHERE id=%s AND state='QUEUED'",
                (permit_id,),
            )
            _event(
                conn,
                workflow,
                "ClaimPublished",
                workflow["current_revision"],
                current_op["id"],
                request.command_id,
                {
                    "permit_id": str(permit_id),
                    "claim_id": str(current_claim["id"]),
                    "content_hash": current_claim["content_hash"],
                },
                trace_id,
            )
            response = {
                "publication_id": str(permit_id),
                "permit_id": str(permit_id),
                "claim_id": str(current_claim["id"]),
                "state": "PUBLISHED",
                "text": text,
                "content_hash": current_claim["content_hash"],
            }
            _receipt(
                conn, request.command_id, "publish_claim", workflow["id"], request_hash, response
            )
    if error is not None:
        raise error
    assert response is not None
    return response


def safe_language(workflow_id: UUID) -> dict[str, str]:
    with _connection() as conn:
        workflow = _one(
            conn,
            "SELECT current_revision,resolution_status FROM workflows WHERE id=%s",
            (workflow_id,),
        )
        if workflow is None:
            raise DomainProblem("workflow-not-found", "Workflow not found", "Unknown workflow", 404)
        operation = _one(
            conn,
            "SELECT effect_knowledge FROM operations WHERE workflow_id=%s "
            "ORDER BY created_at DESC LIMIT 1",
            (workflow_id,),
        )
    if workflow["resolution_status"] == "RESOLVED":
        raise DomainProblem(
            "workflow-resolved", "Workflow resolved", "Progress language is not applicable"
        )
    if operation and operation["effect_knowledge"] in ("UNKNOWN", "PARTIAL"):
        return {"kind": "UNKNOWN", "text": UNKNOWN}
    return {"kind": "PROGRESS", "text": PROGRESS}


def permit_detail(permit_id: UUID) -> dict[str, Any]:
    with _connection() as conn:
        permit = _one(conn, "SELECT * FROM claim_permits WHERE id=%s", (permit_id,))
        if permit is None:
            raise DomainProblem("permit-not-found", "Permit not found", "Unknown permit", 404)
        claim = _one(conn, "SELECT * FROM claims WHERE id=%s", (permit["claim_id"],))
    return {"permit": permit, "claim": claim}
