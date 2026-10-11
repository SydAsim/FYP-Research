"""Inspect stopped offline-control data only; retain existing backup before readback."""
import subprocess
import tarfile
from pathlib import Path
from prepare import HERE, write

name='p85-v8-clock-boundary-remaining-attempt2'
process=subprocess.Popen(['docker','cp',name+':/tmp/cal-v8/.','-'],stdout=subprocess.PIPE)
assert process.stdout
paths=[]
with tarfile.open(fileobj=process.stdout,mode='r|') as source:
    for member in source:
        if len(Path(member.name).parts)<=2 or member.name.endswith('roundtrip.json') or (member.name.endswith('.tar.gz') and '/backup/' in member.name):
            paths.append({'name':member.name,'bytes':member.size})
assert process.wait()==0
write(HERE/'unfinished-metadata-paths.json',paths)
print(paths)
