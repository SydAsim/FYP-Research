"""Per-slot postflight: pinned transfer, archive/member checks, fresh short extraction."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from controls import read, write_new
from storage import ObjectProof, verify_continuation_metadata, verify_local
from transport import Receipt, S3Store, Store, download, extract


def recover(
    proof: ObjectProof, root: Path, store: Store | None = None, local_archive: Path | None = None
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    receipt = Receipt.model_validate(proof.model_dump())
    try:
        archive = local_archive or download(store or S3Store("fyp-research"), receipt, root / "t")
        verify_local(archive, proof.sha256)
        destination = root / "x"
        result = extract(archive, destination, proof.sha256)
        metadata = destination / "slot"
        if (metadata / "master").exists():
            metadata = metadata / "master"
        verify_continuation_metadata(metadata)
        write_new(
            root / "postflight-verified.json",
            {
                "object": proof.model_dump(),
                "extraction": result,
                "cleanup_authorized": False,
                "main_executions": 0,
            },
        )
        return destination
    except BaseException as error:
        write_new(
            root / f"postflight-failure-{time.time_ns()}.json",
            {"type": type(error).__name__, "retained_partial": True, "cleanup_authorized": False},
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proof", type=Path)
    parser.add_argument("short_root", type=Path)
    parser.add_argument("--local-archive", type=Path)
    args = parser.parse_args()
    value = read(args.proof)
    proof = ObjectProof.model_validate(value.get("cloud", value))
    print(recover(proof, args.short_root, local_archive=args.local_archive))


if __name__ == "__main__":
    main()
