import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import urllib.request
from unittest.mock import Mock,patch
import zipfile
import package as release
from rwstudio import VERSION,service,server
from rwstudio.authoring import seed
from rwstudio.builder import ROOT
from rwstudio.storage import Store,write_json
from rwstudio.nwn.area_tools import pack_module
from rwstudio.player_package import write_checked


class ServiceStartupTests(unittest.TestCase):
    def state(self):return dict(version=VERSION,csrf='test-token',settings=dict(user_dir='user'),key_available=False)

    def test_reuses_service_without_key_requirement_or_game_launch(self):
        with patch.object(service.launcher,'state',return_value=self.state()),patch.object(service.launcher,'http') as http,patch.object(service.webbrowser,'open') as browser,patch('subprocess.Popen') as spawn:
            service.main([])
        http.assert_called_once_with('/api/bridge',{'enabled':True},'test-token');browser.assert_called_once_with('http://127.0.0.1:8766/startup');spawn.assert_not_called()

    def test_new_service_starts_only_server_and_player_mode_changes_splash_destination(self):
        with patch.object(service.launcher,'state',return_value=None),patch('rwstudio.server.serve') as serve,patch('subprocess.Popen') as spawn:
            service.main(['--player','--no-browser','--data','temporary-data'])
        serve.assert_called_once_with(Path('temporary-data'),open_browser=False,player=True,adventure=None);spawn.assert_not_called()
        self.assertEqual(service.startup_url(True,8767),'http://127.0.0.1:8767/startup?view=player')

    def test_old_service_is_rejected_before_registration_or_installation(self):
        with patch.object(service.launcher,'http') as http,patch.object(service,'install_adventure') as install:
            for version in ('0.19.0','0.20.0-rc1'):
                with self.assertRaisesRegex(ValueError,'older'):service.reuse(dict(self.state(),version=version))
        http.assert_not_called();install.assert_not_called()

    def test_fresh_server_enables_bridge_and_closes_resources_without_spawning_nwn(self):
        app=Mock();local=Mock();local.server_port=8767
        with patch.object(server,'Application',return_value=app),patch.object(server,'Server',return_value=local),patch.object(server.webbrowser,'open') as browser,patch('subprocess.Popen') as spawn:
            server.serve(Path('test-data'),port=8767,open_browser=True)
        self.assertTrue(app.bridge.enabled);local.serve_forever.assert_called_once();app.bridge.stop.set.assert_called_once();local.server_close.assert_called_once();browser.assert_called_once_with('http://127.0.0.1:8767/startup');spawn.assert_not_called()

    def test_shared_profile_checked_and_registered_without_replacing_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);p=seed();p['ai_conversations']=True;build='a'*20
            module=folder/(p['module_name']+'.mod');raw=('string SPProject(){return "'+p['id']+'";} string SPBuild(){return "'+build+'";}').encode()
            module.write_bytes(pack_module((ROOT/'assets/base.mod').read_bytes(),{('sp_config',2009):raw}));write_json(module.with_suffix('.rwproject.json'),dict(build_id=build,project=p))
            doc=service.adventure_document(module);store=Store(folder/'data');draft=dict(p,story='Author draft remains');store.save(draft)
            def http(route,body,token):
                if route=='/api/player/register':store.register_player_build(body['build_id'],body['project'])
            with patch.object(service.launcher,'http',side_effect=http),patch.object(service,'install_adventure') as install,patch('subprocess.Popen') as spawn:
                service.reuse(self.state(),module,open_browser=False)
            install.assert_called_once_with(module,'user');spawn.assert_not_called();self.assertEqual(store.get(p['id'])['story'],'Author draft remains');self.assertEqual(store.built_project(build),doc['project'])
            write_json(module.with_suffix('.rwproject.json'),dict(build_id='b'*20,project=p))
            with self.assertRaisesRegex(ValueError,'different module build'):service.adventure_document(module)
            module.with_suffix('.rwproject.json').unlink()
            with self.assertRaisesRegex(ValueError,'matching'):service.adventure_document(module)

    def test_install_blocks_running_game_and_does_not_require_game_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            user=Path(tmp);source=user/'source.mod';source.write_bytes(b'module')
            with patch.object(service.launcher,'game_running',return_value=True),patch.object(service.launcher,'install') as install:
                with self.assertRaisesRegex(ValueError,'Exit NWN'):service.install_adventure(source,user)
                install.assert_not_called()
            with patch.object(service.launcher,'game_running',return_value=False),patch.object(service.launcher,'install') as install:
                service.install_adventure(source,user)
                self.assertEqual(install.call_args.args[0]['installed'],str(user/'modules/source.mod'))


