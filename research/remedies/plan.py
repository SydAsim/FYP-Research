"""Immutable six-fixture exploratory plan, fixed before any planned execution."""

import json
from datetime import UTC, datetime

from research.remedies.preserve import OUTPUT, ROOT
from research.scenario_dsl.models import stable_hash

FIXTURES = [
    {
        "id": "E1",
        "family": "stale-claim-after-verification",
        "barriers": ["VERIFIED_BEFORE_CORRECTION", "OLD_CLAIM_ATTEMPT"],
        "hours": [15, 16],
    },
    {
        "id": "E2",
        "family": "resource-change-before-start",
        "barriers": ["PUBLISHED_BEFORE_START", "EXTERNAL_RESOURCE_VERSION_CHANGE"],
        "hours": [15, 16],
        "external_change": "VERSION_ONLY",
    },
    {
        "id": "E3",
        "family": "decisive-late-progress",
        "barriers": ["DECISIVE_ACK_WITHHELD", "REVISION_ACCEPTED_BEFORE_ACK"],
        "hours": [15, 16],
    },
    {
        "id": "E4",
        "family": "restart-before-repair-delivery",
        "barriers": ["OBLIGATION_PERSISTED", "WORKER_PROCESS_RESTART", "AUTOMATIC_PUBLICATION"],
        "hours": [15, 16],
    },
    {
        "id": "E5",
        "family": "missing-ack-reconnect",
        "barriers": ["CORRECTED_STARTED", "COMPLETION_ACK_MISSING", "CLIENT_RECONNECTED"],
        "hours": [15, 16],
    },
    {
        "id": "E6",
        "family": "revision-during-repair",
        "barriers": ["R2_CORRECTION_STARTED", "R3_ACCEPTED", "R2_COMPLETION_DELAYED"],
        "hours": [15, 16, 17],
    },
]


def freeze_plan() -> dict[str, object]:
    path = OUTPUT / "exploratory-plan.json"
    fixtures = ROOT / "research/fixtures/readiness_v2/fixtures.json"
    fixtures.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(FIXTURES, indent=2) + "\n"
    if fixtures.exists() and fixtures.read_text(encoding="utf-8") != text:
        raise ValueError("Fixture version changed; create another version")
    fixtures.write_text(text, encoding="utf-8")
    body: dict[str, object] = {
        "version": "research-readiness-exploratory-v2",
        "classification": "EXPLORATORY_NOT_PHASE8",
        "planned_executions": 18,
        "arms": ["B3", "P1", "P2"],
        "fixtures": FIXTURES,
        "appointment_date": "2026-11-01",
        "timezone": "Asia/Karachi",
        "duration_minutes": 60,
        "fixture_hash": stable_hash(FIXTURES),
        "plan_document_hash": stable_hash(
            (ROOT / "docs/10_RESEARCH_REMEDIES_V2.md").read_text(encoding="utf-8")
        ),
        "budgets": {
            "drain_passes": 30,
            "reconciliation_attempts": 8,
            "provider_http_seconds": 30,
            "runner_http_seconds": 40,
            "scheduler_http_seconds": 15,
            "repair_lease_seconds": 30,
            "recovery_wait_seconds": 40,
            "verification_ttl_seconds": 30,
        },
        "outcomes": [
            "final_business_state_correct",
            "truth_at_publication",
            "evidence_at_publication",
            "truth_at_playback",
            "evidence_at_playback",
            "incompatible_stale_exposure",
            "correct_final_update",
            "explicit_retraction",
            "repair_telemetry",
        ],
        "anchors": {
            "stale": "durable accepted_at",
            "exposure": "recorded client_time",
            "delivery": "server_received_at",
            "correction": "external scripted_at retained separately",
        },
        "voice": "SCRIPTED_TONE_SEMANTIC_PROXY_EQUAL_DURATION_METADATA",
        "missing_evidence": "UNKNOWN; never silence/completion",
        "phase8_started": False,
    }
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if {k: v for k, v in saved.items() if k not in ("created_at", "plan_hash")} != body:
            raise ValueError("Plan drift; new version required")
        return dict(saved)
    body["created_at"] = datetime.now(UTC).isoformat()
    body["plan_hash"] = stable_hash(body)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return body


if __name__ == "__main__":
    print(json.dumps(freeze_plan(), indent=2))
