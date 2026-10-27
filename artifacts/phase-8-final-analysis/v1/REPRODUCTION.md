# Computational reproduction and preservation

The accepted computations have already run. Do not rerun collectors, scenarios,
or analysis into the completed output directories. No AWS credentials, model key,
active Codex chat or running campaign host is needed for the local analysis.

Prerequisites already verified on this computer:

- E:/p8v12/source, exact source package
  cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d.
- Frozen source archive on D:/FYP-ResearchBackups/continuation-v12/,
  SHA25660218b4a7b7a9ac5862b1792e28cd93e1fc2ea7b6bc163da12ef4576b6955e0b.
- Existing .venv-study-design/Scripts/python.exe: Python3.12.14; numpy2.3.5,
  scipy1.16.3, pandas2.3.3, statsmodels0.14.6 and patsy1.0.2.
- Original returned final-records.tar.gz,823115bytes, SHA256
  1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341.
- The retained source/authority verification records and first-two accepted
  timing sidecars; these are reused, not recreated or broadened.

The results ZIP contains outputs, input derivatives, adapters and integrity
records. It does not contain the complete pinned source/runtime or all1500raw
archives. Preserve those independent copies and their pinned backup versions.
No signing key or AWS credential belongs in the ZIP.

## Optional reproduction in a NEW directory (not executed again during closeout)

These commands use already available dependencies. New-Item refuses an existing
reproduction directory. They create a second computational analysis, never a
replacement research execution. Original data and first outputs remain intact.

```powershell
$repo = 'C:\Users\syeda\OneDrive\ドキュメント\ChatGPT\Final Year Project'
$repro = 'D:\FYP-ResearchBackups\phase8-analysis-reproduction-v1'
New-Item -ItemType Directory -Path $repro -ErrorAction Stop
$closeout = Join-Path $repo 'artifacts\phase-8-final-analysis\v1'
foreach ($name in @('prepare_dataset.py','run_analysis.py','source-verification.json','authority-verification.json','extraction-control.json','frozen-cases.json')) {
    Copy-Item -LiteralPath (Join-Path $closeout $name) -Destination $repro -ErrorAction Stop
}
Copy-Item -LiteralPath (Join-Path $closeout 'accepted-existing-sidecars') -Destination $repro -Recurse -ErrorAction Stop
& (Join-Path $repo '.venv-study-design\Scripts\python.exe') -B (Join-Path $repro 'prepare_dataset.py') --bundle 'C:\Users\syeda\Downloads\final-records.tar.gz' --sha256 '1d67c5adc39fc6ef6f9cfcaa32a910532be8a9faf824383946d5c2ed10426341'
& (Join-Path $repo '.venv-study-design\Scripts\python.exe') -B (Join-Path $repro 'run_analysis.py') --run
```

Raw row identities, grades, hashes and denominators must match. Counts and fixed
seed results are reproducible under the qualified runtime; optimizer rounding can
vary across platforms. started.json and runtime/elapsed timestamps intentionally
vary. Do not describe different timestamps as a replacement outcome.

Read FINAL_REPORT.md before interpreting any interval. Original helper claim
flags, censor labels and UNKNOWN outcomes remain restricted/preserved. The raw
CSV uses original timing labels; accepted-timing-rows.json is a separate view
using only the two historically accepted label-only sidecars.
