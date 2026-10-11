"""Fresh PG calibration of all fixed-frame cells, no main-bank execution path."""

import argparse
import hashlib
import json
import os
import subprocess
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row

from research.arms import Arm
from research.remedies.runner import Trial, now
from research.scenario_dsl.models import stable_hash
from research.study.models import StudyCase
from research.study.package import write_json
from research.study_v4.design import ROOT as OUTPUT
from research.study_v4.design import materialize, package
from research.study_v4.runtime import (
    API,
    DATABASE,
    SIM_DATABASE,
    SIMULATOR,
    VOICE,
    WORKER,
    Runtime,
    prepare_databases,
)

ROOT = Path(__file__).resolve().parents[2]


class CalibrationTrial(Trial):
    def __init__(self, runtime: Runtime, case: StudyCase, arm: Arm, directory: Path) -> None:
        if not case.case_id.startswith("cal-v4-"):
            raise ValueError("Calibration cannot execute a main input")
        self.runtime, self.case, self.arm = runtime, case, arm.value
        self.id = str(uuid4())
        self.path = directory / f"{case.case_id}-{arm}-{self.id}.json"
        self.fixture = {
            "id": case.case_id,
            "family": case.generator_family,
            "barriers": case.fault_schedule,
            "hours": [15, 16, 17],
        }
        self.row = {
            "execution_id": self.id,
            "fixture": self.fixture,
            "fixture_hash": case.fixture_hash,
            "arm": arm.value,
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "status": "RUNNING",
            "started_at": now(),
            "http": [],
            "barriers": [],
            "targets": [],
            "client_playback": [],
            "checkpoints": [],
            "input": case.model_dump(mode="json"),
            "main_started": False,
        }
        self.row["driver_source_hash"] = stable_hash(
            {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (
                    Path(__file__),
                    Path("research/study_v4/runtime.py"),
                    Path("research/study_v4/design.py"),
                    Path("research/remedies/runner.py"),
                )
            }
        )
        self.item, self.scenario, self.resource = {}, "", ""
        self.save()

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
        remap = {
            "http://127.0.0.1:18000": API,
            "http://127.0.0.1:18001": VOICE,
            "http://127.0.0.1:18002": WORKER,
            "http://127.0.0.1:18010": SIMULATOR,
        }
        base = remap.get(base, base)
        headers = {"Content-Type": "application/json"}
        if oracle:
            headers["X-Oracle-Token"] = self.runtime.token
        sent, clock = now(), time.monotonic()
        try:
            with urlopen(
                Request(
                    base + path,
                    method=method,
                    headers=headers,
                    data=json.dumps(body).encode() if body is not None else None,
                ),
                timeout=40,
            ) as response:
                data, status = json.load(response), response.status
                trace = response.headers.get("x-trace-id")
        except HTTPError as error:
            status, data, trace = (
                error.code,
                json.loads(error.read()),
                error.headers.get("x-trace-id"),
            )
        except (TimeoutError, URLError, ConnectionError) as error:
            self.row["http"].append(
                {
                    "base": base,
                    "method": method,
                    "path": path,
                    "request": body,
                    "status": None,
                    "transport_error": type(error).__name__,
                    "sent_at": sent,
                    "received_at": now(),
                    "elapsed_seconds": time.monotonic() - clock,
                    "execution_id": self.id,
                }
            )
            self.save()
            raise
        self.row["http"].append(
            {
                "base": base,
                "method": method,
                "path": path,
                "request": body,
                "response": data,
                "status": status,
                "trace_id": trace,
                "sent_at": sent,
                "received_at": now(),
                "elapsed_seconds": time.monotonic() - clock,
            }
        )
        self.save()
        if status >= 400 and not allow_failure:
            raise RuntimeError(f"HTTP {status}: {path}: {data}")
        return dict(data)

    def initialize(self) -> str:
        self.scenario = self.post(
            SIMULATOR, "/internal/scenarios", **self.case.provider.model_dump(mode="json")
        )["scenario_id"]
        self.item = self.post(
            API, "/internal/phase1/fixtures", command_id=str(uuid4()), research_arm=self.arm
        )
        self.resource = f"property:{self.item['property_id']}:maintenance"
        self.row.update(
            fixture_identity=self.item,
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
            idempotency_key=f"cal-v4:{self.id}",
        )
        return str(op["operation_id"])

    def setup(self) -> str:
        op = self.initialize()
        self.drain()
        return op

    def revision(self, number: int, hour: int) -> None:
        intent = self.case.intents[number - 1]
        if number <= 2:
            utterance = self.item["utterance_ids"][number - 1]
        else:
            event = self.post(
                API,
                f"/internal/phase4/calls/{self.item['call_id']}/voice-events",
                event_id=str(uuid4()),
                source_event_id=str(uuid4()),
                event_type="TranscriptFinal",
                occurred_at=now(),
                raw={"script": intent.transcript},
                normalized={"transcript": intent.transcript},
            )
            utterance = event["utterance_id"]
        desired = {
            "ticket_id": self.item["ticket_id"],
            "requested_start": intent.start.isoformat(),
            "requested_end": intent.end.isoformat(),
            "timezone": intent.timezone,
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
                "model": "calibration-v4-scripted",
                "prompt_hash": stable_hash(desired),
                "transcript_version": 1,
            },
        )
        self.row["targets"].append(
            {
                "revision": number,
                "scripted_at": scripted,
                "accepted_at": accepted["accepted_at"],
                "requested_start": desired["requested_start"],
                "requested_end": desired["requested_end"],
                "timezone": intent.timezone,
                "resource_key": self.resource,
            }
        )
        self.barrier(
            "CORRECTION_ACCEPTED" if number > 1 else "INITIAL_ACCEPTED",
            accepted_at=accepted["accepted_at"],
            revision=number,
        )

    def current_operation(self, revision: int) -> str | None:
        return next(
            (
                str(o["id"])
                for o in reversed(self.history()["operations"])
                if o["intent_revision"] == revision
                and o["effect_knowledge"] == "PRESENT"
                and o["applicability"] == "CURRENT"
            ),
            None,
        )

    def stage(self, op: str, revision: int) -> dict[str, Any]:
        if self.arm == "B3":
            result = self.post(
                VOICE,
                "/internal/phase6/b3/stage",
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
                "/internal/phase6/claim/stage",
                permit_id=permit["permit_id"],
                expected_intent_revision=revision,
                repair_obligation_id=None,
            )
        segment = self.detail(str(result["segment_id"]))
        if self.arm != "B3":
            self.post(
                API,
                f"/internal/phase4/audio-segments/{segment['id']}/queue",
                command_id=str(uuid4()),
                expected_intent_revision=revision,
            )
            segment = self.detail(str(segment["id"]))
        return segment

    def finish_update(self, revision: int) -> None:
        for segment in self.recover(revision):
            self.full(segment)

    def concurrent_change(self, op: str) -> None:
        from research.provider_simulator.models import ProviderAction, ProviderOperation
        from research.provider_simulator.store import inject_concurrent_change

        with psycopg.connect(SIM_DATABASE, row_factory=dict_row) as conn:
            appointment = conn.execute(
                "SELECT * FROM provider_appointments WHERE scenario_id=%s", (self.scenario,)
            ).fetchone()
        assert appointment is not None
        previous = os.environ.get("SIMULATOR_DATABASE_URL")
        os.environ["SIMULATOR_DATABASE_URL"] = SIM_DATABASE
        try:
            inject_concurrent_change(
                ProviderOperation(
                    scenario_id=UUID(self.scenario),
                    operation_id=UUID(op),
                    idempotency_key="cal-v4-external-change",
                    request_hash="cal-v4-external-change",
                    action=ProviderAction.RESCHEDULE,
                    resource_key=self.resource,
                    appointment_id=appointment["id"],
                    expected_resource_version=appointment["version"],
                    requested_start=appointment["starts_at"].astimezone(
                        ZoneInfo(appointment["timezone"])
                    ),
                    requested_end=appointment["ends_at"].astimezone(
                        ZoneInfo(appointment["timezone"])
                    ),
                    timezone=appointment["timezone"],
                )
            )
        finally:
            if previous is None:
                os.environ.pop("SIMULATOR_DATABASE_URL", None)
            else:
                os.environ["SIMULATOR_DATABASE_URL"] = previous
        self.barrier("VERSION_ONLY_CHANGE")

    def provider_boundary(self, op: str, barrier: str) -> None:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                self.post,
                WORKER,
                "/internal/phase2/step",
                operation_id=op,
                owner=f"cal-v4:{self.id}",
            )
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                state = self.request(
                    SIMULATOR,
                    "GET",
                    f"/internal/scenarios/{self.scenario}/barriers/{barrier}",
                    allow_failure=True,
                )
                if state.get("reached_at"):
                    break
                Event().wait(0.05)  # observe a durable named barrier, no timing placement
            else:
                raise TimeoutError("Provider named barrier not reached")
            self.barrier(
                "COMMIT_LOG_APPENDED"
                if barrier.startswith("AFTER_COMMIT")
                else "DISPATCHED_BEFORE_COMMIT",
                provider_barrier=state,
            )
            self.revision(2, 16)
            self.post(SIMULATOR, f"/internal/scenarios/{self.scenario}/barriers/{barrier}/release")
            result = future.result(timeout=40)
            self.row["boundary_dispatch_result"] = result
            self.barrier("RESPONSE_WITHHELD", causal_order="correction accepted before release")

    def run(self) -> None:
        name = self.case.generator_family
        if name == "restart-before-repair":
            from research.study_v4.window import observe

            op = self.setup()
            self.full(self.schedule(op, 1))
            self.revision(2, 16)
            self.drain()
            self.checkpoint("persisted-before-worker-restart")
            self.runtime.restart_worker(self.item["workflow_id"])
            if self.arm == "P2":
                watched = observe(
                    self,
                    40,
                    "RESTART_REPAIR_DISCOVERY",
                    lambda s, cutoff: any(
                        v["intent_revision"] == 2
                        and v["state"] == "PUBLISHED"
                        and datetime.fromisoformat(v["published_at"]) <= cutoff
                        for v in s["segments"]
                    ),
                )
                if watched["outcome"] != "CONDITION_OBSERVED":
                    raise TimeoutError(
                        "Automatic repair publication did not meet its recovery budget"
                    )
                current = [
                    s
                    for s in watched["snapshot"]["segments"]
                    if s["intent_revision"] == 2 and s["state"] == "PUBLISHED"
                ]
                self.barrier("AUTOMATIC_PUBLICATION", segments=[s["id"] for s in current])
            else:
                current = self.recover(2)
            for segment in current:
                self.full(segment)
            return
        if name == "reconnect-third-revision":
            op = self.setup()
            old = self.schedule(op, 1)
            self.full(old)
            self.barrier("FULL_ACK", segment_id=old["id"])
            self.revision(2, 16)
            current = self.recover(2)
            withheld = []
            for segment in current:
                self.ack(segment, "STARTED")
                self.ack(segment, "PROGRESS", min(15, len(segment["word_timeline_json"]) - 1))
                withheld.append(
                    (
                        segment,
                        self.ack_body(segment, "COMPLETED", len(segment["word_timeline_json"])),
                    )
                )
            self.barrier("R2_STARTED", segments=[s["id"] for s in current])
            self.barrier("ACK_MISSING", withheld=[body for _, body in withheld])
            self.barrier("CLIENT_DISCONNECTED", evidence="LOGICAL_SCRIPTED_CLIENT_ONLY")
            self.barrier("CLIENT_RECONNECT", evidence="LOGICAL_SCRIPTED_CLIENT_ONLY")
            self.revision(3, 17)
            for segment, body in withheld:
                first = self.ack(segment, "COMPLETED", body=body)
                assert first == self.ack(segment, "COMPLETED", body=body)
            self.barrier("R2_ACK_DELAYED", acknowledgement_count=len(withheld))
            self.checkpoint("stale-r2-completion-does-not-close-r3")
            self.finish_update(3)
            return
        mapping = {
            "verified-stale-attempt": "E1",
            "late-decisive-ack": "E3",
        }
        if name in mapping:
            original = self.fixture["id"]
            self.fixture["id"] = mapping[name]
            try:
                super().run()
            finally:
                self.fixture["id"] = original
            return
        op = self.initialize()
        if self.case.stratum.value == "CLEAN":
            self.drain()
            self.finish_update(1)
            return
        if self.case.provider.held_barriers:
            self.provider_boundary(op, self.case.provider.held_barriers[0])
            self.drain()
            self.finish_update(2)
            return
        if name.startswith("pre-dispatch"):
            self.barrier(
                "BEFORE_DISPATCH",
                truth=self.request(
                    SIMULATOR, "GET", f"/internal/scenarios/{self.scenario}/truth", oracle=True
                ),
            )
            self.revision(2, 16)
            self.drain()
            self.finish_update(2)
            return
        if name == "ack-before-verification":
            step = self.post(
                WORKER, "/internal/phase2/step", operation_id=op, owner=f"cal-v4:{self.id}"
            )
            self.barrier(
                "RESPONSE_RECEIVED_BEFORE_VERIFY", worker_step=step, history=self.history()
            )
            self.revision(2, 16)
            self.drain()
            self.finish_update(2)
            return
        if name in ("resource-only", "redis-loss"):
            step = self.post(
                WORKER, "/internal/phase2/step", operation_id=op, owner=f"cal-v4:{self.id}"
            )
            self.barrier("UNKNOWN_BEFORE_CORRECTION", worker_step=step, history=self.history())
            if name == "redis-loss":
                self.wipe_cache()
            self.revision(2, 16)
            self.drain()
            self.finish_update(2)
            return
        if name in ("precommit-5xx", "partial-effect", "duplicate-request-delivery"):
            step = self.post(
                WORKER, "/internal/phase2/step", operation_id=op, owner=f"cal-v4:{self.id}"
            )
            self.barrier(
                "FAULT_RESPONSE_BEFORE_CORRECTION", worker_step=step, history=self.history()
            )
            self.revision(2, 16)
            self.drain()
            self.finish_update(2)
            return
        self.drain()
        if name == "concurrent-resource-change":
            receipt = self.verify(op, 1)
            self.barrier("VERIFIED", receipt=receipt)
            self.concurrent_change(op)
            self.revision(2, 16)
            self.finish_update(2)
            return
        if name == "queued-stale":
            old = self.stage(op, 1)
            self.barrier("GENERATED_QUEUED", segment=old)
            self.revision(2, 16)
            if self.arm == "B3":
                self.request(
                    VOICE,
                    "POST",
                    "/internal/phase6/b3/schedule",
                    {"workflow_id": self.item["workflow_id"], "expected_intent_revision": 1},
                    allow_failure=True,
                )
            else:
                self.request(
                    API,
                    "POST",
                    f"/internal/phase4/audio-segments/{old['id']}/release",
                    {"command_id": str(uuid4()), "expected_intent_revision": 1},
                    allow_failure=True,
                )
            self.row["unsafe_attempt"] = self.row["http"][-1]
            self.finish_update(2)
            return
        old = self.schedule(op, 1)
        self.barrier("PUBLISHED", segment_id=old["id"])
        if name == "version-change-before-start":
            self.concurrent_change(op)
            self.ack(old, "STARTED", allow_failure=True)
            if self.row["http"][-1]["status"] == 202:
                self.ack(old, "COMPLETED", len(old["word_timeline_json"]))
            self.barrier("START_ATTEMPT")
        elif name == "buffered-stale":
            self.revision(2, 16)
            self.ack(old, "STARTED", allow_failure=True)
            self.row["unsafe_attempt"] = self.row["http"][-1]
            self.barrier("START_ATTEMPT")
            self.finish_update(2)
            return
        else:
            self.ack(old, "STARTED")
            words = (
                2
                if name == "intro-control"
                else 8
                if name == "partial-time"
                else len(old["word_timeline_json"])
            )
            self.ack(
                old, "PROGRESS" if words < len(old["word_timeline_json"]) else "COMPLETED", words
            )
            self.barrier(
                "INTRO_ACK"
                if words == 2
                else "TIME_PREDICATE_ACK"
                if name == "partial-time"
                else "FULL_ACK",
                words=words,
            )
        self.revision(2, 16)
        self.finish_update(2)

    def wipe_cache(self) -> None:
        # Reserved namespace only; do not reset the user's Redis/application.
        command = ["docker", "exec", "phase8-calibration-v4-redis", "redis-cli"]
        key = f"cal-v4:{self.id}"
        for args in (("SET", key, self.row["fixture_hash"]), ("FLUSHDB", "SYNC"), ("DBSIZE",)):
            output = subprocess.run(
                command + list(args), capture_output=True, text=True, check=True, timeout=30
            )
            self.row.setdefault("redis_fault", []).append(
                {"command": args, "output": output.stdout}
            )
        self.barrier("REDIS_FLUSH_RESEARCH_ONLY")

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
            raw_provider_events = conn.execute(
                "SELECT p.* FROM provider_events p JOIN operations o ON o.id=p.operation_id "
                "WHERE o.workflow_id=%s ORDER BY p.occurred_at,p.id",
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
                    "raw_provider_events": raw_provider_events,
                    "truth": truth,
                    "playback_rows": playback_rows,
                },
                default=str,
            )
        )
        return dict(serial)


