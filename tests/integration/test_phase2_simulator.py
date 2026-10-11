"""Simulator truth, capability and visibility behavior on its own PostgreSQL database."""

from uuid import uuid4

import pytest
from psycopg.errors import RaiseException

from research.provider_simulator.models import ProviderOperation, ScenarioConfig, Visibility
from research.provider_simulator.store import (
    apply_operation,
    connection,
    create_scenario,
    operation_status,
    resource_state,
    truth_log,
)


def request(scenario_id: object, operation_id: object) -> ProviderOperation:
    return ProviderOperation.model_validate(
        {
            "scenario_id": str(scenario_id),
            "operation_id": str(operation_id),
            "idempotency_key": f"key:{operation_id}",
            "request_hash": "fixture-hash",
            "action": "CREATE",
            "resource_key": "test-resource",
            "requested_start": "2026-10-02T15:00:00+05:00",
            "requested_end": "2026-10-02T16:00:00+05:00",
            "timezone": "Asia/Karachi",
        }
    )


@pytest.mark.parametrize(
    "visibility,reads",
    [
        (Visibility.IMMEDIATE, 0),
        (Visibility.DELAYED, 2),
        (Visibility.STALE, 1),
    ],
)
def test_truth_is_append_only_and_visibility_is_configurable(
    visibility: Visibility, reads: int
) -> None:
    config = ScenarioConfig(visibility=visibility, visibility_reads=reads)
    scenario_id, operation_id = create_scenario(config), uuid4()
    payload = request(scenario_id, operation_id)
    committed = apply_operation(payload, config)
    replay = apply_operation(payload, config)
    assert replay["idempotent_replay"] is True
    assert len(truth_log(scenario_id)) == 1
    observations = [operation_status(scenario_id, operation_id, config) for _ in range(reads + 2)]
    if visibility is Visibility.IMMEDIATE:
        assert observations[0]["outcome"] == "PRESENT"
    else:
        assert observations[0]["outcome"] == "UNKNOWN"
        assert observations[-1]["outcome"] == "PRESENT"
    resource = resource_state(scenario_id, operation_id, "test-resource", config)
    assert resource["authoritative"] is (reads == 0)
    with pytest.raises(RaiseException, match="append-only"):
        with connection() as conn:
            conn.execute(
                "DELETE FROM provider_commits WHERE sequence=%s", (committed["commit_sequence"],)
            )


def test_absent_capabilities_and_permanently_unavailable_visibility() -> None:
    config = ScenarioConfig(
        status_lookup=False, resource_lookup=False, visibility=Visibility.UNAVAILABLE
    )
    scenario_id = create_scenario(config)
    with pytest.raises(NotImplementedError):
        operation_status(scenario_id, uuid4(), config)
    with pytest.raises(NotImplementedError):
        resource_state(scenario_id, uuid4(), "test-resource", config)

    unavailable = ScenarioConfig(visibility=Visibility.UNAVAILABLE)
    other_scenario = create_scenario(unavailable)
    operation_id = uuid4()
    apply_operation(request(other_scenario, operation_id), unavailable)
    with pytest.raises(ConnectionError):
        operation_status(other_scenario, operation_id, unavailable)
    with pytest.raises(ConnectionError):
        resource_state(other_scenario, operation_id, "test-resource", unavailable)
