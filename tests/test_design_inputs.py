import base64
import copy
import io
import json
import os
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import seed,validate
from rwstudio.authoring_ai import generate
from rwstudio.content import _obj,S
from rwstudio.provider import Provider,AIError
from rwstudio.credentials import Credentials
from rwstudio.reference_images import image_data
from rwstudio.custom_assets import AssetLibrary,archive,install_dependencies
from rwstudio.nwn.area_tools import pack_module
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read
from rwstudio.builder import ROOT,build_project,install_build
from rwstudio.storage import Store

PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')

class DesignInputTests(unittest.TestCase):
 def test_normal_sized_floorplan_is_not_rejected_by_text_limit(self):
  import zlib
  def chunk(kind,data):
   return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  pixels=b''.join(b'\0'+bytes((x+y)%256 for x in range(256*3)) for y in range(256))
  raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',256,256,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels,0))+chunk(b'IEND',b'')
  url='data:image/png;base64,'+base64.b64encode(raw).decode()
  self.assertGreater(len(url),12000)
  p=seed();a=p['areas'][0];a['references']=[dict(name='Throne room.png',notes='Grey stone throne room with a clerk’s desk, red upholstery and a side door near the dais.',data_url=url)]
  self.assertEqual(validate(p)['areas'][0]['references'][0]['data_url'],url)
  provider=Provider('unused')
  with patch.object(provider,'request',return_value=copy.deepcopy(p)) as request:
   result=generate(provider,p,'Use the uploaded throne-room plan','area',a['id'],0)
  self.assertEqual(request.call_args.kwargs['images'],[url])
  self.assertEqual(result['proposal']['areas'][0]['references'],a['references'])
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp));saved=store.save(p)
   self.assertEqual(saved['areas'][0]['references'][0]['data_url'],url)
  too_large=copy.deepcopy(p);too_large['areas'][0]['references'][0]['data_url']='data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'x'*2_000_000).decode()
  with self.assertRaises(ValueError):validate(too_large)
  bad_notes=copy.deepcopy(p);bad_notes['areas'][0]['references'][0]['notes']='x'*3001
  with self.assertRaises(ValueError):validate(bad_notes)
 def test_generate_from_one_floorplan_sends_selected_image_and_preserves_uploads(self):
  p=seed();a=p['areas'][0]
  a['references']=[dict(name='First.png',notes='Ignore for this generation',data_url=PNG),dict(name='Selected.png',notes='Kitchen west, door east',data_url=PNG)]
  provider=Provider('unused')
  with patch.object(provider,'request',return_value=copy.deepcopy(p)) as request:
   result=generate(provider,p,'Use this floor plan','area',a['id'],1)
  self.assertEqual(request.call_args.kwargs['images'],[PNG])
  context=request.call_args.args[1]
  self.assertEqual([r['name'] for r in context['reference_images']],['Selected.png'])
  self.assertTrue(context['floorplan_generation'])
  self.assertEqual(result['proposal']['areas'][0]['references'],a['references'])
  for index in (-1,2,True,'1'):
   with self.assertRaises(ValueError):generate(provider,p,'Use plan','area',a['id'],index)
 def test_floorplan_infers_settings_without_arranging_manual_defaults(self):
  p=seed();a=p['areas'][0];a['references']=[dict(name='Plan.png',notes='',data_url=PNG)]
  proposed=copy.deepcopy(p)
  # User's unfilled/default count must not control image interpretation.
  a['room_count']=16
  proposed['areas'][0]['width']=32
  proposed['areas'][0]['height']=32
  provider=Provider('unused')
  with patch.object(provider,'request',return_value=proposed),patch('rwstudio.authoring_ai.arrange',side_effect=AssertionError('Manual layout should not run')):
   result=generate(provider,p,'Infer from the image','area',a['id'],0)
  self.assertEqual(result['proposal']['areas'][0]['width'],32)
  self.assertEqual(result['proposal']['areas'][0]['height'],32)
  self.assertEqual(result['proposal']['areas'][0]['room_count'],len(proposed['areas'][0]['rooms']))
  self.assertFalse(any('Preserve the configured' in e for e in result['review']['errors']))
 def test_generate_selected_area_preserves_other_areas_and_story(self):
  p=seed();target=p['areas'][0];rooms={r['id'] for r in target['rooms']}
  proposed=copy.deepcopy(p)
  proposed['areas'][0]['description']='A carefully furnished hall'
  proposed['areas'][1]['name']='Unwanted change elsewhere'
  proposed['story']='Unwanted plot rewrite'
  for n in proposed['npcs']:
   n['personality']='New local personality' if n['room'] in rooms else 'Unwanted remote edit'
  provider=Provider('unused')
  with patch.object(provider,'request',return_value=proposed):
   result=generate(provider,p,'Design this area','area',target['id'])['proposal']
  self.assertEqual(result['areas'][0]['description'],'A carefully furnished hall')
  self.assertEqual(result['areas'][1:],p['areas'][1:])
  self.assertEqual(result['story'],p['story'])
  self.assertEqual(result['quests'],p['quests'])
  self.assertEqual([n for n in result['npcs'] if n['room'] not in rooms],[n for n in p['npcs'] if n['room'] not in rooms])
  self.assertEqual([c for c in result['connections'] if not(c['from_room'] in rooms and c['to_room'] in rooms)],[c for c in p['connections'] if not(c['from_room'] in rooms and c['to_room'] in rooms)])
  with self.assertRaises(ValueError):generate(provider,p,'Design','area','missing')
 def test_reference_image_validation_and_scope_preservation(self):
  p=seed();p['areas'][0]['references']=[dict(name='Labels.png',notes='North up; kitchen on west',data_url=PNG)]
  self.assertEqual(validate(p),p)
  provider=Provider('unused')
  with patch.object(provider,'request',return_value=seed()) as request:
   result=generate(provider,p,'Follow the floor plan','areas')
  self.assertEqual(request.call_args.kwargs['images'],[PNG])
  self.assertNotIn('data:image',json.dumps(request.call_args.args[1]))
  self.assertEqual(result['proposal']['areas'][0]['references'],p['areas'][0]['references'])
  for bad in ('https://example.com/p.png','data:image/svg+xml;base64,PHN2Zz4=',PNG.replace('image/png','image/jpeg')):
   with self.assertRaises(ValueError):image_data(bad)
 def test_gemini_transport_uses_header_images_and_validates_json(self):
  provider=Provider('gemini-2.5-flash','gemini')
  response={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"reply":"hello"}'}]}}],'usageMetadata':{'promptTokenCount':9,'candidatesTokenCount':3}}
  with patch.dict(os.environ,{'GEMINI_API_KEY':'fake-gemini-secret'}),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
   self.assertEqual(provider.request('instructions',{'request':'look'},_obj({'reply':S}),images=[PNG]),{'reply':'hello'})
  req=request.call_args.args[0];body=json.loads(req.data)
  self.assertNotIn('fake-gemini-secret',req.full_url);self.assertEqual(req.get_header('X-goog-api-key'),'fake-gemini-secret')
  self.assertEqual(body['contents'][0]['parts'][1]['inlineData']['mimeType'],'image/png')
  self.assertEqual(provider.usage['input_tokens'],9)
 def test_openai_vision_transport_keeps_schema_and_store_false(self):
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':'{"reply":"ok"}'}]}]}
  with patch.dict(os.environ,{'OPENAI_API_KEY':'fake-openai-secret'}),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
   Provider('test-model').request('instructions',{},_obj({'reply':S}),images=[PNG])
  body=json.loads(request.call_args.args[0].data)
  self.assertFalse(body['store']);self.assertEqual(body['input'][1]['content'][1]['type'],'input_image')
  self.assertEqual(body['text']['format']['type'],'json_schema')
 @unittest.skipUnless(os.name=='nt','Windows DPAPI')
 def test_saved_keys_are_encrypted_separate_and_removable(self):
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'OPENAI_API_KEY':'environment-fallback','GEMINI_API_KEY':''}):
   vault=Credentials(temp);vault.update('openai','test-secret-openai-123');vault.update('gemini','test-secret-gemini-123')
   self.assertNotIn('test-secret',vault.path.read_text())
   self.assertEqual(Credentials(temp).get('gemini'),'test-secret-gemini-123')
   self.assertNotIn('test-secret',json.dumps(vault.status()))
   vault.update('openai',remove=True);self.assertEqual(vault.get('openai'),'environment-fallback')

