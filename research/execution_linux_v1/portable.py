"""Read-only aliases for frozen Windows artifact references; never rewrite evidence JSON."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ensure_aliases() -> int:
    manifest = json.loads((ROOT / "linux-package-seal.json").read_text())
    count = 0
    for reference, canonical in manifest.get("reference_aliases", {}).items():
        # Only a single POSIX basename containing Windows separators is allowed.
        # Targets must already be hashed canonical files in this source capsule.
        if "/" in reference or "\\" not in reference or canonical not in manifest["hashes"]:
            raise ValueError("UNSAFE_REFERENCE_ALIAS")
        alias, target = ROOT / reference, ROOT / canonical
        if alias.is_symlink():
            if alias.resolve() != target.resolve():
                raise ValueError("REFERENCE_ALIAS_DRIFT")
        elif alias.exists():
            raise ValueError("REFERENCE_ALIAS_COLLISION")
        else:
            alias.symlink_to(canonical)
        count += 1
    return count


if __name__ == "__main__":
    print(f"Prepared {ensure_aliases()} file-reference aliases; frozen bytes unchanged")
