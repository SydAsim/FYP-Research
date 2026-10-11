"""Actual PG/HTTP exploratory executions with append-only attempt accounting."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from research.oracle.readiness_v2 import RevisionTarget, grade_observable, repair_telemetry
from research.remedies.plan import FIXTURES, freeze_plan
from research.remedies.preserve import OUTPUT, ROOT
from research.remedies.provenance import freeze_source
from research.remedies.runtime import (
    API,
    DATABASE,
    SIM_DATABASE,
    SIMULATOR,
    VOICE,
    WORKER,
    Runtime,
    prepare_databases,
)
from research.scenario_dsl.models import stable_hash


def now() -> str:
    return datetime.now(UTC).isoformat()


class Trial:
    def __init__(
        self, runtime: Runtime, fixture: dict[str, Any], arm: str, directory: Path
    ) -> None:
        self.runtime = runtime
        self.fixture = fixture
        self.arm = arm
        self.id = str(uuid4())
        self.path = directory / f"{fixture['id']}-{arm}-{self.id}.json"
        self.row: dict[str, Any] = {
            "execution_id": self.id,
            "fixture": fixture,
            "fixture_hash": stable_hash(fixture),
            "arm": arm,
            "status": "RUNNING",
            "started_at": now(),
            "http": [],
            "barriers": [],
            "targets": [],
            "client_playback": [],
            "checkpoints": [],
        }
        freeze = OUTPUT / "source-freeze.json"
        if freeze.exists():
            source = json.loads(freeze.read_text(encoding="utf-8"))
            self.row["source_hash"] = source["source_hash"]
            self.row["configuration"] = {
                "fixture_hash": self.row["fixture_hash"], "arm": arm,
                "source_hash": source["source_hash"], "mode": "SCRIPTED_TONE",
                "plan_hash": json.loads((OUTPUT / "exploratory-plan.json").read_text(
                    encoding="utf-8"
                ))["plan_hash"],
            }
            self.row["configuration_hash"] = stable_hash(self.row["configuration"])
        self.item: dict[str, Any] = {}
        self.scenario = ""
        self.resource = ""
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.row, indent=2, default=str) + "\n", encoding="utf-8")

    def request(
        self,
        base: str,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        allow_failure: bool = False,
        oracle: bool = False,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if oracle:
            headers["X-Oracle-Token"] = self.runtime.token
        request = Request(
            base + path,
            method=method,
            headers=headers,
            data=json.dumps(body).encode() if body is not None else None,
        )
        sent = now()
        try:
            with urlopen(request, timeout=40) as response:
                data = json.load(response)
                status = response.status
                trace = response.headers.get("x-trace-id")
        except HTTPError as exc:
            status = exc.code
            data = json.loads(exc.read())
            trace = exc.headers.get("x-trace-id")
        evidence = {
            "base": base,
            "method": method,
            "path": path,
            "request": body,
            "response": data,
            "status": status,
            "trace_id": trace,
            "sent_at": sent,
            "received_at": now(),
        }
        self.row["http"].append(evidence)
        self.save()
        if status >= 400 and not allow_failure:
            raise RuntimeError(f"HTTP {status}: {path}: {data}")
        return dict(data)

    def post(self, base: str, path: str, **body: Any) -> dict[str, Any]:
        return self.request(base, "POST", path, body)

    def barrier(self, name: str, **facts: Any) -> None:
        self.row["barriers"].append({"name": name, "at": now(), **facts})
        self.save()

    def setup(self) -> str:
        self.scenario = self.post(SIMULATOR, "/internal/scenarios")["scenario_id"]
        self.item = self.post(
            API, "/internal/phase1/fixtures", command_id=str(uuid4()), research_arm=self.arm
        )
        # External fixture identity is established before the proposed operation.
        # Never derive an expected resource from the controller's later decision.
        self.resource = f"property:{self.item['property_id']}:maintenance"
        self.row["fixture_identity"] = self.item
        self.row.update(
            workflow_id=self.item["workflow_id"],
            call_id=self.item["call_id"],
            scenario_id=self.scenario,
        )
        self.revision(1, 15)
        op = self.post(
            API,
            "/internal/phase2/operations",
            command_id=str(uuid4()),
            workflow_id=self.item["workflow_id"],
            scenario_id=self.scenario,
            expected_intent_revision=1,
            expected_resource_version=0,
            idempotency_key=f"readiness-v2:{self.id}",
        )
        self.drain()
        return str(op["operation_id"])

    def revision(self, number: int, hour: int) -> None:
        if number <= 2:
            utterance = self.item["utterance_ids"][number - 1]
        else:
            source = str(uuid4())
            event = self.post(
                API,
                f"/internal/phase4/calls/{self.item['call_id']}/voice-events",
                event_id=str(uuid4()),
                source_event_id=source,
                event_type="TranscriptFinal",
                occurred_at=now(),
                raw={"script": "Actually make that 5 PM."},
                normalized={"transcript": "Actually make that 5 PM."},
            )
            utterance = event["utterance_id"]
        desired = {
            "ticket_id": self.item["ticket_id"],
            "requested_start": f"2026-11-01T{hour:02d}:00:00+05:00",
            "requested_end": f"2026-11-01T{hour + 1:02d}:00:00+05:00",
            "timezone": "Asia/Karachi",
        }
        scripted = now()
        accepted = self.post(
            API,
            f"/v1/workflows/{self.item['workflow_id']}/revisions",
            command_id=str(uuid4()),
            expected_revision=number - 1,
            change_class="INITIAL" if number == 1 else "PARAMETER_CORRECTION",
            desired_state=desired,
            candidate_source={
                "utterance_id": utterance,
                "model": "readiness-v2-scripted",
                "prompt_hash": stable_hash(desired),
                "transcript_version": 1,
            },
        )
        self.row["targets"].append(
            {
                "revision": number,
                "scripted_at": scripted,
                "accepted_at": accepted["accepted_at"],
                **{k: v for k, v in desired.items() if k != "ticket_id"},
                "resource_key": self.resource,
            }
        )

    def history(self) -> dict[str, Any]:
        return self.request(API, "GET", f"/v1/workflows/{self.item['workflow_id']}/history")

    def drain(self) -> None:
        steps = []
        for _ in range(30):
            active = False
            for operation in self.history()["operations"]:
                result = self.post(
                    WORKER,
                    "/internal/phase2/step",
                    operation_id=operation["id"],
                    owner=f"trial:{self.id}",
                )
                steps.append(result)
                active |= result["action"] != "idle"
            if not active:
                self.row.setdefault("worker_drains", []).append(steps)
                return
        raise TimeoutError("30 drain passes exhausted")

    def verify(self, op: str, revision: int) -> dict[str, Any]:
        return self.post(
            API,
            "/internal/phase3/verifications",
            command_id=str(uuid4()),
            operation_id=op,
            expected_intent_revision=revision,
            claim_type="CURRENT_APPOINTMENT" if revision == 1 else "RESCHEDULED_APPOINTMENT",
        )

    def schedule(self, op: str, revision: int, *, repair_id: str | None = None) -> dict[str, Any]:
        if self.arm == "B3":
            result = self.post(
                VOICE,
                "/internal/phase6/b3/schedule",
                workflow_id=self.item["workflow_id"],
                expected_intent_revision=revision,
            )
        else:
            receipt = self.verify(op, revision)
            permit = self.post(
                API,
                "/internal/phase3/claims",
                command_id=str(uuid4()),
                receipt_id=receipt["receipt_id"],
                expected_intent_revision=revision,
            )
            self.post(
                API,
                f"/internal/phase3/permits/{permit['permit_id']}/queue",
                command_id=str(uuid4()),
                expected_intent_revision=revision,
            )
            result = self.post(
                VOICE,
                "/internal/phase4/cascade/schedule",
                permit_id=permit["permit_id"],
                expected_intent_revision=revision,
                repair_obligation_id=repair_id,
            )
        return self.detail(str(result["segment_id"]))

    def detail(self, segment_id: str) -> dict[str, Any]:
        return self.request(API, "GET", f"/v1/audio-segments/{segment_id}")

    def ack_body(self, segment: dict[str, Any], kind: str, words: int = 0) -> dict[str, Any]:
        ms = segment["word_timeline_json"][words - 1]["end_ms"] if words else 0
        return {
            "event_id": str(uuid4()),
            "segment_id": str(segment["id"]),
            "event_type": kind,
            "client_time": now(),
            "played_ms": ms,
            "last_frame": ms * 16
            if words < len(segment["word_timeline_json"])
            else segment["frame_count"],
            "last_word_index": words,
        }

    def ack(
        self,
        segment: dict[str, Any],
        kind: str,
        words: int = 0,
        *,
        body: dict[str, Any] | None = None,
        allow_failure: bool = False,
    ) -> dict[str, Any]:
        request = body or self.ack_body(segment, kind, words)
        response = self.request(
            API,
            "POST",
            f"/v1/calls/{self.item['call_id']}/playback-events",
            request,
            allow_failure=allow_failure,
        )
        record = self.row["http"][-1]
        self.row["client_playback"].append(
            {
                "request": request,
                "response": response,
                "status": record["status"],
                "server_received_at": record["received_at"],
            }
        )
        self.save()
        return response

    def full(self, segment: dict[str, Any]) -> None:
        self.ack(segment, "STARTED")
        self.ack(segment, "COMPLETED", len(segment["word_timeline_json"]))

    def snapshot(self) -> dict[str, Any]:
        history = self.history()
        with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
            segments = conn.execute(
                "SELECT * FROM audio_segments WHERE workflow_id=%s ORDER BY generated_at",
                (self.item["workflow_id"],),
            ).fetchall()
            obligations = conn.execute(
                "SELECT * FROM repair_obligations WHERE workflow_id=%s ORDER BY created_at",
                (self.item["workflow_id"],),
            ).fetchall()
            observations = conn.execute(
                "SELECT p.* FROM provider_events p JOIN operations o ON o.id=p.operation_id "
                "WHERE o.workflow_id=%s AND p.event_kind='READINESS_OBSERVATION_V2' "
                "ORDER BY p.occurred_at",
                (self.item["workflow_id"],),
            ).fetchall()
            playback_rows = conn.execute(
                "SELECT * FROM playback_events WHERE call_id=%s ORDER BY server_received_at",
                (self.item["call_id"],),
            ).fetchall()
        for segment in segments:
            audio = bytes(segment.pop("audio_data"))
            if hashlib.sha256(audio).hexdigest() != segment["audio_hash"]:
                raise ValueError("Persisted audio hash mismatch")
            audio_path = self.path.parent / "audio" / f"{segment['audio_hash']}.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            if not audio_path.exists():
                audio_path.write_bytes(audio)
            segment["audio_artifact"] = str(audio_path)
        observed = [
            {
                "source_type": o["normalized_json"]["source_type"],
                "source_identifier": o["normalized_json"]["source_identifier"],
                "available_at": o["normalized_json"]["observed_at"],
                "query": o["normalized_json"]["query"],
                "raw": o["raw_json"],
                "raw_hash": stable_hash(o["raw_json"]),
            }
            for o in observations
        ]
        truth = self.request(
            SIMULATOR, "GET", f"/internal/scenarios/{self.scenario}/truth", oracle=True
        )["commits"]
        serial = json.loads(
            json.dumps(
                {
                    "history": history,
                    "segments": segments,
                    "obligations": obligations,
                    "observations": observed,
                    "raw_provider_events": observations,
                    "truth": truth,
                    "playback_rows": playback_rows,
                },
                default=str,
            )
        )
        return dict(serial)

    def checkpoint(self, name: str) -> None:
        snapshot = self.snapshot()
        self.row["checkpoints"].append(
            {
                "name": name,
                "at": now(),
                "snapshot": snapshot,
                "targets": json.loads(json.dumps(self.row["targets"])),
                "client_playback": json.loads(json.dumps(self.row["client_playback"])),
                "grade": self.grade(snapshot),
                "repair_telemetry": repair_telemetry(snapshot["obligations"]),
            }
        )

    def grade(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        return grade_observable(
            [RevisionTarget.model_validate(t) for t in self.row["targets"]],
            snapshot["truth"],
            snapshot["segments"],
            self.row["client_playback"],
            snapshot["observations"],
        )

    def recover(self, revision: int) -> list[dict[str, Any]]:
        self.drain()
        history = self.history()
        operation = next(
            (
                o
                for o in reversed(history["operations"])
                if o["intent_revision"] == revision
                and o["effect_knowledge"] == "PRESENT"
                and o["applicability"] == "CURRENT"
            ),
            None,
        )
        if operation is None:
            self.row["unresolved_update"] = (
                "No current PRESENT operation; ordinary safeguards retained"
            )
            return []
        snapshot = self.snapshot()
        repairs = [
            o for o in snapshot["obligations"] if o["state"] in ("OPEN", "REPAIR_AUTHORIZED")
        ]
        if self.arm == "P2" and repairs:
            for _ in repairs:
                process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "apps.durable_worker.repair",
                        "--workflow",
                        self.item["workflow_id"],
                    ],
                    cwd=ROOT,
                    env=self.runtime.env,
                    capture_output=True,
                    text=True,
                    timeout=40,
                )
                self.row.setdefault("recovery_processes", []).append(
                    {
                        "returncode": process.returncode,
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                    }
                )
                if process.returncode:
                    raise RuntimeError("Repair recovery process failed")
            snapshot = self.snapshot()
            return [
                s
                for s in snapshot["segments"]
                if s["intent_revision"] == revision and s["state"] == "PUBLISHED"
            ]
        return [self.schedule(operation["id"], revision)]

    def run(self) -> None:
        op = self.setup()
        kind = self.fixture["id"]
        if kind == "E1":
            receipt = self.verify(op, 1)
            self.barrier("VERIFIED_BEFORE_CORRECTION", receipt_id=receipt["receipt_id"])
            self.revision(2, 16)
            if self.arm == "B3":
                response = self.request(
                    VOICE,
                    "POST",
                    "/internal/phase6/b3/schedule",
                    {"workflow_id": self.item["workflow_id"], "expected_intent_revision": 1},
                    allow_failure=True,
                )
            else:
                response = self.request(
                    API,
                    "POST",
                    "/internal/phase3/claims",
                    {
                        "command_id": str(uuid4()),
                        "receipt_id": receipt["receipt_id"],
                        "expected_intent_revision": 1,
                    },
                    allow_failure=True,
                )
            self.row["unsafe_attempt"] = self.row["http"][-1]
            self.row["first_blocker"] = response.get("type", "accepted")
            for segment in self.recover(2):
                self.full(segment)
            return
        old = self.schedule(op, 1)
        if kind == "E2":
            self.barrier("PUBLISHED_BEFORE_START", segment_id=old["id"])
            # Named external fault, append-only simulator log; VERSION_ONLY was predeclared.
            with psycopg.connect(SIM_DATABASE, row_factory=dict_row) as conn:
                facts = conn.execute(
                    "SELECT id FROM provider_appointments WHERE scenario_id=%s", (self.scenario,)
                ).fetchone()
                assert facts is not None
            from research.provider_simulator.models import ProviderAction, ProviderOperation
            from research.provider_simulator.store import inject_concurrent_change

            previous = os.environ.get("SIMULATOR_DATABASE_URL")
            os.environ["SIMULATOR_DATABASE_URL"] = SIM_DATABASE
            try:
                inject_concurrent_change(
                    ProviderOperation(
                        scenario_id=UUID(self.scenario),
                        operation_id=UUID(op),
                        idempotency_key="external-fault",
                        request_hash="external-fault",
                        action=ProviderAction.RESCHEDULE,
                        resource_key=self.resource,
                        appointment_id=facts["id"],
                        expected_resource_version=0,
                        requested_start=datetime.fromisoformat("2026-11-01T15:00:00+05:00"),
                        requested_end=datetime.fromisoformat("2026-11-01T16:00:00+05:00"),
                        timezone="Asia/Karachi",
                    )
                )
            finally:
                if previous is None:
                    os.environ.pop("SIMULATOR_DATABASE_URL", None)
                else:
                    os.environ["SIMULATOR_DATABASE_URL"] = previous
            self.barrier("EXTERNAL_RESOURCE_VERSION_CHANGE")
            response = self.ack(old, "STARTED", allow_failure=True)
            self.row["unsafe_attempt"] = self.row["http"][-1]
            self.row["first_blocker"] = response.get(
                "type", "none: baseline current-revision check allows start"
            )
            if self.row["http"][-1]["status"] == 202:
                self.ack(old, "COMPLETED", len(old["word_timeline_json"]))
            self.revision(2, 16)
            for segment in self.recover(2):
                self.full(segment)
            return
        self.ack(old, "STARTED")
        if kind == "E3":
            self.ack(old, "PROGRESS", 2)
            self.checkpoint("before-decisive-content-control")
            delayed = self.ack_body(old, "PROGRESS", 8)
            self.barrier("DECISIVE_ACK_WITHHELD", request=delayed)
            self.revision(2, 16)
            self.barrier("REVISION_ACCEPTED_BEFORE_ACK")
            first = self.ack(old, "PROGRESS", body=delayed)
            retry = self.ack(old, "PROGRESS", body=delayed)
            assert first == retry
            lower = self.ack_body(old, "PROGRESS", 2)
            lower["client_time"] = delayed["client_time"]
            self.ack(old, "PROGRESS", body=lower)
            interrupted = {**delayed, "event_id": str(uuid4()), "event_type": "INTERRUPTED"}
            self.ack(old, "INTERRUPTED", body=interrupted)
            self.checkpoint("late-ack-capability-and-idempotency")
        else:
            self.ack(old, "COMPLETED", len(old["word_timeline_json"]))
            self.revision(2, 16)
        if kind == "E4":
            self.drain()
            self.checkpoint("persisted-before-worker-restart")
            start = len(self.runtime.events)
            self.runtime.restart_worker(self.item["workflow_id"])
            if self.arm == "P2":
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    snapshot = self.snapshot()
                    current = [
                        s
                        for s in snapshot["segments"]
                        if s["intent_revision"] == 2 and s["state"] == "PUBLISHED"
                    ]
                    if current:
                        break
                    Event().wait(0.1)
                else:
                    raise TimeoutError("AUTOMATIC_PUBLICATION barrier not reached")
            else:
                current = self.recover(2)
            self.row["process_restart"] = self.runtime.events[start:]
            self.barrier("AUTOMATIC_PUBLICATION", segments=[s["id"] for s in current])
            for segment in current:
                self.full(segment)
            self.runtime.stop("worker")
            self.runtime.start("worker")
            return
        current = self.recover(2)
        if kind == "E5":
            for segment in current:
                self.ack(segment, "STARTED")
            self.barrier("COMPLETION_ACK_MISSING")
            self.barrier(
                "CLIENT_DISCONNECTED", evidence="scripted logical client outage; no WebRTC fault"
            )
            self.checkpoint("missing-completion-unknown")
            self.barrier("CLIENT_RECONNECTED", client_instance=str(uuid4()))
            for segment in current:
                completion = self.ack_body(segment, "COMPLETED", len(segment["word_timeline_json"]))
                assert self.ack(segment, "COMPLETED", body=completion) == self.ack(
                    segment, "COMPLETED", body=completion
                )
            return
        if kind == "E6":
            for segment in current:
                self.ack(segment, "STARTED")
                self.ack(segment, "PROGRESS", min(15, len(segment["word_timeline_json"]) - 1))
            self.revision(3, 17)
            for segment in current:
                self.ack(segment, "COMPLETED", len(segment["word_timeline_json"]))
            self.checkpoint("stale-r2-completion-does-not-close-r3")
            current = self.recover(3)
        for segment in current:
            self.full(segment)


def execute(runtime: Runtime, fixture: dict[str, Any], arm: str, directory: Path) -> dict[str, Any]:
    trial = Trial(runtime, fixture, arm, directory)
    try:
        trial.run()
        trial.row["status"] = "COMPLETED"
    except Exception as exc:
        # Harness failure is explicitly retained with raw steps, trace IDs and traceback.
        trial.row.update(
            status="TIMEOUT" if isinstance(exc, TimeoutError) else "FAILED",
            failure={
                "type": type(exc).__name__,
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
    if trial.item:
        try:
            snapshot = trial.snapshot()
            trial.row.update(
                snapshot=snapshot,
                grade=trial.grade(snapshot),
                repair_telemetry=repair_telemetry(snapshot["obligations"]),
            )
        except Exception as exc:
            trial.row["grading_failure"] = {"type": type(exc).__name__, "detail": str(exc)}
    trial.row["finished_at"] = now()
    trial.row["trace_hash"] = stable_hash(trial.row)
    trial.save()
    print(
        f"{fixture['id']} {arm} {trial.row['status']} "
        f"{trial.row.get('grade', {}).get('correct_final_update')} {trial.path.name}",
        flush=True,
    )
    return {
        "execution_id": trial.id,
        "fixture": fixture["id"],
        "arm": arm,
        "path": str(trial.path),
        "status": trial.row["status"],
        "trace_hash": trial.row["trace_hash"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--planned", action="store_true")
    parser.add_argument("--fixture", choices=[f["id"] for f in FIXTURES])
    parser.add_argument("--arm", choices=["B3", "P1", "P2"])
    args = parser.parse_args()
    prepare_databases()
    identifier = str(uuid4())
    directory = OUTPUT / ("planned" if args.planned else f"debug/{identifier}")
    if args.planned and directory.exists():
        raise ValueError("Planned set already exists; do not overwrite attempts")
    plan = freeze_plan() if args.planned else None
    source = freeze_source() if args.planned else None
    directory.mkdir(parents=True, exist_ok=False)
    selected = (
        FIXTURES
        if args.planned or not args.fixture
        else [f for f in FIXTURES if f["id"] == args.fixture]
    )
    arms = ("B3", "P1", "P2") if args.planned or not args.arm else (args.arm,)
    manifest: dict[str, Any] = {
        "classification": "PLANNED_EXPLORATORY" if args.planned else "DEBUG_NOT_PLANNED",
        "plan": plan,
        "source_hash": source["source_hash"] if source else None,
        "started_at": now(),
        "executions": [],
        "phase8_started": False,
    }
    manifest["planned_slots"] = [
        {"fixture": f["id"], "arm": a, "status": "PLANNED"} for f in selected for a in arms
    ]
    target = directory / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with Runtime(directory / "logs") as runtime:
        for fixture in selected:
            for arm in arms:
                row = execute(runtime, fixture, arm, directory)
                manifest["executions"].append(row)
                for slot in manifest["planned_slots"]:
                    if slot["fixture"] == row["fixture"] and slot["arm"] == row["arm"]:
                        slot.update(row)
                target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest.update(completed_at=now(), process_events=runtime.events)
    manifest["manifest_hash"] = stable_hash(manifest)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
