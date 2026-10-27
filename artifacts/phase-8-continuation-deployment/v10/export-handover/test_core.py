"""Eight finite synthetic filesystem/archive controls, not research executions."""
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from core import Identity, archive_record, atomic_exact, choose_exact, committed_local_record, digest, file_hash, publish_exact

class Checks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.identity=Identity(1,'cal-export-handover-only','B3',1,'a'*64)
        self.data=json.dumps({'execution_id':self.identity.execution_id,'arm':'B3','attempt':1,'fixture_hash':'a'*64,'status':'FAILED','grades':{'endpoint':'UNKNOWN'}}).encode()
    def tearDown(self):self.temp.cleanup()
    def archive(self, *, missing=False, bad_member=False):
        p=self.root/'original.tar.gz';member='executions/'+self.identity.execution_id+'/export.json'
        manifest=json.dumps({'files':{member:'0'*64 if bad_member else digest(self.data)}}).encode()
        with tarfile.open(p,'w:gz') as t:
            for name,b in ([('slot/'+member,self.data)] if not missing else [])+[('slot/manifest.json',manifest)]:
                item=tarfile.TarInfo(name);item.size=len(b);t.addfile(item,io.BytesIO(b))
        return p
    def test_normal_and_resume_identical(self):
        p=self.archive();b,h,m=archive_record(p,file_hash(p),p.stat().st_size,self.identity)
        staged=self.root/'stage/export.json';atomic_exact(staged,b,maximum_tree_bytes=1024**2,budget_root=self.root)
        target=self.root/'view/0001/export.json';publish_exact(staged,target,h);publish_exact(staged,target,h)
        self.assertEqual(target.read_bytes(),self.data);self.assertIn('export.json',m)
    def test_destination_collision(self):
        p=self.root/'existing.json';p.write_bytes(b'original conflicting bytes')
        with self.assertRaisesRegex(ValueError,'COLLISION'):atomic_exact(p,self.data,maximum_tree_bytes=1024**2,budget_root=self.root)
        self.assertEqual(p.read_bytes(),b'original conflicting bytes')
    def test_identity_failure(self):
        wrong=Identity(1,'other-original','B3',1,'a'*64)
        with self.assertRaisesRegex(ValueError,'IDENTITY'):wrong.check(self.data)
    def test_archive_hash_failure(self):
        p=self.archive()
        with self.assertRaisesRegex(ValueError,'ARCHIVE_HASH'):archive_record(p,'f'*64,p.stat().st_size,self.identity)
    def test_missing_required_member(self):
        p=self.archive(missing=True)
        with self.assertRaisesRegex(ValueError,'MISSING'):archive_record(p,file_hash(p),p.stat().st_size,self.identity)
    def test_member_hash_failure(self):
        p=self.archive(bad_member=True)
        with self.assertRaisesRegex(ValueError,'MEMBER_HASH'):archive_record(p,file_hash(p),p.stat().st_size,self.identity)
    def test_history_conflict(self):
        p=self.root/'historical.json';p.write_bytes(b'different retained evidence')
        with self.assertRaisesRegex(ValueError,'CONFLICTING'):choose_exact(self.data,digest(self.data),[p],self.identity)
    def test_partial_resume_and_capacity(self):
        p=self.root/'stage/export.json';p.parent.mkdir();tmp=p.with_name(p.name+'.partial-'+digest(self.data));tmp.write_bytes(self.data[:13])
        with self.assertRaisesRegex(ValueError,'CAPACITY'):atomic_exact(p,self.data,maximum_tree_bytes=20,budget_root=self.root)
        self.assertEqual(tmp.read_bytes(),self.data[:13]);atomic_exact(p,self.data,maximum_tree_bytes=1024**2,budget_root=self.root)
        self.assertEqual(p.read_bytes(),self.data)
    def test_frozen_history_without_cloud(self):
        p=self.root/'history/export.json';p.parent.mkdir();p.write_bytes(self.data)
        selected=committed_local_record([p],digest(self.data),self.identity)
        self.assertEqual(selected,(self.data,str(p)))
        self.assertIsNone(committed_local_record([self.root/'absent'],digest(self.data),self.identity))

if __name__=='__main__':unittest.main(verbosity=2)
