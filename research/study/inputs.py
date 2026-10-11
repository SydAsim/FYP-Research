"""Materialize 500 new specifications; not 500 independently sampled people."""

import random
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from research.arms import Arm
from research.provider_simulator.models import (
    BarrierName,
    FaultKind,
    FaultRule,
    ScenarioConfig,
    Visibility,
)
from research.scenario_dsl.models import stable_hash
from research.study.models import Intent, Stratum, StudyCase

SEED = 8042026
ZONES = ("Asia/Karachi", "Europe/London", "America/New_York", "Australia/Sydney", "UTC")
PRIMARY = [Arm.B3, Arm.P1, Arm.P2]
SECONDARY = [Arm.B0, Arm.B1, Arm.B2]


def recipes() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def add(
        stratum: Stratum,
        name: str,
        phase: str,
        *,
        provider: ScenarioConfig | None = None,
        exposure: str = "FULL",
        hooks: list[str] | None = None,
        **extra: Any,
    ) -> None:
        result.append(
            {
                "stratum": stratum.value,
                "name": name,
                "phase": phase,
                "provider": (provider or ScenarioConfig()).model_dump(mode="json"),
                "exposure": exposure,
                "hooks": hooks or [],
                **extra,
            }
        )

    for zone in ZONES:
        for duration in (30, 60):
            add(Stratum.CLEAN, f"clean-{zone}-{duration}", "NONE", zone=zone, duration=duration)
    for atomic in (True, False):
        for visibility in Visibility:
            for response in ("DROP_RESPONSE", "REORDER_RESPONSE"):
                config = ScenarioConfig(
                    supports_reschedule=atomic,
                    visibility=visibility,
                    visibility_reads=2
                    if visibility in (Visibility.DELAYED, Visibility.STALE)
                    else 0,
                    held_barriers=["AFTER_COMMIT_BEFORE_RESPONSE:1"],
                    faults=[
                        FaultRule(
                            request_index=1,
                            stage=BarrierName.AFTER_COMMIT_BEFORE_RESPONSE,
                            kind=FaultKind(response.removesuffix("_RESPONSE"))
                            if response == "REORDER_RESPONSE"
                            else FaultKind.DROP_RESPONSE,
                        )
                    ],
                )
                add(
                    Stratum.AMBIGUITY,
                    f"hidden-{atomic}-{visibility}-{response}",
                    "P3",
                    provider=config,
                    hooks=["COMMIT_LOG_APPENDED", "RESPONSE_WITHHELD"],
                )
    for atomic in (True, False):
        for status in (True, False):
            config = ScenarioConfig(
                supports_reschedule=atomic,
                status_lookup=status,
                resource_lookup=not status,
                held_barriers=["AFTER_COMMIT_BEFORE_RESPONSE:1"],
                faults=[
                    FaultRule(
                        request_index=1,
                        stage=BarrierName.AFTER_COMMIT_BEFORE_RESPONSE,
                        kind=FaultKind.DROP_RESPONSE,
                    )
                ],
            )
            add(
                Stratum.AMBIGUITY,
                f"hidden-single-observation-{atomic}-{status}",
                "P3",
                provider=config,
                hooks=["COMMIT_LOG_APPENDED", "RESPONSE_WITHHELD"],
            )
    for name, phase, exposure, hooks in (
        (
            "verified-stale-attempt",
            "P5",
            "NONE",
            ["VERIFIED", "CORRECTION_ACCEPTED", "OLD_CLAIM_ATTEMPT"],
        ),
        ("queued-stale", "P6", "NONE", ["GENERATED_QUEUED", "CORRECTION_ACCEPTED"]),
        ("buffered-stale", "P7", "NONE", ["PUBLISHED", "CORRECTION_ACCEPTED", "START_ATTEMPT"]),
        ("intro-control", "P8", "INTRO_TWO_WORDS", ["INTRO_ACK", "CORRECTION_ACCEPTED"]),
        ("partial-time", "P8", "THROUGH_AM_PM", ["TIME_PREDICATE_ACK", "CORRECTION_ACCEPTED"]),
        ("full-before-correction", "P9", "FULL", ["FULL_ACK", "CORRECTION_ACCEPTED"]),
        (
            "version-change-before-start",
            "P7",
            "START_ATTEMPT",
            ["PUBLISHED", "VERSION_ONLY_CHANGE", "START_ATTEMPT"],
        ),
        (
            "late-decisive-ack",
            "P8",
            "THROUGH_AM_PM_DELAYED",
            ["ACK_WITHHELD", "CORRECTION_ACCEPTED", "ACK_DELIVERED"],
        ),
        (
            "restart-before-repair",
            "P9",
            "FULL",
            ["FULL_ACK", "CORRECTION_ACCEPTED", "REPAIR_PERSISTED_OR_ABLATED", "WORKER_RESTART"],
        ),
        (
            "reconnect-third-revision",
            "P8",
            "REPAIR_TIME_PREDICATE",
            [
                "FULL_ACK",
                "R2_ACCEPTED",
                "R2_STARTED",
                "ACK_MISSING",
                "CLIENT_RECONNECT",
                "R3_ACCEPTED",
                "R2_ACK_DELAYED",
            ],
        ),
    ):
        add(Stratum.EXPOSURE, name, phase, exposure=exposure, hooks=hooks)
    for name, phase, atomic, kind, stage, hooks, status in (
        ("pre-dispatch-atomic", "P1", True, None, None, ["BEFORE_DISPATCH"], True),
        ("pre-dispatch-compensating", "P1", False, None, None, ["BEFORE_DISPATCH"], True),
        ("pre-commit-delay", "P2", True, FaultKind.DELAY, BarrierName.BEFORE_COMMIT, [], True),
        ("precommit-5xx", "P2", True, FaultKind.RETURN_5XX, BarrierName.BEFORE_COMMIT, [], True),
        (
            "partial-effect",
            "P2",
            False,
            FaultKind.PARTIAL_EFFECT,
            BarrierName.BEFORE_COMMIT,
            [],
            True,
        ),
        (
            "ack-before-verification",
            "P4",
            True,
            None,
            None,
            ["RESPONSE_RECEIVED_BEFORE_VERIFY"],
            True,
        ),
        (
            "redis-loss",
            "P3",
            True,
            FaultKind.DROP_RESPONSE,
            BarrierName.AFTER_COMMIT_BEFORE_RESPONSE,
            ["REDIS_FLUSH_RESEARCH_ONLY"],
            True,
        ),
        (
            "resource-only",
            "P3",
            True,
            FaultKind.DROP_RESPONSE,
            BarrierName.AFTER_COMMIT_BEFORE_RESPONSE,
            [],
            False,
        ),
        (
            "duplicate-response",
            "P4",
            True,
            FaultKind.DUPLICATE,
            BarrierName.AFTER_RESPONSE,
            ["DUPLICATE_DELIVERY"],
            True,
        ),
        (
            "concurrent-resource-change",
            "P5",
            True,
            None,
            None,
            ["VERIFIED", "EXTERNAL_VERSION_CHANGE"],
            True,
        ),
    ):
        held = [f"{stage}:1"] if kind is FaultKind.DELAY else []
        faults = [FaultRule(request_index=1, stage=stage, kind=kind)] if stage and kind else []
        add(
            Stratum.BOUNDARY,
            name,
            phase,
            provider=ScenarioConfig(
                supports_reschedule=atomic, status_lookup=status, held_barriers=held, faults=faults
            ),
            hooks=hooks,
        )
    if len(result) != 50:
        raise ValueError("Exactly 50 declared recipe clusters required")
    return result


