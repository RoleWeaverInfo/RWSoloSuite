import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from rwstudio import bundled_example as example
from rwstudio.storage import Store
from rwstudio.server import Application
from rwstudio.launcher import native_context
from rwstudio.nwn.analysis_formats import Archive


class BundledExampleTests(unittest.TestCase):
    def test_pinned_build_has_one_module_matching_profile_and_geometry(self):
        files=dict(example.checked_files());info=example.information()
        self.assertEqual([name for name in files if name.endswith('.mod')],['rw_ember_v3.mod'])
        self.assertEqual(native_context(files['rw_ember_v3.mod']),dict(build_id=info['build_id'],project_id='emberseal_demo'))
        module=Archive(files['rw_ember_v3.mod'])
        self.assertIn(b'!aisettings',module.get('sp_chat',2009))
        for name in ('aw_dlg_ui','aw_dlg_pref'):
            self.assertIn((name,2009),module.index)
        self.assertIn(('aw_dlg_evt',2010),module.index)
        p=json.loads(files['project.json'].read_text(encoding='utf-8'))
        sidecar=json.loads(files['rw_ember_v3.rwproject.json'].read_text(encoding='utf-8'))
        self.assertEqual(sidecar['project'],p);self.assertEqual(sidecar['build_id'],info['build_id'])
        self.assertEqual(len(p['areas']),3);self.assertEqual(sum(len(a['rooms']) for a in p['areas']),14)
        self.assertEqual(len(p['npcs']),15);self.assertTrue(all(a['references'] for a in p['areas']))
        self.assertTrue(all(n['behavior']['accept_visits'] and n['behavior']['social_enabled'] for n in p['npcs']))
        self.assertTrue(all(t['inspect_containers'] and t['social_visits'] for t in p['companions']['templates']))
        for dep in json.loads(files['dependencies.json'].read_text()):
            self.assertEqual(hashlib.sha256(files['hak/'+dep['file']].read_bytes()).hexdigest(),dep['sha256'])

    def test_fresh_workspace_loads_only_emberseal_and_download_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp),include_example=True);info=example.information()
            self.assertEqual([p['id'] for p in store.list()],['emberseal_demo'])
            self.assertEqual([b['build_id'] for b in store.builds()],[info['build_id']])
            folder=store.root/'builds'/info['build_id']
            with zipfile.ZipFile(folder/'rw_ember_v3-aurora.zip') as archive:
                names=archive.namelist();self.assertIsNone(archive.testzip())
                self.assertEqual([n for n in names if n.endswith('.mod')],['rw_ember_v3.mod'])
                self.assertIn('rw_ember_v3.rwproject.json',names);self.assertIn('EMBERSEAL.md',names)
                self.assertTrue(any(n.startswith('hak/') and n.endswith('.hak') for n in names))
                self.assertEqual(archive.read('rw_ember_v3.mod'),(folder/'rw_ember_v3.mod').read_bytes())
            store.delete('emberseal_demo')
            self.assertEqual(Store(Path(tmp),include_example=True).list(),[])

    def test_explicit_reload_backs_up_draft_and_preserves_other_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp),include_example=True)
            draft=store.get('emberseal_demo');draft['story']='My unsaved-in-release changes';store.save(draft)
            other=copy.deepcopy(draft);other['id']='my_own_project';other['module_name']='my_own_project';store.save(other)
            existing=store.path('emberseal_demo').read_bytes()
            result=example.install(store,replace=True)
            self.assertEqual(Path(result['backup']).read_bytes(),existing)
            self.assertNotEqual(store.get('emberseal_demo')['story'],draft['story'])
            self.assertEqual(store.get('my_own_project')['story'],draft['story'])

    def test_existing_workspace_is_not_replaced_on_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp));store.get('area_workshop')
            self.assertEqual([p['id'] for p in Store(Path(tmp),include_example=True).list()],['area_workshop'])
            self.assertEqual(store.builds(),[])

    def test_import_route_requires_confirmation_before_writes(self):
        app=type('App',(),{})()
        for confirm in (None,False,1,'true'):
            with self.assertRaisesRegex(ValueError,'Confirm'):
                Application.post(app,'/api/example/load',dict(confirm=confirm))

    def test_changed_bundle_checksum_is_rejected(self):
        original=Path.read_bytes
        def changed(path):
            if path==example.BUNDLE/'rw_ember_v3.mod':return b'changed'
            return original(path)
        with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'checksum'):
            example.checked_files()
