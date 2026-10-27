"""Three finite offline controls. Synthetic provider files; never call AWS."""
import hashlib
import io
import json
from pathlib import Path
import random
import sqlite3
import sys
import tarfile
import time
import unittest

from cloud_extract_v2 import Budget, ByteGroup, ObjectSpec, Stop, extract_archive, make_bundle, refuse_existing_attempt

HERE = Path(__file__).resolve().parent
ATTEMPT = HERE / ("offline-controls-" + str(time.time_ns()))
ATTEMPT.mkdir()


class Controls(unittest.TestCase):
    def place(self, name):
        p = ATTEMPT / name
        p.mkdir()
        return p

    def test_01_normal_extraction_and_streamed_bundle(self):
        folder = self.place("normal")
        execution = "cal-cloud145-v2-only"
        checkpoint = json.dumps({"id": execution, "synthetic": True}).encode()
        export = json.dumps({"execution_id": execution, "failure": {
            "type": "SyntheticControlOnly", "detail": "not a research outcome", "traceback": "synthetic"}}).encode()
        source = folder / "provider-ledger.sqlite3"
        with sqlite3.connect(source) as db:
            db.executescript("""CREATE TABLE slots(sequence,case_id,arm,execution_id,state,deadline,attempt,error);
                CREATE TABLE events(n,at,body,previous,hash);
                CREATE TABLE checkpoints(execution_id,body,hash);""")
            at = "2026-10-12T00:00:00Z"
            body = json.dumps({"kind": "DRIVER_FAILURE", "execution_id": execution})
            h = hashlib.sha256((at + body + "GENESIS").encode()).hexdigest()
            db.execute("INSERT INTO events VALUES(1,?,?,?,?)", (at, body, "GENESIS", h))
            db.execute("INSERT INTO slots VALUES(1,'cal-control','B3',?,'FAILED',?,1,'synthetic')", (execution, at))
            db.execute("INSERT INTO checkpoints VALUES(?,?,?)", (execution, checkpoint.decode(), hashlib.sha256(checkpoint).hexdigest()))
        members = {"ledger.sqlite3": source.read_bytes(), f"executions/{execution}/export.json": export,
                   f"executions/{execution}/checkpoint.json": checkpoint}
        manifest = json.dumps({"files": {n: hashlib.sha256(b).hexdigest() for n, b in members.items()}}).encode()
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as tar:
            for name, data in {"manifest.json": manifest, **members}.items():
                info = tarfile.TarInfo("slot/" + name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        archive = stream.getvalue()
        root = folder / "staging"
        b = Budget(root, cap=8*1024**2, reserve=65536)
        with b.open("original145.tar.gz", len(archive)) as out:
            for offset in range(0, len(archive), 113):
                out.write(archive[offset:offset+113])
        spec = ObjectSpec("offline", "synthetic", "offline", len(archive), hashlib.sha256(archive).hexdigest(), execution)
        result = extract_archive(b, spec)
        self.assertEqual(result["status"], "VERIFIED_REQUIRED_RECORDS_READY")
        self.assertLessEqual(b.usage(), b.cap-b.reserve)
        with tarfile.open(root/"required-records.tar.gz") as tar:
            self.assertEqual(json.load(tar.extractfile(f"required/executions/{execution}/export.json"))["failure"]["type"], "SyntheticControlOnly")

    def test_02_prewrite_refusal_generated_records_and_bundle(self):
        folder = self.place("refusals")
        b = Budget(folder/"stream", cap=65536, reserve=16384)
        with b.open("partial.bin", 100000) as out:
            out.write(b"kept")
            with self.assertRaises(Stop):
                out.write(b"x"*65536)
        self.assertEqual((b.root/"partial.bin").read_bytes(), b"kept")
        with self.assertRaises(Stop):
            b.json("derived.json", {"value": "x"*1000}, group=ByteGroup(50))
        self.assertLessEqual(b.usage(), b.cap-b.reserve)
        b.json("failure.json", {"status":"STOPPED"}, emergency=True)
        self.assertLessEqual(b.usage(), b.cap)
        c = Budget(folder/"compressed", cap=300000, reserve=32768)
        c.mkdir("required")
        data = random.Random(20261012).randbytes(200000)
        with c.open("required/opaque.bin", len(data)) as out:
            out.write(data)
        with self.assertRaises(Stop):
            make_bundle(c)
        self.assertTrue((c.root/"required-records.tar.gz").exists())
        self.assertLessEqual(c.usage(), c.cap-c.reserve)
        self.assertEqual((c.root/"required/opaque.bin").read_bytes(), data)

    def test_03_existing_files_logs_metadata_and_attempts_counted(self):
        root = self.place("existing")
        old = {"historical.bin":b"h"*8192, "old.log":b"l"*4096, "metadata.json":b'{}'}
        for name,data in old.items():
            (root/name).write_bytes(data)
        b = Budget(root, cap=65536, reserve=16384)
        self.assertGreaterEqual(b.initial_usage, sum(len(v) for v in old.values()))
        with b.open("new.bin", 65536) as out:
            with self.assertRaises(Stop):
                out.write(b"x"*32768)
        for name,data in old.items():
            self.assertEqual((root/name).read_bytes(), data)
        b.json("attempt.json", {"old":"attempt"})
        with self.assertRaises(Stop):
            refuse_existing_attempt(b)
        self.assertEqual(json.loads((root/"attempt.json").read_text()), {"old":"attempt"})


if __name__ == "__main__":
    started=time.monotonic()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    record={"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
            "elapsed_seconds":time.monotonic()-started,"aws_calls":0,"synthetic_only":True,
            "python":sys.version,"source_sha256":hashlib.sha256((HERE/"cloud_extract_v2.py").read_bytes()).hexdigest()}
    (ATTEMPT/"result.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps(record,indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
