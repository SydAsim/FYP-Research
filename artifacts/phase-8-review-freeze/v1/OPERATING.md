# Phase 8.4 review and evidence-only verification

Run from the repository in an ordinary terminal. No active Codex session is
required. There is intentionally no main launch or freeze command here.
The main scheduler still requires the guarded admission adapter and control
qualification listed in REVIEW.md. The old pilot script must not be used as
a substitute for a 500-input campaign command.

## Verify review files (PowerShell)

```powershell
.\.venv\Scripts\python.exe artifacts/phase-8-review-freeze/v1/verify_review.py
```

It checks the review inventory, historical hashes, 1,500 unstarted slots and
absence of acceptance/freeze/launch receipts. A failure means stop and retain
the evidence. Do not rewrite the inventory to make a failure pass.

## Regression checks

The existing separate analysis environment is required for SciPy/AFT checks;
the application's environment and uv.lock remain unchanged.

```powershell
$env:PYTHONPATH = (Resolve-Path '.venv-study-design/Lib/site-packages').Path
.\.venv\Scripts\python.exe -m pytest artifacts/phase-8-review-freeze/v1/test_transport.py artifacts/phase-8-review-freeze/v1/test_schedule.py tests/test_execution_setup.py tests/unit/test_phase8_candidate_v4.py tests/unit/test_readiness_v2.py artifacts/phase-8-aws-qualification/v3.1/test_integrity.py -q
.\.venv\Scripts\python.exe -m ruff check artifacts/phase-8-review-freeze/v1
.\.venv\Scripts\python.exe -m mypy artifacts/phase-8-review-freeze/v1/transport.py artifacts/phase-8-review-freeze/v1/build_review.py artifacts/phase-8-review-freeze/v1/qualify.py artifacts/phase-8-review-freeze/v1/verify_review.py --strict --follow-imports=silent --ignore-missing-imports
```

Linux process tests require Linux. The retained initial Docker image predates a
qualified Docker missing-container message fix; use the current protected Linux
module directory (which matches the preserved final source archive), read-only.
No Docker socket or AWS credentials are mounted for these platform tests.

```powershell
docker run --rm --pull=never --memory=1g --cpus=1 --mount 'type=bind,source=C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/artifacts/phase-8-linux-setup/v1,target=/qualification,readonly' --mount 'type=bind,source=C:/Users/syeda/OneDrive/ドキュメント/ChatGPT/Final Year Project/research/execution_linux_v1,target=/opt/fyp-phase8-linux-v1/research/execution_linux_v1,readonly' --network none fyp-phase8-linux-v1@sha256:57f0599663bac37f39ab491e99e23ebd478977ae654fad0451a5a0644f833826 python -m pytest /qualification/test_linux.py -q -p no:cacheprovider
```

## Evidence download or short-path extraction

Use a separate Python 3.12 environment with the pinned transport requirements.
AWS CLI profile `fyp-research` must be usable for versioned S3 read access. IAM
credentials remain in the local provider, outside source and receipts. The local
qualification used boto3/botocore 1.43.108 and pydantic 2.13.5. For saved oracle
replay, retain the application's locked dependencies and separate analysis
requirements from `research/study/requirements.txt` as well. Do not mix analysis
or AWS credentials into application service processes.

```powershell
py -3.12 -m venv E:/P84Transport
E:/P84Transport/Scripts/python.exe -m pip install -r artifacts/phase-8-review-freeze/v1/requirements.txt
E:/P84Transport/Scripts/python.exe artifacts/phase-8-review-freeze/v1/transport.py artifacts/phase-8-review-freeze/v1/pilot-receipt.json E:/P84TransportAttempt01
```

This last command only reads/extracts the **already completed pilot**. It starts
no business scenario or AWS service. Its 1,800s checkpoint deadline persists on
restart. Resume the same root and receipt before that deadline. Retain the stale
lock after confirming its exact process is gone; never clear a live lock. If a
piece is unproven or drifted, stop and retain it. To begin a separately labelled
transport attempt after expiration, use a new root, retain/link the old attempt,
and explicitly verify any pieces reused; no automatic deadline reset is supplied.
All attempts count toward storage accounting. There is no automatic cleanup in
this component.

For extraction of an existing verified archive without an S3 read:

```powershell
E:/P84Transport/Scripts/python.exe artifacts/phase-8-review-freeze/v1/transport.py artifacts/phase-8-review-freeze/v1/pilot-receipt.json E:/P84ExtractAttempt02 --local-archive E:/P83R7/p83-c525d267c8ec/b863ee5eec8a409373f67a09c55571e96746b05b4e5c6bc09218c7e1b02a03b7.tar.gz
```

Use new short roots. Existing or partial `x` trees are retained and rejected,
not overwritten. The full-size pilot qualification already saved in this package
used `E:/P84Q1/x` and retained all 24 unchanged independent replay results.
`qualify.py` is a one-shot retained check; do not rerun it into its existing output.

## Review → freeze → launch

Read REVIEW.md and its checklist. Acceptance must identify the concrete inventory
being accepted; edits create a new candidate version. Resolve the listed main
runtime/control checks before creating a launchable freeze. Then make a separate
immutable freeze receipt referencing the accepted inventory and verify it.
Launch requires a later, explicit user instruction bound to that freeze and budget.
Review acceptance is not spend or deployment authorization. No approval or receipt
is inferred by any command above.
