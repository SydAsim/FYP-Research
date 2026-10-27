"""Bounded, read-only S3 version inventory; never returns an incomplete total."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from pydantic import BaseModel, ConfigDict, Field

ATTEMPTS = 3
BACKOFF_SECONDS = (1.0, 2.0)
TOTAL_SECONDS = 120.0
RETRYABLE_CODES = frozenset(
    {"SlowDown", "InternalError", "ServiceUnavailable", "RequestTimeout", "Throttling"}
)


class InventoryUnavailable(RuntimeError):
    pass


class Version(BaseModel):
    model_config = ConfigDict(extra="ignore")
    Key: str
    VersionId: str = Field(min_length=1)
    Size: int = Field(ge=0, strict=True)


class Page(BaseModel):
    model_config = ConfigDict(extra="ignore")
    IsTruncated: bool = Field(strict=True)
    Versions: list[Version] = []
    NextKeyMarker: str | None = None
    NextVersionIdMarker: str | None = None


class InventoryClient(Protocol):
    def list_object_versions(self, **kwargs: Any) -> dict[str, Any]: ...


def retryable(error: Exception) -> bool:
    if isinstance(
        error,
        (ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError),
    ):
        return True
    return (
        isinstance(error, ClientError)
        and error.response.get("Error", {}).get("Code") in RETRYABLE_CODES
    )


def read_inventory(
    client: InventoryClient,
    bucket: str,
    prefix: str,
    *,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    seconds: float = TOTAL_SECONDS,
) -> int:
    deadline = clock() + seconds
    for attempt in range(1, ATTEMPTS + 1):
        # A failed later page invalidates the entire attempt. Never keep a partial sum.
        total = 0
        markers: dict[str, Any] = {}
        seen_markers: set[tuple[str, str | None]] = set()
        seen_versions: set[tuple[str, str]] = set()
        pages = 0
        try:
            while True:
                if clock() >= deadline:
                    raise InventoryUnavailable("S3_INVENTORY_TOTAL_TIME_LIMIT")
                raw = client.list_object_versions(Bucket=bucket, Prefix=prefix, **markers)
                page = Page.model_validate(raw)
                pages += 1
                if clock() >= deadline:
                    raise InventoryUnavailable("S3_INVENTORY_TOTAL_TIME_LIMIT")
                for item in page.Versions:
                    identity = (item.Key, item.VersionId)
                    if not item.Key.startswith(prefix) or identity in seen_versions:
                        raise InventoryUnavailable("S3_INVENTORY_SCOPE_OR_DUPLICATE_VERSION")
                    seen_versions.add(identity)
                    total += item.Size
                if not page.IsTruncated:
                    return total
                # A version marker may be absent when the boundary is a delete marker.
                if not page.NextKeyMarker:
                    raise InventoryUnavailable("S3_INVENTORY_INCOMPLETE_PAGINATION")
                marker = (page.NextKeyMarker, page.NextVersionIdMarker)
                if marker in seen_markers:
                    raise InventoryUnavailable("S3_INVENTORY_REPEATED_PAGINATION")
                seen_markers.add(marker)
                markers = {"KeyMarker": page.NextKeyMarker}
                if page.NextVersionIdMarker:
                    markers["VersionIdMarker"] = page.NextVersionIdMarker
        except Exception as error:
            print(
                json.dumps(
                    {
                        "event": "S3_INVENTORY_ATTEMPT_FAILED",
                        "prefix": prefix,
                        "attempt": attempt,
                        "pages": pages,
                        "type": type(error).__name__,
                        "detail": str(error),
                        "retryable": retryable(error),
                    }
                ),
                file=sys.stderr,
                flush=True,
            )
            if not retryable(error):
                raise
            if attempt == ATTEMPTS:
                raise InventoryUnavailable("S3_INVENTORY_RETRY_EXHAUSTED") from error
            delay = BACKOFF_SECONDS[attempt - 1]
            if clock() + delay >= deadline:
                raise InventoryUnavailable("S3_INVENTORY_TOTAL_TIME_LIMIT") from error
            sleep(delay)
    raise AssertionError("unreachable")


def bounded_inventory(bucket: str, prefix: str, *, seconds: float = TOTAL_SECONDS) -> int:
    # Isolated read process makes the whole listing (including DNS/credentials)
    # killable. SDK socket timeouts alone do not bound a complete pagination.
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                "--bucket",
                bucket,
                "--prefix",
                prefix,
                "--seconds",
                str(seconds),
            ],
            capture_output=True,
            text=True,
            timeout=seconds,
        )
    except subprocess.TimeoutExpired as error:
        if error.stderr:
            print(
                error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr,
                file=sys.stderr,
                flush=True,
            )
        raise InventoryUnavailable("S3_INVENTORY_TOTAL_TIME_LIMIT") from error
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="", flush=True)
    if result.returncode:
        raise InventoryUnavailable("S3_INVENTORY_UNAVAILABLE: " + result.stderr[-4000:])
    value = json.loads(result.stdout)
    if (
        value.get("bucket") != bucket
        or value.get("prefix") != prefix
        or value.get("complete") is not True
        or type(value.get("bytes")) is not int
        or value["bytes"] < 0
    ):
        raise InventoryUnavailable("S3_INVENTORY_INVALID_COMPLETE_RESULT")
    return int(value["bytes"])


def main() -> None:
    import boto3
    from botocore.config import Config

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--seconds", type=float, default=TOTAL_SECONDS)
    args = parser.parse_args()
    # This client can only be used by this inventory program. Existing shared
    # PUT/HEAD/find clients and all appointment adapters are unchanged.
    client = boto3.Session(region_name="ap-southeast-2").client(
        "s3",
        config=Config(
            connect_timeout=5,
            read_timeout=10,
            retries={"total_max_attempts": 1, "mode": "standard"},
        ),
    )
    try:
        total = read_inventory(client, args.bucket, args.prefix, seconds=args.seconds)
        print(
            json.dumps(
                {"bucket": args.bucket, "prefix": args.prefix, "bytes": total, "complete": True}
            )
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
