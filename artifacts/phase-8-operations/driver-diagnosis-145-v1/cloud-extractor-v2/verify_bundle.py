"""Local-only verification. No AWS calls, campaign import, oracle or regrading."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tarfile

from cloud_extract_v2 import Budget, CAP, SPEC, Stop, file_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if bundle.stat().st_size > 16 * 1024**2 or file_hash(bundle) != args.sha256.lower():
        raise Stop("RETURN_BUNDLE_HASH_OR_SIZE_FAILED")
    directory = bundle.parent / "verified-cloud-v2"
    if directory.exists():
        raise Stop("EXISTING_LOCAL_VERIFICATION_NEVER_OVERWRITTEN")
    # Existing local staging files, not just this extraction, count toward 128 MiB.
    budget = Budget(bundle.parent)
    budget.mkdir(directory.name)
    with tarfile.open(bundle, "r:gz") as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
        if len(names) != len(set(names)) or len(members) > 32:
            raise Stop("RETURN_BUNDLE_DUPLICATE_OR_MEMBER_COUNT")
        total = 0
        for member in members:
            name = Path(member.name)
            if not member.isfile() or name.parts[0] != "required" or name.is_absolute() or ".." in name.parts:
                raise Stop("RETURN_BUNDLE_UNSAFE_MEMBER")
            total += member.size
            if total > 32 * 1024**2:
                raise Stop("RETURN_BUNDLE_EXPANSION_BOUND")
            with tar.extractfile(member) as source, budget.open(directory.name + "/" + member.name, member.size) as target:
                for block in iter(lambda: source.read(65536), b""):
                    target.write(block)
    root = directory / "required"
    proof = json.loads((root/"verification.json").read_text(encoding="utf-8"))
    manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    expected_members = {"required/" + n for n in set(proof["derived_files"]) | set(proof["members"])} | {"required/verification.json"}
    if set(names) != expected_members:
        raise Stop("UNACCOUNTED_RETURN_BUNDLE_MEMBER")
    if (proof["archive_sha256"], proof["archive_bytes"], proof["bucket"], proof["key"], proof["version_id"], proof["execution_id"]) != (SPEC.sha256, SPEC.size, SPEC.bucket, SPEC.key, SPEC.version, SPEC.execution):
        raise Stop("PINNED_ORIGINAL_PROOF_MISMATCH")
    if file_hash(root/"manifest.json") != proof["manifest_sha256"]:
        raise Stop("MANIFEST_HASH_MISMATCH")
    for name, digest in {**proof["derived_files"], **proof["members"]}.items():
        p = root / name
        if not p.resolve().is_relative_to(root.resolve()) or file_hash(p) != digest:
            raise Stop("RETURNED_MEMBER_HASH_MISMATCH")
    for name, digest in proof["members"].items():
        if manifest["files"][name] != digest:
            raise Stop("ORIGINAL_MEMBER_MANIFEST_MISMATCH")
    with sqlite3.connect((root/"ledger.sqlite3").resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise Stop("LOCAL_LEDGER_INTEGRITY")
        previous = "GENESIS"
        for number, at, body, prior, digest in db.execute("SELECT n,at,body,previous,hash FROM events ORDER BY n"):
            if prior != previous or hashlib.sha256((at+body+prior).encode()).hexdigest() != digest:
                raise Stop("LOCAL_LEDGER_EVENT_CHAIN")
            previous = digest
        for body, digest in db.execute("SELECT body,hash FROM checkpoints WHERE execution_id=?",(SPEC.execution,)):
            if hashlib.sha256(body.encode()).hexdigest() != digest:
                raise Stop("LOCAL_CHECKPOINT_HASH")
        row = db.execute("SELECT arm,attempt FROM slots WHERE execution_id=?",(SPEC.execution,)).fetchall()
        if row != [("B3",1)]:
            raise Stop("LOCAL_SLOT_IDENTITY")
    export = json.loads((root/f"executions/{SPEC.execution}/export.json").read_text(encoding="utf-8"))
    if export["execution_id"] != SPEC.execution:
        raise Stop("LOCAL_EXPORT_IDENTITY")
    result = {"status":"VERIFIED_LOCALLY", "bundle_sha256":args.sha256.lower(),
              "original_archive_sha256":SPEC.sha256, "verification_directory":str(directory),
              "execution_id":SPEC.execution, "failure":export.get("failure"),
              "evidence_scope":"Cloud extractor verified full pinned original; local verification checks returned bundle/member hashes and immutable ledger. No grades changed."}
    budget.json(directory.name+"/local-verification.json",result,maximum=16*1024**2)
    print(json.dumps({"status":result["status"],"verification_directory":str(directory),
                      "original_failure_type":(export.get("failure") or {}).get("type")},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
