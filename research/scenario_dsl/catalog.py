"""Small versioned high-risk catalog, with secondary covering cells."""

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from research.scenario_dsl.models import (
    Barrier,
    CleanScenarioCase,
    FaultFamily,
    ProviderCapability,
    ProviderVisibility,
    ScenarioCase,
)

CATALOG_VERSION = "phase6-synthetic-maintenance-v1"
ZONE = ZoneInfo("Asia/Karachi")
BASE = datetime(2026, 11, 5, 15, tzinfo=ZONE)
FIXTURE_AUDIO_HASH = hashlib.sha256(
    (Path(__file__).parents[1] / "fixtures" / "audio" / "p8_correction.wav").read_bytes()
).hexdigest()
CLEAN_AUDIO_HASH = hashlib.sha256(
    (Path(__file__).parents[1] / "fixtures" / "audio" / "clean_booking.wav").read_bytes()
).hexdigest()


def case_for(
    barrier: Barrier,
    *,
    seed: int = 1,
    fault: FaultFamily = FaultFamily.NONE,
    key: str | None = None,
    provider_capability: ProviderCapability = ProviderCapability.ATOMIC_RESCHEDULE,
    visibility: ProviderVisibility = ProviderVisibility.IMMEDIATE,
) -> ScenarioCase:
    return ScenarioCase(
        fixture_version=CATALOG_VERSION,
        scenario_key=key or f"maintenance-correction-{barrier.value.lower()}-{seed}",
        revision_type=(
            "PRE_ACCEPT_CORRECTION" if barrier is Barrier.P0 else "PARAMETER_CORRECTION"
        ),
        action_semantics=(
            "CREATE_AFTER_PREACCEPT_CORRECTION"
            if barrier is Barrier.P0
            else (
                "CREATE_THEN_RESCHEDULE"
                if provider_capability.supports_reschedule
                else "CREATE_THEN_COMPENSATE_CANCEL_THEN_CREATE"
            )
        ),
        workflow_shape="ONE_TICKET_ONE_APPOINTMENT",
        acoustic_condition="CLEAN_SCRIPTED_TRANSCRIPT",
        provider_capability=provider_capability,
        visibility=visibility,
        speech_exposure="PARTIAL" if barrier is Barrier.P8 else "NONE",
        fault_family=fault,
        correction_barrier=barrier,
        seed=seed,
        initial_start=BASE,
        final_start=BASE.replace(hour=16),
        timezone="Asia/Karachi",
        initial_transcript="Book maintenance on November fifth twenty twenty six at three P M.",
        correction_transcript="Actually change it to four P M.",
        audio_hash=FIXTURE_AUDIO_HASH,
    )


MANDATORY_HIGH_RISK = (
    case_for(Barrier.P1),
    case_for(Barrier.P2),
    case_for(Barrier.P3, fault=FaultFamily.RESPONSE_LOSS),
    case_for(Barrier.P5),
    case_for(Barrier.P8, fault=FaultFamily.PARTIAL_PLAYBACK),
)
SECONDARY_COVERING = tuple(
    case_for(phase, seed=index + 2)
    for index, phase in enumerate((Barrier.P0, Barrier.P4, Barrier.P6, Barrier.P7, Barrier.P9))
)

CAPABILITY_COVERING = (
    case_for(
        Barrier.P3,
        seed=11,
        fault=FaultFamily.RESPONSE_LOSS,
        key="maintenance-p3-compensate-cancel-create-11",
        provider_capability=ProviderCapability.COMPENSATE_CANCEL_CREATE,
    ),
)

VISIBILITY_COVERING = (
    case_for(
        Barrier.P3,
        seed=12,
        fault=FaultFamily.RESPONSE_LOSS,
        key="maintenance-p3-hidden-commit-delayed-two-reads-12",
        visibility=ProviderVisibility.DELAYED_TWO_READS,
    ),
)

DELAY_COVERING = (
    case_for(
        Barrier.P2,
        seed=13,
        fault=FaultFamily.DELAY,
        key="maintenance-p2-precommit-provider-delay-13",
    ),
)

UNAVAILABLE_COVERING = (
    case_for(
        Barrier.P3,
        seed=15,
        fault=FaultFamily.RESPONSE_LOSS,
        key="maintenance-p3-hidden-commit-unavailable-evidence-15",
        visibility=ProviderVisibility.UNAVAILABLE,
    ),
)

