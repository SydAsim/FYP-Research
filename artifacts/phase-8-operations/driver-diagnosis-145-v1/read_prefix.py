"""Provisional triage only; complete archive hash verification remains required."""
import io
import json
import tarfile
from pathlib import Path, PurePosixPath

pieces = Path("E:/p8driver145v1/transport3/pieces")
data = bytearray()
index = 0
while (pieces / f"{index:08d}.bin").exists():
    data.extend((pieces / f"{index:08d}.bin").read_bytes())
    index += 1
out = Path("E:/p8driver145v1/provisional")
out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(data), mode="r|gz") as archive:
    for member in archive:
        if member.name.endswith("verified-master.tar.gz"):
            break
        name = PurePosixPath(member.name)
        assert not name.is_absolute() and ".." not in name.parts
        if member.isdir():
            (out / member.name).mkdir(parents=True, exist_ok=True)
        else:
            assert member.isfile() and member.size < 30 * 1024**2
            target = out / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                stream = archive.extractfile(member)
                assert stream is not None
                output.write(stream.read())
journal = json.loads((out / "inspection/campaign-journal.json").read_text())["stdout"]
with (out / "campaign-journal.txt").open("x") as output:
    output.write(journal)
lines = journal.splitlines()
hits = [i for i, line in enumerate(lines) if "18:06:53" in line or "Traceback" in line]
for i in hits:
    print("\n".join(lines[max(0, i-4):min(len(lines), i+65)]))
print("PROVISIONAL_PREFIX_ONLY_FULL_ARCHIVE_HASH_NOT_YET_VERIFIED")
