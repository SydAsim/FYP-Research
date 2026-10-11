from pathlib import Path
here=Path(__file__).resolve().parent
original=(here/'progress.sh').read_text(encoding='utf-8')
fixed=original.replace('from controls import read,utc','from controls import read,utc\nfrom operational_limits import effective_policy')
fixed=fixed.replace("read(root/'run.json')['policy']['stop_at']", "effective_policy(read(root/'run.json')['policy']).stop_at.isoformat()")
with (here/'progress-v2.sh').open('x',encoding='utf-8',newline='\n') as out:out.write(fixed)
human=(here/'Check-Progress.ps1').read_text(encoding='utf-8').replace("'progress.sh'","'progress-v2.sh'")
with (here/'Check-Progress-v2.ps1').open('x',encoding='utf-8',newline='\n') as out:out.write(human)
with (here/'progress-display-correction.txt').open('x') as out:out.write('Read-only display failure retained: raw policy does not contain stop_at; the deadline is a validated computed property. Separate display v2 uses effective_policy.stop_at. No admission, source, grade, authorization, or policy behaviour changed.\n')
