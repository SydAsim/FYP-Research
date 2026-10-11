"""Assemble and verify the unaccepted v5 candidate; no cloud/freeze/launch actions."""
from __future__ import annotations

import difflib
import hashlib
import hmac
import json
import shutil
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path("E:/p8v5/source")
PARENT = Path("E:/p8v4/source")
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
RUNTIME = SOURCE / PREFIX
sys.path.insert(0, str(RUNTIME))
from controls import canonical, hash_file, read, write_new


def main() -> None:
    parent = read(PARENT / PREFIX / "candidate-inventory.json")
    expected = {f"{PREFIX}/{name}" for name in ("storage.py", "runner.py", "handover.py")}
    changed = set()
    for name, digest in parent["files"].items():
        if hash_file(PARENT / name) != digest:
            raise ValueError("PARENT_SOURCE_DRIFT: " + name)
        if hash_file(SOURCE / name) != digest:
            changed.add(name)
    if changed != expected:
        raise ValueError("UNREVIEWED_RUNTIME_DIFFERENCE: " + repr(changed))
    differences = sorted(p for p in RUNTIME.glob("*.py")
                         if not (PARENT / PREFIX / p.name).exists()
                         or hash_file(p) != hash_file(PARENT / PREFIX / p.name))
    prior_diff = HERE / "runtime.diff"
    if prior_diff.exists() and not (HERE / "runtime-before-helper-finalization.diff").exists():
        shutil.copyfile(prior_diff, HERE / "runtime-before-helper-finalization.diff")
    chunks = []
    for p in differences:
        previous = PARENT / PREFIX / p.name
        before = previous.read_text(encoding="utf-8").splitlines(keepends=True) if previous.exists() else []
        after = p.read_text(encoding="utf-8").splitlines(keepends=True)
        chunks.extend(difflib.unified_diff(before, after,
                      fromfile="accepted-v4/" + p.name if before else "/dev/null",
                      tofile="candidate-v5/" + p.name))
    prior_diff.write_text("".join(chunks), encoding="utf-8")
    tested = ("inventory_read.py", "storage.py", "closed_restart.py", "handover.py", "runner.py",
              "test_inventory_read.py", "test_closed_restart.py")
    with tarfile.open(HERE / "attempt2/source.tar.gz", "r:gz") as incoming:
        for name in tested:
            stream = incoming.extractfile(f"{PREFIX}/{name}")
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != hash_file(RUNTIME / name):
                raise ValueError("QUALIFIED_SOURCE_DRIFT: " + name)
    write_new(HERE / "qualified-source-closure.json", {
        "status": "PASS", "qualified_core_and_tests": {n: hash_file(RUNTIME / n) for n in tested},
        "qualification_archive": str(HERE / "attempt2/source.tar.gz"),
        "qualification_archive_sha256": hash_file(HERE / "attempt2/source.tar.gz"),
        "excluded_from_deployment_archive": "Independent retained duplicate test-source archive; reference only",
        "preparation_helper": "Static checks only; live deployment qualification remains a gate",
    })
    # Reverify the immutable parent AFTER implementation, without touching it.
    frozen = HERE.parents[1] / "phase-8-continuation-freeze/v4"
    if sys.platform == "win32":
        frozen = Path("\\\\?\\" + str(frozen.resolve()))
    manifest = read(frozen / "freeze-manifest.json")
    attestation = read(frozen / "freeze-attestation.json")
    key = (Path.home() / ".fyp-research/phase8-owner/phase84-final-v2/owner.key").read_bytes()
    parent_freeze = "cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c"
    if (hash_file(frozen / "freeze-manifest.json") != parent_freeze
        or attestation["manifest_sha256"] != parent_freeze
        or not hmac.compare_digest(attestation["signature"], hmac.new(key, canonical(manifest), "sha256").hexdigest())):
        raise ValueError("PARENT_FREEZE_DRIFT")
    for name, digest in manifest["files"].items():
        if hash_file(frozen / name) != digest:
            raise ValueError("PARENT_FREEZE_MEMBER_DRIFT: " + name)
    write_new(HERE / "parent-final-preservation.json", {
        "status": "PASS", "at_utc": datetime.now(UTC).isoformat(),
        "source_members_verified": len(parent["files"]), "freeze_members_verified": len(manifest["files"]),
        "parent_freeze_sha256": parent_freeze, "signature_verified": True,
        "permitted_existing_source_differences": sorted(changed),
        "actual_new_runtime_files": [p.name for p in differences if not (PARENT / PREFIX / p.name).exists()],
    })
    review_prefix = "artifacts/phase-8-continuation/v5"
    for p in sorted(HERE.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or p.suffix == ".pyc" or p.name == "source.tar.gz":
            continue
        if p.name in {"candidate-inventory.json", "candidate-package.json", "final-verification.json",
                      "v5-complete-continuation-review-candidate.tar.gz"}:
            continue
        target = SOURCE / review_prefix / p.relative_to(HERE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    inventory_name = f"{PREFIX}/candidate-inventory.json"
    files = {p.relative_to(SOURCE).as_posix(): hash_file(p) for p in sorted(SOURCE.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
             and p.relative_to(SOURCE).as_posix() != inventory_name}
    package_hash = hashlib.sha256(canonical(files)).hexdigest()
    inventory = {
        "kind": "CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE", "version": "phase85-continuation-v5",
        "package_hash": package_hash, "parent_package_hash": parent["package_hash"],
        "parent_freeze_sha256": parent_freeze, "files": files,
        "accepted": False, "frozen": False, "launch_authorized": False,
        "closed_originals": 82, "planned_originals": 1418,
        "next_sequence": 83, "next_execution_id": "01a11705-11f1-792b-ae1e-36bfc6773842",
    }
    write_new(RUNTIME / "candidate-inventory.json", inventory)
    write_new(HERE / "candidate-inventory.json", inventory)
    archive = HERE / "v5-complete-continuation-review-candidate.tar.gz"
    with tarfile.open(archive, "x:gz") as outgoing:
        for name in sorted([*files, inventory_name]):
            outgoing.add(SOURCE / name, arcname=name, recursive=False)
    with tarfile.open(archive, "r:gz") as incoming:
        members = incoming.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)) or set(names) != set(files) | {inventory_name}:
            raise ValueError("ARCHIVE_CLOSURE_MISMATCH")
        for member in members:
            if not member.isfile() or member.name.startswith("/") or ".." in Path(member.name).parts:
                raise ValueError("UNSAFE_ARCHIVE_MEMBER")
            stream = incoming.extractfile(member)
            expected_digest = hash_file(RUNTIME / "candidate-inventory.json") if member.name == inventory_name else files[member.name]
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != expected_digest:
                raise ValueError("ARCHIVE_MEMBER_HASH_MISMATCH: " + member.name)
    for name, digest in files.items():
        if hash_file(SOURCE / name) != digest:
            raise ValueError("POST_PACKAGE_SOURCE_DRIFT: " + name)
    package = {
        "kind": "REVIEW_CANDIDATE_NOT_FREEZE", "version": "phase85-continuation-v5",
        "package_hash": package_hash, "archive_sha256": hash_file(archive),
        "archive_bytes": archive.stat().st_size,
        "inventory_sha256": hash_file(RUNTIME / "candidate-inventory.json"),
        "archive_members": len(files) + 1, "expanded_bytes": sum((SOURCE / n).stat().st_size for n in files),
        "parent_package_hash": parent["package_hash"], "parent_freeze_sha256": parent_freeze,
        "source": str(SOURCE), "accepted": False, "frozen": False, "launch_authorized": False,
    }
    write_new(HERE / "candidate-package.json", package)
    write_new(HERE / "final-verification.json", {
        "status": "PASS", "scope": "REVIEW_PACKAGE_NOT_LIVE_HOST_READINESS",
        "at_utc": datetime.now(UTC).isoformat(), **package,
        "archive_closure_and_every_member_hash": "PASS", "qualified_source_closure": "PASS",
        "parent_source_and_signed_freeze": "PASS", "Linux_mocked_controls": 22,
        "Linux_test_seconds": 73.52, "unsuccessful_attempts_retained": ["attempt1 preparation timeout"],
        "metadata_boundary": {"BACKED_UP": 82, "PLANNED": 1418, "active": 0, "original_identities": 1500,
                              "next_sequence": 83, "next_arm": "B3", "next_attempt": 1,
                              "next_execution_id": inventory["next_execution_id"]},
        "application_fixture_oracle_analysis_and_window_changes": 0,
        "shared_upload_client_changes": 0, "research_executions": 0, "AWS_started": False,
        "new_live_boot_qualified": False,
        "pending_deployment_gates": ["Explicit exact-package acceptance, freeze and deployment authorization",
              "Refreshed time/cost fit without reducing allowance", "Independent verified prestart preparation stop",
              "Actual source/runtime/ledger/all82backups/permissions/resources/timers and signed launch readiness"],
        "feasibility_evidence_sha256": hash_file(HERE / "feasibility.json"),
        "original_deadline": "2026-10-22T15:24:23.810674Z", "guard_usd": 55, "total_usd": 65,
    })
    print(json.dumps(package, indent=2))


if __name__ == "__main__":
    main()
