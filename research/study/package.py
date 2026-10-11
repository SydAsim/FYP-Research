"""Deterministic review catalogue and NOT_STARTED slot ledger; no execution."""

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.scenario_dsl.models import stable_hash
from research.study.analysis import analyze
from research.study.inputs import SEED, materialize, recipes
from research.study.models import VERSION

ROOT = Path("artifacts/phase-8-study-design/v3")
DECISIONS = [
    {
        "id": "D1",
        "topic": "Sampling frame and inferential unit",
        "proposal": "500 new task configurations, 50 purposive recipe clusters; member 0 primary",
        "required": (
            "Approve conditional finite-bank estimand or establish independent recipe frame"
        ),
    },
    {
        "id": "D2",
        "topic": "Clean tolerance and allocation",
        "proposal": "100/200/100/100 tasks; absolute 5pp utility margin",
        "required": (
            "10 clean recipe units are insufficient; redraw allocation/frame or narrow claims"
        ),
    },
    {
        "id": "D3",
        "topic": "Comparison scope and multiple testing",
        "proposal": "P2 versus competent B3 co-primary; P1 and B0-B2 secondary",
        "required": "Approve paired scope, endpoint multiplicity and baseline exclusions",
    },
    {
        "id": "D4",
        "topic": "Typed protocol versus actual speech",
        "proposal": "Scripted tone protocol proxies only; no speech superiority claim",
        "required": (
            "Approve protocol-only scope or separately preregister intelligible aligned voice study"
        ),
    },
    {
        "id": "D5",
        "topic": "Domain and endpoint support",
        "proposal": "Booking and time correction only; no standalone cancellation endpoint",
        "required": (
            "Approve restricted domain; separately version any cancellation oracle expansion"
        ),
    },
    {
        "id": "D6",
        "topic": "Covariates and model assumptions",
        "proposal": "Exact paired summaries; clustered sensitivities; VB mixed and censored AFT",
        "required": (
            "Resolve aliased full covariates, Bayesian versus frequentist "
            "scope and informative censoring"
        ),
    },
    {
        "id": "D7",
        "topic": "Driver qualification and budgets",
        "proposal": "600s observation, equal evidence opportunities and named barriers",
        "required": (
            "Qualify all new hooks across arms on separate calibration inputs before freeze"
        ),
    },
    {
        "id": "D8",
        "topic": "Freeze receipt and source",
        "proposal": (
            "No campaign until explicit human review and immutable versioned "
            "source/configuration freeze"
        ),
        "required": (
            "Review this candidate; create new candidate version if sampling/design changes"
        ),
    },
]
BUDGETS = {
    "observation_seconds": 600,
    "provider_request_seconds": 30,
    "runner_request_seconds": 40,
    "scheduler_request_seconds": 15,
    "simulator_barrier_seconds": 120,
    "core_worker_lease_seconds": 180,
    "repair_worker_lease_seconds": 30,
    "reconciliation_attempts": 8,
    "drain_passes": 30,
    "claim_permit_ttl_seconds": 30,
    "recovery_seconds": 40,
    "model_calls": 0,
    "primary_attempts_per_slot": 1,
    "baseline_corrective_statement_enabled": True,
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build() -> dict[str, Any]:
    cases = materialize()
    body = [c.model_dump(mode="json") for c in cases]
    catalogue = {
        "version": VERSION,
        "status": "DRAFT",
        "seed": SEED,
        "inputs": body,
        "catalogue_hash": stable_hash(body),
    }
    path = Path("research/fixtures/phase8_design_v3/inputs.json")
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != catalogue:
        raise ValueError("Candidate changed: create a new design/fixture version")
    write_json(path, catalogue)
    write_json(ROOT / "inputs.json", catalogue)
    write_json(ROOT / "recipe-provenance.json", recipes())
    slots = [
        {
            "slot_id": f"{case.case_id}:{arm.value}:1",
            "case_id": case.case_id,
            "arm": arm.value,
            "order": order,
            "attempt": 1,
            "cluster_id": case.cluster_id,
            "fixture_hash": case.fixture_hash,
            "status": "NOT_STARTED",
            "execution_id": None,
        }
        for case in cases
        for order, arm in enumerate(case.arm_order)
    ]
    write_json(ROOT / "planned-slots.json", slots)
    manifest = {
        "version": VERSION,
        "status": "DRAFT",
        "seed": SEED,
        "inputs": len(cases),
        "recipe_clusters": len(recipes()),
        "allocation": dict(Counter(c.stratum.value for c in cases)),
        "planned_slots": len(slots),
        "executed_slots": 0,
        "catalogue_hash": catalogue["catalogue_hash"],
        "slot_ledger_hash": stable_hash(slots),
        "budgets": BUDGETS,
        "unresolved_decisions": DECISIONS,
        "review_receipt": None,
        "freeze_hash": None,
        "phase8_started": False,
        "history_reused_as_campaign_data": False,
    }
    inventory_path = ROOT / "source-candidate-inventory.json"
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        manifest["draft_source_hash"] = inventory["source_hash"]
        manifest["draft_source_archive_sha256"] = inventory["archive_sha256"]
        manifest["source_status"] = "UNAPPROVED_DRAFT_SOURCE_CANDIDATE"
    manifest["candidate_hash"] = stable_hash(manifest)
    write_json(ROOT / "manifest.json", manifest)
    write_json(ROOT / "analysis-not-started.json", analyze(cases, []))
    with (ROOT / "input-review.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "stratum",
                "cluster_id",
                "generator_family",
                "member",
                "representative",
                "initial_start",
                "final_start",
                "timezone",
                "revisions",
                "phase",
                "exposure",
                "arm_order",
                "fixture_hash",
            ],
        )
        writer.writeheader()
        for c in cases:
            writer.writerow(
                {
                    "case_id": c.case_id,
                    "stratum": c.stratum,
                    "cluster_id": c.cluster_id,
                    "generator_family": c.generator_family,
                    "member": c.member,
                    "representative": c.cluster_representative,
                    "initial_start": c.intents[0].start.isoformat(),
                    "final_start": c.intents[-1].start.isoformat(),
                    "timezone": c.intents[-1].timezone,
                    "revisions": len(c.intents),
                    "phase": c.correction_barrier,
                    "exposure": c.speech_exposure,
                    "arm_order": ",".join(c.arm_order),
                    "fixture_hash": c.fixture_hash,
                }
            )
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
