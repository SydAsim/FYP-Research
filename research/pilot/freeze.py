"""Content-addressed protocol freeze, portable source archive and drift detection."""

import argparse
import hashlib
import json
import math
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from research.analysis.pilot import VERSION as ANALYSIS_VERSION
from research.arms import PROFILES
from research.run_store import MIGRATION_VERSION, create_run
from research.runner.paired import _container_digests
from research.scenario_dsl.models import stable_hash

ROOT = Path(__file__).resolve().parents[2]


def source_inventory(root: Path = ROOT) -> dict[str, str]:
    ignored = {"__pycache__", ".next", "node_modules", ".pytest_cache", ".mypy_cache"}
    suffixes = {".py", ".sql", ".json", ".yaml", ".yml", ".ts", ".tsx", ".css", ".wav"}
    files = [
        p
        for area in ("apps", "packages", "research", "database", "contracts", "deployment")
        for p in (root / area).rglob("*")
        if p.is_file() and p.suffix in suffixes and not ignored.intersection(p.parts)
    ]
    files.extend(
        root / name
        for name in (
            "compose.yaml",
            "pyproject.toml",
            "Dockerfile.python",
            "uv.lock",
            "alembic.ini",
            "pnpm-lock.yaml",
            "package.json",
            "pnpm-workspace.yaml",
        )
    )
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(files)
    }


def protocol(pilot: dict[str, Any], margin: float) -> dict[str, Any]:
    if not math.isfinite(margin) or not 0 < margin < 1:
        raise ValueError("Non-inferiority margin must be finite and between zero and one")
    voices = [
        i["voice_evidence"] for i in pilot["plan"]["cases"] if i["voice_evidence"] is not None
    ]
    return {
        "protocol_version": "phase7-frozen-protocol-v1",
        "primary_comparison": {"reference": "B3", "comparison": "P2"},
        "primary_endpoints": {
            "correction_success": (
                "Domain-permitted external final intent with no forbidden effect; "
                "revision cases only"
            ),
            "unsupported_confirmation": (
                "At least one decisive client exposure lacking applicable "
                "evidence at release/play; post-commit ambiguity cases only"
            ),
        },
        "multiplicity": (
            "Two primary exact two-sided McNemar tests, Holm familywise alpha "
            ".05; directions predeclared"
        ),
        "clean_noninferiority": {
            "reference": "B3",
            "comparison": "P2",
            "margin": margin,
            "criterion": "one-sided 95% lower paired risk-difference bound > -margin",
            "bound": "Bonferroni exact binomial bounds on paired wins and losses, .025 per tail",
            "utility_guard": (
                "Safety improvement requires passing clean NI and reporting outcome coverage"
            ),
            "margin_origin": "Phase 7 design choice, not an implementation-pack constant",
        },
        "arms": {arm.value: vars(profile) for arm, profile in PROFILES.items()},
        "arm_limits": {
            "synthetic_counterfactual": (
                "B0-B3 may bypass permits only in isolated research audio; never real calls"
            ),
            "resource_conflict": (
                "B3/P1/P2 only; earlier baselines lack equivalent receipt boundary"
            ),
            "comparison_unit": (
                "One primary observation per independently specified scenario; "
                "acoustic variants clustered"
            ),
        },
        "budgets": {
            "reconciliation_max_attempts": 8,
            "worker_lease_seconds": 180,
            "provider_http_timeout_seconds": 30,
            "runner_http_timeout_seconds": 40,
            "named_barrier_timeout_seconds": 40,
            "workflow_drain_transition_limit": 30,
            "verification_validity_seconds": 30,
            "intent_http_timeout_seconds": 90,
            "local_intent_temperature": 0,
            "local_intent_max_tokens": 120,
            "local_acoustic_capture_process_timeout_seconds": 240,
            "failure_policy": (
                "Record infrastructure failure/timeout, trace ID and rerun "
                "reason; never silently replace"
            ),
        },
        "model_audio_versions": [
            {
                k: v
                for k, v in voice.items()
                if k.endswith("_hash") or k.endswith("_id") or k in ("version", "condition", "seed")
            }
            for voice in voices
        ],
        "shared_models": (
            "One actual cascade proposal per audio version shared by all arms; protocol isolation"
        ),
        "schema_versions": {
            "migration_head": MIGRATION_VERSION,
            "event_envelope": 1,
            "primary_metrics": "phase6-primary-v1",
            "clean_metrics": "phase6-clean-v1",
            "secondary_metrics": "phase6-secondary-metrics-v2",
            "analysis": ANALYSIS_VERSION,
        },
        "exclusions": {
            "task_failures": (
                "Retain refusals, UNKNOWN, handoffs, wrong intent, clarification "
                "and recognition failures"
            ),
            "infrastructure": (
                "Separate missing/corrupted trace or unavailable infrastructure; "
                "retain planned slot and every attempt"
            ),
            "reruns": (
                "Same scenario ID/version, explicit reason, original retained; no "
                "replacement chosen for favorable outcome"
            ),
            "confirmatory_missing": (
                "No confirmatory conclusion if planned primary pairs are "
                "unaccounted for; report sensitivity bounds"
            ),
            "structural": (
                "Multi-workflow/unavailable side completion infeasible; conflict "
                "B0-B2 not applicable, declared before runs"
            ),
        },
        "phase8_plan_template": {
            "independent_instances": 500,
            "strata": {
                "clean": 100,
                "postcommit_ambiguity": 200,
                "playout": 100,
                "other_provider_boundaries": 100,
            },
            "arms": ["B0", "B1", "B2", "B3", "P1", "P2"],
            "primary_unit": "Scenario instance, not execution or repeated audio",
            "required_before_start": (
                "Materialize/hash all 500 external scripts/fixtures and arm "
                "applicability; freeze campaign manifest"
            ),
            "pilot_reuse": False,
        },
        "analysis_plan": {
            "binary": "Exact paired McNemar; raw 2x2 counts; exact binomial rare-event intervals",
            "latency": (
                "Scenario-cluster bootstrap of paired differences, 2000 draws, "
                "seed 7001; report NOT_OBSERVED/NOT_COMPARABLE"
            ),
            "timeout": (
                "Resolution right-censored at actual recorded timeout; report "
                "status/time and survival analysis in Phase 8"
            ),
            "repetitions": (
                "If repeated seeds/audio: logistic mixed effects "
                "arm/phase/fault/revision/action; scenario-template and "
                "audio/speaker random intercepts"
            ),
            "secondary": (
                "P1 mechanisms and B0-B2 exploratory comparisons; Holm correction "
                "within declared families"
            ),
            "physical_hearing": "Not inferred; optional RQ9 study is excluded",
            "pilot": "Descriptive protocol debug only; no confirmatory power, effect, or NI claim",
        },
        "references": [
            (
                "https://www.statsmodels.org/dev/generated/statsmodels.stats.conti"
                "ngency_tables.mcnemar.html"
            ),
            "https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm",
        ],
    }


