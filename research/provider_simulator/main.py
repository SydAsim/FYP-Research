"""Isolated deterministic provider with durable truth and named barriers."""

import hmac
import os
from collections.abc import Awaitable, Callable, MutableMapping
from contextlib import asynccontextmanager
from threading import Condition
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, Response

from packages.observability.logging import configure_logging
from research.provider_simulator.models import (
    BarrierName,
    FaultKind,
    ProviderOperation,
    ScenarioConfig,
)
from research.provider_simulator.store import (
    SimulatorConflict,
    apply_operation,
    barrier_state,
    bootstrap,
    create_scenario,
    inject_concurrent_change,
    next_request_index,
    operation_status,
    reach_barrier,
    release_barrier,
    resource_state,
    scenario_config,
    truth_log,
)

configure_logging("provider-simulator")


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    bootstrap()
    yield


app = FastAPI(
    title="Deterministic Provider Simulator", lifespan=lifespan, docs_url=None, redoc_url=None
)
barrier_condition = Condition()


class DroppedResponse(Response):
    """Start an incomplete HTTP body so clients observe a transport disconnect."""

    async def __call__(
        self,
        scope: MutableMapping[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        await send(
            {"type": "http.response.start", "status": 200, "headers": [(b"content-length", b"1")]}
        )


def _reach(
    scenario_id: UUID,
    stage: BarrierName,
    request_index: int,
    fault: FaultKind | None = None,
) -> None:
    name = f"{stage.value}:{request_index}"
    with barrier_condition:
        held = reach_barrier(scenario_id, name)
        barrier_condition.notify_all()
        if fault is FaultKind.DELAY and not held:
            raise RuntimeError(f"DELAY fault at {name} requires a held barrier")
        if held:
            released = barrier_condition.wait_for(
                lambda: (barrier_state(scenario_id, name) or {}).get("state") == "RELEASED",
                timeout=120,
            )
            if not released:
                raise TimeoutError(f"Barrier {name} was not released")


def _fault(config: ScenarioConfig, stage: BarrierName, request_index: int) -> FaultKind | None:
    for fault in config.faults:
        if fault.stage is stage and fault.request_index == request_index:
            return fault.kind
    return None


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok", "service": "provider-simulator"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    # The status query also proves the isolated truth database is reachable.
    from research.provider_simulator.store import connection

    with connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "service": "provider-simulator", "truth_database": "reachable"}


@app.post("/internal/scenarios", status_code=201)
def scenario(config: ScenarioConfig) -> dict[str, str]:
    return {"scenario_id": str(create_scenario(config))}


@app.get("/internal/scenarios/{scenario_id}/truth")
def truth(scenario_id: UUID, x_oracle_token: str | None = Header(default=None)) -> dict[str, Any]:
    token = os.environ.get("ORACLE_READ_TOKEN")
    if token and not hmac.compare_digest(token, x_oracle_token or ""):
        raise HTTPException(status_code=403, detail="Oracle-only truth boundary")
    try:
        scenario_config(scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario") from exc
    return {"scenario_id": str(scenario_id), "commits": truth_log(scenario_id)}


@app.get("/internal/scenarios/{scenario_id}")
def scenario_details(scenario_id: UUID) -> dict[str, Any]:
    try:
        config = scenario_config(scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario") from exc
    return {"scenario_id": str(scenario_id), "config": config.model_dump(mode="json")}


@app.get("/internal/scenarios/{scenario_id}/barriers/{barrier_name}")
def barrier(scenario_id: UUID, barrier_name: str, wait: bool = False) -> dict[str, Any]:
    with barrier_condition:
        if wait:
            barrier_condition.wait_for(
                lambda: (
                    (barrier_state(scenario_id, barrier_name) or {}).get("reached_at") is not None
                ),
                timeout=120,
            )
        row = barrier_state(scenario_id, barrier_name)
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown barrier")
    return {"barrier_name": barrier_name, **row}


@app.post("/internal/scenarios/{scenario_id}/barriers/{barrier_name}/release")
def release(scenario_id: UUID, barrier_name: str) -> dict[str, str]:
    with barrier_condition:
        release_barrier(scenario_id, barrier_name)
        barrier_condition.notify_all()
    return {"barrier_name": barrier_name, "state": "RELEASED"}


@app.post("/v1/operations")
def mutate(request: ProviderOperation, background: BackgroundTasks) -> Response:
    try:
        config = scenario_config(request.scenario_id)
        index = next_request_index(request.scenario_id)
        before_fault = _fault(config, BarrierName.BEFORE_COMMIT, index)
        _reach(request.scenario_id, BarrierName.BEFORE_COMMIT, index, before_fault)
        if before_fault is FaultKind.RETURN_5XX:
            return JSONResponse({"error": "injected provider 5xx"}, status_code=503)
        if before_fault is FaultKind.CONFLICTING_CHANGE:
            inject_concurrent_change(request)
        result = apply_operation(request, config, partial=before_fault is FaultKind.PARTIAL_EFFECT)
        if before_fault is FaultKind.DUPLICATE:
            # Simulate duplicate delivery through the provider's configured idempotency behavior.
            result = apply_operation(request, config)
        after_fault = _fault(config, BarrierName.AFTER_COMMIT_BEFORE_RESPONSE, index)
        _reach(request.scenario_id, BarrierName.AFTER_COMMIT_BEFORE_RESPONSE, index, after_fault)
        if after_fault is FaultKind.DROP_RESPONSE or after_fault is FaultKind.CRASH:
            return DroppedResponse()
        if after_fault is FaultKind.RETURN_5XX:
            return JSONResponse({"error": "injected provider 5xx after commit"}, status_code=503)
        background.add_task(_reach, request.scenario_id, BarrierName.AFTER_RESPONSE, index)
        return JSONResponse(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario") from exc
    except SimulatorConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/v1/operations/{operation_id}")
def status(scenario_id: UUID, operation_id: UUID) -> dict[str, Any]:
    try:
        return operation_status(scenario_id, operation_id, scenario_config(scenario_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario") from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/resources/{resource_key:path}")
def resource(scenario_id: UUID, operation_id: UUID, resource_key: str) -> dict[str, Any]:
    try:
        return resource_state(scenario_id, operation_id, resource_key, scenario_config(scenario_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario") from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
