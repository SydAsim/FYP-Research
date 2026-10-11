"""Fixed-destination HTTP adapter; responses are observations, never proof alone."""

import json
import os
from dataclasses import dataclass
from http.client import HTTPException, IncompleteRead, RemoteDisconnected
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID


@dataclass(frozen=True)
class Exchange:
    status: int | None
    raw: dict[str, Any]
    body: dict[str, Any] | None
    transport_error: bool


def _base() -> str:
    return os.environ.get("SIMULATOR_BASE_URL", "http://127.0.0.1:8010").rstrip("/")


def exchange(method: str, path: str, payload: dict[str, Any] | None = None) -> Exchange:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode() if payload else None
    request = Request(
        _base() + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urlopen(request, timeout=30) as response:
            raw_bytes = response.read()
            parsed: dict[str, Any] = json.loads(raw_bytes) if raw_bytes else {}
            return Exchange(
                response.status, {"status": response.status, "body": parsed}, parsed, False
            )
    except HTTPError as exc:
        raw_bytes = exc.read()
        try:
            parsed = json.loads(raw_bytes) if raw_bytes else {}
        except json.JSONDecodeError:
            parsed = {"body_hash_unavailable": True}
        return Exchange(exc.code, {"status": exc.code, "body": parsed}, parsed, False)
    except (
        URLError,
        IncompleteRead,
        RemoteDisconnected,
        TimeoutError,
        ConnectionError,
        HTTPException,
    ) as exc:
        return Exchange(None, {"transport_error": type(exc).__name__}, None, True)


def send_operation(payload: dict[str, Any]) -> Exchange:
    return exchange("POST", "/v1/operations", payload)


def operation_status(scenario_id: UUID, operation_id: UUID) -> Exchange:
    query = urlencode({"scenario_id": str(scenario_id)})
    return exchange("GET", f"/v1/operations/{operation_id}?{query}")


def resource_state(scenario_id: UUID, operation_id: UUID, resource_key: str) -> Exchange:
    query = urlencode({"scenario_id": str(scenario_id), "operation_id": str(operation_id)})
    return exchange("GET", f"/v1/resources/{quote(resource_key, safe='')}?{query}")


def scenario_config(scenario_id: UUID) -> Exchange:
    return exchange("GET", f"/internal/scenarios/{scenario_id}")
