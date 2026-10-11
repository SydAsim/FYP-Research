"""API controller with durable commands, evidence, and text policy boundaries."""

import os
from collections.abc import Awaitable, Callable
from uuid import uuid4

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api_controller.phase1_routes import router as phase1_router
from apps.api_controller.phase1_service import DomainProblem, translate_integrity_error
from apps.api_controller.phase2_routes import router as phase2_router
from apps.api_controller.phase3_routes import router as phase3_router
from apps.api_controller.phase4_routes import router as phase4_router
from apps.api_controller.phase5_routes import router as phase5_router
from apps.api_controller.phase6_routes import router as phase6_router
from packages.observability.logging import configure_logging

configure_logging("api-controller")
app = FastAPI(title="Commit-Aware Voice Agent API", docs_url=None, redoc_url=None)
app.include_router(phase1_router)
app.include_router(phase2_router)
app.include_router(phase3_router)
app.include_router(phase4_router)
app.include_router(phase5_router)
app.include_router(phase6_router)


@app.middleware("http")
async def trace_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # A server-generated ID is used until the trusted tracing boundary is added.
    request.state.trace_id = str(uuid4())
    response = await call_next(request)
    response.headers["x-trace-id"] = request.state.trace_id
    return response


def problem_response(request: Request, problem: DomainProblem) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        media_type="application/problem+json",
        content={
            "type": f"https://example.invalid/problems/{problem.slug}",
            "title": problem.title,
            "status": problem.status,
            "detail": problem.detail,
            "instance": str(request.url.path),
            "trace_id": request.state.trace_id,
            "retryable": False,
        },
    )


@app.exception_handler(DomainProblem)
async def domain_problem(request: Request, exc: DomainProblem) -> JSONResponse:
    return problem_response(request, exc)


@app.exception_handler(psycopg.IntegrityError)
async def database_problem(request: Request, exc: psycopg.IntegrityError) -> JSONResponse:
    return problem_response(request, translate_integrity_error(exc))


@app.exception_handler(RequestValidationError)
async def validation_problem(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(
        request,
        DomainProblem(
            "invalid-request",
            "Invalid request",
            "Request body or path did not match the command schema",
            422,
        ),
    )


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "api-controller"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    finally:
        await engine.dispose()
    return {"status": "ok", "service": "api-controller", "database": "reachable"}
