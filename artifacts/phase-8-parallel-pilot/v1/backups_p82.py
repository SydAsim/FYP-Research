"""Read-only exported backup integrity; no restore or main-execution claim."""

import argparse
import gzip
import hashlib
import sqlite3
import sys
from pathlib import Path

# Relocated copy: preserve the 8.2 backup checks, adapt only import root.
parents = Path(__file__).resolve().parents
sys.path.insert(0, str(parents[3] if len(parents) > 3 else Path("/opt/fyp-phase8-linux-v1")))
from research.execution_setup.core import digest, immutable, load  # noqa: E402


def verify(root: Path) -> dict[str, int]:
    files = objects = checkpoints = dumps = 0
    for manifest_path in root.rglob("backup-manifest.json"):
        manifest = load(manifest_path)
        for name, expected in manifest["hashes"].items():
            path = manifest_path.parent / name
            if digest(path) != expected:
                raise ValueError(f"BACKUP_HASH_DRIFT: {path}")
            files += 1
            if name.endswith(".sql.gz"):
                with gzip.open(path) as handle:
                    if b"PostgreSQL database dump" not in handle.read(300):
                        raise ValueError(f"INVALID_SQL_DUMP: {path}")
                dumps += 1
        if (manifest_path.parent / "ledger.sqlite3").exists():
            path = manifest_path.parent / "ledger.sqlite3"
            with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as conn:
                if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("SQLITE_CHECKPOINT_CORRUPT")
            checkpoints += 1
        for obj in manifest["objects"]:
            path = manifest_path.parent.parent / "objects-v2" / obj["object"]
            if digest(path) != obj["compressed_hash"]:
                raise ValueError("COMPRESSED_OBJECT_HASH_DRIFT")
            with gzip.open(path) as handle:
                if hashlib.file_digest(handle, "sha256").hexdigest() != obj["raw_hash"]:
                    raise ValueError("RAW_OBJECT_HASH_DRIFT")
            objects += 1
    return {
        "manifest_file_hashes": files,
        "compressed_raw_object_pairs": objects,
        "sqlite_integrity_checks": checkpoints,
        "logical_postgres_dumps": dumps,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    immutable(args.output, {"checks": verify(args.root), "restoration_tested": False})
