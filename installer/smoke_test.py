"""Exercise the real installer in an isolated workspace; never start NWN."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import winreg

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=r'Software\RoleWeaver\ModuleStudio'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)


def installed_directory():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,REGISTRY) as key:return Path(winreg.QueryValueEx(key,'InstallDir')[0]).resolve()
    except FileNotFoundError:return None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('setup',type=Path);parser.add_argument('--full-suite',action='store_true');args=parser.parse_args()
    if installed_directory() is not None:raise RuntimeError('An installed Studio is already registered. Do not overwrite it with the smoke test.')
    base=(ROOT/'data'/('installer-smoke-'+str(time.time_ns()))).resolve();app=base/'Program with spaces';workspace=base/'Retained workspace';user=base/'NWN user'
    assert base.is_relative_to((ROOT/'data').resolve())
    workspace.mkdir(parents=True);user.mkdir()
    (workspace/'settings.json').write_text(json.dumps({'user_dir':str(user)}),encoding='utf8')
    env=dict(os.environ,ROLEWEAVER_DATA_DIR=str(workspace),OPENAI_API_KEY='',GEMINI_API_KEY='',PYTHONHOME='no-external-python',PYTHONPATH='no-external-python',PATH=os.environ['WINDIR']+r'\System32;'+os.environ['WINDIR'])
    result={'test_folder':str(base),'setup':str(args.setup.resolve())};service=None;holder=None
    def run(command,log,timeout=45,check=True,environment=env):
        with (base/log).open('wb') as output:
            process=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=output,stderr=output,cwd=ROOT,env=environment,creationflags=FLAGS,timeout=timeout)
        if check and process.returncode:raise RuntimeError('Smoke test failed: '+log+' (exit '+str(process.returncode)+')')
        return process.returncode
    def setup(log):return [str(args.setup.resolve()),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/NOICONS','/TASKS=','/DIR='+str(app),'/LOG='+str(base/log)]
    def request(path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Studio-Token']=token
        req=urllib.request.Request('http://127.0.0.1:8767'+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        with urllib.request.urlopen(req,timeout=4) as response:return json.load(response)
    try:
        run(setup('install.log'),'install-output.log');assert installed_directory()==app
        python=app/'runtime/python.exe';launcher=app/'Role Weaver Module Studio.exe'
        print('Installed in an isolated folder.',flush=True)
        run([str(launcher),'--runtime-info'],'runtime-info.json')
        info=json.loads((base/'runtime-info.json').read_text());assert Path(info['executable'])==python and Path(info['data'])==workspace
        result['python']=info['python'];result['bundled_launcher']='passed without external Python paths'
        # Genuine installed code and native libraries, with only a deliberately fake test key.
        code="from rwstudio.credentials import Credentials; from rwstudio.paths import default_data; import ssl,sqlite3; c=Credentials(default_data()); c.update('openai','installer-test-key-not-a-real-secret'); assert c.get('openai')=='installer-test-key-not-a-real-secret'; ssl.create_default_context(); sqlite3.connect(':memory:').execute('select 1'); print('Native runtime dependencies and encrypted test key passed')"
        run([str(python),'-B','-c',code],'native-runtime.log')
        key_file=workspace/'credentials.json';key_hash=hashlib.sha256(key_file.read_bytes()).hexdigest()
        output=(base/'service.log').open('wb')
        service=subprocess.Popen([str(python),'-B',str(app/'studio.py'),'--port','8767'],env=env,cwd=app,stdin=subprocess.DEVNULL,stdout=output,stderr=output,creationflags=FLAGS)
        state=None
        for _ in range(40):
            try:state=request('/api/state');break
            except OSError:
                if service.poll() is not None:raise RuntimeError('Installed service exited; inspect service.log')
                time.sleep(.25)
        assert state and state['bridge']['enabled'] and len(state['projects'])==1
        project=request('/api/project?id=area_workshop')['project'];project['title']='Retained installer test project'
        request('/api/project/save',{'project':project},state['csrf'])
        sentinel=workspace/'projects/area_workshop.json';saved=sentinel.read_bytes()
        for route in ('/startup','/branding/splash.png','/player'):
            with urllib.request.urlopen('http://127.0.0.1:8767'+route,timeout=4) as response:assert response.status==200
        service.terminate();service.wait(timeout=10);service=None;output.close()
        result['installed_service']='passed';print('Bundled service and saved workspace passed.',flush=True)
        # Build a real module using only the installed application and its compiler.
        code="from rwstudio.authoring import blank; from rwstudio.design_tools import area_test_project; from rwstudio.builder import build_project; from rwstudio.storage import Store; from rwstudio.paths import default_data; from rwstudio.server import defaults; from pathlib import Path; c=defaults(); assert c['game_root']; p=area_test_project(blank('installer_probe','Installer probe'),'starting_area'); p['module_name']='rw_setup_probe'; b=build_project(p,Store(default_data()),c['game_root'],c['compiler']); assert Path(b['path']).is_file(); print('Installed runtime built '+b['module'])"
        run([str(python),'-B','-c',code],'installed-native-build.log',timeout=150)
        result['installed_native_module_build']='passed'
        if args.full_suite:
            print('Running regression suite under bundled Python.',flush=True)
            code="import sys,unittest; sys.path.insert(0,"+repr(str(ROOT))+"); result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests')); raise SystemExit(not result.wasSuccessful())"
            # The repo tests need Node and normal developer tools on PATH; the
            # separate launcher/service probes above used only Windows PATH.
            test_env=dict(os.environ,OPENAI_API_KEY='',GEMINI_API_KEY='')
            test_env.pop('ROLEWEAVER_DATA_DIR',None)
            run([str(python),'-B','-c',code],'bundled-python-regressions.log',timeout=420,environment=test_env)
            result['bundled_python_regressions']='passed'
        # Hold the real application's mutex without touching the primary service.
        code="from rwstudio.installation import service_lock; import time;\nwith service_lock():\n print('ready',flush=True)\n time.sleep(45)"
        holder=subprocess.Popen([str(python),'-B','-c',code],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,creationflags=FLAGS)
        assert holder.stdout.readline().strip()=='ready'
        blocked=run(setup('blocked-upgrade.log'),'blocked-upgrade-output.log',check=False)
        assert blocked!=0 and 'running' in (base/'blocked-upgrade.log').read_text(encoding='utf-8-sig').lower()
        holder.terminate();holder.wait(timeout=10);holder=None;result['running_service_blocks_upgrade']='passed'
        run(setup('upgrade.log'),'upgrade-output.log')
        assert sentinel.read_bytes()==saved and hashlib.sha256(key_file.read_bytes()).hexdigest()==key_hash
        run([str(launcher),'--runtime-info'],'upgraded-runtime-info.json');result['reinstall_preserves_data']='passed'
        # Exercise the actual exported bootstrap with no discoverable Python.
        # A temporary diagnostic entry script prevents installation into the
        # primary service's real NWN folder; the launcher/runtime stay genuine.
        module=next((workspace/'builds').glob('*/rw_setup_probe.mod'))
        script=app/'service.py';original=script.read_bytes()
        try:
            script.write_text("import json,sys; print(json.dumps({'args':sys.argv[1:],'python':sys.executable}))",encoding='utf8')
            bootstrap_env=dict(env,LOCALAPPDATA=str(base/'No external Python installed'))
            powershell=str(Path(os.environ['WINDIR'])/'System32/WindowsPowerShell/v1.0/powershell.exe')
            run([powershell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(module.parent/'Start-RoleWeaver.ps1'),'-AdventurePath',str(module),'-Player','-NoBrowser'],'adventure-bootstrap.json',environment=bootstrap_env)
            forwarded=json.loads((base/'adventure-bootstrap.json').read_text(encoding='utf-8-sig'))
            assert Path(forwarded['python'])==python
            assert forwarded['args']==['--adventure',str(module),'--player','--no-browser']
            result['shared_adventure_detects_installation']='passed without external Python'
        finally:script.write_bytes(original)
        result['nwn_launched']=False
    finally:
        for process in (service,holder):
            if process is not None and process.poll() is None:process.terminate();process.wait(timeout=10)
        # Only uninstall this test's exact registered location inside its workspace.
        if installed_directory()==app and app.resolve().is_relative_to(base):
            uninstaller=app/'unins000.exe'
            if uninstaller.is_file():run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(base/'uninstall.log')],'uninstall-output.log')
    assert installed_directory() is None and not (app/'Role Weaver Module Studio.exe').exists()
    assert sentinel.read_bytes()==saved and hashlib.sha256(key_file.read_bytes()).hexdigest()==key_hash
    result['uninstall_preserves_data']='passed'
    (ROOT/'data/installer-smoke-result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
