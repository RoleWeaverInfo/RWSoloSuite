import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from rwstudio.aurora import open_project
from rwstudio.authoring import seed
from rwstudio.storage import Store


class AuroraTests(unittest.TestCase):
 def test_launches_unique_editable_copy_without_overwriting_edits(self):
  with tempfile.TemporaryDirectory() as tmp,patch('rwstudio.aurora.sys.platform','win32'):
   root=Path(tmp);game=root/'Game with spaces';exe=game/'bin/win32/nwtoolset.exe';exe.parent.mkdir(parents=True);exe.touch()
   store=Store(root/'data');p=seed();area=p['areas'][0]
   build=store.root/'builds'/('a'*20);build.mkdir(parents=True);source=build/(p['module_name']+'.mod');source.write_bytes(b'compiled module')
   manifest=dict(build_id='a'*20,sha256=hashlib.sha256(source.read_bytes()).hexdigest())
   with patch('rwstudio.aurora.build_project',return_value=manifest),patch('rwstudio.aurora.install_dependencies') as deps,patch('rwstudio.aurora.subprocess.Popen') as launch:
    launch.return_value.pid=123
    first=open_project(p,area['id'],store,game,'compiler',root/'user')
    Path(first['module']).write_bytes(b'author edits')
    second=open_project(p,area['id'],store,game,'compiler',root/'user')
   self.assertNotEqual(first['module'],second['module'])
   self.assertEqual(Path(first['module']).read_bytes(),b'author edits')
   self.assertEqual(source.read_bytes(),b'compiled module')
   self.assertEqual(Path(second['module']).read_bytes(),source.read_bytes())
   self.assertEqual(launch.call_args.args[0],[str(exe.resolve()),str(Path(second['module']).resolve())])
   deps.assert_called_with(build,root/'user')
 def test_missing_toolset_or_area_does_not_build_or_launch(self):
  with tempfile.TemporaryDirectory() as tmp,patch('rwstudio.aurora.build_project') as build,patch('rwstudio.aurora.subprocess.Popen') as launch:
   p=seed();store=Store(Path(tmp)/'data')
   for area in (p['areas'][0]['id'],'missing'):
    with self.assertRaises(ValueError):open_project(p,area,store,tmp,'compiler',tmp)
   build.assert_not_called();launch.assert_not_called()
