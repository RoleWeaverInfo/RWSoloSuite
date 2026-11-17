import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from rwstudio.server import Application
from rwstudio.provider import Provider
from rwstudio.content import _obj,S
from rwstudio.authoring import blank

class ModelRoleTests(unittest.TestCase):
 def test_authoring_routes_and_bridge_use_separate_models(self):
  with tempfile.TemporaryDirectory() as tmp,patch('rwstudio.server.Bridge') as bridge:
   app=Application(Path(tmp));p=blank()
   self.assertEqual(app.provider.model,'gpt-5.6-luna');self.assertEqual(app.authoring_provider.model,'gpt-6-astra')
   self.assertEqual(app.authoring_provider.reasoning_effort,'medium')
   self.assertIs(bridge.call_args.args[2],app.provider)
   with patch('rwstudio.authoring_ai.generate',return_value={}) as generate:
    app.post('/api/author/generate',{'project':p});self.assertIs(generate.call_args.args[0],app.authoring_provider)
   with patch('rwstudio.design_tools.interpretation',return_value={}) as interpret:
    app.post('/api/design/interpret',{'project':p,'area_id':'starting_area','reference_index':0});self.assertIs(interpret.call_args.args[0],app.authoring_provider)
   with patch('rwstudio.design_tools.regenerate_room',return_value={}) as room:
    app.post('/api/design/room',{'project':p,'room_id':'arrival'});self.assertIs(room.call_args.args[0],app.authoring_provider)
   app.post('/api/settings',{'authoring_model':'gpt-6-astra','authoring_reasoning':'high'})
   self.assertEqual(app.provider.model,'gpt-5.6-luna');self.assertEqual(app.authoring_provider.reasoning_effort,'high')
   self.assertEqual(Application(Path(tmp)).authoring_provider.reasoning_effort,'high')
   with self.assertRaises(ValueError):app.post('/api/settings',{'authoring_reasoning':'invalid'})
 def test_reasoning_payload_changes_only_authoring_requests(self):
  response={'status':'completed','output':[{'content':[{'type':'output_text','text':'{"reply":"ok"}'}]}]}
  credentials=Mock();credentials.get.return_value='fake-test-key'
  for effort in (None,'medium'):
   provider=Provider('gpt-6-astra' if effort else 'gpt-5.6-luna',credentials=credentials,reasoning_effort=effort)
   with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as request:
    provider.request('test',{},_obj({'reply':S}),max_tokens=1400)
   body=json.loads(request.call_args.args[0].data)
   if effort:
    self.assertEqual(body['reasoning'],{'effort':'medium'});self.assertGreaterEqual(body['max_output_tokens'],32000);self.assertEqual(request.call_args.kwargs['timeout'],300)
   else:self.assertNotIn('reasoning',body);self.assertEqual(body['max_output_tokens'],1400)
