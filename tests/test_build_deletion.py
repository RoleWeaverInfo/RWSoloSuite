import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rwstudio.authoring import blank
from rwstudio.builder import ROOT
from rwstudio.server import Application
from rwstudio.storage import Store,write_json


class BuildDeletion(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.project=self.store.save(blank('adventure','Adventure'))
        self.ident='a'*20;self.folder=self.make_build(self.ident)
        self.other=self.make_build('b'*20)

    def make_build(self,ident):
        self.store.register_player_build(ident,self.project)
        folder=self.store.root/'builds'/ident
        write_json(folder/'manifest.json',dict(build_id=ident,project_id=self.project['id']))
        (folder/'module.mod').write_bytes(b'module');(folder/'share.zip').write_bytes(b'zip')
        (folder/'source').mkdir();(folder/'source/script.nss').write_text('source')
        return folder

    def test_deletes_export_only_and_retains_runtime_registration(self):
        installed=self.store.root/'installed.mod';installed.write_bytes(b'installed')
        result=self.store.delete_build(self.ident)
        self.assertEqual(result,dict(deleted=self.ident,ai_profile_preserved=True))
        self.assertEqual([f.name for f in self.folder.iterdir()],['project.json'])
        self.assertEqual(self.store.built_project(self.ident),self.project)
        self.assertEqual(self.store.get('adventure'),self.project)
        self.assertEqual([b['build_id'] for b in self.store.builds()],['b'*20])
        self.assertEqual(installed.read_bytes(),b'installed')
        # Re-registering a deleted export does not resurrect its build-list entry.
        self.store.register_player_build(self.ident,self.project)
        self.assertEqual(len(self.store.builds()),1)
        with self.assertRaisesRegex(ValueError,'already'):self.store.delete_build(self.ident)

    def test_bad_ids_missing_manifest_and_wrong_identity_are_inert(self):
        for ident in ('../builds','..\\builds','',None,[],'A'*20,'c'*20):
            with self.subTest(ident=ident),self.assertRaises(ValueError):self.store.delete_build(ident)
        write_json(self.folder/'manifest.json',dict(build_id='b'*20,project_id='adventure'))
        with self.assertRaisesRegex(ValueError,'identity'):self.store.delete_build(self.ident)
        self.assertTrue((self.folder/'module.mod').is_file());self.assertTrue((self.other/'module.mod').is_file())

    def test_symlink_and_junction_rejected_before_any_deletion(self):
        real=Path.is_symlink
        for suspect in (self.store.root/'builds',self.folder,self.folder/'source/script.nss'):
            with self.subTest(path=suspect),patch.object(Path,'is_symlink',lambda p:p==suspect or real(p)),self.assertRaisesRegex(ValueError,'outside|linked'):
                self.store.delete_build(self.ident)
            self.assertTrue((self.folder/'module.mod').exists())
        real_stat=Path.lstat
        def reparse(path):
            if path==self.folder/'source':return type('Info',(),{'st_file_attributes':0x400,'st_mode':real_stat(path).st_mode})()
            return real_stat(path)
        with patch.object(Path,'lstat',reparse),self.assertRaisesRegex(ValueError,'linked'):
            self.store.delete_build(self.ident)
        self.assertTrue((self.folder/'module.mod').exists())

    def test_confirmation_and_failed_deletion_keep_listing_and_context(self):
        app=type('App',(),{'store':self.store})()
        for confirm in (None,False,1,'true'):
            with self.assertRaisesRegex(ValueError,'Confirm'):
                Application.post(app,'/api/build/delete',dict(build_id=self.ident,confirm=confirm))
        with patch.object(Path,'unlink',side_effect=PermissionError('File is open')),self.assertRaises(PermissionError):
            Application.post(app,'/api/build/delete',dict(build_id=self.ident,confirm=True))
        self.assertEqual(len(self.store.builds()),2)
        self.assertEqual(self.store.built_project(self.ident),self.project)

    def test_frontend_confirmation_refresh_failures_and_draft_preservation(self):
        result=subprocess.run(['node','tests/build_deletion_checks.js'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
