"""Two genuine backup stages; never signs readiness, clears a pause, or starts a driver."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Literal

from controls import Journal, hash_file, read, write_new
from handover import ContinuationAuthority
from postflight import recover
from storage import Cloud, S3Cloud, final_backup, upload, verify_local


def verify_proof(root: Path, phase: Literal["prelaunch", "complete"], cloud: Cloud) -> None:
    from storage import ObjectProof

    record = read(root / f"{phase}-backup-proof.json")
    config = read(root / "run.json")
    receipts = Path(config["continuation"]["receipts"])
    required = {
        "run.json": hash_file(root / "run.json"),
        "restart-boundary.json": hash_file(root / "restart-boundary.json"),
        "CONTINUATION_FREEZE.json": hash_file(receipts / "CONTINUATION_FREEZE.json"),
    }
    if phase == "complete":
        required.update(
            {
                "continuation-readiness.json": hash_file(root / "continuation-readiness.json"),
                "CONTINUATION_LAUNCH.json": hash_file(receipts / "CONTINUATION_LAUNCH.json"),
            }
        )
    if (
        record["phase"] != phase
        or record["bindings"] != required
        or record["status"] != "VERIFIED_READBACK_NOT_AUTHORIZATION"
    ):
        raise ValueError("BACKUP_PROOF_BINDING_DRIFT")
    archive = Path(record["archive"])
    proof = ObjectProof.model_validate(record["cloud"])
    verify_local(archive, proof.sha256)
    cloud.verify(proof)
    if hash_file(Path(record["readback_record"])) != record["readback_sha256"]:
        raise ValueError("BACKUP_READBACK_PROOF_DRIFT")


def run(
    root: Path, destination: Path, phase: Literal["prelaunch", "complete"], cloud: Cloud
) -> None:
    config = read(root / "run.json")
    authority = ContinuationAuthority(root, config)
    authority.verify(prelaunch=phase == "prelaunch")  # before any backup or readiness write
    if phase == "complete":
        verify_proof(root, "prelaunch", cloud)
    archive = final_backup(Journal(root), destination, prelaunch=phase == "prelaunch")
    proof = upload(Journal(root), cloud, authority.policy, archive)
    # Fresh, bounded version-specific independent readback; no use of local_archive.
    output = destination / f"readback-{time.time_ns()}"
    recover(proof, output)
    authority.verify(prelaunch=phase == "prelaunch")
    receipts = Path(config["continuation"]["receipts"])
    bindings = {
        "run.json": hash_file(root / "run.json"),
        "restart-boundary.json": hash_file(root / "restart-boundary.json"),
        "CONTINUATION_FREEZE.json": hash_file(receipts / "CONTINUATION_FREEZE.json"),
    }
    if phase == "complete":
        bindings.update(
            {
                "continuation-readiness.json": hash_file(root / "continuation-readiness.json"),
                "CONTINUATION_LAUNCH.json": hash_file(receipts / "CONTINUATION_LAUNCH.json"),
            }
        )
    write_new(
        root / f"{phase}-backup-proof.json",
        {
            "phase": phase,
            "status": "VERIFIED_READBACK_NOT_AUTHORIZATION",
            "bindings": bindings,
            "archive": str(archive),
            "cloud": proof.model_dump(),
            "readback_record": str(output / "postflight-verified.json"),
            "readback_sha256": hash_file(output / "postflight-verified.json"),
        },
    )
    verify_proof(root, phase, cloud)
    Journal(root).event(
        "CONTINUATION_BACKUP_READBACK_VERIFIED", phase=phase, cloud=proof.model_dump()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prelaunch", "complete"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    config = read(args.root / "cloud.json")
    phase: Literal["prelaunch", "complete"] = args.phase
    run(args.root, args.destination, phase, S3Cloud(config["bucket"], config["prefix"]))


if __name__ == "__main__":
    main()
