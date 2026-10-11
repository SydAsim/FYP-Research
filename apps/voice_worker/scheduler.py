"""Voice worker only speaks text supplied by the controller's claim policy."""

import base64
import hashlib
import json
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from apps.voice_worker.cascade import TTSAdapter


class ControllerPort(Protocol):
    def get(self, path: str) -> dict[str, Any]: ...
    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]: ...


class HttpControllerPort:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            self.base_url + path,
            data=encoded,
            method=method,
            headers={"content-type": "application/json"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.load(response)
                if not isinstance(payload, dict):
                    raise ValueError("Controller returned a non-object response")
                return dict(payload)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ValueError(f"Controller rejected {method} {path}: {exc.code} {detail}") from exc

    def get(self, path: str) -> dict[str, Any]:
        return self._request("GET", path)

    def get_bytes(self, path: str) -> bytes:
        with urlopen(Request(self.base_url + path, method="GET"), timeout=15) as response:
            return bytes(response.read())

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, body)


class VoiceScheduler:
    def __init__(self, controller: ControllerPort, tts: TTSAdapter) -> None:
        self.controller = controller
        self.tts = tts

    def schedule(
        self, permit_id: UUID, intent_revision: int, repair_obligation_id: UUID | None = None
    ) -> dict[str, Any]:
        prepared = self.stage_claim(permit_id, intent_revision, repair_obligation_id)
        segment_id = prepared["segment_id"]
        self.controller.post(
            f"/internal/phase4/audio-segments/{segment_id}/queue",
            {
                "command_id": str(uuid4()),
                "expected_intent_revision": intent_revision,
            },
        )
        released = self.controller.post(
            f"/internal/phase4/audio-segments/{segment_id}/release",
            {
                "command_id": str(uuid4()),
                "expected_intent_revision": intent_revision,
            },
        )
        return {
            **released,
            "text_hash": prepared["text_hash"],
            "audio_hash": prepared["audio_hash"],
        }

    def stage_claim(
        self, permit_id: UUID, intent_revision: int, repair_obligation_id: UUID | None = None
    ) -> dict[str, Any]:
        suffix = f"?repair_obligation_id={repair_obligation_id}" if repair_obligation_id else ""
        synthesis = self.controller.get(
            f"/internal/phase4/permits/{permit_id}/synthesis-input{suffix}"
        )
        text = synthesis["text"]
        if synthesis["intent_revision"] != intent_revision:
            raise ValueError("Synthesis text belongs to another revision")
        audio = self.tts.synthesize(text)
        prepared = self.controller.post(
            "/internal/phase4/audio-segments",
            {
                "command_id": str(uuid4()),
                "permit_id": str(permit_id),
                "expected_intent_revision": intent_revision,
                "audio_base64": base64.b64encode(audio).decode("ascii"),
                "audio_hash": hashlib.sha256(audio).hexdigest(),
                "text_hash": synthesis["text_hash"],
                "tts_model_id": self.tts.model_id,
                "tts_config_hash": self.tts.config_hash,
                "repair_obligation_id": str(repair_obligation_id) if repair_obligation_id else None,
            },
        )
        return {
            **prepared,
            "text_hash": synthesis["text_hash"],
            "audio_hash": prepared["audio_hash"],
        }

    def schedule_b3(self, workflow_id: UUID, intent_revision: int) -> dict[str, Any]:
        return self._b3_audio(workflow_id, intent_revision, stage=False)

    def stage_b3(self, workflow_id: UUID, intent_revision: int) -> dict[str, Any]:
        return self._b3_audio(workflow_id, intent_revision, stage=True)

    def _b3_audio(self, workflow_id: UUID, intent_revision: int, *, stage: bool) -> dict[str, Any]:
        synthesis = self.controller.get(
            f"/internal/phase6/b3/workflows/{workflow_id}/synthesis-input"
            f"?revision={intent_revision}"
        )
        if synthesis["intent_revision"] != intent_revision:
            raise ValueError("B3 synthesis belongs to another revision")
        audio = self.tts.synthesize(synthesis["text"])
        return self.controller.post(
            "/internal/phase6/b3/audio-segments/stage"
            if stage
            else "/internal/phase6/b3/audio-segments",
            {
                "command_id": str(uuid4()),
                "workflow_id": str(workflow_id),
                "expected_intent_revision": intent_revision,
                "audio_base64": base64.b64encode(audio).decode("ascii"),
                "audio_hash": hashlib.sha256(audio).hexdigest(),
                "text_hash": synthesis["text_hash"],
                "tts_model_id": self.tts.model_id,
                "tts_config_hash": self.tts.config_hash,
            },
        )
