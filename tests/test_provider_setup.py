import io
import json
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock,patch

from rwstudio.builder import ROOT
from rwstudio.provider_setup import check_models,NoRedirect
from rwstudio.server import Application,Server


class ProviderSetupTests(unittest.TestCase):
    def test_metadata_checks_are_get_only_and_do_not_return_credentials(self):
        for provider,model in [('openai','gpt-6-luna'),('gemini','gemini-3.5-flash-lite')]:
            credentials=Mock();credentials.get.return_value='fake-private-test-key'
            data={'id':model} if provider=='openai' else {'name':'models/'+model,'supportedGenerationMethods':['generateContent']}
            opener=Mock();opener.open.return_value=io.BytesIO(json.dumps(data).encode())
            with patch('rwstudio.provider_setup.urllib.request.build_opener',return_value=opener):
                result=check_models(credentials,provider,[model,model])
            opener.open.assert_called_once();request=opener.open.call_args.args[0]
            self.assertEqual(request.get_method(),'GET');self.assertIsNone(request.data)
            self.assertNotIn('fake-private',request.full_url);self.assertNotIn('fake-private',json.dumps(result))
            self.assertEqual(result['models'],[model]);self.assertIn('does not verify',result['message'])
            credentials.get.assert_called_once_with(provider)

    def test_untrusted_names_and_missing_keys_cannot_trigger_network(self):
        credentials=Mock();credentials.get.return_value=''
        with patch('rwstudio.provider_setup.urllib.request.build_opener') as network:
            for provider,models in [('other',['valid']),('openai',[]),('openai',['valid']*3),('openai',['../key']),('openai',['https://bad.example']),('gemini',[None]),('openai','gpt-6-luna')]:
                with self.subTest(provider=provider,models=models),self.assertRaises(ValueError):check_models(credentials,provider,models)
            with self.assertRaisesRegex(ValueError,'Save a key'):check_models(credentials,'openai',['valid'])
            network.assert_not_called()

    def test_failures_are_sanitized_and_gemini_requires_generate_content(self):
        credentials=Mock();credentials.get.return_value='fake-private-test-key'
        for code in (401,403,404,429,500,302):
            opener=Mock();opener.open.side_effect=urllib.error.HTTPError('https://provider',code,'fake-private-test-key',{},io.BytesIO(b'fake-private-test-key'))
            with patch('rwstudio.provider_setup.urllib.request.build_opener',return_value=opener),self.assertRaises(ValueError) as error:check_models(credentials,'openai',['test-model'])
            self.assertNotIn('fake-private',str(error.exception))
        for raw in (b'not json',b'[]',b'{"name":"models/test-model","supportedGenerationMethods":["embedContent"]}'):
            opener=Mock();opener.open.return_value=io.BytesIO(raw)
            with patch('rwstudio.provider_setup.urllib.request.build_opener',return_value=opener),self.assertRaises(ValueError):check_models(credentials,'gemini',['test-model'])
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere'))

    def test_both_roles_checked_and_saved_provider_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp,patch('rwstudio.server.Bridge'):
            app=Application(temp);before=dict(app.config)
            with patch('rwstudio.provider_setup.check_models',return_value={'models':['first','second']}) as check:
                self.assertEqual(app.post('/api/credentials/check',{'provider':'gemini','models':['first','second']})['models'],['first','second'])
                check.assert_called_once_with(app.credentials,'gemini',['first','second'])
            self.assertEqual(app.config,before)

    def test_setup_page_and_check_require_local_session(self):
        with tempfile.TemporaryDirectory() as temp,patch('rwstudio.server.Bridge'):
            app=Application(temp);server=Server(('127.0.0.1',0),app)
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            url='http://127.0.0.1:'+str(server.server_port)
            try:
                for route in ('/?view=settings','/provider-setup.js','/player'):
                    with urllib.request.urlopen(url+route) as response:self.assertEqual(response.status,200)
                body=json.dumps({'provider':'gemini','models':['test-model']}).encode()
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(urllib.request.Request(url+'/api/credentials/check',data=body,headers={'Content-Type':'application/json'}))
                self.assertEqual(error.exception.code,403)
                with patch('rwstudio.provider_setup.check_models',return_value={'models':['test-model']}) as check:
                    request=urllib.request.Request(url+'/api/credentials/check',data=body,headers={'Content-Type':'application/json','X-Studio-Token':app.token})
                    with urllib.request.urlopen(request) as response:self.assertEqual(json.load(response)['models'],['test-model'])
                    check.assert_called_once()
            finally:server.shutdown();server.server_close();worker.join()

    def test_guided_setup_browser_logic(self):
        result=subprocess.run(['node','tests/provider_setup_checks.js'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
