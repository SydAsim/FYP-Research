"""Dev-mode LiveKit room token for the optional local media smoke test."""

import base64
import hashlib
import hmac
import json
import time
from uuid import uuid4


def _encoded(value: dict[str, object]) -> str:
    data = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def dev_room_token(room: str, identity: str | None = None) -> str:
    now = int(time.time())
    header = _encoded({"alg": "HS256", "typ": "JWT"})
    payload = _encoded(
        {
            "iss": "devkey",
            "sub": identity or f"phase4-agent-{uuid4()}",
            "nbf": now - 5,
            "exp": now + 300,
            "video": {"roomJoin": True, "room": room, "canPublish": True, "canSubscribe": True},
        }
    )
    signing_input = f"{header}.{payload}"
    signature = hmac.new(b"secret", signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')}"
