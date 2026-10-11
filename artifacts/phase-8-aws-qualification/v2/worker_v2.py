"""One calibration execution; read-only recovery never replays an ambiguous command."""

import argparse
import json
import subprocess
import time
import traceback
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Any

from research.arms import Arm
from research.execution_setup.core import (
    PREFIX,
    Ledger,
    atomic,
    check_source,
    immutable,
    load,
    now,
    runner_lock,
)
from research.execution_setup.resources import (
    GIB,
    cpu_fraction,
    database,
    docker_stats,
    host,
    tree_bytes,
)
from research.execution_setup.runtime import Runtime
from research.scenario_dsl.models import stable_hash
from research.study.models import Acceptance, Evidence, StudyCase
from research.study_v4.oracle import adapt_calibration, revised_evaluate


def bind(runtime: Runtime) -> None:
    """Legacy research adapters have process globals; each OS process owns one binding.

    Never use threads to bind two executions. Application modules are not patched.
    """
    import research.remedies.runner as legacy
    import research.study_v4.calibration as v4

    for module in (legacy, v4):
        for key, value in {
            "API": "http://127.0.0.1:19100",
            "VOICE": "http://127.0.0.1:19101",
            "WORKER": "http://127.0.0.1:19102",
            "SIMULATOR": "http://127.0.0.1:19110",
            "DATABASE": runtime.database,
            "SIM_DATABASE": runtime.sim_database,
        }.items():
            setattr(module, key, value)


# Imported only after the module-level research adapters; bind() changes their resources.
from research.study_v4.calibration import CalibrationTrial  # noqa: E402


