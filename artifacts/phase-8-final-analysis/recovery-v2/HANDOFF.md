# One manual recovery handoff

Upload C:/Users/syeda/Downloads/cloud_recover_final_v2.py to /home/cloudshell-user.
Keep cloud_extract_final_v1.py and the entire original staging directory intact.

This explicitly records one additional pinned1129read after unknown transport
completion and first reads1130–1500. No research execution is retried. Do not run
v1 again. Do not run this command twice. The original16:40:05.249100UTC deadline
is preserved. Keep CloudShell active and press Enter at each50-archive prompt.

```bash
cd /home/cloudshell-user
printf '%s  %s\n' 'bdb1ed3791410dbdbeea1c50026d8e90179ea26ea7b2e537a312bf7f8271508d' 'cloud_recover_final_v2.py' | sha256sum -c - &&
python3 -B cloud_recover_final_v2.py --self-test &&
seconds=$(python3 -B cloud_recover_final_v2.py --remaining-seconds) &&
timeout --foreground --signal=TERM --kill-after=10s "${seconds}s" \
  python3 -B -u cloud_recover_final_v2.py --resume-once --recover-request-1129-once
```

Expected: hash OK,8tests OK, REUSING1128/1500, progressive VERIFIED1129...1500,
then JSONstatusPASS,records1500,bundle,bytes,sha256. No research scenarios execute.
On any failure/expiry, preserve the output and recovery-v2/failure.json if present.
Do not automatically rerun or reset the deadline. A hard environment termination
may leave no Python failure record; request files remain unresolved until checked.

On PASS, Actions > Download file:
/home/cloudshell-user/fyp-phase8-final-evidence-v1/final-records.tar.gz

Return the bundle and printed SHA256. Local read-only hash check:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Users\syeda\Downloads\final-records.tar.gz'
```
