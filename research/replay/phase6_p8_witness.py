"""Live P2 P8 witness and offline independent check; not a paired arm result."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from research.oracle.p8_witness import grade_p8_witness
from research.replay.phase4_p8 import run as run_phase4_p8
from research.run_store import MIGRATION_VERSION
from research.runner.paired import _container_digests, _source_identity
from research.scenario_dsl.catalog import MANDATORY_HIGH_RISK
from research.scenario_dsl.models import ScenarioCase, stable_hash

WITNESS_VERSION = "phase6-p8-live-p2-witness-v1"


def witness_case() -> ScenarioCase:
    zone = ZoneInfo("Asia/Karachi")
    data = MANDATORY_HIGH_RISK[4].model_dump(mode="json")
    data.update(
        {
            "fixture_version": WITNESS_VERSION,
            "scenario_key": "maintenance-p8-live-p2-witness",
            "initial_start": datetime(2026, 10, 1, 15, tzinfo=zone).isoformat(),
            "final_start": datetime(2026, 10, 1, 16, tzinfo=zone).isoformat(),
            "initial_transcript": "Please book maintenance at 3 PM.",
            "correction_transcript": "Actually, make that four PM.",
        }
    )
    return ScenarioCase.model_validate(data)


def verify_witness(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    body = {key: value for key, value in bundle.items() if key != "bundle_hash"}
    if stable_hash(body) != bundle["bundle_hash"]:
        raise ValueError("P8 witness bundle hash differs")
    manifest = bundle["manifest"]
    case = ScenarioCase.model_validate(manifest["scenario"])
    if case.fixture_hash != manifest["fixture_hash"]:
        raise ValueError("P8 witness fixture hash differs")
    if bundle["trace"]["prerecorded_audio_sha256"] != case.audio_hash:
        raise ValueError("P8 witness audio hash differs")
    if bundle["trace"]["correction"]["audio_hash"] != case.audio_hash:
        raise ValueError("P8 correction did not use the frozen audio")
    result = grade_p8_witness(bundle["trace"], case)
    if result != bundle["oracle_result"]:
        raise ValueError("P8 witness independent grade differs")
    return {
        "scenario_id": bundle["trace"]["scenario_id"],
        "bundle_hash": bundle["bundle_hash"],
        "played_span_repair_complete": result["played_span_repair_complete"],
        "correction_success": result["correction_success"],
    }


def run_witness(output_dir: Path = Path("artifacts") / "phase-6-replays") -> dict[str, Any]:
    case = witness_case()
    source_commit, tree_hash = _source_identity()
    manifest = {
        "witness_version": WITNESS_VERSION,
        "arm": "P2",
        "paired": False,
        "scenario": case.model_dump(mode="json"),
        "fixture_hash": case.fixture_hash,
        "source_commit": source_commit,
        "source_tree_hash": tree_hash,
        "container_digests": _container_digests(),
        "migration_version": MIGRATION_VERSION,
        "model_profile": "phase4-scripted-stt-and-intent",
    }
    trace = run_phase4_p8(research_arm="P2")
    result = grade_p8_witness(trace, case)
    if not result["played_span_repair_complete"]:
        raise AssertionError("The live P8 witness did not complete repair")
    bundle: dict[str, Any] = {"manifest": manifest, "trace": trace, "oracle_result": result}
    bundle["bundle_hash"] = stable_hash(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"p8-p2-witness-{trace['scenario_id']}.json"
    if path.exists():
        raise FileExistsError("A frozen P8 witness cannot be overwritten")
    path.write_text(json.dumps(bundle, indent=2, default=str) + "\n", encoding="utf-8")
    verified = verify_witness(path)
    return {"bundle_path": str(path.resolve()), **verified}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run or verify a live P2 P8 witness")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_witness(args.verify) if args.verify else run_witness(), indent=2))
