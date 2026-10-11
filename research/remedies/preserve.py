"""Hash historical pilot artifacts independently of the mutable working source."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/research-remedies/v2"


def inventory() -> dict[str, str]:
    paths = set((ROOT / "artifacts/phase-7-pilot/v1").rglob("*"))
    paths.update((ROOT / "artifacts").glob("phase-7-*"))
    paths.add(ROOT / "artifacts/research-readiness-audit.md")
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--after", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = OUTPUT / "historical-hashes-before.json"
    current = inventory()
    if args.after:
        original = json.loads(before.read_text(encoding="utf-8"))
        if original != current:
            raise ValueError("Historical evidence changed")
        target = OUTPUT / "historical-hashes-after.json"
    else:
        target = before
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8")) != current:
            raise ValueError("Refusing to overwrite a different preservation record")
    else:
        target.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verified_files": len(current), "record": str(target)}))


if __name__ == "__main__":
    main()
