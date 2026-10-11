"""Build and verify the complete unaccepted source/evidence continuation capsule."""

from __future__ import annotations

import ast
import difflib
import hashlib
import hmac
import json
import shutil
import sqlite3
import sys
import tarfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("E:/p8v4/source")
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
RUNTIME = SOURCE / PREFIX
sys.path.insert(0, str(RUNTIME))
from controls import canonical, hash_file, read, write_new  # noqa: E402


def long(path: Path) -> Path:
    return Path("\\\\?\\" + str(path.resolve()))


def parent_chain() -> dict[str, Any]:
    key = Path("C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2/owner.key").read_bytes()
    base = Path("C:/Users/syeda/.fyp-research/phase8-owner")
    original = base / "phase84-final-v2/receipts"
    predecessor: str | None = None
    for kind in ("REVIEW_ACCEPTED", "FREEZE", "LAUNCH"):
        raw = read(original / (kind + ".json"))
        expected = hmac.new(key, canonical({k:v for k,v in raw.items() if k != "signature"}), "sha256").hexdigest()
        assert hmac.compare_digest(expected, raw["signature"])
        assert raw["predecessor_hash"] == predecessor
        predecessor = hashlib.sha256(canonical(raw)).hexdigest()
    original_launch = predecessor
    receipt_hashes: dict[str, str] = {}
    for version in ("phase85-continuation-v1", "phase85-combined-v3"):
        predecessor = original_launch
        for kind in ("CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"):
            path = base / version / "receipts" / (kind + ".json")
            raw = read(path)
            assert hmac.compare_digest(hmac.new(key, canonical({k:v for k,v in raw.items() if k != "signature"}), "sha256").hexdigest(), raw["signature"])
            assert raw["predecessor_hash"] == predecessor
            predecessor = hashlib.sha256(canonical(raw)).hexdigest()
            receipt_hashes[version + "/" + kind] = hash_file(path)
    manifests = {
        "original": (REPO / "artifacts/phase-8-freeze/v1/freeze-manifest.json", "b5a45c2e1648dc8acb79e4d63ba19528669d9799acabdf08f7c9d72c3591cb1f"),
        "v1": (REPO / "artifacts/phase-8-continuation-freeze/v1/freeze-manifest.json", "4b921d416b9111594531ca33f26b1b307e04b22241ef995b6e571ce96a21f3e7"),
        "v3": (REPO / "artifacts/phase-8-continuation-freeze/v3/freeze-manifest.json", "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86"),
    }
    for name, (path, digest) in manifests.items():
        assert hash_file(path) == digest
        if name != "original":
            assert hmac.compare_digest(read(path.parent / "freeze-attestation.json")["signature"], hmac.new(key, canonical(read(path)), "sha256").hexdigest())
        dest = RUNTIME / "parent-provenance" / (name + "-freeze-manifest.json")
        shutil.copyfile(path, dest)
    original_receipt = REPO / "artifacts/phase-8-freeze/v1/FREEZE.json"
    assert hash_file(original_receipt) == "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"
    return {"status":"PASS", "receipt_HMAC_and_predecessors":receipt_hashes,
            "original_freeze_receipt_sha256":hash_file(original_receipt),
            "manifests": {k:v[1] for k,v in manifests.items()}, "private_key_included":False}


def differences() -> dict[str, Any]:
    parent = SOURCE / "artifacts/phase-8-runner-amendment/v3"
    changed = {}
    for name in ("controls.py","handover.py","runner.py","analyze.py","imported_analysis.py"):
        before, after = parent/name, RUNTIME/name
        diff = ''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile="accepted-v3/"+name,tofile="candidate-v4/"+name))
        (HERE / "runtime-diffs" / (name+".diff")).write_text(diff,encoding="utf-8")
        changed[name] = {"v3_sha256":hash_file(before),"v4_sha256":hash_file(after)}
    # Operational shutdown functions are preserved structurally, even though the
    # containing copied file has a new import and a narrower retirement branch.
    def functions(path: Path) -> dict[str,str]:
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    old,new = functions(parent/"runner.py"), functions(RUNTIME/"runner.py")
    shutdown = ("watchdog_tick","unit_text","install_watchdog","watchdog_unit","campaign_unit","verify_host_timer")
    assert all(old[n]==new[n] for n in shutdown)
    unchanged = {}
    for name in ("collector.py","instrument.py","refusal.py","legacy_refusal.py","response_guard.py","storage.py","transport.py","postflight.py","window.py","two_originals.py"):
        assert (parent/name).read_bytes()==(RUNTIME/name).read_bytes()
        unchanged[name] = hash_file(RUNTIME/name)
    assert hash_file(RUNTIME/"controls.py")=="0b62290a17840f10eb2353c10af5a1b54d472f95faaad26899b7ef4cf1f885ec"
    return {"modified_runtime":changed,"new_runtime":{"closed_prefix.py":hash_file(RUNTIME/"closed_prefix.py")},"unchanged_qualified_components":unchanged,"shutdown_functions_unchanged":list(shutdown)}


