# Package existing results only

Upload C:/Users/syeda/Downloads/cloud_package_final_v3.py to /home/cloudshell-user.
Keep both old scripts and every existing record/attempt/failure file unchanged.
No extractors, network downloads or campaign executions run in this command.

```bash
cd /home/cloudshell-user
printf '%s  %s\n' 'e215465063681c12b942465be866861f479835c3ea3bebbb7c69dd024c074117' 'cloud_package_final_v3.py' | sha256sum -c - &&
python3 -B cloud_package_final_v3.py --self-test &&
timeout --foreground --signal=TERM --kill-after=10s 75s \
  python3 -B -u cloud_package_final_v3.py --package-only
```

Expected: hashOK,5testsOK, final JSONstatusPASS,records1500,network_requests0,
bundle path,bytes,sha256. No VERIFIED archive-download loop is started.
On failure preserve output; do not rerun either extractor or overwrite results.

On PASS use Actions > Download file:
/home/cloudshell-user/fyp-phase8-final-evidence-v1/final-records.tar.gz

Attach bundle plus its printed SHA256. Local hash verification:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\syeda\Downloads\final-records.tar.gz'
```
