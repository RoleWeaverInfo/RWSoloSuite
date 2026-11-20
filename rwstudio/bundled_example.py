"""The single curated example, independent of personal workspaces and test fixtures."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from .paths import ROOT

BUNDLE = ROOT/'bundled/emberseal'
PROJECT = 'emberseal_demo'
MODULE = 'rw_ember_v3'


def information(folder=BUNDLE):
    path = Path(folder)/'bundle.json'
    if not path.is_file():return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('project_id') != PROJECT or data.get('module') != MODULE+'.mod' or not re.fullmatch(r'[0-9a-f]{20}',data.get('build_id','')):
        raise ValueError('The bundled Emberseal example has invalid identifiers.')
    return {k:data[k] for k in ('build_id','project_id','module','title')}


def checked_files(folder=BUNDLE):
    folder = Path(folder);information(folder)
    index = json.loads((folder/'bundle.json').read_text(encoding='utf-8'))['files']
    required = {'project.json','manifest.json',MODULE+'.mod',MODULE+'.rwproject.json','dependencies.json','PLAY.txt'}
    if not required.issubset(index):raise ValueError('The bundled adventure is incomplete.')
    files = []
    for name, digest in index.items():
        path = PurePosixPath(name)
        if not path.parts or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe bundled example path.')
        source = folder.joinpath(*path.parts)
        if not source.resolve().is_relative_to(folder.resolve()) or not source.is_file():raise ValueError('A bundled example file is missing.')
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:raise ValueError('Bundled example checksum mismatch: '+name)
        if source.suffix=='.mod' and name != MODULE+'.mod':raise ValueError('Only Emberseal may be bundled as an example module.')
        files.append((name,source))
    return files


def prepare_share(output, folder=BUNDLE):
    """Build the portable adventure ZIP from pinned resources and current guides."""
    from .player_package import refresh_share_zip
    from .storage import write_json
    output = Path(output);output.mkdir(parents=True,exist_ok=True)
    for name, source in checked_files(folder):
        target = output/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
    manifest.pop('path',None);write_json(output/'manifest.json',manifest)
    cached=Path(folder)/(MODULE+'-aurora.zip');checksum=Path(folder)/'share.sha256'
    if cached.is_file() and checksum.is_file():
        if hashlib.sha256(cached.read_bytes()).hexdigest()!=checksum.read_text(encoding='ascii').split()[0]:raise ValueError('The bundled adventure download is damaged. Reinstall Studio.')
        target=output/cached.name;shutil.copy2(cached,target);return target
    return refresh_share_zip(output,manifest)


def install(store, replace=False, folder=BUNDLE):
    """Explicit re-import backs up the draft; installing never touches NWN files."""
    from .content import canonical, validate_project
    from .storage import write_json
    info = information(folder)
    if info is None:raise ValueError('This installation does not contain the Emberseal example. Download the current Studio package.')
    project = validate_project(json.loads((Path(folder)/'project.json').read_text(encoding='utf-8')))
    if project['id']!=info['project_id'] or project['module_name']+'.mod'!=info['module']:raise ValueError('Bundled project does not match its module.')
    existing = store.root/'builds'/info['build_id']/'project.json'
    if existing.is_file() and canonical(store.built_project(info['build_id']))!=canonical(project):raise ValueError('The example build conflicts with an existing profile.')
    with tempfile.TemporaryDirectory(prefix='example-',dir=store.root) as temporary:
        stage=Path(temporary);prepare_share(stage,folder)
        destination=store.root/'builds'/info['build_id']
        manifest=json.loads((stage/'manifest.json').read_text(encoding='utf-8'))
        manifest['path']=str(destination/info['module']);write_json(stage/'manifest.json',manifest)
        shutil.copytree(stage,destination,dirs_exist_ok=True)
    draft=store.path(project['id']);backup=None
    if draft.exists() and replace:
        raw=draft.read_bytes();backup=store.root/'backups'/(project['id']+'-'+hashlib.sha256(raw).hexdigest()[:12]+'.json')
        backup.parent.mkdir(exist_ok=True);backup.write_bytes(raw)
    if not draft.exists() or replace:store.save(project)
    return dict(project=store.get(project['id']),build=manifest,backup=str(backup) if backup else None)