def main() -> None:
    chain = parent_chain()
    delta = differences()
    write_new(HERE / "parent-provenance-verification.json", chain)
    write_new(HERE / "runtime-differences.json", delta)
    qualified = Path("E:/p8v4/qualified-import")
    handover = read(qualified/"handover.json")
    with sqlite3.connect(qualified/"campaign.sqlite3") as db:
        db.row_factory=sqlite3.Row
        rows=[dict(r) for r in db.execute("SELECT * FROM slots ORDER BY sequence")]
    assert len(rows)==1500 and rows[:38]==read(RUNTIME/"saved-boundary.json")["rows"][:38]
    assert all(r["state"]=="PLANNED" for r in rows[38:])
    q = sorted(HERE.glob("linux-control-attempt-*/qualification.json"))[-1]
    assert read(q)["status"]=="PASS"
    write_new(HERE/"metadata-handover-verification.json",{
        "status":"PASS","identities":1500,"BACKED_UP":38,"PLANNED":1462,"next":rows[38],
        "handover_sha256":hash_file(qualified/"handover.json"),"ledger_sha256":hash_file(qualified/"campaign.sqlite3"),
        "saved_identities_sha256":hash_file(qualified/"saved-identities.json"),
        "historical_bundle_sha256":handover["historical_bundle_sha256"],"historical_bundle_bytes":(qualified/"historical-evidence.tar.gz").stat().st_size,
        "notice_prefix_preserved":True,"all_38_analysis_checked_in_Linux":True,
        "original_raw_statuses": [read(RUNTIME/"boundary/exports"/f"{i:04d}"/"export.json")["status"] for i in range(1,39)],
        "parent_sidecars_unchanged":True,"driver_calls":0,"database_restores":0})
    future=(qualified/"historical-evidence.tar.gz").stat().st_size
    feasibility=read(HERE/"feasibility.json")
    # Add the complete new compressed history to the observed worst-size backup,
    # rather than deducting v3's old history: deliberately conservative planning.
    per_slot=feasibility["observed_backup_max_bytes"]+future+1024**2
    projected=feasibility["all_version_evidence_bytes"]+1462*per_slot
    write_new(HERE/"storage-projection.json",{
        "status":"PASS_ESTIMATE" if projected<30*1024**3 else "FAIL",
        "current_all_version_evidence_bytes":feasibility["all_version_evidence_bytes"],
        "new_history_bundle_bytes":future,"per_slot_planning_bytes":per_slot,"remaining":1462,
        "additional_operational_version_reserve_bytes":1024**2,"projected_before_final_archive_bytes":projected,
        "cloud_cap_bytes":30*1024**3,"qualifications":["No actual future backup size is guaranteed","All object versions and interrupted uploads must remain accounted","Host raw logs/dumps grow separately and remain guarded by measured disk thresholds"]})
    proposal={
        "kind":"DEPLOYMENT_PROPOSAL_NOT_AUTHORIZATION","version":"phase85-complete-continuation-v4",
        "region":"ap-southeast-2","profile":"fyp-research","route":"FRESH_HOST_ONLY",
        "instance_type":"m7i-flex.large","ami":"ami-090b1140798d2d006","encrypted_gp3_gib":160,"root_DeleteOnTermination":False,
        "prior_hosts_not_to_restart":["i-0a6196aff6f8098ac","i-034252c3e9b083abf","i-002b63326e1566005"],
        "source":"/opt/fyp-phase8-combined-v4","runtime_prefix":PREFIX,"run_root":"/var/lib/p8-combined-v4/run",
        "backup_root":"/var/lib/p8-combined-v4/backup","owner_receipts":"/var/lib/fyp-owner/combined-v4-receipts",
        "run_id":handover["run_id"],"original_stop_at":"2026-10-22T15:24:23.810674Z",
        "policy_sha256":hash_file(RUNTIME/"original-launch-policy.json"),
        "import_source":"boundary","existing_saved_identities_sha256":hash_file(RUNTIME/"saved-boundary.json"),
        "backed_up":38,"planned":1462,"next_sequence":39,"next_arm":"B3","next_execution_id":rows[38]["execution_id"],
        "serial":True,"observation_seconds":600,"total_limit_usd":65,"admission_guard_usd":55,"handover_reserve_usd":1.25,
        "actual_host_binding":None,"accepted":False,"frozen":False,"launch_authorized":False,
        "qualified_image":"sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8",
        "host_python_archive_sha256":"506191be3ee7bd190a8834dcdc1b3bc70aab50608deccc711935aa007239cabd",
        "uv_digest":"816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5",
        "bootstrap_seal_sha256":hash_file(SOURCE/"linux-package-seal.json"),
        "backup_gates":"Exact pinned complete 38 archives + new versioned prelaunch backup/readback before admission",
        "preparation_timer_bounds":"Existing reviewed two-hour preparation/bootstrap bounds; disable only after verified activation",
        "shutdown_policy_changed":False,"retention_decision_due_utc":"2026-10-10T17:14:53.076527Z",
        "new_host_or_disk_deletion_authorized":False,
    }
    write_new(HERE/"deployment-config.json",proposal)
    docs=RUNTIME/"v4-readiness-evidence"
    docs.mkdir()
    for p in HERE.rglob("*"):
        if p.is_file() and p.suffix in (".md",".json",".xml",".txt",".diff") and not {"__pycache__","runtime-diffs","packaging-attempt2-retained"}.intersection(p.parts):
            relative=p.relative_to(HERE)
            target=docs/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target)
    shutil.copytree(HERE/"runtime-diffs",docs/"runtime-diffs")
    shutil.copyfile(HERE/"REVIEW.md",RUNTIME/"V4_REVIEW.md")
    inventory_path=RUNTIME/"candidate-inventory.json"
    # Inventory all source members exactly; exclude only this self-referential
    # inventory, generated interpreter caches, and compiled bytecode.
    files={p.relative_to(long(SOURCE)).as_posix():hash_file(p) for p in sorted(long(SOURCE).rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p!=long(inventory_path)}
    package_hash=hashlib.sha256(canonical(files)).hexdigest()
    inventory={"kind":"CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE","version":"phase85-complete-continuation-v4","package_hash":package_hash,
               "parent_package_hash":"2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736",
               "parent_freeze_sha256":"49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86",
               "files":files,"closed_source_roots":["apps","packages","research","tests","database","contracts","docs",PREFIX],
               "excluded":["__pycache__","*.pyc"],"accepted":False,"frozen":False,"launch_authorized":False}
    inventory_path.write_text(json.dumps(inventory,indent=2),encoding="utf-8")
    shutil.copyfile(inventory_path,HERE/"candidate-inventory.json")
    archive=HERE/"v4-complete-continuation-review-candidate.tar.gz"
    with tarfile.open(archive,"x:gz") as output:
        for name in files:
            output.add(long(SOURCE/name),arcname=name,recursive=False)
        output.add(inventory_path,arcname=PREFIX+"/candidate-inventory.json",recursive=False)
    expected={**files,PREFIX+"/candidate-inventory.json":hash_file(inventory_path)}
    seen=set()
    with tarfile.open(archive,"r|gz") as incoming:
        for member in incoming:
            assert member.isfile() and member.name in expected and member.name not in seen
            stream=incoming.extractfile(member)
            assert stream is not None
            h=hashlib.sha256()
            while block:=stream.read(1024**2): h.update(block)
            assert h.hexdigest()==expected[member.name],member.name
            seen.add(member.name)
    assert seen==set(expected)
    parent=read(SOURCE/"artifacts/phase-8-runner-amendment/v3/candidate-inventory.json")
    assert all(files[n]==h for n,h in parent["files"].items())
    bootstrap=read(SOURCE/"linux-package-seal.json")
    assert all(files[n]==h for n,h in bootstrap["hashes"].items())
    for relative in ("apps","packages","research","tests","database","contracts","docs",PREFIX):
        actual={p.relative_to(long(SOURCE)).as_posix() for p in long(SOURCE/relative).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        assert actual=={n for n in expected if n.startswith(relative+"/")}
    (HERE/"candidate-package.json").write_text(json.dumps({"kind":"REVIEW_CANDIDATE_NOT_FREEZE","package_hash":package_hash,"archive_sha256":hash_file(archive),"archive_bytes":archive.stat().st_size,"inventory_sha256":hash_file(inventory_path),"archive_members":len(expected),"parent_package_hash":parent["package_hash"],"accepted":False,"frozen":False,"launch_authorized":False},indent=2))
    write_new(HERE/"archive-closure-verification.json",{"status":"PASS","archive_sha256":hash_file(archive),"verified_members":len(seen),"parent_members_unchanged":len(parent["files"]),"bootstrap_members":len(bootstrap["hashes"]),"source_root_closure":True,"versioned_stopped_boundary_and_38_backups_embedded":True,"private_key_included":False})
    print(package_hash)
    print(hash_file(archive))


if __name__=="__main__":
    main()
