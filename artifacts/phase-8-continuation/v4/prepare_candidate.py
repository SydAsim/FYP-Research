"""Finite local source assembly and read-only version-specific evidence retrieval."""
from __future__ import annotations

import hashlib
import base64
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PARENT = REPO / "artifacts/phase-8-runner-amendment/v3"
BASE = Path("E:/p8v4")
SOURCE = BASE / "source"
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
SNAPSHOT = Path("E:/FYP Project/p8-observation-20261008-1/x/inspection")
sys.path.insert(0, str(PARENT))
from controls import canonical, hash_file, read, write_new  # noqa: E402
from transport import Receipt, download, extract  # noqa: E402


class CLIStore:
    """Read-only Store adapter using the already configured AWS CLI."""

    def call(self, args: list[str]) -> dict[str, Any]:
        from uuid import uuid4
        result = subprocess.run(["aws", *args, "--profile", "fyp-research", "--region", "ap-southeast-2", "--no-cli-pager", "--output", "json"], capture_output=True, encoding="utf-8", timeout=60)
        write_new(BASE / "cli-reads" / f"{uuid4()}.json", {"args": args, "exit": result.returncode, "stderr": result.stderr, "result": result.stdout})
        if result.returncode:
            raise RuntimeError("VERSION_SPECIFIC_EVIDENCE_READ_FAILED")
        return json.loads(result.stdout)

    def head(self, receipt: Receipt) -> None:
        head = self.call(["s3api", "head-object", "--bucket", receipt.bucket, "--key", receipt.key, "--version-id", receipt.version_id, "--checksum-mode", "ENABLED"])
        if head.get("VersionId") != receipt.version_id or head["ContentLength"] != receipt.bytes or head.get("Metadata", {}).get("sha256") != receipt.sha256 or base64.b64decode(head["ChecksumSHA256"]).hex() != receipt.sha256:
            raise ValueError("S3_VERSION_SIZE_HASH_DRIFT")

    def read(self, receipt: Receipt, start: int, end: int) -> bytes:
        from uuid import uuid4
        target = BASE / "cli-pieces" / f"{uuid4()}.bin"
        target.parent.mkdir(exist_ok=True)
        reply = self.call(["s3api", "get-object", "--bucket", receipt.bucket, "--key", receipt.key, "--version-id", receipt.version_id, "--range", f"bytes={start}-{end}", str(target)])
        if reply.get("VersionId") != receipt.version_id or reply.get("ContentRange") != f"bytes {start}-{end}/{receipt.bytes}":
            raise ValueError("S3_RANGE_OR_VERSION_DRIFT")
        return target.read_bytes()


def extended(path: Path) -> Path:
    return Path("\\\\?\\" + str(path.resolve())) if sys.platform == "win32" else path


