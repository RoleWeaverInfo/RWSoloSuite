"""Package explicit source files and named example builds; never local settings."""
from pathlib import Path
import argparse
import json
import os
import zipfile
from rwstudio import VERSION

ROOT=Path(__file__).resolve().parent

def package(build,examples=()):
    builds=list(dict.fromkeys([build,*examples]));manifests=[]
    files=[ROOT/f for f in ('.gitignore','.gitattributes','studio.py','package.py','Start Module Studio.cmd','Start AI Player.cmd','Start Solo Studio.cmd','Start-SoloStudio.ps1','README.md','PLAYTEST.md','VALIDATION.md','AI-NPC-PORT-PLAN.md','ROLE-WEAVER-LICENSE.txt')]
    for name in ('rwstudio','scripts','authoring_scripts','web','assets','vendor','tests','examples'):
        files += [f for f in (ROOT/name).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc']
    for ident in builds:
        if len(ident)!=20 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('Invalid build ID')
        folder=ROOT/'data/builds'/ident
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));manifests.append((folder,manifest))
        files += [f for f in folder.rglob('*') if f.is_file()]
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    target=out/('Role-Weaver-Module-Studio-'+VERSION+'.zip')
    prefix='Role-Weaver-Module-Studio'
    key=os.environ.get('OPENAI_API_KEY','').encode()
    def checked(file):
        raw=file.read_bytes()
        if key and key in raw:raise ValueError('Credential found in a package candidate; export stopped')
        return raw
    payloads=[(str(Path(prefix)/file.relative_to(ROOT)),checked(file)) for file in files]
    projects={manifest['project_id']:folder/'project.json' for folder,manifest in manifests}
    payloads += [(prefix+'/data/projects/'+ident+'.json',checked(file)) for ident,file in projects.items()]
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in payloads:z.writestr(name.replace('\\','/'),raw)
    artifacts=[]
    for folder,manifest in manifests:
        for suffix in ('.mod','.rwproject.json','-aurora.zip'):
            name=Path(manifest['module']).stem+suffix;(out/name).write_bytes(checked(folder/name));artifacts.append(str(out/name))
    print(json.dumps({'package':str(target),'bytes':target.stat().st_size,'builds':builds,'artifacts':artifacts,'credential_scan':'passed' if key else 'no environment key; source allowlist used'}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('build');parser.add_argument('--example',action='append',default=[])
    args=parser.parse_args();package(args.build,args.example)

