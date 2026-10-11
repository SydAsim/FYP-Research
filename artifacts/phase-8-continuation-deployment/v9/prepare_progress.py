from pathlib import Path
from ops import HERE

text=(HERE.parent/'v7-attempt3/Check-Progress-v3.ps1').read_text().replace('fyp-v7-progress-','fyp-v9-progress-')
with (HERE/'Check-Progress.ps1').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
old=(HERE.parent/'v7-attempt3/disable-preparation-timers.sh').read_text()
old=old.replace('continuation-v7','continuation-v9').replace('rows[82]','rows[120]').replace('01a11705-11f1-792b-ae1e-36bfc6773842','01a11705-11f1-75f4-b64e-8f0a3679518b').replace('sequence83_state','sequence121_state')
with (HERE/'verify-disable-owned-preparation-timers.sh').open('x',encoding='utf-8',newline='\n') as f:f.write(old)
print('Read-only terminal progress command and owned preparation timer checks prepared.')
