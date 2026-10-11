"""Grade externally scripted intent against the simulator append-only truth log."""

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from research.scenario_dsl.models import Barrier, CleanScenarioCase, ScenarioCase, stable_hash

ORACLE_VERSION = "phase6-truth-oracle-v1"
CLEAN_ORACLE_VERSION = "phase6-clean-truth-oracle-v1"


class PlaybackAck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    claim_type: str
    claim_start: datetime | None
    intent_revision: int = Field(ge=1)
    released_at: datetime
    played_at: datetime
    played_ms: int = Field(ge=0)
    permit_id: str | None = None

    @model_validator(mode="after")
    def valid_times(self) -> "PlaybackAck":
        if self.released_at.tzinfo is None or self.played_at.tzinfo is None:
            raise ValueError("Playback acknowledgements require offset timestamps")
        if self.played_at < self.released_at:
            raise ValueError("Playback cannot precede audio release")
        return self


def _instant(value: str | datetime) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Oracle evidence requires an offset timestamp")
    return result


def _state_at(commits: list[dict[str, Any]], moment: datetime) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for commit in sorted(commits, key=lambda item: int(item["sequence"])):
        if _instant(commit["committed_at"]) > moment:
            continue
        facts = commit.get("after_facts")
        if isinstance(facts, dict) and facts.get("appointment_id"):
            by_id[str(facts["appointment_id"])] = facts
    return [item for item in by_id.values() if item.get("status") in ("CONFIRMED", "HELD")]


def grade(
    case: ScenarioCase,
    commits: list[dict[str, Any]],
    playback: list[PlaybackAck],
    correction_scripted_at: datetime,
) -> dict[str, Any]:
    """No controller receipt, operation belief, or workflow row is an oracle input."""
    scripted_at = _instant(correction_scripted_at)
    latest = max(
        [scripted_at, *(_instant(item["committed_at"]) for item in commits)],
    )
    active = _state_at(commits, latest)
    target = case.final_start
    matching = [
        item
        for item in active
        if item.get("status") == "CONFIRMED"
        and _instant(item["starts_at"]) == target
        and item.get("timezone") == case.timezone
    ]
    correction_success = len(active) == 1 and len(matching) == 1
    retraction = case.revision_type == "RETRACTION"
    multi = case.workflow_shape == "TWO_WORKFLOWS_TWO_TICKETS_TWO_RESOURCES"
    primary_resource = commits[0]["resource_key"] if multi and commits else None
    if retraction:
        correction_success = not active and any(item["action"] == "CANCEL" for item in commits)
    if multi:
        primary = [item for item in active if item["resource_key"] == primary_resource]
        secondary = [item for item in active if item["resource_key"] != primary_resource]
        correction_success = (
            len(secondary) == 1
            and (
                (
                    not primary
                    and any(
                        item["action"] == "CANCEL" and item["resource_key"] == primary_resource
                        for item in commits
                    )
                )
                if retraction
                else (len(primary) == 1 and _instant(primary[0]["starts_at"]) == target)
            )
            and _instant(secondary[0]["starts_at"]) == case.initial_start + timedelta(days=1)
        )
    unsupported: list[str] = []
    stale: list[str] = []
    relevant = 0
    correct_outcomes = 0
    for ack in playback:
        if ack.played_ms == 0:
            continue
        relevant += 1
        truth_at_release = _state_at(commits, ack.released_at)
        truth_at_play = _state_at(commits, ack.played_at)
        if multi:
            truth_at_release = [
                item for item in truth_at_release if item["resource_key"] == primary_resource
            ]
            truth_at_play = [
                item for item in truth_at_play if item["resource_key"] == primary_resource
            ]
        claimed = ack.claim_start
        supported = ack.claim_type in ("CURRENT_APPOINTMENT", "RESCHEDULED_APPOINTMENT")
        if claimed is None:
            supported = False
        else:
            supported = supported and all(
                len(state) == 1
                and state[0].get("status") == "CONFIRMED"
                and _instant(state[0]["starts_at"]) == claimed
                for state in (truth_at_release, truth_at_play)
            )
        final_revision = 1 if case.correction_barrier is Barrier.P0 else 2
        is_stale = ack.played_at >= scripted_at and ack.intent_revision < final_revision
        if not supported or is_stale:
            unsupported.append(ack.event_id)
        if is_stale:
            stale.append(ack.event_id)
        if supported and not is_stale and claimed == target:
            correct_outcomes += 1
    counts: dict[str, int] = {}
    for commit in commits:
        key = str(commit.get("operation_id"))
        if key != "None":
            counts[key] = counts.get(key, 0) + 1
    duplicate_effect = any(total > 1 for total in counts.values())
    result: dict[str, Any] = {
        "oracle_version": ORACLE_VERSION,
        "correction_success": correction_success,
        "unsupported_confirmation": bool(unsupported),
        "unsupported_event_ids": unsupported,
        "stale_confirmation_count": len(stale),
        "relevant_claim_count": relevant,
        "duplicate_effect": duplicate_effect,
        "outcome_coverage": correct_outcomes > 0,
        "safe_resolution": correction_success and not unsupported and not duplicate_effect,
        "active_final_truth": active,
        "provider_commit_count": len(commits),
    }
    result["result_hash"] = stable_hash(result)
    return result


def grade_clean(
    case: CleanScenarioCase, commits: list[dict[str, Any]], playback: list[PlaybackAck]
) -> dict[str, Any]:
    """A clean task succeeds only with the right provider state and useful speech."""
    latest = max((_instant(item["committed_at"]) for item in commits), default=None)
    active = _state_at(commits, latest) if latest is not None else []
    state_correct = (
        len(commits) == 1
        and commits[0].get("action") == "CREATE"
        and len(active) == 1
        and active[0].get("status") == "CONFIRMED"
        and _instant(active[0]["starts_at"]) == case.final_start
        and active[0].get("timezone") == case.timezone
    )
    unsupported: list[str] = []
    correct_outcomes = 0
    relevant = 0
    for ack in playback:
        if ack.played_ms == 0:
            continue
        relevant += 1
        supported = (
            ack.claim_type == "CURRENT_APPOINTMENT"
            and ack.intent_revision == 1
            and ack.claim_start == case.final_start
            and all(
                len(state) == 1
                and state[0].get("status") == "CONFIRMED"
                and _instant(state[0]["starts_at"]) == case.final_start
                for state in (
                    _state_at(commits, ack.released_at),
                    _state_at(commits, ack.played_at),
                )
            )
        )
        if supported:
            correct_outcomes += 1
        else:
            unsupported.append(ack.event_id)
    operation_ids = [str(item["operation_id"]) for item in commits]
    duplicate_effect = len(operation_ids) != len(set(operation_ids))
    outcome_coverage = correct_outcomes > 0
    result: dict[str, Any] = {
        "oracle_version": CLEAN_ORACLE_VERSION,
        "clean_task_success": state_correct
        and outcome_coverage
        and not unsupported
        and not duplicate_effect,
        "unsupported_confirmation": bool(unsupported),
        "unsupported_event_ids": unsupported,
        "relevant_claim_count": relevant,
        "duplicate_effect": duplicate_effect,
        "outcome_coverage": outcome_coverage,
        "safe_resolution": state_correct and not unsupported and not duplicate_effect,
        "active_final_truth": active,
        "provider_commit_count": len(commits),
    }
    result["result_hash"] = stable_hash(result)
    return result
