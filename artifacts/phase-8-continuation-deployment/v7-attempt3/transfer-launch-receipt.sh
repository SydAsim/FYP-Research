set -euo pipefail
umask 077
python3 - <<'RECEIPT'
from pathlib import Path
p=Path('/var/lib/fyp-owner/continuation-v7-receipts/CONTINUATION_LAUNCH.json')
with p.open('x') as f:f.write('{\n  "kind": "CONTINUATION_LAUNCH",\n  "package_hash": "9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817",\n  "predecessor_hash": "4d74787679f29bc31b98705aa402b3272fb8f4ec2a0947aac65c4faa86e495d6",\n  "operational_limits_sha256": "60d8dbb2b7f3f6a83bd442ac491316e9a9e17d45a039e4b59d9400821d377791",\n  "policy_sha256": "87ff3ac98c8f7646ecd25ecb641e7ffd49e5008a1d0b3c8f97cca6a7d091e246",\n  "identities_sha256": "ab585ba36f9a78c5058916e412dca407d57db83a893c32018b60ff3d071838c0",\n  "parent_freeze_sha256": "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2",\n  "immediate_parent_freeze_sha256": "95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26",\n  "first_export_sha256": "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b",\n  "second_export_sha256": "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42",\n  "expires_at": "2026-10-22T15:24:23.810674+00:00",\n  "signer": "Explicit human instruction recorded by local FYP operator",\n  "readiness_sha256": "455c9bc866fff5a8ef5c9b0565e69e077c5769468a91956333eec23eba7bbfdb",\n  "instance_id": "i-057344e5372faf62f",\n  "signature": "1bee16586203dcfcc0af0c9be2928ab4625129ddf32eccfa3c4b6978799f452e"\n}\n')
p.chmod(0o600)
RECEIPT