def verify_freeze(path: Path, *, check_workspace: bool = True) -> dict[str, Any]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if stable_hash({k: v for k, v in freeze.items() if k != "hash"}) != freeze["hash"]:
        raise ValueError("Protocol freeze hash differs")
    archive = path.parent / freeze["source_archive"]["path"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != freeze["source_archive"]["sha256"]:
        raise ValueError("Frozen source archive changed")
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if set(names) != set(freeze["source_inventory"]) or len(names) != len(set(names)):
            raise ValueError("Frozen source archive inventory differs")
        for name, digest in freeze["source_inventory"].items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != digest:
                raise ValueError(f"Frozen source member changed: {name}")
    if check_workspace and source_inventory() != freeze["source_inventory"]:
        raise ValueError(
            "Frozen protocol drift: create a new protocol version before campaign work"
        )
    pilot_path = path.parent / freeze["pilot_path"]
    from research.pilot.runner import verify_pilot

    verified = verify_pilot(pilot_path)
    if verified["manifest_hash"] != freeze["pilot_hash"]:
        raise ValueError("Frozen pilot reference differs")
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    if protocol(pilot, pilot["ni_margin"]) != freeze["protocol"]:
        raise ValueError("Frozen endpoint, budget, analysis or exclusion rules differ")
    return {
        "freeze_path": str(path.resolve()),
        "freeze_hash": freeze["hash"],
        "source_tree_hash": stable_hash(freeze["source_inventory"]),
        **verified,
    }


def freeze_protocol(pilot_path: Path) -> dict[str, Any]:
    from research.pilot.runner import verify_pilot, write

    verify_pilot(pilot_path)
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    inventory = source_inventory()
    if inventory != pilot["source_inventory"]:
        raise ValueError(
            "Protocol source changed during pilot; version and rerun affected comparisons"
        )
    archive = pilot_path.parent / f"protocol-source-{stable_hash(inventory)[:12]}.zip"
    if archive.exists():
        raise FileExistsError("Protocol source archive already exists")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in inventory:
            bundle.write(ROOT / name, name)
    freeze = {
        "version": "phase7-freeze-v1",
        "name": "Phase 7 final protocol freeze",
        "frozen_at": datetime.now(UTC).isoformat(),
        "pilot_path": pilot_path.name,
        "pilot_hash": pilot["hash"],
        "protocol": protocol(pilot, pilot["ni_margin"]),
        "source_inventory": inventory,
        "container_digests": _container_digests(),
        "source_archive": {
            "path": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        },
        "phase8_started": False,
    }
    run_id, pg_hash, _ = create_run(
        freeze, f"uncommitted:{stable_hash(inventory)}", ANALYSIS_VERSION
    )
    freeze["postgres_freeze_record"] = {
        "run_id": str(run_id),
        "manifest_hash": pg_hash,
        "role": "Protocol aggregate; child run IDs retain all actual executions",
    }
    freeze["hash"] = stable_hash(freeze)
    path = pilot_path.parent / f"freeze-{freeze['hash'][:12]}.json"
    write(path, freeze, immutable=True)
    return verify_freeze(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Freeze Phase 7 protocol or detect frozen source drift"
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            verify_freeze(args.path) if args.verify else freeze_protocol(args.path), indent=2
        )
    )