def main() -> None:
    resume = "--resume-assembly" in sys.argv
    BASE.mkdir(exist_ok=resume)
    parent = read(PARENT / "candidate-inventory.json")
    if hashlib.sha256(canonical(parent["files"])).hexdigest() != "2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736":
        raise ValueError("ACCEPTED_PARENT_INVENTORY_DRIFT")
    archive = PARENT.parent / "v3-combined-review-candidate.tar.gz"
    if hash_file(archive) != "0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf":
        raise ValueError("ACCEPTED_PARENT_ARCHIVE_DRIFT")
    if not resume:
        SOURCE.mkdir()
    with tarfile.open(archive) as incoming:
        for member in incoming:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts or not member.isfile():
                raise ValueError("UNSAFE_PARENT_MEMBER")
            target = extended(SOURCE.joinpath(*relative.parts))
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = incoming.extractfile(member)
            assert stream is not None
            if not resume:
                with target.open("xb") as output:
                    shutil.copyfileobj(stream, output)
    assert all(hash_file(extended(SOURCE / n)) == h for n, h in parent["files"].items())
    runtime = SOURCE / PREFIX
    if not resume:
        shutil.copytree(extended(SOURCE / "artifacts/phase-8-runner-amendment/v3"), extended(runtime))
        shutil.copyfile(REPO / "artifacts/phase-8-runner-amendment/v4/controls.py", runtime / "controls.py")
    seal = subprocess.run([
        "docker", "run", "--pull=never", "--network", "none", "--rm", "--memory", "256m",
        "sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8",
        "cat", "/opt/fyp-phase8-linux-v1/linux-package-seal.json"], capture_output=True, timeout=60, check=True).stdout
    if hashlib.sha256(seal).hexdigest() != "bfaf6a67ced678b45f5cfd911be8cefafcbf7725d45bbfb10be87ac472d7fb42":
        raise ValueError("PINNED_BOOTSTRAP_SEAL_DRIFT")
    if not resume:
        (SOURCE / "linux-package-seal.json").write_bytes(seal)
    assert (SOURCE / "linux-package-seal.json").read_bytes() == seal
    bootstrap = json.loads(seal)
    assert all(hash_file(extended(SOURCE / n)) == h for n, h in bootstrap["hashes"].items())
    boundary = runtime / "boundary"
    if not resume:
        shutil.copytree(SNAPSHOT, boundary)
    snapshot_proof = read(REPO / "artifacts/phase-8-observation/2026-10-08/evidence-readback.json")["proof"]
    if not resume:
        shutil.copyfile(Path("E:/FYP Project/p8-observation-20261008-1/evidence.tar.gz"), boundary / "authoritative-snapshot.tar.gz")
        write_new(runtime / "stopped-boundary-reference.json", snapshot_proof)
        write_new(runtime / "retained-boundary-members.json", read(SNAPSHOT / "manifest.json")["files"])
    ledger = read(SNAPSHOT / "ledger-read-only.json")
    rows = ledger["rows"]
    if not resume:
        write_new(runtime / "saved-boundary.json", {"rows": rows, "kind": "EXISTING_38_CLOSED_IDENTITIES_NO_GENERATION"})
    assert len(rows) == 1500 and rows[38]["sequence"] == 39 and rows[38]["arm"] == "B3"
    proofs: list[dict[str, Any]] = []
    store = CLIStore()
    for row in rows[:38]:
        receipt_file = SNAPSHOT / "backups" / (row["execution_id"] + ".json")
        receipt = read(receipt_file)
        if hash_file(receipt_file) != row["backup_hash"]:
            raise ValueError("AUTHORITATIVE_BACKUP_RECEIPT_DRIFT")
        proof = Receipt.model_validate(receipt["cloud"])
        attempt = BASE / "retained" / f"{row['sequence']:04d}"
        if (attempt / "t").exists() and not (attempt / "t/e.tar.gz").exists():
            attempt = BASE / "retained" / f"{row['sequence']:04d}-diagnostic-assembly3"
        archived = download(store, proof, attempt / "t", workers=2, chunk=1024**2, seconds=180)
        if not (attempt / "x").exists():
            extract(archived, attempt / "x", proof.sha256, max_bytes=1024**3)
        folder = attempt / "x/slot"
        manifest = read(folder / "manifest.json")
        if manifest.get("postgres_dumps") is not True or not {"setup_app.sql.gz", "setup_truth.sql.gz"}.issubset(manifest["files"]):
            raise ValueError("INCOMPLETE_RETAINED_BACKUP")
        if any(hash_file(folder / n) != h for n, h in manifest["files"].items()):
            raise ValueError("RETAINED_BACKUP_MEMBER_DRIFT")
        exported = folder / "executions" / row["execution_id"] / "export.json"
        retained_export = boundary / "exports" / f"{row['sequence']:04d}" / "export.json"
        if hash_file(exported) != hash_file(retained_export):
            raise ValueError("SNAPSHOT_EXPORT_BACKUP_MISMATCH")
        target = runtime / "retained-archives" / f"{row['sequence']:04d}.tar.gz"
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(archived, target)
        proofs.append({"identity": {k: row[k] for k in ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")},
                       "receipt_sha256": row["backup_hash"], "export_sha256": hash_file(exported),
                       "cloud": proof.model_dump(), "archive": f"retained-archives/{row['sequence']:04d}.tar.gz",
                       "manifest_sha256": hash_file(folder / "manifest.json"),
                       "members": manifest["files"], "postgres_dumps": True})
        print(f"Verified retained backup {row['sequence']}/38", flush=True)
    write_new(runtime / "retained-slot-proofs.json", proofs)
    write_new(HERE / "assembly-provenance.json", {"status": "PASS", "parent_package_hash": parent["package_hash"],
        "parent_archive_sha256": hash_file(archive), "parent_files": len(parent["files"]),
        "parent_freeze_sha256": "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86",
        "snapshot": snapshot_proof, "verified_archives": len(proofs), "source": str(SOURCE),
        "bootstrap_seal_sha256": hashlib.sha256(seal).hexdigest(), "bootstrap_members": len(bootstrap["hashes"]),
        "AWS_compute_started": False, "driver_calls": 0, "database_restores": 0})


if __name__ == "__main__":
    main()
