"""Service-only launchers and source fallback inside exported adventure ZIPs."""
from pathlib import Path
import os
import shutil
import zipfile
from .module_names import validate_module_name

ROOT=Path(__file__).resolve().parents[1]

def write_player_bundle(folder,module):
    folder=Path(folder);name=Path(module).stem
    validate_module_name(name)
    player=folder/'AI Player';player.mkdir(exist_ok=True);copied=[]
    for filename in ('studio.py','service.py','ROLE-WEAVER-LICENSE.txt','requirements-guardrails.txt','requirements-platform.txt','GUARDRAILS-AND-USAGE.md'):
        shutil.copy2(ROOT/filename,player/filename);copied.append(player/filename)
    for directory in ('rwstudio','web','assets'):
        for source in (ROOT/directory).rglob('*'):
            if not source.is_file() or '__pycache__' in source.parts or source.suffix=='.pyc':continue
            target=player/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied.append(target)
    shutil.copy2(ROOT/'Start-RoleWeaver.ps1',folder/'Start-RoleWeaver.ps1')
    command='@echo off\r\ncd /d "%~dp0"\r\ntitle Role Weaver Service\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-RoleWeaver.ps1" -Player -AdventurePath "%~dp0'+name+'.mod" %*\r\nif errorlevel 1 pause\r\n'
    (folder/'Start Role Weaver.cmd').write_bytes(command.encode('ascii'))
    shell='''#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
app=${ROLEWEAVER_APP:-}
if [ -z "$app" ] && [ "$(uname -s)" = Darwin ]; then
    for location in "/Applications/Role Weaver Module Studio.app" "$HOME/Applications/Role Weaver Module Studio.app"; do
        if [ -x "$location/Contents/MacOS/RoleWeaverModuleStudio" ]; then app="$location/Contents/MacOS/RoleWeaverModuleStudio"; break; fi
    done
fi
if [ -z "$app" ]; then app=$(command -v RoleWeaverModuleStudio || true); fi
if [ -n "$app" ] && [ -x "$app" ]; then
    exec "$app" --player --adventure "$root/MODULE.mod" "$@"
fi
echo 'Start the installed Role Weaver app, import the matching .rwproject.json on its AI service page, and install the module and HAKs as described in INSTALLATION.md.'
echo 'You can also set ROLEWEAVER_APP to the full path of the installed executable and run this script again.'
exit 1
'''.replace('MODULE',name)
    for filename in ('Start Role Weaver.sh','Start Role Weaver.command'):
        path=folder/filename;path.write_text(shell,encoding='utf8',newline='\n');path.chmod(0o755);copied.append(path)
    for filename in ('INSTALLATION.md','PLAYER-GUIDE.md','EMBERSEAL.md','CREATE-AN-ADVENTURE.md'):
        path=folder/filename;shutil.copy2(ROOT/'docs'/filename,path);copied.append(path)
    return [folder/'Start Role Weaver.cmd',folder/'Start-RoleWeaver.ps1',*copied]


def export_keys():
    from .credentials import Credentials,ENV
    from .paths import default_data
    keys={os.environ.get(name,'').encode() for name in ENV.values()}
    credentials=Credentials(default_data(ROOT))
    for provider in ENV:
        try:keys.add(credentials.get(provider).encode())
        except ValueError:pass  # Encrypted records themselves are never in the allowlist.
    return [key for key in keys if key]


def write_checked(archive,file,name,keys):
    tail=b'';overlap=max([len(key)-1 for key in keys],default=0)
    info=zipfile.ZipInfo.from_file(file,name)
    info.compress_type=zipfile.ZIP_DEFLATED
    if Path(file).suffix in ('.sh','.command'):info.create_system=3;info.external_attr=(0o100755<<16)
    with Path(file).open('rb') as source,archive.open(info,'w',force_zip64=True) as output:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            combined=tail+chunk
            if any(key in combined for key in keys):raise ValueError('Credential found in an export candidate; packaging stopped')
            tail=combined[-overlap:] if overlap else b''
            output.write(chunk)

def refresh_share_zip(folder,manifest):
    folder=Path(folder);launch_files=write_player_bundle(folder,manifest['module']);name=Path(manifest['module']).stem
    files=[folder/manifest['module'],folder/'PLAY.txt',folder/'ROLE-WEAVER-LICENSE.txt',folder/'manifest.json',folder/'validation.json',folder/'layout.json',folder/(name+'.rwproject.json'),*(folder/'source').iterdir(),*launch_files]
    files += list((folder/'geometry-source').glob('*'))
    files += [f for f in [folder/'dependencies.json',*(folder/'hak').glob('*.hak')] if f.is_file()]
    target=folder/(name+'-aurora.zip')
    keys=export_keys()
    temporary=target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for file in files:
            write_checked(z,file,file.relative_to(folder).as_posix(),keys)
    os.replace(temporary,target)
    return target


def package_build_files(folder,manifest):
    folder=Path(folder);name=Path(manifest['module']).stem
    explicit=[folder/f for f in (manifest['module'],name+'.rwproject.json',name+'-aurora.zip','PLAY.txt','ROLE-WEAVER-LICENSE.txt','manifest.json','project.json','validation.json','layout.json','Start Role Weaver.cmd','Start-RoleWeaver.ps1','Start Role Weaver.sh','Start Role Weaver.command','INSTALLATION.md','PLAYER-GUIDE.md','EMBERSEAL.md','CREATE-AN-ADVENTURE.md')]
    explicit += [f for f in (folder/'source').glob('*') if f.is_file() and f.suffix in ('.ifo','.are','.git','.gic','.utc','.uti','.utp','.dlg','.jrl','.fac','.nss','.ncs','.utt','.utm')]
    explicit += list((folder/'geometry-source').glob('*'))
    explicit += [f for f in [folder/'dependencies.json',*(folder/'hak').glob('*.hak')] if f.is_file()]
    runtime=folder/'AI Player'
    explicit += [runtime/f for f in ('studio.py','service.py','ROLE-WEAVER-LICENSE.txt','requirements-guardrails.txt','requirements-platform.txt','GUARDRAILS-AND-USAGE.md')]
    for directory in ('rwstudio','web','assets'):
        explicit += [runtime/f.relative_to(ROOT) for f in (ROOT/directory).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
    return [f for f in explicit if f.is_file()]