class ReleasePackageTests(unittest.TestCase):
    def test_clean_release_allowlist_branding_and_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=release.package(output=tmp);path=Path(result['package'])
            with zipfile.ZipFile(path) as archive:
                names=archive.namelist();prefix='Role-Weaver-Module-Studio/'
                for name in ('Start Role Weaver.cmd','Start-RoleWeaver.ps1','service.py','web/branding/splash.png','web/startup.html','vendor/nwnsc/nwnsc.exe'):
                    self.assertIn(prefix+name,names)
                self.assertFalse(any(n.startswith(prefix+'data/') or n.startswith(prefix+'examples/') or n.endswith(('credentials.json','settings.json','Play Adventure.cmd','Start-Adventure.ps1','/play.py')) for n in names))
                self.assertEqual(len(names),len(set(names)));self.assertIsNone(archive.testzip());self.assertIn(b'Python 3.10',archive.read(prefix+'README.md'))
                self.assertEqual(archive.read(prefix+'web/branding/splash.png'),(ROOT/'web/branding/splash.png').read_bytes())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),result['sha256']);self.assertIn(result['sha256'],path.with_suffix('.zip.sha256').read_text())

    def test_credential_scanner_catches_secret_across_chunk_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'candidate';key=b'fake-gemini-test-credential';path.write_bytes(b'x'*(1024*1024-7)+key+b'tail')
            with zipfile.ZipFile(Path(tmp)/'test.zip','w') as archive:
                with self.assertRaisesRegex(ValueError,'Credential'):write_checked(archive,path,'candidate',[key])

    def test_startup_assets_are_served_locally_with_image_mime_and_no_traversal(self):
        local=server.Server(('127.0.0.1',0),Mock());thread=threading.Thread(target=local.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(local.server_port)
        try:
            with urllib.request.urlopen(url+'/branding/splash.png') as response:
                self.assertEqual(response.headers.get_content_type(),'image/png');self.assertEqual(response.read(),(ROOT/'web/branding/splash.png').read_bytes())
            for route in ('/startup','/startup.js','/startup.css','/','/player'):
                with urllib.request.urlopen(url+route) as response:self.assertEqual(response.status,200)
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(url+'/branding/../../data/credentials.json')
        finally:local.shutdown();local.server_close();thread.join()

    def test_splash_readiness_transition_stay_and_failure(self):
        code=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
async function run(query,fail,stay){const elements={},timers=[],moved=[];for(const id of ['#startupStatus','#enterStudio','#stayOnSplash','#splashArt'])elements[id]={href:'/',getAttribute(){return this.href;},decode:async()=>{}};
const ctx={document:{querySelector:s=>elements[s]},location:{search:query,replace:x=>moved.push(x)},URLSearchParams,fetch:async()=>{if(fail)throw Error('offline');return {ok:true,json:async()=>({version:'test',key_available:false})};},setTimeout:f=>{timers.push(f);return 1;},clearTimeout:()=>timers.length=0};vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/startup.js','utf8'),ctx);await new Promise(r=>setImmediate(r));if(stay)elements['#stayOnSplash'].onclick({currentTarget:elements['#stayOnSplash']});for(const f of timers)f();return {elements,moved};}
(async()=>{let r=await run('',false,false);assert.deepEqual(r.moved,['/']);assert(r.elements['#startupStatus'].textContent.includes('Add your OpenAI or Gemini key'));r=await run('?view=player',false,false);assert.deepEqual(r.moved,['/player']);r=await run('',false,true);assert.equal(r.moved.length,0);r=await run('',true,false);assert.equal(r.moved.length,0);assert(r.elements['#startupStatus'].textContent.includes('Unable to reach'));})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        result=subprocess.run(['node','-e',code],cwd=ROOT,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
