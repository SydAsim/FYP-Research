"""Remaining Phase 6 covering cells use real services and independent replay."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from research.replay.verify_clean_paired import verify_clean_bundle
from research.replay.verify_p8_paired import verify_p8_paired
from research.replay.verify_phase6 import verify_bundle
from research.replay.verify_playout_paired import verify_playout_paired
from research.runner.clean_paired import run_clean_paired
from research.runner.p8_paired import run_p8_paired
from research.runner.paired import ALL_ARMS, run_paired
from research.runner.playout_paired import run_playout_paired
from research.scenario_dsl.catalog import (
    CAPABILITY_COVERING,
    MULTI_COVERING,
    PARTIAL_COVERING,
    REDIS_COVERING,
    REVISION_COVERING,
    STALE_COVERING,
    VISIBILITY_COVERING,
    case_for,
)
from research.scenario_dsl.models import Barrier, FaultFamily, ScenarioCase, stable_hash


@pytest.mark.parametrize("case", [PARTIAL_COVERING[0], REDIS_COVERING[0], STALE_COVERING[0]])
def test_recovery_covering_cases_run_live_and_reject_tampering(
    case: ScenarioCase, tmp_path: Path
) -> None:
    outcome = run_paired(case, output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert not execution["oracle_result"]["unsupported_confirmation"]
        assert not execution["oracle_result"]["duplicate_effect"]
        assert execution["oracle_result"]["correction_success"] == (
            case.fault_family is not FaultFamily.PARTIAL_EFFECT
        )
    changed = deepcopy(bundle)
    execution = changed["executions"][0]
    if case.fault_family is FaultFamily.REDIS_LOSS:
        execution["redis_loss_evidence"]["after"]["intent_revisions"] = []
    elif case.fault_family is FaultFamily.PARTIAL_EFFECT:
        execution["simulator_truth"][0]["after_facts"]["status"] = "CONFIRMED"
    else:
        execution["provider_evidence"][0]["attempts"][1]["raw_response_json"]["status"]["body"][
            "stale"
        ] = False
    changed["bundle_hash"] = stable_hash(
        {key: value for key, value in changed.items() if key != "bundle_hash"}
    )
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="Redis loss|Partial effect|Stale evidence"):
        verify_bundle(path)


@pytest.mark.parametrize("case", [*REVISION_COVERING, *MULTI_COVERING])
def test_revision_and_multiple_resource_cases_use_independent_truth(
    case: ScenarioCase, tmp_path: Path
) -> None:
    outcome = run_paired(case, output_dir=tmp_path)
    path = Path(outcome["bundle_path"])
    assert verify_bundle(path)["verified_executions"] == 3
    bundle = json.loads(path.read_text(encoding="utf-8"))
    for execution in bundle["executions"]:
        assert execution["oracle_result"]["correction_success"]
        actions = [row["action"] for row in execution["simulator_truth"]]
        if case.revision_type == "RETRACTION":
            assert actions == ["CREATE", "CANCEL"]
            assert execution["playback_ack"] is None
        elif case.revision_type == "ADDITIVE_COMPATIBLE":
            assert actions == ["CREATE"]
        elif case.workflow_shape.startswith("TWO_"):
            assert actions == ["CREATE", "CREATE", "RESCHEDULE"]
            assert len({row["resource_key"] for row in execution["simulator_truth"]}) == 2


@pytest.mark.parametrize(
    "case",
    [
        *(
            case_for(stage)
            for stage in (Barrier.P0, Barrier.P1, Barrier.P2, Barrier.P4, Barrier.P5)
        ),
        CAPABILITY_COVERING[0],
        VISIBILITY_COVERING[0],
    ],
)
def test_baselines_share_non_p3_and_provider_covering_cells(
    case: ScenarioCase, tmp_path: Path
) -> None:
    result = run_paired(case, arms=ALL_ARMS, output_dir=tmp_path)
    assert verify_bundle(Path(result["bundle_path"]))["verified_executions"] == 6


@pytest.mark.parametrize("stage", [Barrier.P6, Barrier.P7, Barrier.P8, Barrier.P9])
def test_all_arms_share_audio_boundaries_and_reject_forged_baseline_audio(
    stage: Barrier, tmp_path: Path
) -> None:
    result = (
        run_p8_paired(tmp_path, arms=ALL_ARMS)
        if stage is Barrier.P8
        else run_playout_paired(stage, tmp_path, arms=ALL_ARMS)
    )
    verifier = verify_p8_paired if stage is Barrier.P8 else verify_playout_paired
    path = Path(result["bundle_path"])
    assert verifier(path)["verified_executions"] == 6
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bundle["executions"][0]["trace"]["corrected_claim"]["scheduled"]["audio_hash"] = "0" * 64
    bundle["bundle_hash"] = stable_hash({k: v for k, v in bundle.items() if k != "bundle_hash"})
    path.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="generated audio"):
        verifier(path)


def test_all_six_arms_run_the_clean_control(tmp_path: Path) -> None:
    result = run_clean_paired(output_dir=tmp_path, arms=ALL_ARMS)
    assert verify_clean_bundle(Path(result["bundle_path"]))["verified_executions"] == 6
