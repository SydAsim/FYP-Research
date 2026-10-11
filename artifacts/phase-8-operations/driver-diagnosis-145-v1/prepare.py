"""Prepare bounded, evidence-only retrieval using the qualified pinned-range route."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
previous = here.parent / "clock-diagnosis-120-v1"
proof = json.loads((here.parent / "v9-stop-145-20261011/preservation-proof.json").read_text())
with (here / "inspection-receipt.json").open("x") as target:
    json.dump(proof["inspection"], target, indent=2)
body = (previous / "download_last_original.py").read_text()
start = body.index("proof = json.loads")
end = body.index("size = proof['bytes']")
body = body[:start] + "proof = json.loads((HERE/'inspection-receipt.json').read_text())\n" + body[end:]
body = body.replace("original120", "inspection")
with (here / "download_inspection.py").open("x", newline="\n") as target:
    target.write(body)
body = (previous / "extract_evidence.py").read_text()
body = body.replace("E:/p8clock120v1", "E:/p8driver145v1")
body = body.replace("7dbfc44f3df08717acd802cd6fda7b79c9e6e281cd87a7e4fbb423747ac59859", proof["inspection"]["sha256"])
body = body.replace("5892e3b90b577537c99720debd87726ed424c06b319f404edd60169a449ca7e7", proof["summary"]["master_backup"]["sha256"])
with (here / "extract_evidence.py").open("x", newline="\n") as target:
    target.write(body)
print("Evidence-only scripts prepared; no host, pause, source or campaign mutation")