REFUSAL_COVERING = (
    case_for(
        Barrier.P2,
        seed=14,
        fault=FaultFamily.PROVIDER_REFUSAL,
        key="maintenance-p2-precommit-provider-refusal-14",
    ),
)

CONFLICT_COVERING = (
    ScenarioCase.model_validate(
        {
            **case_for(
                Barrier.P5,
                seed=16,
                fault=FaultFamily.PROVIDER_CONFLICT,
                key="maintenance-p5-provider-version-conflict-16",
            ).model_dump(mode="json"),
            "action_semantics": "CREATE_THEN_BLOCKED_RESCHEDULE",
        }
    ),
)

CLEAN_CASES = (
    CleanScenarioCase(
        fixture_version="phase6-clean-maintenance-v1",
        scenario_key="maintenance-clean-create-nov05-15",
        seed=21,
        final_start=BASE,
        timezone="Asia/Karachi",
        transcript="Book maintenance on November fifth twenty twenty six at three P M.",
        audio_hash=CLEAN_AUDIO_HASH,
        acoustic_condition="CLEAN_SCRIPTED_TRANSCRIPT",
        provider_capability=ProviderCapability.ATOMIC_RESCHEDULE,
        visibility=ProviderVisibility.IMMEDIATE,
    ),
)

PARTIAL_COVERING = (
    case_for(
        Barrier.P2,
        seed=17,
        fault=FaultFamily.PARTIAL_EFFECT,
        key="maintenance-p2-partial-provider-effect-17",
    ),
)
STALE_COVERING = (
    case_for(
        Barrier.P3,
        seed=18,
        fault=FaultFamily.RESPONSE_LOSS,
        key="maintenance-p3-stale-two-reads-18",
        visibility=ProviderVisibility.STALE_TWO_READS,
    ),
)
REDIS_COVERING = (
    case_for(Barrier.P3, seed=19, fault=FaultFamily.REDIS_LOSS, key="maintenance-p3-redis-loss-19"),
)

REVISION_COVERING = tuple(
    ScenarioCase.model_validate(
        {
            **case_for(Barrier.P3, seed=30 + index, fault=FaultFamily.RESPONSE_LOSS).model_dump(
                mode="json"
            ),
            "fixture_version": "phase6-revision-maintenance-v2",
            "scenario_key": f"maintenance-p3-{kind.lower()}-{30 + index}",
            "revision_type": kind,
            "action_semantics": action,
            "final_start": final.isoformat(),
            "correction_transcript": transcript,
        }
    )
    for index, (kind, action, final, transcript) in enumerate(
        (
            (
                "RETRACTION",
                "CREATE_THEN_CANCEL",
                BASE,
                "Cancel the maintenance appointment. I no longer want it.",
            ),
            (
                "ADDITIVE_COMPATIBLE",
                "CREATE_THEN_REUSE",
                BASE,
                "Keep November fifth at three P M. The same appointment is still wanted.",
            ),
            (
                "REPLACEMENT",
                "CREATE_THEN_REPLACE",
                BASE + timedelta(days=2, hours=2),
                "Instead book maintenance on November seventh twenty twenty six at five P M.",
            ),
            (
                "CONFLICTING_CHANGE",
                "CREATE_THEN_RESCHEDULE",
                BASE.replace(hour=17),
                "I said four P M but that conflicts with my plans. "
                "My final instruction is five P M.",
            ),
        )
    )
)
MULTI_COVERING = (
    ScenarioCase.model_validate(
        {
            **case_for(Barrier.P3, seed=40, fault=FaultFamily.RESPONSE_LOSS).model_dump(
                mode="json"
            ),
            "fixture_version": "phase6-multi-workflow-v2",
            "scenario_key": "two-workflows-isolated-resources-p3-40",
            "workflow_shape": "TWO_WORKFLOWS_TWO_TICKETS_TWO_RESOURCES",
        }
    ),
)

READ_COVERING = (
    ScenarioCase.model_validate(
        {
            **REVISION_COVERING[1].model_dump(mode="json"),
            "scenario_key": "maintenance-read-preserves-booking-41",
            "seed": 41,
            "action_semantics": "CREATE_READ_REUSE",
            "correction_transcript": "Keep my appointment. Read back its details "
            "without changing it.",
        }
    ),
)
