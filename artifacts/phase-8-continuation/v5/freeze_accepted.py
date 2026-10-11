"""Freeze the explicit v5 acceptance, without any AWS operation."""
from __future__ import annotations

import hashlib
import hmac
import json
import shutil
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CANDIDATE = REPO / "artifacts/phase-8-continuation/v5"
SOURCE = Path("E:/p8v5/source")
RUNTIME = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete"
sys.path.insert(0, str(RUNTIME))
from controls import Authority, Policy, canonical, hash_file, read, write_new
from handover import FIRST_HASH, PARENT_FREEZE, verify_chain
from two_originals import SECOND_HASH
IMMEDIATE_PARENT = "cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c"

PACKAGE = sys.argv[1] if len(sys.argv)==3 else "EXPECTED_ACCEPTED_PACKAGE_HASH_REQUIRED"
ARCHIVE = sys.argv[2] if len(sys.argv)==3 else "EXPECTED_ACCEPTED_ARCHIVE_HASH_REQUIRED"


def main() -> None:
    inventory = read(CANDIDATE / "candidate-inventory.json")
    archive = CANDIDATE / "v5-complete-continuation-review-candidate.tar.gz"
    if (read(CANDIDATE / "final-verification.json")["status"] != "PASS"
        or inventory["package_hash"] != PACKAGE
        or hashlib.sha256(canonical(inventory["files"])).hexdigest() != PACKAGE
        or hash_file(archive) != ARCHIVE):
        raise ValueError("ACCEPTED_EXACT_PACKAGE_MISMATCH")
    for name, digest in inventory["files"].items():
        if hash_file(SOURCE / name) != digest:
            raise ValueError("ACCEPTED_SOURCE_DRIFT: " + name)
    with tarfile.open(archive, "r:gz") as incoming:
        names = incoming.getnames()
        if len(names) != len(set(names)) or set(names) != set(inventory["files"]) | {
            "artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json"
        }:
            raise ValueError("ARCHIVE_CLOSURE_DRIFT")
        for name, digest in inventory["files"].items():
            stream = incoming.extractfile(name)
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != digest:
                raise ValueError("ARCHIVE_MEMBER_DRIFT: " + name)
        if json.load(incoming.extractfile("artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json")) != inventory:
            raise ValueError("ARCHIVED_INVENTORY_DRIFT")
    sys.path.insert(0, str(CANDIDATE))
    from preserve import verify_preserved
    protected = verify_preserved()
    owner = Path.home() / ".fyp-research/phase8-owner/phase84-final-v2"
    key = (owner / "owner.key").read_bytes()
    policy = Policy.model_validate(read(owner / "launch-policy.json"))
    Authority(SOURCE, SOURCE / "artifacts/phase-8-review-freeze/v2/review-inventory.json",
              policy, hash_file(SOURCE / "artifacts/phase-8-review-freeze/v2/schedule.json"),
              owner / "receipts", owner / "owner.key").verify()
    if hash_file(owner / "receipts/FREEZE.json") != PARENT_FREEZE:
        raise ValueError("ORIGINAL_FREEZE_DRIFT")
    parent = REPO / "artifacts/phase-8-continuation-freeze/v4"
    if sys.platform == "win32":
        parent = Path("\\\\?\\" + str(parent.resolve()))
    parent_manifest = read(parent / "freeze-manifest.json")
    attestation = read(parent / "freeze-attestation.json")
    if (hash_file(parent / "freeze-manifest.json") != IMMEDIATE_PARENT
        or attestation["manifest_sha256"] != IMMEDIATE_PARENT
        or not hmac.compare_digest(attestation["signature"], hmac.new(key, canonical(parent_manifest), "sha256").hexdigest())):
        raise ValueError("IMMEDIATE_PARENT_FREEZE_DRIFT")
    for name, digest in parent_manifest["files"].items():
        if hash_file(parent / name) != digest:
            raise ValueError("IMMEDIATE_PARENT_MEMBER_DRIFT")
    for kind in ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE"):
        raw = read(parent / (kind + ".json"))
        body = {k: v for k, v in raw.items() if k != "signature"}
        if not hmac.compare_digest(raw["signature"], hmac.new(key, canonical(body), "sha256").hexdigest()):
            raise ValueError("IMMEDIATE_PARENT_RECEIPT_SIGNATURE_DRIFT")
    frozen = REPO / "artifacts/phase-8-continuation-freeze/v5"
    if sys.platform == "win32":
        frozen = Path("\\\\?\\" + str(frozen.resolve()))
    receipts = Path.home() / ".fyp-research/phase8-owner/phase85-continuation-v5/receipts"
    frozen.mkdir(parents=True, exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=False)
    at = datetime.now(UTC).isoformat()
    statement = {
        "kind": "EXPLICIT_HUMAN_ACCEPTANCE", "at_utc": at,
        "package_hash": PACKAGE, "archive_sha256": ARCHIVE,
        "authority": "Explicit human instruction in this conversation, 9 October 2026",
        "accepted": ["qualified B3/P1/P2 refusals", "permissive response guard",
                     "82-original metadata handover", "qualified ledger snapshot correction", "bounded read-only inventory retry", "guarded stopped-host reuse", "separate timing sidecars", "unchanged pause/shutdown limitations"],
        "parent_freeze_sha256": PARENT_FREEZE, "immediate_parent_freeze_sha256": IMMEDIATE_PARENT,
        "first_export_sha256": FIRST_HASH, "second_export_sha256": SECOND_HASH,
        "acceptance_is_not_actual_launch": True,
    }
    write_new(frozen / "acceptance-statement.json", statement)
    shutil.copyfile(archive, frozen / archive.name)
    for name in ("candidate-inventory.json", "candidate-package.json", "final-verification.json", "REPORT.md"):
        shutil.copyfile(CANDIDATE / name, frozen / name)
    for name, digest in inventory["files"].items():
        target = frozen / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, target)
        if hash_file(target) != digest:
            raise ValueError("FREEZE_COPY_DRIFT")
    predecessor = hashlib.sha256(canonical(read(owner / "receipts/LAUNCH.json"))).hexdigest()
    anchor = predecessor
    identities = hash_file(RUNTIME / "saved-boundary.json")
    policy_hash = hashlib.sha256(canonical(policy.model_dump(mode="json"))).hexdigest()
    for kind in ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE"):
        body = dict(kind=kind, package_hash=PACKAGE, predecessor_hash=predecessor,
                    policy_sha256=policy_hash, identities_sha256=identities,
                    parent_freeze_sha256=PARENT_FREEZE, immediate_parent_freeze_sha256=IMMEDIATE_PARENT,
                    first_export_sha256=FIRST_HASH, second_export_sha256=SECOND_HASH,
                    expires_at=policy.stop_at.isoformat(), signer="Explicit human instruction recorded by local FYP operator",
                    readiness_sha256=None, instance_id=None)
        receipt = {**body, "signature": hmac.new(key, canonical(body), "sha256").hexdigest()}
        write_new(receipts / (kind + ".json"), receipt)
        shutil.copyfile(receipts / (kind + ".json"), frozen / (kind + ".json"))
        predecessor = hashlib.sha256(canonical(receipt)).hexdigest()
    verify_chain(receipts, key, PACKAGE, policy, identities, anchor, datetime.now(UTC), prelaunch=True)
    manifest = {
        "kind": "IMMUTABLE_COMBINED_CONTINUATION_FREEZE", "version": "phase85-continuation-v5",
        "created_at_utc": at, "package_hash": PACKAGE, "archive_sha256": ARCHIVE,
        "parent_freeze_sha256": PARENT_FREEZE, "immediate_parent_freeze_sha256": IMMEDIATE_PARENT,
        "files": {p.relative_to(frozen).as_posix(): hash_file(p) for p in frozen.rglob("*") if p.is_file()},
        "accepted": True, "frozen": True, "actual_host_bound": False, "main_continuation_started": False,
        "private_key_included": False,
    }
    write_new(frozen / "freeze-manifest.json", manifest)
    write_new(frozen / "freeze-attestation.json", {
        "kind": "LOCAL_OPERATOR_HMAC_FREEZE_ATTESTATION", "manifest_sha256": hash_file(frozen / "freeze-manifest.json"),
        "signature": hmac.new(key, canonical(manifest), "sha256").hexdigest(), "human_identity_signature_claimed": False,
    })
    if any(hash_file(frozen / n) != v for n, v in manifest["files"].items()):
        raise ValueError("FINAL_FREEZE_DRIFT")
    write_new(frozen / "freeze-verification.json", {
        "status": "PASS", "at_utc": datetime.now(UTC).isoformat(), "package_hash": PACKAGE,
        "archive_sha256": ARCHIVE, "parent_chain": "PASS", "continuation_chain": "PASS",
        "freeze_manifest_sha256": hash_file(frozen / "freeze-manifest.json"),
        "verified_members": len(manifest["files"]), "preservation": protected,
        "main_continuation_started": False,
    })
    for p in frozen.rglob("*"):
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps(read(frozen / "freeze-verification.json"), indent=2))


if __name__ == "__main__":
    main()
