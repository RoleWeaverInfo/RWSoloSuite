"""Open an isolated editable build copy in the locally installed toolset."""
import hashlib
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path
from .authoring import validate
from .builder import build_project
from .custom_assets import install_dependencies


def open_project(project, area_id, store, game_root, compiler, user_dir):
    if sys.platform!='win32':raise ValueError('Aurora is a Windows tool. Use Build & share to export the module and HAKs, then open them in Aurora on Windows. Studio editing and native module compilation work on this platform.')
    project=validate(project)
    area=next((a for a in project['areas'] if a['id']==area_id),None)
    if area is None:raise ValueError('Choose an area to open in Aurora')
    root=Path(game_root).resolve()
    toolset=next((p for p in (root/'bin/win32/nwtoolset.exe',root/'nwtoolset.exe') if p.is_file()),None)
    if toolset is None:raise ValueError('Aurora Toolset was not found. Check the NWN installation folder in Local settings.')
    manifest=build_project(project,store,root,compiler)
    folder=store.root/'builds'/manifest['build_id']
    source=folder/(project['module_name']+'.mod')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('Build checksum mismatch')
    install_dependencies(folder,user_dir)
    copies=store.root/'aurora';copies.mkdir(parents=True,exist_ok=True)
    destination=Path(tempfile.mkdtemp(prefix=project['module_name']+'-',dir=copies))
    module=destination/source.name
    shutil.copy2(source,module)
    (destination/'README.txt').write_text('Editable Aurora copy. Open Areas > '+area['name']+' ('+area['id']+').\nSave edits here. Studio rebuilds do not overwrite this copy. Aurora edits are not imported into Studio.\n',encoding='utf-8')
    try:
        process=subprocess.Popen([str(toolset),str(module.resolve())],cwd=str(root))
    except OSError as exc:
        raise ValueError('Could not start Aurora. Your editable module is at '+str(module)) from exc
    return {'module':str(module),'area':area['name'],'area_id':area['id'],'process_id':process.pid,'build_id':manifest['build_id']}
