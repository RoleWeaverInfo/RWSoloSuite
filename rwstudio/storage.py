import json
import os
import re
import threading
import time
from pathlib import Path
from .content import seed, validate_project,canonical


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)


class Store:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.RLock()
        first_workspace=not (self.root/'projects').exists()
        for name in ('projects','builds'): (self.root/name).mkdir(parents=True,exist_ok=True)
        if first_workspace:
            from .authoring import blank
            p=blank('area_workshop','Untitled area');p['design_mode']='area';self.save(p)

    def path(self,ident):
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',ident): raise ValueError('Invalid project ID')
        return self.root/'projects'/(ident+'.json')

    def get(self,ident):
        with self.lock: return validate_project(json.loads(self.path(ident).read_text(encoding='utf-8')))

    def save(self,project):
        project=validate_project(project)
        with self.lock: write_json(self.path(project['id']),project)
        return project

    def delete(self,ident):
        with self.lock:
            path=self.path(ident);directory=self.root/'projects'
            # Only a regular project file in this workspace may be removed.
            if directory.resolve().parent!=self.root.resolve() or path.is_symlink() or path.resolve().parent!=directory.resolve():
                raise ValueError('Project file is outside the workspace')
            if not path.is_file():raise ValueError('This project has already been deleted or is missing')
            remaining=[p for p in self.list() if p['id']!=ident]
            path.unlink()
            return {'deleted':ident,'projects':remaining}

    def list(self):
        with self.lock:
            return [{'id':p['id'],'title':p['title'],'module_name':p['module_name'],'schema_version':p['schema_version'],'design_mode':p.get('design_mode','adventure')} for p in
                    (json.loads(f.read_text(encoding='utf-8')) for f in sorted((self.root/'projects').glob('*.json')))]

    def register_player_build(self,build,project):
        if not isinstance(build,str) or not re.fullmatch(r'[0-9a-f]{20}',build):raise ValueError('Invalid build ID')
        project=validate_project(project);target=self.root/'builds'/build/'project.json'
        with self.lock:
            if target.is_file() and canonical(validate_project(json.loads(target.read_text(encoding='utf-8'))))!=canonical(project):raise ValueError('Build ID conflicts with the existing adventure context')
            if not target.is_file():write_json(target,project)
        return {'registered':True,'build_id':build,'project_id':project['id']}

    def built_project(self,build):
        if not re.fullmatch(r'[0-9a-f]{20}',build): raise ValueError('Unknown build ID')
        return validate_project(json.loads((self.root/'builds'/build/'project.json').read_text(encoding='utf-8')))
