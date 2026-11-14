"""Portable Windows AI Player files inside each exported adventure ZIP."""
from pathlib import Path
import re
import os
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def write_player_bundle(folder,module):
    folder=Path(folder);name=Path(module).stem
    if not re.fullmatch('[a-z][a-z0-9_]{0,15}',name):raise ValueError('Invalid module launcher filename')
    player=folder/'AI Player';player.mkdir(exist_ok=True);copied=[]
    for filename in ('studio.py','play.py','ROLE-WEAVER-LICENSE.txt'):
        shutil.copy2(ROOT/filename,player/filename);copied.append(player/filename)
    for directory in ('rwstudio','web','assets'):
        for source in (ROOT/directory).rglob('*'):
            if not source.is_file() or '__pycache__' in source.parts or source.suffix=='.pyc':continue
            target=player/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied.append(target)
    shutil.copy2(ROOT/'Start-Adventure.ps1',folder/'Start-Adventure.ps1')
    command='@echo off\r\ncd /d "%~dp0"\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Adventure.ps1" -ChooseMode -Module "'+name+'" -ModuleFile "%~dp0'+name+'.mod" -Sidecar "%~dp0'+name+'.rwproject.json" %*\r\nif errorlevel 1 pause\r\n'
    (folder/'Play Adventure.cmd').write_bytes(command.encode('ascii'))
    return [folder/'Play Adventure.cmd',folder/'Start-Adventure.ps1',*copied]

def refresh_share_zip(folder,manifest):
    folder=Path(folder);launch_files=write_player_bundle(folder,manifest['module']);name=Path(manifest['module']).stem
    files=[folder/manifest['module'],folder/'PLAY.txt',folder/'ROLE-WEAVER-LICENSE.txt',folder/'manifest.json',folder/'validation.json',folder/'layout.json',folder/(name+'.rwproject.json'),*(folder/'source').iterdir(),*launch_files]
    target=folder/(name+'-aurora.zip')
    key=os.environ.get('OPENAI_API_KEY','').encode()
    temporary=target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for file in files:
            raw=file.read_bytes()
            if key and key in raw:raise ValueError('Credential found in an adventure export; sharing stopped')
            z.writestr(file.relative_to(folder).as_posix(),raw)
    os.replace(temporary,target)
    return target


def package_build_files(folder,manifest):
    folder=Path(folder);name=Path(manifest['module']).stem
    explicit=[folder/f for f in (manifest['module'],name+'.rwproject.json',name+'-aurora.zip','PLAY.txt','ROLE-WEAVER-LICENSE.txt','manifest.json','project.json','validation.json','layout.json','compile.log','Play Adventure.cmd','Start-Adventure.ps1')]
    explicit += [f for f in (folder/'source').glob('*') if f.is_file() and f.suffix in ('.ifo','.are','.git','.gic','.utc','.uti','.utp','.dlg','.jrl','.fac','.nss','.ncs','.utt','.utm')]
    runtime=folder/'AI Player'
    explicit += [runtime/f for f in ('studio.py','play.py','ROLE-WEAVER-LICENSE.txt')]
    for directory in ('rwstudio','web','assets'):
        explicit += [runtime/f.relative_to(ROOT) for f in (ROOT/directory).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
    return [f for f in explicit if f.is_file()]