class AssetTests(unittest.TestCase):
 def make_pack(self,path):
  raw=pack_module((ROOT/'assets/base.mod').read_bytes(),{('placeables',2017):b'2DA V2.0\n\n Label ModelName\n8000 Test_Table plc_test\n',('plc_test',2002):b'test-model-placeholder'})
  path.write_bytes(b'HAK V1.0'+raw[8:]);return path
 def test_pack_discovery_checksum_and_corrupt_table(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);library=AssetLibrary(root/'studio');path=self.make_pack(root/'custom.hak')
   scanned=library.scan(str(path));self.assertEqual(scanned['assets'][0]['appearance'],8000)
   p=seed();p['custom_assets']=[scanned['assets'][0]];p['custom_placements']=[dict(id='custom_table',name='Test',room='guest_hall',asset_id=scanned['assets'][0]['id'],placement='north',description='')]
   self.assertEqual(validate(p),p);self.assertEqual(len(library.resolve(p)),1)
   library.resolve(p)[0][1].write_bytes(b'changed')
   with self.assertRaises(ValueError):library.resolve(p)
   broken=bytearray(path.read_bytes());struct.pack_into('<I',broken,16,999999)
   with self.assertRaises(ValueError):archive(bytes(broken))
 @unittest.skipUnless(GAME.exists(),'Installed NWN compiler/resources')
 def test_custom_appearance_build_packages_and_installs_dependencies(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);store=Store(root/'studio');library=AssetLibrary(store.root);scanned=library.scan(str(self.make_pack(root/'custom.hak')))
   p=seed();asset=scanned['assets'][0];p['custom_assets']=[asset];p['custom_placements']=[dict(id='custom_table',name='Test',room='guest_hall',asset_id=asset['id'],placement='north',description='')]
   m=build_project(p,store,GAME,ROOT/'vendor/nwnsc/nwnsc.exe');folder=Path(m['path']).parent
   r={(n,k):v for n,k,v in resources(Path(m['path']).read_bytes())}
   self.assertEqual(read(r['custom_table',2044])[1][1]['Appearance'][1],8000)
   self.assertEqual(len(read(r['module',2014])[1][1]['Mod_HakList'][1]),1)
   with zipfile.ZipFile(folder/(p['module_name']+'-aurora.zip')) as z:
    self.assertIn('hak/'+asset['pack']+'.hak',z.namelist());self.assertNotIn('credentials.json',' '.join(z.namelist()))
   user=root/'user';user.mkdir();install_build(store,m['build_id'],user)
   self.assertTrue((user/'hak'/(asset['pack']+'.hak')).is_file())
 def test_dependency_path_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'dependencies.json').write_text(json.dumps([{'file':'../bad.hak','sha256':'0'*64}]))
   with self.assertRaises(ValueError):install_dependencies(root,root/'user')
