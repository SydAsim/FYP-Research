"""Pre-fix PostgreSQL reproduction. Separate from the 18 planned remedy trials."""

import json
from datetime import UTC, datetime
from urllib.error import HTTPError
from uuid import uuid4

from research.remedies.preserve import OUTPUT
from research.replay.phase2_decisive import API, SIMULATOR, _revision, call
from research.replay.phase4_p8 import _b3_audio, _claim_audio, _drain, _play


def main() -> None:
    target = OUTPUT / "debug/pre-fix-late-ack.json"
    if target.exists():
        raise ValueError("Reproduction evidence already exists; never overwrite it")
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm in ("B3", "P1", "P2"):
        for kind in ("PROGRESS", "COMPLETED"):
            scenario = call(SIMULATOR, "POST", "/internal/scenarios", {})
            item = call(
                API,
                "POST",
                "/internal/phase1/fixtures",
                {"command_id": str(uuid4()), "research_arm": arm},
            )
            workflow = item["workflow_id"]
            call(API, "POST", f"/v1/workflows/{workflow}/revisions", _revision(item, 1, 15))
            op = call(
                API,
                "POST",
                "/internal/phase2/operations",
                {
                    "command_id": str(uuid4()),
                    "workflow_id": workflow,
                    "scenario_id": scenario["scenario_id"],
                    "expected_intent_revision": 1,
                    "expected_resource_version": 0,
                    "idempotency_key": f"late-ack:{uuid4()}",
                },
            )
            _drain(workflow)
            scheduled = (
                _b3_audio(workflow, 1) if arm == "B3" else _claim_audio(op["operation_id"], 1)
            )["scheduled"]
            segment = call(API, "GET", f"/v1/audio-segments/{scheduled['segment_id']}")
            evidence: list[dict[str, object]] = []
            _play(item["call_id"], segment["id"], "STARTED")
            client_time = datetime.now(UTC).isoformat()
            call(API, "POST", f"/v1/workflows/{workflow}/revisions", _revision(item, 2, 16))
            words = len(segment["word_timeline_json"]) if kind == "COMPLETED" else 7
            ms = segment["duration_ms"] if kind == "COMPLETED" else 1260
            request = {
                "event_id": str(uuid4()),
                "segment_id": segment["id"],
                "event_type": kind,
                "client_time": client_time,
                "played_ms": ms,
                "last_frame": ms * 16,
                "last_word_index": words,
            }
            try:
                response = call(
                    API, "POST", f"/v1/calls/{item['call_id']}/playback-events", request
                )
                status = 202
            except HTTPError as exc:
                status = exc.code
                response = json.loads(exc.read())
            evidence.append({"request": request, "response": response, "status": status})
            row = {
                "arm": arm,
                "kind": kind,
                "workflow_id": workflow,
                "scenario_id": scenario["scenario_id"],
                "segment": segment,
                "playback": evidence,
                "history": call(API, "GET", f"/v1/workflows/{workflow}/history"),
                "truth": call(
                    SIMULATOR, "GET", f"/internal/scenarios/{scenario['scenario_id']}/truth"
                ),
            }
            rows.append(row)
            target.write_text(
                json.dumps(
                    {"classification": "pre-fix-debug-not-planned", "executions": rows}, indent=2
                )
                + "\n",
                encoding="utf-8",
            )
            print(arm, kind, status, response.get("repair_obligation_id", response.get("type")))


if __name__ == "__main__":
    main()
