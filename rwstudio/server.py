"""Loopback-only dashboard. Python standard library, no remote frontend assets."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import argparse
import hashlib
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import threading
import webbrowser
from . import VERSION
from .content import seed, canonical, validate_project, CREATURES, DECOR, APPEARANCES
from .storage import Store, write_json
from .provider import Provider
from .bridge import Bridge
from .builder import ROOT, build_project, install_build
from . import authoring
from .merchants import CATALOG as GOODS, defaults as merchant_defaults

def defaults():
    bundled=ROOT/'vendor/nwnsc/nwnsc.exe'
    return {'model':'gpt-5.6-luna','game_root':'D:/SteamLibrary/steamapps/common/Neverwinter Nights',
            'user_dir':str(Path.home()/'Documents/Neverwinter Nights'),
            'compiler':str(bundled if bundled.exists() else ROOT.parent/'missing-courier/vendor/nwnsc/nwnsc.exe')}

def database_path(user_dir):
    folder=Path(user_dir)/'database'
    for suffix in ('.sqlite3','.sqlite'):
        path=folder/('rwsp_bridge'+suffix)
        if path.is_file():return path
    return folder/'rwsp_bridge.sqlite3'

class Application:
    def __init__(self,data):
        self.store=Store(Path(data).resolve());self.config=defaults();self.lock=threading.RLock();self.token=secrets.token_urlsafe(32)
        if not any(p['schema_version']==2 for p in self.store.list()):
            self.store.save(authoring.seed())
            for example_file in sorted((ROOT/'examples').glob('*.rwproject.json')):
                document=json.loads(example_file.read_text(encoding='utf-8-sig'))
                self.store.save(document.get('project',document))
        config=self.store.root/'settings.json'
        if config.is_file():self.config.update({k:v for k,v in json.loads(config.read_text(encoding='utf-8')).items() if k in self.config})
        self.provider=Provider(self.config['model']);self.bridge=Bridge(database_path(self.config['user_dir']),self.store,self.provider)
        self.bridge.start()

    def state(self):
        self.bridge.path=database_path(self.config['user_dir'])
        return {'version':VERSION,'csrf':self.token,'projects':self.store.list(),'settings':self.config,
                'key_available':bool(os.environ.get('OPENAI_API_KEY')),'usage':self.provider.usage,
                'bridge':self.bridge.status(),'receipts':self.bridge.receipts(),
                'catalog':{'creatures':list(CREATURES),'furnishings':list(DECOR),'appearances':list(APPEARANCES)},
                'authoring_catalog':{'creatures':list(authoring.CREATURES),'furnishings':list(authoring.DECOR),'appearances':list(authoring.APPEARANCES),'area_types':authoring.AREA_TYPES,'merchandise':GOODS,'merchant_defaults':merchant_defaults()}}

    def post(self,route,b):
        if not isinstance(b,dict):raise ValueError('Expected a JSON object')
        if route=='/api/project/save':return {'project':self.store.save(b['project'])}
        if route=='/api/project/new':
            ident=b['id'];path=self.store.path(ident)
            if path.exists():raise ValueError('A project with that ID already exists')
            p=authoring.blank(ident,b.get('title') or 'Untitled adventure')
            return {'project':self.store.save(p)}
        if route=='/api/project/import':
            wrapped=b['document'];p=validate_project(wrapped.get('project',wrapped))
            ident=wrapped.get('build_id')
            if ident is not None:
                if not re.fullmatch(r'[0-9a-f]{20}',ident):raise ValueError('Invalid build ID')
                target=self.store.root/'builds'/ident/'project.json'
                if target.exists() and canonical(json.loads(target.read_text(encoding='utf-8')))!=canonical(p):raise ValueError('Build ID conflicts with an existing project')
                write_json(target,p)
            # Import is explicit in the UI; back up any previous authoring project.
            path=self.store.path(p['id'])
            if path.exists():
                old=path.read_bytes();backup=self.store.root/'backups'/(p['id']+'-'+hashlib.sha256(old).hexdigest()[:12]+'.json')
                backup.parent.mkdir(exist_ok=True);backup.write_bytes(old)
            return {'project':self.store.save(p)}
        if route=='/api/draft':return {'proposal':self.provider.draft(validate_project(b['project']),str(b['instruction']))}
        if route=='/api/author/generate':
            from .authoring_ai import generate
            return generate(self.provider,b['project'],str(b.get('instruction','')),b.get('scope','adventure'),b.get('area_id',''))
        if route=='/api/author/review':return authoring.review(authoring.validate(b['project']))
        if route=='/api/author/arrange':
            from .layout import arrange
            p=authoring.validate(b['project']);area=next((a for a in p['areas'] if a['id']==b['area_id']),None)
            if area is None:raise ValueError('Choose an area')
            p['areas'][p['areas'].index(area)]=arrange(area)
            return {'project':p,'review':authoring.review(p)}
        if route=='/api/npc/preview':
            snapshot={'quest_stage':int(b.get('stage',0)),'has_satchel':bool(b.get('has_satchel',False)),'area':b.get('area','mc_hall'),'party':[]}
            return self.provider.npc(validate_project(b['project']),b['tag'],str(b['message']),snapshot)
        if route=='/api/dm':
            session=next((s for s in self.bridge.sessions() if s['session_id']==b.get('session_id')),None)
            if session:
                project=self.store.built_project(session['build_id']);snapshot=session['snapshot']
            else:
                if b.get('session_id'):raise ValueError('The game session is no longer current; resume the module')
                project=validate_project(b['project']);snapshot={'area':b.get('area','mc_cave'),'quest_stage':int(b.get('stage',1)),'party':[],'preview':True}
            result=self.provider.dm(project,str(b['message']),snapshot)
            if session:
                with self.bridge.lock:self.bridge.proposals[session['session_id']]=result
            return result
        if route=='/api/bridge':
            self.bridge.enabled=bool(b.get('enabled'))
            if not self.bridge.enabled:
                try:
                    with self.bridge.connect() as db:
                        db.execute("UPDATE sp_commands SET state='cancelled',receipt='Companion paused' WHERE state='queued'")
                        db.execute("UPDATE sp_requests SET state='expired' WHERE state IN ('queued','working')")
                except (FileNotFoundError, sqlite3.Error):pass
            return self.bridge.status()
        if route=='/api/command':return self.bridge.command(b['session_id'],b['action'],b.get('encounter_id',''),b.get('message',''))
        if route=='/api/build':
            project=self.store.save(b['project'])
            return build_project(project,self.store,self.config['game_root'],self.config['compiler'])
        if route=='/api/install':return install_build(self.store,b['build_id'],self.config['user_dir'])
        if route=='/api/settings':
            if set(b)!=set(self.config) or any(not isinstance(v,str) or not v.strip() or len(v)>1000 for v in b.values()):raise ValueError('Invalid settings')
            if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',b['model']):raise ValueError('Invalid model name')
            with self.lock:
                self.config=dict(b);self.provider.model=b['model'];self.bridge.path=database_path(b['user_dir']);write_json(self.store.root/'settings.json',self.config)
            return {'saved':True}
        raise ValueError('Unknown operation')

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,app):self.app=app;super().__init__(address,Handler)

class Handler(BaseHTTPRequestHandler):
    server_version='RoleWeaverSolo'
    def log_message(self,*args):pass # Player dialogue and credentials are never logged.
    def trusted(self):
        host=self.headers.get('Host','');port=self.server.server_port
        if host not in (f'127.0.0.1:{port}',f'localhost:{port}'):return False
        origin=self.headers.get('Origin')
        return origin is None or origin in (f'http://127.0.0.1:{port}',f'http://localhost:{port}')
    def send(self,status,data,content_type='application/json; charset=utf-8',filename=None):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header('Referrer-Policy','no-referrer')
        if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):
        if not self.trusted():return self.send(403,{'error':'Local access only'})
        parts=urlsplit(self.path);route=parts.path;query=parse_qs(parts.query);app=self.server.app
        try:
            if route=='/api/state':return self.send(200,app.state())
            if route=='/api/project':return self.send(200,{'project':app.store.get(query.get('id',[''])[0])})
            if route=='/api/live':
                session=next((s for s in app.bridge.sessions() if s['session_id']==query.get('session_id',[''])[0]),None)
                if session is None:raise ValueError('No active session')
                return self.send(200,{'project':app.store.built_project(session['build_id'])})
            if route=='/api/proposal':
                with app.bridge.lock:proposal=app.bridge.proposals.get(query.get('session_id',[''])[0])
                return self.send(200,{'proposal':proposal})
            if route=='/api/builds':
                result=[json.loads(f.read_text(encoding='utf-8')) for f in sorted((app.store.root/'builds').glob('*/manifest.json'),key=lambda f:f.stat().st_mtime)]
                return self.send(200,{'builds':result})
            if route=='/download':
                ident=query.get('build',[''])[0];p=app.store.built_project(ident);kind=query.get('kind',['zip'])[0]
                suffix={'zip':'-aurora.zip','mod':'.mod','project':'.rwproject.json'}.get(kind)
                if suffix is None:raise ValueError('Unknown download type')
                file=app.store.root/'builds'/ident/(p['module_name']+suffix)
                return self.send(200,file.read_bytes(),'application/octet-stream',file.name)
            static={'/':'author.html','/legacy':'index.html','/app.js':'app.js','/style.css':'style.css','/editor.js':'editor.js','/editor.css':'editor.css','/player':'player.html','/player.js':'player.js'}
            if route not in static:return self.send(404,{'error':'Not found'})
            file=ROOT/'web'/static[route];return self.send(200,file.read_bytes(),mimetypes.guess_type(file.name)[0]+'; charset=utf-8')
        except (ValueError,FileNotFoundError,KeyError):self.send(400,{'error':'Project or artifact not found'})
    def do_POST(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-Studio-Token',''),self.server.app.token):return self.send(403,{'error':'Reload Studio to establish a local session'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1_000_000:raise ValueError('Request is empty or too large')
            body=json.loads(self.rfile.read(length));result=self.server.app.post(urlsplit(self.path).path,body)
            self.send(200,result)
        except (ValueError,KeyError,TypeError) as exc:self.send(400,{'error':str(exc)[:6500]})
        except PermissionError:self.send(400,{'error':'Windows denied access to that location. Check the configured folder permissions.'})
        except Exception:self.send(500,{'error':'The operation could not finish. Check the configured paths and retry.'})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);parser.add_argument('--data',type=Path,default=ROOT/'data');parser.add_argument('--open',action='store_true');parser.add_argument('--player',action='store_true');args=parser.parse_args()
    app=Application(args.data);server=Server(('127.0.0.1',args.port),app)
    url=f'http://127.0.0.1:{server.server_port}'
    print('Role Weaver Module Studio: '+url,flush=True)
    if args.player:app.bridge.enabled=True
    if args.open:webbrowser.open(url+('/player' if args.player else ''))
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:app.bridge.stop.set();server.server_close()
