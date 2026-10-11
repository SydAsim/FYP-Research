"""Host orchestration for free local speech fixtures and paired protocol execution."""

import argparse
import base64
import json
import subprocess
from pathlib import Path
from typing import Any

from research.replay.verify_clean_paired import verify_clean_bundle
from research.runner.acoustic_source import CONDITIONS, SOURCE, AcousticEvidence
from research.runner.clean_paired import run_clean_paired
from research.runner.paired import ALL_ARMS
from research.scenario_dsl.catalog import BASE
from research.scenario_dsl.models import (
    CleanScenarioCase,
    ProviderCapability,
    ProviderVisibility,
    stable_hash,
)

ROOT = Path(__file__).resolve().parents[2]


def capture_local(conditions: tuple[str, ...] = CONDITIONS) -> list[dict[str, Any]]:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "voice-worker",
            "/app/.venv/bin/python",
            "-m",
            "research.runner.acoustic_source",
        ],
        cwd=ROOT,
        input=json.dumps({"conditions": conditions, "seed": 60}),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
        timeout=240,
    )
    evidence: list[dict[str, Any]] = json.loads(result.stdout)
    return [AcousticEvidence.model_validate(row).model_dump(mode="json") for row in evidence]


def acoustic_case(evidence: dict[str, Any]) -> CleanScenarioCase:
    return CleanScenarioCase(
        fixture_version="phase6-local-acoustic-v1",
        scenario_key=f"local-acoustic-{evidence['condition'].lower()}-{evidence['seed']}",
        seed=evidence["seed"],
        final_start=BASE,
        timezone="Asia/Karachi",
        transcript=SOURCE,
        audio_hash=evidence["input_audio_hash"],
        acoustic_condition=evidence["condition"],
        provider_capability=ProviderCapability.ATOMIC_RESCHEDULE,
        visibility=ProviderVisibility.IMMEDIATE,
    )


def run_acoustic(output_dir: Path = ROOT / "artifacts" / "phase-6-replays") -> dict[str, Any]:
    evidence = capture_local()
    outcomes = []
    fixture_dir = ROOT / "research" / "fixtures" / "audio" / "phase6-local-v1"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    for row in evidence:
        fixture = fixture_dir / f"{row['condition'].lower()}-{row['input_audio_hash'][:12]}.wav"
        if not fixture.exists():
            fixture.write_bytes(base64.b64decode(row["input_audio_base64"], validate=True))
        result = run_clean_paired(
            acoustic_case(row), output_dir=output_dir, voice_evidence=row, arms=ALL_ARMS
        )
        verified = verify_clean_bundle(Path(result["bundle_path"]))
        outcomes.append(
            {
                "condition": row["condition"],
                "status": row["status"],
                "transcript": row["transcript"],
                "replay": result,
                "verified": verified,
            }
        )
    body: dict[str, Any] = {
        "version": "phase6-local-acoustic-v1",
        "independent_scenarios": len(evidence),
        "model_output_sharing": "one measured cascade proposal per fixture shared by paired arms",
        "outcomes": outcomes,
    }
    body["hash"] = stable_hash(body)
    path = output_dir / f"acoustic-summary-{body['hash'][:12]}.json"
    if not path.exists():
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return {"summary_path": str(path), "independent_scenarios": len(evidence), "outcomes": outcomes}


if __name__ == "__main__":
    argparse.ArgumentParser(description="Run Phase 6 local acoustic covering cases").parse_args()
    print(json.dumps(run_acoustic(), indent=2))