def materialize() -> list[StudyCase]:
    rng = random.Random(SEED)
    cases = []
    for family, recipe in enumerate(recipes()):
        stratum = Stratum(recipe["stratum"])
        cluster = f"p8v3-family-{family + 1:02d}-{stable_hash(recipe)[:8]}"
        for member in range(10):
            zone = recipe.get("zone", rng.choice(ZONES))
            start = datetime(
                2027,
                rng.choice((1, 2, 4, 5, 7, 10)),
                rng.randint(1, 25),
                rng.randint(9, 13),
                rng.choice((0, 15, 30)),
                tzinfo=ZoneInfo(zone),
            )
            minutes = recipe.get("duration", rng.choice((30, 45, 60)))
            starts = [start]
            if stratum is not Stratum.CLEAN:
                starts.append(start + timedelta(hours=rng.choice((1, 2, 3))))
            if recipe["name"] == "reconnect-third-revision":
                starts.append(starts[-1] + timedelta(days=1, hours=1))
            issue = (
                "tap leak",
                "door hinge",
                "window latch",
                "wall patch",
                "sink seal",
                "cabinet handle",
                "drain inspection",
                "floorboard",
                "vent grille",
                "light fixture",
            )[member]
            intents = [
                Intent(
                    revision=index + 1,
                    start=value,
                    end=value + timedelta(minutes=minutes),
                    timezone=zone,
                    transcript=(
                        f"Book a {minutes}-minute maintenance visit for the {issue} at "
                        if index == 0
                        else "Change that maintenance visit to "
                    )
                    + f"{value.isoformat()} in {zone}.",
                )
                for index, value in enumerate(starts)
            ]
            secondary = [] if stratum is Stratum.EXPOSURE else SECONDARY
            order = PRIMARY + secondary
            rng.shuffle(order)
            cases.append(
                StudyCase(
                    case_id=f"p8v3-{family + 1:02d}-{member + 1:02d}",
                    stratum=stratum,
                    cluster_id=cluster,
                    generator_family=recipe["name"],
                    member=member,
                    cluster_representative=member == 0,
                    seed=rng.getrandbits(31),
                    resource_binding="NEW_SYNTHETIC_PROPERTY_MAINTENANCE",
                    initial_state="EMPTY_RESOURCE",
                    issue=issue,
                    intents=intents,
                    correction_barrier=recipe["phase"],
                    fault_schedule=recipe["hooks"],
                    provider=ScenarioConfig.model_validate(recipe["provider"]),
                    speech_exposure=recipe["exposure"],
                    media="SCRIPTED_TONE_PROTOCOL_PROXY",
                    primary_arms=PRIMARY,
                    secondary_arms=secondary,
                    arm_order=order,
                    observation_budget_seconds=600,
                )
            )
    if len(cases) != 500 or len({c.semantic_hash for c in cases}) != 500:
        raise ValueError("Inputs must be 500 distinct semantic specifications, not ID-only copies")
    return cases
