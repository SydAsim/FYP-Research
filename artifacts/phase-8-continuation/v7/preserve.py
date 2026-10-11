from pathlib import Path
import json, hashlib

def verify_preserved() -> dict[str, int]:
    parent = Path("E:/p8v6/source")
    inv = json.loads((parent/"artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json").read_text())
    for name, digest in inv["files"].items():
        with (parent/name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("QUALIFIED_V6_SOURCE_DRIFT: " + name)
    return {"qualified_v6_members": len(inv["files"])}
