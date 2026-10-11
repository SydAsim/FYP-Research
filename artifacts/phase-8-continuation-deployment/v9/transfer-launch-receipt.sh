set -euo pipefail
umask 077
python3 - <<'RECEIPT'
from pathlib import Path
p=Path('/var/lib/fyp-owner/continuation-v9-receipts/CONTINUATION_LAUNCH.json')
with p.open('x') as f:f.write('{\n  "kind": "CONTINUATION_LAUNCH",\n  "package_hash": "5cbf273011c505984fe103955a94a256b1c84d1683de74cfa7a2a396cc223b60",\n  "predecessor_hash": "1f3f37b1aa7f7e835c7bb130241a24c3cdf196188309ea531d16fb0e67030baf",\n  "operational_limits_sha256": "b0349d0814cb519445a40cf430ee3f4aad50cf2d326509f96d6b59f36b4c44eb",\n  "policy_sha256": "87ff3ac98c8f7646ecd25ecb641e7ffd49e5008a1d0b3c8f97cca6a7d091e246",\n  "identities_sha256": "ab585ba36f9a78c5058916e412dca407d57db83a893c32018b60ff3d071838c0",\n  "parent_freeze_sha256": "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2",\n  "immediate_parent_freeze_sha256": "3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46",\n  "first_export_sha256": "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b",\n  "second_export_sha256": "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42",\n  "expires_at": "2026-10-22T15:24:23.810674+00:00",\n  "signer": "Explicit human instruction recorded by local FYP operator",\n  "readiness_sha256": "1e2f4ec2061ba3059ab54b18ddeb87059f160db0922cd974e00c991d9433306d",\n  "instance_id": "i-057344e5372faf62f",\n  "signature": "f72d0045c78d27e6195ccd257966542b69003d6a7c5bf16e3aad10182e6df851"\n}\n')
p.chmod(0o600)
RECEIPT
