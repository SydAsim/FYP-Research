"""Prepare, but never execute, the post-acceptance freeze helper."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
text = (HERE.parent/'v5/freeze_accepted.py').read_text()
text = text.replace('v5', 'v7')
text = text.replace('cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c',
                    '95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26')
text = text.replace('phase-8-continuation-freeze/v4', 'phase-8-continuation-freeze/v5')
text = text.replace('len(sys.argv)==3', 'len(sys.argv)==4')
text = text.replace('from handover import FIRST_HASH, PARENT_FREEZE, verify_chain',
                    'from handover import FIRST_HASH, PARENT_FREEZE, verify_chain\nfrom operational_limits import LIMITS_SHA256, verified_limits')
text = text.replace('    inventory = read(CANDIDATE / "candidate-inventory.json")',
    '''    accepted = read(Path(sys.argv[3])) if len(sys.argv) == 4 else {}
    if (accepted.get("explicit_human_acceptance") is not True
        or accepted.get("package_hash") != PACKAGE
        or accepted.get("archive_sha256") != ARCHIVE
        or accepted.get("operational_limits_sha256") != LIMITS_SHA256
        or not accepted.get("verbatim_user_instruction")):
        raise ValueError("CURRENT_EXACT_HUMAN_ACCEPTANCE_REQUIRED")
    verified_limits()
    inventory = read(CANDIDATE / "candidate-inventory.json")''')
text = text.replace('"authority": "Explicit human instruction in this conversation, 9 October 2026",',
                    '"authority": accepted["verbatim_user_instruction"],\n        "operational_limits_sha256": LIMITS_SHA256,')
text = text.replace('"bounded read-only inventory retry", "guarded stopped-host reuse",',
    '"bounded read-only inventory retry", "guarded stopped-host reuse",\n                     "qualified v6 backup closure/order", "60USD admission/60GiB evidence proposal",\n                     "verified redundant future staging removal",')
text = text.replace('body = dict(kind=kind, package_hash=PACKAGE, predecessor_hash=predecessor,',
                    'body = dict(kind=kind, package_hash=PACKAGE, predecessor_hash=predecessor,\n                    operational_limits_sha256=LIMITS_SHA256,')
(HERE/'freeze_accepted.py').write_text(text)
# This preservation function is only called after human acceptance by the helper.
(HERE/'preserve.py').write_text('''from pathlib import Path
import json, hashlib

def verify_preserved() -> dict[str, int]:
    parent = Path("E:/p8v6/source")
    inv = json.loads((parent/"artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json").read_text())
    for name, digest in inv["files"].items():
        with (parent/name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("QUALIFIED_V6_SOURCE_DRIFT: " + name)
    return {"qualified_v6_members": len(inv["files"])}
''')
print('Prepared only; no receipt, acceptance, freeze or authorization recorded')
