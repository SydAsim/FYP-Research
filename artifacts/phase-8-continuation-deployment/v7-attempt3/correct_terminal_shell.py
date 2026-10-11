from pathlib import Path
here=Path(__file__).resolve().parent
text=(here/'Check-Progress-v2.ps1').read_text(encoding='utf-8')
old="$payload = @{ commands = @([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'progress-v2.sh')).Replace(\"`r`n\", \"`n\")); executionTimeout = @('60') }"
new="$taskProgressBody = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'progress-v2.sh')).Replace(\"`r`n\", \"`n\")\n$taskBashCommand = \"bash -s <<'FYP_READ_ONLY_PROGRESS'`n\" + $taskProgressBody + \"`nFYP_READ_ONLY_PROGRESS`n\"\n$payload = @{ commands = @($taskBashCommand); executionTimeout = @('60') }"
assert old in text
text=text.replace(old,new)
with (here/'Check-Progress-v3.ps1').open('x',encoding='utf-8',newline='\n') as out:out.write(text)
with (here/'terminal-shell-correction.txt').open('x') as out:out.write('The reused terminal wrapper sent the read-only Bash body to the default SSM /bin/sh, which refused pipefail before any ledger read or mutation. Original wrapper and failed invocation retained. Separate wrapper v3 invokes Bash explicitly. The progress body remains identical to v2; no campaign or admission control changed.\n')
