import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rwstudio.authoring import blank
from rwstudio.builder import ROOT
from rwstudio.server import Application
from rwstudio.storage import Store


class ProjectDeletion(unittest.TestCase):
    def test_removes_only_selected_saved_project(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);project=blank('delete_me','Delete me');store.save(project)
            build='a'*20;store.register_player_build(build,project)
            backup=store.root/'backups/delete_me-backup.json';backup.parent.mkdir();backup.write_text('backup')
            settings=store.root/'settings.json';settings.write_text('{}')
            result=store.delete('delete_me')
            self.assertFalse(store.path('delete_me').exists())
            self.assertEqual(result['deleted'],'delete_me')
            self.assertEqual([p['id'] for p in result['projects']],['area_workshop'])
            self.assertEqual(store.built_project(build),project)
            self.assertEqual(backup.read_text(),'backup');self.assertEqual(settings.read_text(),'{}')

    def test_invalid_ids_and_missing_files_do_not_delete_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);before=store.path('area_workshop').read_bytes()
            for ident in ('../settings','..\\settings','C:\\settings','area_workshop.json','missing','',None,[],'AREA_WORKSHOP'):
                with self.subTest(ident=ident),self.assertRaises(ValueError):store.delete(ident)
                self.assertEqual(store.path('area_workshop').read_bytes(),before)
            with patch.object(Path,'is_symlink',return_value=True),self.assertRaisesRegex(ValueError,'outside'):
                store.delete('area_workshop')
            self.assertEqual(store.path('area_workshop').read_bytes(),before)

    def test_last_project_stays_deleted_after_service_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);store.delete('area_workshop')
            self.assertEqual(Store(temp).list(),[])
            with patch('rwstudio.bridge.Bridge.start'):
                restarted=Application(temp)
            self.assertEqual(restarted.store.list(),[])

    def test_confirmation_required_and_permission_failure_preserves_file(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);app=type('TestApp',(),{'store':store})()
            for confirm in (None,False,'true',1):
                with self.assertRaisesRegex(ValueError,'Confirm'):
                    Application.post(app,'/api/project/delete',{'id':'area_workshop','confirm':confirm})
            with patch.object(Path,'unlink',side_effect=PermissionError('denied')),self.assertRaises(PermissionError):
                Application.post(app,'/api/project/delete',{'id':'area_workshop','confirm':True})
            self.assertTrue(store.path('area_workshop').is_file())

    def test_frontend_confirmation_success_failure_and_empty_workspace(self):
        result=subprocess.run(['node','tests/project_deletion_checks.js'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
