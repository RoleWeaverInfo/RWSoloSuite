import json
import os
import re
import threading
import time
from pathlib import Path
from .content import seed, validate_project


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temp,path)


class Store:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.RLock()
        for name in ('projects','builds'): (self.root/name).mkdir(parents=True,exist_ok=True)
        if not list((self.root/'projects').glob('*.json')): self.save(seed())

    def path(self,ident):
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',ident): raise ValueError('Invalid project ID')
        return self.root/'projects'/(ident+'.json')

    def get(self,ident):
        with self.lock: return validate_project(json.loads(self.path(ident).read_text(encoding='utf-8')))

    def save(self,project):
        project=validate_project(project)
        with self.lock: write_json(self.path(project['id']),project)
        return project

    def list(self):
        with self.lock:
            return [{'id':p['id'],'title':p['title'],'module_name':p['module_name'],'schema_version':p['schema_version']} for p in
                    (json.loads(f.read_text(encoding='utf-8')) for f in sorted((self.root/'projects').glob('*.json')))]

    def built_project(self,build):
        if not re.fullmatch(r'[0-9a-f]{20}',build): raise ValueError('Unknown build ID')
        return validate_project(json.loads((self.root/'builds'/build/'project.json').read_text(encoding='utf-8')))