def execute(runtime: Runtime, case: StudyCase, arm: Arm, directory: Path) -> dict[str, Any]:
    trial = CalibrationTrial(runtime, case, arm, directory)
    try:
        trial.run()
        trial.row["status"] = "COMPLETED"
    except Exception as error:
        trial.row.update(
            status="TIMEOUT" if isinstance(error, TimeoutError) else "FAILED",
            failure={
                "type": type(error).__name__,
                "detail": str(error),
                "traceback": traceback.format_exc(),
            },
        )
    if trial.item:
        try:
            snapshot = trial.snapshot()
            trial.row.update(snapshot=snapshot, grade=trial.grade(snapshot))
        except Exception as error:
            trial.row["grading_failure"] = {"type": type(error).__name__, "detail": str(error)}
    trial.row.update(finished_at=now(), processes=runtime.events)
    trial.row["trace_hash"] = stable_hash(trial.row)
    trial.save()
    print(f"{case.case_id} {case.generator_family} {arm} {trial.row['status']}", flush=True)
    return {
        "case_id": case.case_id,
        "arm": arm.value,
        "path": str(trial.path),
        "execution_id": trial.id,
        "status": trial.row["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", type=int)
    parser.add_argument("--arm", choices=[a.value for a in Arm if a.value in ("B3", "P1", "P2")])
    args = parser.parse_args()
    package()
    prepare_databases()
    directory = OUTPUT / "calibration" / str(uuid4())
    directory.mkdir(parents=True, exist_ok=False)
    selected = materialize(calibration=True)
    if args.cell:
        selected = [selected[args.cell - 1]]
    manifest: dict[str, Any] = {
        "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
        "purpose": "DEBUG_SELECTED" if args.cell or args.arm else "PLANNED_150",
        "executions": [],
        "main_started": False,
        "planned_slots": [
            {"case_id": c.case_id, "arm": a.value}
            for c in selected
            for a in ([Arm(args.arm)] if args.arm else c.primary_arms)
        ],
    }
    write_json(directory / "manifest.json", manifest)
    with Runtime(directory / "logs") as runtime:
        for case in selected:
            for arm in [Arm(args.arm)] if args.arm else case.primary_arms:
                manifest["executions"].append(execute(runtime, case, arm, directory))
                write_json(directory / "manifest.json", manifest)


if __name__ == "__main__":
    main()
