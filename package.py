"""Build a clean release ZIP; local workspaces and credentials are never implicit."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import zipfile
from rwstudio import VERSION
from rwstudio.player_package import package_build_files,refresh_share_zip,export_keys,write_checked

ROOT=Path(__file__).resolve().parent


def package(build=None,examples=(),output=None):
    builds=list(dict.fromkeys(([build] if build else [])+list(examples)))
    files={name:ROOT/name for name in ('studio.py','service.py','Start Role Weaver.cmd','Start-RoleWeaver.ps1','Start-RoleWeaver.sh','RELEASE-NOTES.md','ROLE-WEAVER-LICENSE.txt','requirements-guardrails.txt','requirements-platform.txt','GUARDRAILS-AND-USAGE.md')}
    files['README.md']=ROOT/'RELEASE-GUIDE.md'
    for name in ('rwstudio','scripts','authoring_scripts','web','assets','vendor','docs'):
        for file in (ROOT/name).rglob('*'):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix not in ('.pyc','.log'):
                files[file.relative_to(ROOT).as_posix()]=file
    for ident in builds:
        if len(ident)!=20 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('Invalid build ID')
        folder=ROOT/'data/builds'/ident
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        refresh_share_zip(folder,manifest)
        for file in package_build_files(folder,manifest):files[file.relative_to(ROOT).as_posix()]=file
        files['data/projects/'+manifest['project_id']+'.json']=folder/'project.json'
    out=Path(output) if output else ROOT/'dist';out.mkdir(parents=True,exist_ok=True)
    target=out/('Role-Weaver-Module-Studio-'+VERSION+'-source.zip');temporary=target.with_suffix('.zip.tmp')
    keys=export_keys();prefix='Role-Weaver-Module-Studio/'
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,file in sorted(files.items()):write_checked(archive,file,prefix+name,keys)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:raise ValueError('Release ZIP integrity check failed')
        os.replace(temporary,target)
    finally:
        if temporary.exists():temporary.unlink()
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
    return dict(package=str(target),bytes=target.stat().st_size,sha256=digest,files=len(files),builds=builds,credential_scan='passed',requires='Source package: Python 3.10+, platform dependencies and native nwnsc; NWN:EE assets for export')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('build',nargs='?');parser.add_argument('--example',action='append',default=[]);parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(json.dumps(package(args.build,args.example,args.output),indent=2))
