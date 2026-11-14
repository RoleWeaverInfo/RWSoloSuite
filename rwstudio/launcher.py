"""Readiness-checked, supervised single-player launcher. Never puts keys in arguments."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from .content import validate_project
from .nwn.module_copy import resources

ROOT=Path(__file__).resolve().parents[1]
BASE_URL='http://127.0.0.1:8766'
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)

class LaunchError(ValueError):pass

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def game_candidates(configured=None):
    roots=[Path(configured)] if configured else []
    steam=[]
    if os.name=='nt':
        import winreg
        for hive,key,value in [(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam','SteamPath'),(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam','InstallPath')]:
            try:
                with winreg.OpenKey(hive,key) as reg:steam.append(Path(winreg.QueryValueEx(reg,value)[0]))
            except OSError:pass
    for env in ('ProgramFiles(x86)','ProgramFiles'):
        if os.environ.get(env):steam.append(Path(os.environ[env])/'Steam')
    for folder in list(steam):
        vdf=folder/'steamapps/libraryfolders.vdf'
        if vdf.is_file():
            for entry in re.findall(r'"path"\s*"([^"]+)"',vdf.read_text(encoding='utf-8',errors='replace')):steam.append(Path(entry.replace('\\\\','\\')))
    roots += [s/'steamapps/common/Neverwinter Nights' for s in steam]
    return list(dict.fromkeys(roots))

def native_context(module):
    try:raw=next((b for n,k,b in resources(Path(module).read_bytes()) if n=='sp_config' and k==2009),None)
    except (ValueError,AssertionError,IndexError,KeyError,struct.error):raise LaunchError('The selected file is not a readable NWN module.') from None
    if raw is None:return None
    text=raw.decode('utf-8',errors='replace')
    build=re.search(r'\bSPBuild\s*\(\s*\)\s*\{\s*return\s*"([0-9a-f]{20})"',text)
    project=re.search(r'\bSPProject\s*\(\s*\)\s*\{\s*return\s*"([a-z][a-z0-9_]{0,39})"',text)
    if not build or not project:raise LaunchError('The module AI identifiers are invalid. Export it again from Studio.')
    return dict(build_id=build[1],project_id=project[1])

def plan(module='rw_uifix',module_file=None,sidecar=None,game_root=None,user_dir=None,resume=False,offline=False,root=ROOT):
    root=Path(root);settings=read_json(root/'data/settings.json') if (root/'data/settings.json').is_file() else {}
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,15}(?:\.mod)?',module):raise LaunchError('Use the module filename without a path; --module-file accepts a full file path.')
    name=module.removesuffix('.mod');user=Path(user_dir or settings.get('user_dir') or Path.home()/'Documents/Neverwinter Nights').expanduser().resolve()
    if not user.is_dir():raise LaunchError('The NWN user folder does not exist. Start NWN once or specify --user-dir.')
    candidates=[Path(game_root)] if game_root else game_candidates(settings.get('game_root'))
    game=next((p.resolve() for p in candidates if (p/'bin/win32/nwmain.exe').is_file()),None)
    if game is None:raise LaunchError('NWN:EE was not found. Set its game folder in Studio or pass -GameRoot to the launcher.')
    source=Path(module_file).expanduser().resolve() if module_file else user/'modules'/(name+'.mod')
    if not source.is_file() and module_file is None:
        bundled=sorted((root/'data/builds').glob('*/'+name+'.mod'),key=lambda f:f.stat().st_mtime,reverse=True)
        source=next((f for f in bundled if re.fullmatch(r'[0-9a-f]{20}',f.parent.name)),source)
    if not source.is_file():raise LaunchError('The module is missing. Install it from Studio or extract the complete share ZIP.')
    context=native_context(source);document=None
    ai=bool(context) and not offline
    if ai:
        choices=[Path(sidecar).expanduser().resolve()] if sidecar else [source.with_suffix('.rwproject.json'),root/'data/builds'/context['build_id']/(name+'.rwproject.json')]
        file=next((f for f in choices if f.is_file()),None)
        if file is not None:document=read_json(file)
        else:
            built=root/'data/builds'/context['build_id']/'project.json'
            if built.is_file():document=dict(build_id=context['build_id'],project=read_json(built))
        if document is None:raise LaunchError('The matching .rwproject.json file is missing. Keep it beside the .mod or import the matching build in Studio.')
        project=validate_project(document.get('project',{}))
        if document.get('build_id')!=context['build_id'] or project['id']!=context['project_id'] or project['module_name']!=name:raise LaunchError('The project file does not match this module build. Use the sidecar exported with this exact module.')
        document=dict(build_id=context['build_id'],project=project)
    args=['-userdirectory',str(user)]
    if not resume:args+=['+LoadNewModule',name]
    return dict(module=name,source=str(source),installed=str(user/'modules'/(name+'.mod')),game_root=str(game),executable=str(game/'bin/win32/nwmain.exe'),user_dir=str(user),game_arguments=args,ai=ai,offline=offline,document=document,data=str(root/'data'),root=str(root))

def http(path,body=None,token=None):
    headers={'Content-Type':'application/json'}
    if token:headers['X-Studio-Token']=token
    req=urllib.request.Request(BASE_URL+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=3) as response:
            if not response.headers.get('Server','').startswith('RoleWeaverSolo'):raise LaunchError('Port 8766 is occupied by a different application.')
            return json.load(response)
    except urllib.error.HTTPError as e:
        # Never expose response bodies; configuration and player text stay local.
        raise LaunchError('AI Player rejected the operation (HTTP '+str(e.code)+'). Check that the matching Studio version is running.') from None

def state():
    try:
        s=http('/api/state')
        if not isinstance(s,dict) or not all(k in s for k in ('csrf','bridge','settings','key_available','version')):raise LaunchError('The local service is not a compatible AI Player.')
        return s
    except (urllib.error.URLError,TimeoutError,ConnectionError):return None

def install(p):
    source=Path(p['source']);target=Path(p['installed'])
    if source==target:return
    if target.name=='mc_courier.mod' and target.exists() and source.read_bytes()!=target.read_bytes():raise LaunchError('The original courier module is protected; use a separate module filename.')
    raw=source.read_bytes();target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_file():
        old=target.read_bytes()
        if old==raw:return
        backup=target.parent/'RoleWeaverBackups'/(target.stem+'-'+hashlib.sha256(old).hexdigest()[:12]+'.mod')
        backup.parent.mkdir(exist_ok=True);shutil.copy2(target,backup)
        print('Previous module backed up to '+str(backup),flush=True)
    shutil.copy2(source,target)

def configure(s,p):
    version=tuple(map(int,re.findall(r'\d+',str(s.get('version','')))[:3]))
    if version<(0,7,1):raise LaunchError('AI Player 0.7.1 or newer is required. Close the older AI Player and run this launcher again.')
    if not s['key_available']:raise LaunchError('AI Player has no OPENAI_API_KEY. Configure your key and restart AI Player, or launch with -Offline for native play.')
    if Path(s['settings']['user_dir']).resolve()!=Path(p['user_dir']).resolve():raise LaunchError('The running AI Player uses a different NWN user folder. Correct its settings before playing.')
    http('/api/player/register',p['document'],s['csrf'])
    http('/api/bridge',dict(enabled=True),s['csrf'])

def game_running():
    if os.name!='nt':return False
    result=subprocess.run(['tasklist','/FI','IMAGENAME eq nwmain.exe','/FO','CSV','/NH'],capture_output=True,text=True,creationflags=NO_WINDOW)
    return any(row and row[0].lower()=='nwmain.exe' for row in csv.reader(result.stdout.splitlines()))

def run(p,popen=subprocess.Popen,check_state=state,check_game=game_running,sleep=time.sleep):
    bridge=None;logs=[];started_game=None;restarts=0
    def start_bridge():
        if not os.environ.get('OPENAI_API_KEY'):raise LaunchError('OPENAI_API_KEY is missing. Configure your own API key or use -Offline to play without live AI.')
        data=Path(p['data']);data.mkdir(parents=True,exist_ok=True)
        from .storage import write_json
        settings=read_json(data/'settings.json') if (data/'settings.json').is_file() else {}
        settings.update(game_root=p['game_root'],user_dir=p['user_dir']);write_json(data/'settings.json',settings)
        out=(data/'player-launch.log').open('ab');err=(data/'player-launch-error.log').open('ab');logs.extend([out,err])
        return popen([sys.executable,str(Path(p['root'])/'studio.py'),'--player','--data',str(data)],cwd=p['root'],stdout=out,stderr=err,creationflags=NO_WINDOW)
    def ready():
        deadline=time.monotonic()+10
        for _ in range(40):
            s=check_state()
            if s:return s
            if bridge is not None and bridge.poll() is not None:raise LaunchError('AI Player exited during startup. See data/player-launch-error.log.')
            if time.monotonic()>=deadline:break
            sleep(.25)
        raise LaunchError('AI Player did not become ready within 10 seconds. The game was not launched.')
    try:
        if p['ai']:
            s=check_state()
            if s is None:bridge=start_bridge();s=ready()
            configure(s,p)
            print('AI Player is ready. Matching adventure registered. Keep this launcher window open while playing.',flush=True)
        else:
            if p.get('offline'):
                s=check_state()
                if s:http('/api/bridge',dict(enabled=False),s['csrf'])
            print('Native/offline play: live AI is not started.',flush=True)
        already_running=check_game()
        if already_running and Path(p['source'])!=Path(p['installed']) and (not Path(p['installed']).is_file() or Path(p['source']).read_bytes()!=Path(p['installed']).read_bytes()):raise LaunchError('Save and quit NWN before installing a different module version. The running game was left untouched.')
        install(p)
        if already_running:
            print('NWN is already running. No second game was opened. Switch back and load your adventure/save there.',flush=True)
        else:
            print('Starting NWN'+(' at character selection for '+p['module'] if '+LoadNewModule' in p['game_arguments'] else ' at the main menu; choose Load Game')+'.',flush=True)
            started_game=popen([p['executable'],*p['game_arguments']],cwd=p['game_root'])
        while (started_game.poll() is None or check_game() if started_game is not None else check_game()):
            if p['ai'] and ((bridge is not None and bridge.poll() is not None) or (bridge is None and check_state() is None)):
                restarts+=1
                if restarts>3:raise LaunchError('AI Player repeatedly exited. Check player-launch-error.log. The game has been left running.')
                print('AI Player stopped; restarting it. Repeat any interrupted question.',flush=True)
                bridge=start_bridge();configure(ready(),p)
            sleep(1)
        if started_game is not None and started_game.returncode not in (None,0):raise LaunchError('NWN exited with code '+str(started_game.returncode)+'. Check the game installation/Steam client.')
    finally:
        # Leave reused services and the game alone. Stop only this launcher's own AI worker.
        if bridge is not None and bridge.poll() is None:
            bridge.terminate()
            try:bridge.wait(timeout=5)
            except subprocess.TimeoutExpired:bridge.kill();bridge.wait(timeout=5)
        for handle in logs:handle.close()

def saved_game_choice(text):
    choice=text.strip()
    if choice in ('','1'):return False
    if choice=='2':return True
    raise LaunchError('Choose 1 for a new adventure or 2 to load a saved game.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--module',default='rw_uifix');parser.add_argument('--module-file');parser.add_argument('--sidecar');parser.add_argument('--game-root');parser.add_argument('--user-dir');parser.add_argument('--resume',action='store_true');parser.add_argument('--choose-mode',action='store_true');parser.add_argument('--offline',action='store_true');parser.add_argument('--check-only',action='store_true')
    args=vars(parser.parse_args());check=args.pop('check_only');choose=args.pop('choose_mode')
    try:
        if choose and not check and not args['resume'] and sys.stdin.isatty() and not game_running():
            print('Role Weaver Adventure\n1. Start a new adventure\n2. Load a saved game')
            args['resume']=saved_game_choice(input('Choose [1]: '))
        p=plan(**args)
        if check:
            safe={k:v for k,v in p.items() if k!='document'};safe['matching_project_available']=p['document'] is not None;safe['key_available']=bool(os.environ.get('OPENAI_API_KEY'));print(json.dumps(safe,indent=2));return
        run(p)
    except KeyboardInterrupt:print('Launcher closed. NWN was left running. Only a worker started by this launcher was stopped; pre-existing AI Players were left alone.')
    except (LaunchError,ValueError,OSError,KeyError) as e:
        # Exceptions here contain paths/configuration only, never API request headers or credentials.
        print('Cannot launch adventure: '+str(e),file=sys.stderr);raise SystemExit(1)
