"""Build a clean release ZIP; local workspaces and credentials are never implicit."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import zipfile
from rwstudio import VERSION
from rwstudio.player_package import export_keys,write_checked
from rwstudio.bundled_example import BUNDLE,information,checked_files,prepare_share,MODULE
import shutil
import tempfile

ROOT=Path(__file__).resolve().parent


def package(build=None,examples=(),output=None):
    if build or examples:raise ValueError('Official packages include only The Emberseal of Briarwatch. Export other adventures from Build & share.')
    example=information()
    if example is None:raise ValueError('The pinned Emberseal example is missing from this checkout.')
    files={name:ROOT/name for name in ('studio.py','service.py','package.py','build_native.py','build_installer.py','Start Role Weaver.cmd','Start-RoleWeaver.ps1','Start-RoleWeaver.sh','RELEASE-NOTES.md','ROLE-WEAVER-LICENSE.txt','requirements-guardrails.txt','requirements-platform.txt','GUARDRAILS-AND-USAGE.md')}
    files['README.md']=ROOT/'RELEASE-GUIDE.md'
    for name in ('rwstudio','scripts','authoring_scripts','web','assets','vendor','docs','installer'):
        for file in (ROOT/name).rglob('*'):
            if file.is_file() and file.name!='DEVELOPMENT-HISTORY.md' and '__pycache__' not in file.parts and file.suffix not in ('.pyc','.log'):
                if file.suffix.lower() in ('.mod','.hak','.tlk') or file.name.lower().endswith('.rwproject.json'):
                    raise ValueError('Adventure content outside the pinned Emberseal bundle cannot be released: '+file.relative_to(ROOT).as_posix())
                files[file.relative_to(ROOT).as_posix()]=file
    for name,file in checked_files():files['bundled/emberseal/'+name]=file
    files['bundled/emberseal/bundle.json']=BUNDLE/'bundle.json'
    out=Path(output) if output else ROOT/'dist';out.mkdir(parents=True,exist_ok=True)
    example_download=export_example(out)
    files['bundled/emberseal/'+MODULE+'-aurora.zip']=Path(example_download['package'])
    files['bundled/emberseal/share.sha256']=Path(example_download['package']).with_suffix('.zip.sha256')
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
    return dict(package=str(target),bytes=target.stat().st_size,sha256=digest,files=len(files),builds=[example['build_id']],example=example_download,credential_scan='passed',requires='Source package: Python 3.12+, platform dependencies and native nwnsc; NWN:EE assets for export')


def export_example(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    target=out/('The-Emberseal-of-Briarwatch-'+VERSION+'.zip')
    with tempfile.TemporaryDirectory(prefix='emberseal-share-') as temporary:
        archive=prepare_share(Path(temporary));shutil.copy2(archive,target)
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
    return dict(package=str(target),sha256=digest,build_id=information()['build_id'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    args=parser.parse_args();print(json.dumps(package(output=args.output),indent=2))
