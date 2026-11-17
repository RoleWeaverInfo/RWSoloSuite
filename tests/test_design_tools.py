import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from types import SimpleNamespace
from rwstudio.authoring import seed,blank,validate
from rwstudio.design_tools import interpretation,apply_interpretation,edit_map,preserve_locks,regenerate_room,encounter_template,area_test_project
from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store

PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='

class DesignToolTests(unittest.TestCase):
 def test_update_area_saves_current_edits_and_builds_without_launching(self):
  from rwstudio.server import Application
  game=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights');compiler=ROOT/'vendor/nwnsc/nwnsc.exe'
  if not game.is_dir() or not compiler.exists():self.skipTest('Local NWN compiler unavailable')
  with tempfile.TemporaryDirectory() as tmp,patch('rwstudio.aurora.open_project') as launch:
   store=Store(Path(tmp));p=blank('updated_area');p['areas'][0]['rooms'][0].update(name='Edited hall',x=2,y=2,width=4)
   app=SimpleNamespace(store=store,config={'game_root':str(game),'compiler':str(compiler),'user_dir':tmp})
   result=Application.post(app,'/api/design/update-area',{'project':p,'area_id':'starting_area'})
   generated=store.built_project(result['build']['build_id'])
   self.assertEqual(generated['areas'],p['areas']);self.assertEqual(store.get(p['id'])['areas'],p['areas'])
   self.assertTrue(Path(result['build']['path']).is_file());self.assertFalse(generated['ai_conversations'])
   launch.assert_not_called()
 def test_interpretation_is_image_backed_layout_only_and_keeps_draft(self):
  p=blank();a=p['areas'][0];a['references']=[dict(name='Plan.png',notes='North up',data_url=PNG)]
  expected={'area':copy.deepcopy({k:v for k,v in a.items() if k!='references'}),'connections':[],'assumptions':['Scale estimated']}
  provider=Mock();provider.request.return_value=expected
  original=copy.deepcopy(p);result=interpretation(provider,p,a['id'],0)
  self.assertEqual(p,original);self.assertEqual(result,expected);self.assertEqual(provider.request.call_args.kwargs['images'],[PNG])
  proposal=apply_interpretation(p,a['id'],result)['proposal']
  self.assertEqual(proposal['areas'][0]['references'],a['references'])
  result['area']['rooms'][0]['id']='renamed'
  with self.assertRaisesRegex(ValueError,'Keep room IDs'):apply_interpretation(p,a['id'],result)
 def test_map_rejects_out_of_bounds_and_locks_without_mutating_source(self):
  p=blank();old=copy.deepcopy(p)
  with self.assertRaises(ValueError):edit_map(p,'arrival','move',{'x':100,'y':1})
  self.assertEqual(p,old)
  updated=edit_map(p,'arrival','move',{'x':2,'y':2})['project'];self.assertEqual(updated['areas'][0]['rooms'][0]['x'],2)
  p['locked_rooms']=['arrival']
  with self.assertRaisesRegex(ValueError,'Unlock'):edit_map(p,'arrival','resize',{'width':4,'height':4})
 def test_wall_connections_route_and_reject_duplicate_ports(self):
  p=blank();a=p['areas'][0];a['width']=16;a['rooms'][0].update(x=1,y=1,width=3,height=3)
  r=copy.deepcopy(a['rooms'][0]);r.update(id='second',name='Second',x=8);a['rooms'].append(r);a['room_count']=2
  values={'to_room':'second','from_side':'east','to_side':'west'}
  result=edit_map(p,'arrival','connect',values)
  self.assertEqual(result['project']['connections'][0]['kind'],'corridor')
  with self.assertRaisesRegex(ValueError,'already'):edit_map(result['project'],'arrival','connect',values)
 def test_locks_restore_geometry_content_and_connections(self):
  p=seed();rid=p['areas'][0]['rooms'][0]['id'];p['locked_rooms']=[rid];result=copy.deepcopy(p)
  result['areas'][0]['rooms'][0]['x']=7;result['areas'][0]['width']=30
  for n in result['npcs']:
   if n['room']==rid:n['name']='Changed'
  result['connections']=[]
  restored=preserve_locks(result,p)
  self.assertEqual(next(r for r in restored['areas'][0]['rooms'] if r['id']==rid),p['areas'][0]['rooms'][0])
  self.assertEqual([n for n in restored['npcs'] if n['room']==rid],[n for n in p['npcs'] if n['room']==rid])
  self.assertTrue(all(c in restored['connections'] for c in p['connections'] if rid in (c['from_room'],c['to_room'])))
  validate(restored)
 def test_room_regeneration_cannot_change_other_rooms_or_geometry(self):
  p=seed();rid=p['areas'][0]['rooms'][0]['id'];changed=copy.deepcopy(p)
  for n in changed['npcs']:n['personality']='Changed'
  changed['areas'][0]['width']=30
  with patch('rwstudio.authoring_ai.generate',return_value={'proposal':changed}):result=regenerate_room(Mock(),p,rid,'Improve furnishings')['proposal']
  self.assertEqual(result['areas'],p['areas']);self.assertEqual(result['quests'],p['quests'])
  self.assertEqual([n for n in result['npcs'] if n['room']!=rid],[n for n in p['npcs'] if n['room']!=rid])
 def test_templates_are_editable_native_encounters(self):
  p=blank()
  for kind in ('combat','ambush','puzzle','treasure','story'):
   result=encounter_template(p,'arrival',kind,'standard','My brief')['proposal'];e=result['encounters'][0]
   self.assertEqual(e['kind'],kind);self.assertEqual(e['description'],'My brief');validate(result)
   if kind=='puzzle':self.assertTrue(0<=e['answer']<len(e['options']))
  self.assertEqual(p['encounters'],[])
 def test_area_test_does_not_require_finished_story_or_modify_original(self):
  p=blank();original=copy.deepcopy(p);test=area_test_project(p,p['areas'][0]['id'])
  self.assertFalse(test['ai_conversations']);self.assertNotEqual(test['module_name'],p['module_name']);self.assertEqual(p,original);validate(test,complete=True)
  p=seed();test=area_test_project(p,p['areas'][0]['id']);self.assertEqual(len(test['areas']),1);validate(test,complete=True)
 def test_area_test_builds_native_module(self):
  game=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights');compiler=ROOT/'vendor/nwnsc/nwnsc.exe'
  if not game.is_dir() or not compiler.exists():self.skipTest('Local NWN compiler unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   p=area_test_project(blank(),'starting_area');manifest=build_project(p,Store(Path(tmp)),game,compiler)
   self.assertTrue(Path(manifest['path']).is_file())
 def test_test_area_endpoint_installs_without_launching_and_preserves_running_game(self):
  from rwstudio.server import Application
  with tempfile.TemporaryDirectory() as tmp:
   app=SimpleNamespace(store=Store(Path(tmp)),config={'game_root':'game','compiler':'compiler','user_dir':'user'})
   body={'project':blank(),'area_id':'starting_area'}
   with patch('rwstudio.launcher.game_running',return_value=True),patch('rwstudio.server.build_project') as build,patch('subprocess.Popen') as launch:
    with self.assertRaisesRegex(ValueError,'Save and exit'):Application.post(app,'/api/design/test-area',body)
    build.assert_not_called();launch.assert_not_called()
   with patch('rwstudio.launcher.game_running',return_value=False),patch('rwstudio.server.build_project',return_value={'path':str(Path(tmp)/'test.mod'),'build_id':'a'*20}) as build,patch('subprocess.Popen') as launch,patch('rwstudio.server.install_build',return_value={'installed':'user/modules/test.mod'}) as install:
    result=Application.post(app,'/api/design/test-area',body)
    launch.assert_not_called();install.assert_called_once_with(app.store,'a'*20,'user')
    self.assertFalse(build.call_args.args[0]['ai_conversations']);self.assertEqual(result['installed'],'user/modules/test.mod')
