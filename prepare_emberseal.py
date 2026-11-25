"""Maintainer tool: pin the latest authored Emberseal build for reproducible releases."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store,write_json
from rwstudio.content import validate_project


def prepare(source, game_root, compiler, destination=None):
    destination=Path(destination) if destination is not None else ROOT/'bundled/emberseal'
    if destination.exists():raise ValueError('The bundle already exists. Review it before replacing the pinned example.')
    project=validate_project(json.loads(Path(source).read_text(encoding='utf-8')))
    if project['id']!='emberseal_demo' or project['module_name']!='rw_ember_v3':raise ValueError('Use the latest rw_ember_v3 Emberseal project.')
    if any(a['pack']!='builtin' for a in project.get('custom_assets',[])):raise ValueError('The distributable example must use stock assets and its generated geometry only.')
    # Keep authored maps, object placements and floorplan images intact. Apply
    # the conversation/storage defaults requested for the current demo.
    project['ai_conversations']=True;project['ambient']['social']=True
    project['companions'].update(enabled=True,familiars=True,summons=True)
    for n in project['npcs']:
        n['ai_enabled']=True;n['behavior'].update(social_enabled=True,accept_visits=True,partners=[])
        n['companion'].update(movement=True,inventory=True,inspect_containers=True,social_visits=True)
    for t in project['companions']['templates']:t.update(ai_enabled=True,movement=True,inventory=True,inspect_containers=True,social_visits=True)
    store=Store(ROOT/'data/example-build');manifest=build_project(project,store,game_root,compiler)
    source=Path(manifest['path']).parent
    destination.mkdir(parents=True)
    names=['project.json','manifest.json','layout.json','validation.json','PLAY.txt','ROLE-WEAVER-LICENSE.txt','dependencies.json',manifest['module'],'rw_ember_v3.rwproject.json']
    names += [f.relative_to(source).as_posix() for d in ('source','geometry-source','hak') for f in (source/d).glob('*') if f.is_file()]
    for name in names:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
    manifest.pop('path',None);write_json(destination/'manifest.json',manifest)
    files={name:hashlib.sha256((destination/name).read_bytes()).hexdigest() for name in names}
    write_json(destination/'bundle.json',dict(title=project['title'],project_id=project['id'],module=manifest['module'],build_id=manifest['build_id'],files=files))
    return dict(build=manifest,bundle=str(destination),files=len(files))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path);p.add_argument('--game-root',type=Path,required=True);p.add_argument('--compiler',type=Path,default=ROOT/'vendor/nwnsc/nwnsc.exe')
    p.add_argument('--output',type=Path,help='New staging folder for review before replacing the pinned bundle')
    args=p.parse_args();print(json.dumps(prepare(args.project,args.game_root,args.compiler,args.output),indent=2))