class Trial(CalibrationTrial):
    runtime: Runtime

    def __init__(
        self, runtime: Runtime, case: StudyCase, slot: dict[str, Any], ledger: Ledger
    ) -> None:
        if not case.case_id.startswith(PREFIX):
            raise ValueError("Main inputs are disabled")
        self.ledger, self.slot = ledger, slot
        self.execution_directory = ledger.root / "executions" / slot["execution_id"]
        super().__init__(runtime, case, Arm(slot["arm"]), self.execution_directory)
        self.row.update(
            setup_version="phase8-execution-setup-v1",
            attempt=slot["attempt"],
            attempt_label=slot["label"],
            original_id=slot["original_id"],
        )
        self.save()

    def save(self) -> None:
        self.id = self.slot["execution_id"]
        self.path = self.execution_directory / "checkpoint.json"
        self.row["execution_id"] = self.id
        self.row.setdefault("external_requests", [])
        self.row["checkpointed_at"] = now()
        self.ledger.checkpoint(self.id, self.row)
        atomic(self.path, self.row)  # convenience view; authoritative checkpoint is transactional

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
        if method == "POST" and path.endswith("/revisions") and body is not None:
            revision = int(body["expected_revision"]) + 1
            issued = now()
            self.row["external_requests"].append(
                {"revision": revision, "issued_at": issued, "command_id": body["command_id"]}
            )
            # Durable script-issuance intent precedes network transmission. If the process
            # dies in this tiny gap, publication is uncertain and grading stays unknown.
            if revision == self.case.intents[-1].revision:
                deadline = (datetime.fromisoformat(issued) + timedelta(seconds=600)).isoformat()
                self.ledger.update(self.id, deadline=deadline)
                self.row["original_deadline"] = deadline
            self.save()
        return super().request(base, method, path, body, allow_failure=allow_failure, oracle=oracle)

    def wipe_cache(self) -> None:
        cache = self.runtime.config["containers"][2]
        inspected = subprocess.run(
            ["docker", "inspect", cache], check=True, capture_output=True, text=True, timeout=10
        )
        info = json.loads(inspected.stdout)[0]
        if info["Config"]["Labels"].get("research.setup") != self.runtime.config["resource_id"]:
            raise ValueError("Cache ownership mismatch; flush rejected")
        for args in (("SET", self.id, self.case.fixture_hash), ("FLUSHDB", "SYNC"), ("DBSIZE",)):
            result = subprocess.run(
                ["docker", "exec", cache, "redis-cli", *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.row.setdefault("redis_fault", []).append(
                {"container": cache, "args": args, "stdout": result.stdout, "at": now()}
            )
            self.save()
        self.barrier("DEDICATED_RESEARCH_CACHE_FLUSH_NEGATIVE_CONTROL")


def recover_trial(runtime: Runtime, slot: dict[str, Any], ledger: Ledger) -> Trial:
    path = ledger.root / "executions" / slot["execution_id"] / "checkpoint.json"
    trial = Trial.__new__(Trial)
    trial.ledger, trial.slot = ledger, slot
    trial.execution_directory = path.parent
    trial.path, trial.row = path, ledger.recover_checkpoint(slot["execution_id"])
    if slot["deadline"] and not trial.row.get("original_deadline"):
        trial.row.update(original_deadline=slot["deadline"], missing_final_anchor=True)
    trial.id, trial.arm = slot["execution_id"], slot["arm"]
    trial.runtime, trial.case = runtime, StudyCase.model_validate(trial.row["input"])
    trial.fixture = trial.row["fixture"]
    trial.item = trial.row.get("fixture_identity", {})
    trial.scenario = trial.row.get("scenario_id", "")
    trial.resource = f"property:{trial.item['property_id']}:maintenance" if trial.item else ""
    trial.row.setdefault("collector_resumes", []).append(now())
    # An interrupted driver is never reissued. Existing services and DB effects remain.
    if not trial.row.get("driver_finished_at"):
        trial.row.update(
            status="FAILED",
            driver_finished_at=now(),
            failure={"type": "INTERRUPTED_DRIVER", "detail": "No commands replayed"},
        )
        ledger.event("INTERRUPTED_DRIVER", execution_id=trial.id)
    trial.save()
    return trial


def fixed_deadline(row: dict[str, Any]) -> tuple[str, bool]:
    if row.get("original_deadline"):
        return str(row["original_deadline"]), bool(row.get("missing_final_anchor", False))
    # No final request observed: a bounded collection horizon, NOT an invented anchor.
    # This can never earn a negative exposure result or complete resolution timing.
    return (datetime.fromisoformat(row["started_at"]) + timedelta(seconds=600)).isoformat(), True


def evidence_for(trace: dict[str, Any]) -> tuple[StudyCase, Evidence]:
    case, evidence = adapt_calibration(trace)
    revisions = {r["revision"]: r for r in trace["snapshot"]["history"]["revisions"]}
    anchors = []
    for issued in trace["external_requests"]:
        revision = revisions.get(issued["revision"])
        actual = revision["desired_state_json"] if revision else {}
        anchors.append(
            Acceptance(
                revision=issued["revision"],
                scripted_at=issued["issued_at"],
                accepted_at=revision["accepted_at"] if revision else None,
                actual_start=actual.get("requested_start"),
                actual_end=actual.get("requested_end"),
                actual_timezone=actual.get("timezone"),
            )
        )
    # Prefer durable server timestamps over response-receipt proxy times.
    server = {str(p["id"]): p["server_received_at"] for p in trace["snapshot"]["playback_rows"]}
    playback = [
        {
            **p,
            "server_received_at": server.get(
                str(p["request"]["event_id"]), p.get("server_received_at")
            ),
        }
        for p in evidence.playback
    ]
    known = {str(p["request"]["event_id"]) for p in playback}
    for event in trace["snapshot"]["playback_rows"]:
        if str(event["id"]) in known:
            continue
        playback.append(
            {
                "request": {
                    "event_id": str(event["id"]),
                    "segment_id": str(event["segment_id"]),
                    "event_type": event["event_type"],
                    "client_time": event["client_time"],
                    "played_ms": event["played_ms"] or 0,
                    "last_frame": event["last_frame"] or 0,
                    "last_word_index": event["last_word_index"] or 0,
                },
                "response": event["response_json"],
                "status": 202,
                "server_received_at": event["server_received_at"],
                "source": "DURABLE_SERVER_ACK_JOURNAL_NOT_SYNTHESIZED_HUMAN_EVIDENCE",
            }
        )
    gaps = bool(trace.get("collection_errors"))
    return case, evidence.model_copy(
        update={
            "attempt": trace["attempt"],
            "acceptances": anchors,
            "playback": playback,
            "truth_complete": not gaps,
            "publication_journal_complete": not gaps,
            "playback_journal_complete": not gaps,
            "repair_journal_complete": not gaps,
        }
    )


def collect(trial: Trial, *, checkpoint_once: bool = False) -> bool:
    ledger, runtime = trial.ledger, trial.runtime
    deadline_text, missing = fixed_deadline(trial.row)
    ledger.update(trial.id, deadline=deadline_text, state="RUNNING")
    trial.row.update(original_deadline=deadline_text, missing_final_anchor=missing)
    until = datetime.fromisoformat(deadline_text)
    backup = Path(load(ledger.root / "config.json")["backup"])
    prior: dict[str, Any] | None = None
    next_check = 0.0
    while True:
        at = now()
        number = len(trial.row.setdefault("polls", [])) + 1
        sample = host(ledger.root, backup)
        sample["cpu_load_fraction"] = cpu_fraction(prior, sample) if prior else None
        prior = sample
        if sample["available_memory_bytes"] < 0.75 * GIB or sample["system_free_bytes"] < 2 * GIB:
            atomic(ledger.root / "pause.json", {"reason": "ACTIVE_RESOURCE_PRESSURE", "at": at})
            ledger.event("RESOURCE_NOTICE", execution_id=trial.id, sample=sample)
        try:
            snapshot = trial.snapshot()
            poll = {"at": at, "ended_at": now(), "snapshot": snapshot, "host": sample}
            trial.row["snapshot"] = snapshot
        except Exception as error:
            # This is evidence capture, not a swallowed business transition.
            poll = {
                "at": at,
                "ended_at": now(),
                "host": sample,
                "error": {"type": type(error).__name__, "detail": str(error)},
            }
            trial.row.setdefault("collection_errors", []).append(poll["error"])
            ledger.event("COLLECTION_FAILURE", execution_id=trial.id, detail=poll["error"])
            atomic(ledger.root / "pause.json", {"reason": "COLLECTION_FAILURE", "at": at})
        path = trial.execution_directory / "polls" / f"{number:05d}.json"
        immutable(path, poll)
        hashed = ledger.seal(path)
        trial.row["polls"].append({"at": at, "path": str(path), "hash": hashed})
        trial.save()
        if time.monotonic() >= next_check:
            try:
                check_source(ledger.root)
                ledger.verify()
            except ValueError as error:
                atomic(ledger.root / "pause.json", {"reason": str(error), "at": now()})
                ledger.event("DRIFT_STOP_ADMISSIONS", execution_id=trial.id, detail=str(error))
                trial.row["source_drift"] = str(error)
                trial.save()
            next_check = time.monotonic() + 60
            remaining = max(0, (until - datetime.now(UTC)).total_seconds())
            print(
                f"COLLECT {trial.id} {trial.arm}: {number} polls, {remaining:.0f}s remaining",
                flush=True,
            )
        if checkpoint_once and not trial.row.get("qualification_checkpoint_done") and number >= 2:
            trial.row["qualification_checkpoint_done"] = True
            trial.save()
            ledger.update(trial.id, state="CHECKPOINTED")
            ledger.event("COLLECTOR_CHECKPOINT_EXIT", execution_id=trial.id, deadline=deadline_text)
            return False  # Services continue independently; next invocation attaches read-only.
        if datetime.fromisoformat(at) >= until:
            break
        Event().wait(min(5, max(0, (until - datetime.now(UTC)).total_seconds())))
    trial.row.update(finished_at=now(), processes=runtime.events)
    trial.row["resource_end"] = {
        "app": database(runtime.database),
        "truth": database(runtime.sim_database),
        "docker": docker_stats(runtime.config["containers"]),
        "logs_bytes": tree_bytes(trial.execution_directory / "logs"),
        "audio_bytes": tree_bytes(trial.execution_directory / "audio"),
        "poll_bytes": tree_bytes(trial.execution_directory / "polls"),
    }
    trial.row["trace_hash"] = stable_hash(trial.row)
    try:
        case, evidence = evidence_for(trial.row)
        accepted = [a.accepted_at for a in evidence.acceptances if a.revision > 1 and a.accepted_at]
        grade, analysis = revised_evaluate(
            case, evidence, challenge_at=max(accepted) if accepted else None
        )
        trial.row["revised_grade"] = grade
        trial.row["analysis_row"] = analysis.model_dump(mode="json")
    except Exception as error:
        trial.row["oracle_failure"] = {"type": type(error).__name__, "detail": str(error)}
        ledger.event("ORACLE_FAILURE", execution_id=trial.id, detail=trial.row["oracle_failure"])
        atomic(ledger.root / "pause.json", {"reason": "ORACLE_FAILURE", "at": now()})
    # Keep the raw evidence hash used by the oracle; the sealed export hash additionally
    # covers grades, the analysis row and checkpoint convenience metadata.
    trial.save()
    export = trial.execution_directory / "export.json"
    immutable(export, trial.row)
    hashed = ledger.seal(export)
    for audio in (trial.execution_directory / "audio").glob("*.wav"):
        ledger.seal(audio)
    ledger.update(trial.id, state="EXPORTED", export_hash=hashed)
    ledger.event("EXPORTED", execution_id=trial.id, deadline=deadline_text, hash=hashed)
    runtime.stop_all()
    return True


def execute(root: Path, slot: dict[str, Any], *, checkpoint_once: bool = False) -> bool:
    ledger = Ledger(root)
    execution = root / "executions" / slot["execution_id"]
    execution.mkdir(parents=True, exist_ok=True)
    with runner_lock(execution):
        attach = (execution / "checkpoint.json").exists()
        runtime = Runtime(root, execution, attach=attach)
        bind(runtime)
        if attach:
            trial = recover_trial(runtime, slot, ledger)
            ledger.event("READ_ONLY_RESUME", execution_id=trial.id, deadline=slot["deadline"])
        else:
            case = StudyCase.model_validate(
                load(root / "qualification-plan.json")["cases"][slot["case_id"]]
            )
            trial = Trial(runtime, case, slot, ledger)
            trial.row["resource_start"] = {
                "app": database(runtime.database),
                "truth": database(runtime.sim_database),
                "host": host(root, Path(load(root / "config.json")["backup"])),
            }
            trial.save()
            try:
                runtime.start_all()
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
                ledger.event("DRIVER_FAILURE", execution_id=trial.id, failure=trial.row["failure"])
                atomic(root / "pause.json", {"reason": "DRIVER_FAILURE", "at": now()})
            trial.row["driver_finished_at"] = now()
            trial.save()
        return collect(trial, checkpoint_once=checkpoint_once)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execution", required=True)
    parser.add_argument("--checkpoint-once", action="store_true")
    args = parser.parse_args()
    slot = next(r for r in Ledger(args.root).rows() if r["execution_id"] == args.execution)
    try:
        complete = execute(args.root, slot, checkpoint_once=args.checkpoint_once)
    except Exception as error:
        ledger = Ledger(args.root)
        ledger.event(
            "WORKER_PROTOCOL_FAILURE",
            execution_id=args.execution,
            detail=str(error),
            traceback=traceback.format_exc(),
        )
        atomic(args.root / "pause.json", {"reason": str(error), "at": now()})
        raise
    raise SystemExit(0 if complete else 75)


if __name__ == "__main__":
    main()
