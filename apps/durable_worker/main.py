"""Durable worker health and deterministic Phase 2 lease stepping."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from apps.durable_worker.phase2 import WorkerCrash, step
from apps.durable_worker.repair import run_once
from packages.observability.logging import configure_logging

configure_logging("durable-worker")


@asynccontextmanager
async def lifespan(application: FastAPI) -> Any:
    async def consume_repairs() -> None:
        while True:
            scope = (
                os.getenv("REPAIR_WORKFLOW_SCOPE")
                if os.getenv("EXPERIMENT_MODE") == "true"
                else None
            )
            await asyncio.to_thread(
                run_once, f"repair-daemon:{os.getpid()}", UUID(scope) if scope else None
            )
            await asyncio.sleep(1)

    task = (
        asyncio.create_task(consume_repairs())
        if os.getenv("REPAIR_DELIVERY_ENABLED") == "true"
        else None
    )
    application.state.repair_consumer = task
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Durable Worker Health", lifespan=lifespan, docs_url=None, redoc_url=None)


class StepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    owner: str = "phase2-worker"
    crash_at: str | None = None
    operation_id: UUID | None = None


@app.post("/internal/phase2/step")
def phase2_step(body: StepRequest) -> dict[str, object]:
    if os.environ.get("EXPERIMENT_MODE") != "true":
        raise HTTPException(status_code=404, detail="Experiment endpoint disabled")
    try:
        return step(body.owner, body.crash_at, body.operation_id)
    except WorkerCrash as exc:
        raise HTTPException(status_code=503, detail={"crashed_after": exc.boundary}) from exc


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "durable-worker"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    consumer = getattr(app.state, "repair_consumer", None)
    if consumer is not None and consumer.done():
        raise HTTPException(status_code=503, detail="Repair consumer stopped; inspect worker logs")
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    finally:
        await engine.dispose()
    return {"status": "ok", "service": "durable-worker", "database": "reachable"}
