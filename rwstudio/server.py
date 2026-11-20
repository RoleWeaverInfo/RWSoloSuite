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
from .builder import ROOT, BUILD_LOCK, build_project, install_build
from .paths import default_data
from .installation import service_lock
from . import authoring
from .merchants import CATALOG as GOODS, defaults as merchant_defaults
from .ambient import defaults as ambient_defaults,npc_defaults as behavior_defaults
from .companions import defaults as companion_defaults,npc_defaults as npc_companion_defaults

def defaults():
    from .paths import compiler_path,nwn_user_dir
    bundled=compiler_path(ROOT);user=nwn_user_dir()
    from .launcher import game_candidates
    game=next((str(p) for p in game_candidates() if (p/'data/nwn_base.key').is_file() or (p/'data/nwn_retail.key').is_file()),'')
    return {'content_root':str(user/'hak'),'provider':'openai','gemini_model':'gemini-3.5-flash-lite','model':'gpt-5.6-luna','authoring_model':'gpt-6-astra','authoring_gemini_model':'gemini-3.6-flash','authoring_reasoning':'medium','game_root':game,
            'user_dir':str(user),
            'compiler':str(bundled)}

def database_path(user_dir):
    folder=Path(user_dir)/'database'
    for suffix in ('.sqlite3','.sqlite'):
        path=folder/('rwsp_bridge'+suffix)
        if path.is_file():return path
    return folder/'rwsp_bridge.sqlite3'

class Application:
    def __init__(self,data):
        self.store=Store(Path(data).resolve());self.config=defaults();self.lock=threading.RLock();self.token=secrets.token_urlsafe(32)
        projects=self.store.list()
        if projects and not any(p['schema_version']==2 for p in projects):
            p=authoring.blank('area_workshop','Untitled area');p['design_mode']='area';self.store.save(p)
        config=self.store.root/'settings.json'
        if config.is_file():self.config.update({k:v for k,v in json.loads(config.read_text(encoding='utf-8')).items() if k in self.config})
        from .credentials import Credentials
        from .custom_assets import AssetLibrary
        from .guardrails import GameplayGuardrails
        from .usage import UsageStore
        self.guardrails=GameplayGuardrails(self.store.root/'guardrails.json')
        self.ai_usage=UsageStore(self.store.root/'ai-usage.sqlite3')
        self.credentials=Credentials(self.store.root);self.asset_library=AssetLibrary(self.store.root,self.config['game_root'])
        self.provider=Provider(self.config['gemini_model'] if self.config['provider']=='gemini' else self.config['model'],self.config['provider'],self.credentials,scope='gameplay',guardrails=self.guardrails,usage_store=self.ai_usage);self.bridge=Bridge(database_path(self.config['user_dir']),self.store,self.provider)
        self.authoring_provider=Provider(self.config['authoring_gemini_model'] if self.config['provider']=='gemini' else self.config['authoring_model'],self.config['provider'],self.credentials,reasoning_effort=None if self.config['authoring_reasoning']=='default' else self.config['authoring_reasoning'],scope='authoring',usage_store=self.ai_usage)
        self.bridge.start()

    def state(self):
        from .area_presets import catalog as preset_catalog
        self.bridge.path=database_path(self.config['user_dir'])
        return {'version':VERSION,'csrf':self.token,'projects':self.store.list(),'settings':self.config,'guardrails':self.guardrails.status(),
                'credentials':self.credentials.status(),'key_available':self.credentials.status()[self.config['provider']]['available'],'usage':self.provider.usage,'authoring_usage':self.authoring_provider.usage,
                'bridge':self.bridge.status(),'receipts':self.bridge.receipts(),
                'catalog':{'creatures':list(CREATURES),'furnishings':list(DECOR),'appearances':list(APPEARANCES)},'area_presets':preset_catalog(),
                'authoring_catalog':{'creatures':list(authoring.CREATURES),'furnishings':list(authoring.DECOR),'appearances':list(authoring.APPEARANCES),'area_types':authoring.AREA_TYPES,'merchandise':GOODS,'merchant_defaults':merchant_defaults(),'companion_defaults':companion_defaults(True),'npc_companion_defaults':npc_companion_defaults(),'ambient_defaults':ambient_defaults(),'behavior_defaults':behavior_defaults()}}

    def post(self,route,b):
        if not isinstance(b,dict):raise ValueError('Expected a JSON object')
        if route=='/api/service/stop':
            if b.get('confirm') is not True:raise ValueError('Confirm stopping the service first')
            self.bridge.stop.set()
            threading.Thread(target=self.http_server.shutdown,daemon=True).start()
            return {'stopped':True}
        if route=='/api/guardrails':return self.guardrails.configure(b.get('settings'))
        if route.startswith('/api/design/'):
            from . import design_tools as design
            if route=='/api/design/analyze-reference':
                from .floorplan_design import analyze
                return analyze(self.authoring_provider,self.asset_library,b['project'],b['area_id'],b['reference_index'])
            if route=='/api/design/groups':
                from .native_groups import catalog
                from .layout import TILESETS
                return {'groups':catalog(self.config['game_root'],TILESETS[b['area_type']])}
            if route=='/api/design/apply-group':
                from .native_groups import catalog,apply
                from .layout import TILESETS
                area=next(a for a in b['project']['areas'] if any(r['id']==b['room_id'] for r in a['rooms']))
                definition=next((g for g in catalog(self.config['game_root'],TILESETS[area['type']]) if g['id']==b.get('group_id')),None)
                if b.get('group_id') and definition is None:raise ValueError('Unknown native group')
                return apply(b['project'],b['room_id'],definition,b.get('rotation',0))
            if route=='/api/design/generate-reviewed':
                from .floorplan_design import generate_reviewed
                return generate_reviewed(self.authoring_provider,self.asset_library,b['project'],b['area_id'],b['plan'],b.get('accept_substitutions',False) is True)
            if route=='/api/design/interpret':return design.interpretation(self.authoring_provider,b['project'],b['area_id'],b['reference_index'])
            if route=='/api/design/apply-plan':return design.apply_interpretation(b['project'],b['area_id'],b['interpretation'])
            if route=='/api/design/map':return design.edit_map(b['project'],b['room_id'],b['operation'],b['values'])
            if route=='/api/design/room':return design.regenerate_room(self.authoring_provider,b['project'],b['room_id'],str(b.get('instruction',''))[:8000],asset_library=self.asset_library)
            if route=='/api/design/encounter':return design.encounter_template(b['project'],b['room_id'],b['kind'],b['difficulty'],b.get('brief',''))
            if route=='/api/design/attach-area':
                target=self.store.get(b['target_id'])
                result=design.attach_area(b['project'],b['area_id'],target)
                self.store.save(result['proposal'])
                return result
            if route=='/api/design/update-area':
                project=authoring.validate(b['project'])
                p=design.area_test_project(project,b['area_id'])
                manifest=build_project(p,self.store,self.config['game_root'],self.config['compiler'])
                self.store.save(project)
                return {'build':manifest,'area':design.find_area(project,b['area_id'])['name']}
            if route=='/api/design/open-area-build':
                from .aurora import open_project
                p=self.store.built_project(b['build_id'])
                return open_project(p,p['areas'][0]['id'],self.store,self.config['game_root'],self.config['compiler'],self.config['user_dir'])
            if route=='/api/design/test-area':
                from .launcher import game_running
                if game_running():raise ValueError('Save and exit NWN before starting an area test. Your running game was left untouched.')
                p=design.area_test_project(b['project'],b['area_id'])
                manifest=build_project(p,self.store,self.config['game_root'],self.config['compiler'])
                result=install_build(self.store,manifest['build_id'],self.config['user_dir'])
                return {'module':p['module_name'],'path':manifest['path'],'installed':result['installed']}
        if route=='/api/credentials':return {'credentials':self.credentials.update(b['provider'],b.get('key'),b.get('remove',False))}
        if route=='/api/credentials/check':
            from .provider_setup import check_models
            return check_models(self.credentials,b.get('provider'),b.get('models'))
        if route=='/api/assets/scan':return self.asset_library.scan(b['path'])
        if route=='/api/assets/list':return self.asset_library.list()
        if route=='/api/assets/detail':
            from .asset_catalog import detail
            return detail(self.asset_library,b['id'])[0]
        if route=='/api/player/register':return self.store.register_player_build(b['build_id'],b['project'])
        if route=='/api/project/save':return {'project':self.store.save(b['project'])}
        if route=='/api/project/delete':
            if b.get('confirm') is not True:raise ValueError('Confirm deletion of the selected project first')
            return self.store.delete(b['id'])
        if route=='/api/project/new':
            ident=b['id'];path=self.store.path(ident)
            if path.exists():raise ValueError('A project with that ID already exists')
            p=authoring.blank(ident,b.get('title') or 'Untitled area');p['design_mode']=b.get('design_mode','area')
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
        if route=='/api/draft':return {'proposal':self.authoring_provider.draft(validate_project(b['project']),str(b['instruction']))}
        if route=='/api/author/generate':
            from .authoring_ai import generate
            selected=next((a for a in b['project'].get('areas',[]) if a['id']==b.get('area_id')),None)
            if b.get('reference_index') is not None or (b.get('scope')=='area' and selected and selected.get('references')):
                raise ValueError('Floor-plan generation requires the objects-and-scale review. Refresh Studio and use Generate from floor plan; apply the generated proposal before opening Aurora.')
            return generate(self.authoring_provider,b['project'],str(b.get('instruction','')),b.get('scope','adventure'),b.get('area_id',''),b.get('reference_index'),asset_library=self.asset_library)
        if route=='/api/author/room-design':
            from .furnishing import room_proposal
            return room_proposal(b['project'],b['room_id'],b['style'])
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
            if project.get('design_mode')=='area':
                from .design_tools import area_test_project
                project=area_test_project(project,b.get('area_id') or project['areas'][0]['id'])
            return build_project(project,self.store,self.config['game_root'],self.config['compiler'])
        if route=='/api/build/delete':
            if b.get('confirm') is not True:raise ValueError('Confirm deletion of the selected build first')
            with BUILD_LOCK:return self.store.delete_build(b['build_id'])
        if route=='/api/install':
            with BUILD_LOCK:return install_build(self.store,b['build_id'],self.config['user_dir'])
        if route=='/api/author/open-aurora':
            from .aurora import open_project
            p=b['project']
            if p.get('design_mode')=='area':
                from .design_tools import area_test_project
                p=area_test_project(p,b['area_id'])
            return open_project(p,b['area_id'],self.store,self.config['game_root'],self.config['compiler'],self.config['user_dir'])
        if route=='/api/settings':
            b={**self.config,**b}
            if set(b)!=set(self.config) or any(not isinstance(v,str) or (not v.strip() and k!='game_root') or len(v)>1000 for k,v in b.items()):raise ValueError('Invalid settings')
            if b['provider'] not in ('openai','gemini') or any(not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',b[k]) for k in ('model','gemini_model','authoring_model','authoring_gemini_model')):raise ValueError('Invalid provider or model name')
            if b['authoring_reasoning'] not in ('default','low','medium','high','xhigh','max'):raise ValueError('Choose a supported authoring reasoning effort')
            with self.lock:
                self.asset_library.game_root=b['game_root']
                self.authoring_provider.provider=b['provider'];self.authoring_provider.model=b['authoring_gemini_model'] if b['provider']=='gemini' else b['authoring_model'];self.authoring_provider.reasoning_effort=None if b['authoring_reasoning']=='default' else b['authoring_reasoning']
                self.config=dict(b);self.provider.provider=b['provider'];self.provider.model=b['gemini_model'] if b['provider']=='gemini' else b['model'];self.bridge.path=database_path(b['user_dir']);write_json(self.store.root/'settings.json',self.config)
            return {'saved':True}
        raise ValueError('Unknown operation')

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,app):self.app=app;app.http_server=self;super().__init__(address,Handler)

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
            if route=='/api/guardrails':return self.send(200,app.guardrails.status())
            if route=='/api/usage':return self.send(200,app.ai_usage.report(query.get('period',['24h'])[0]))
            if route=='/api/assets/preview':
                from .asset_catalog import preview
                return self.send(200,preview(app.asset_library,query.get('id',[''])[0],int(query.get('angle',['35'])[0])),'image/svg+xml')
            if route=='/api/design/group-preview':
                from .native_groups import preview
                from .layout import TILESETS
                return self.send(200,preview(app.config['game_root'],TILESETS[query.get('area_type',[''])[0]],query.get('id',[''])[0],int(query.get('rotation',['0'])[0])),'image/svg+xml')
            if route=='/api/project':return self.send(200,{'project':app.store.get(query.get('id',[''])[0])})
            if route=='/api/live':
                session=next((s for s in app.bridge.sessions() if s['session_id']==query.get('session_id',[''])[0]),None)
                if session is None:raise ValueError('No active session')
                return self.send(200,{'project':app.store.built_project(session['build_id'])})
            if route=='/api/proposal':
                with app.bridge.lock:proposal=app.bridge.proposals.get(query.get('session_id',[''])[0])
                return self.send(200,{'proposal':proposal})
            if route=='/api/builds':
                return self.send(200,{'builds':app.store.builds()})
            if route=='/download':
                ident=query.get('build',[''])[0];p=app.store.built_project(ident);kind=query.get('kind',['zip'])[0]
                suffix={'zip':'-aurora.zip','mod':'.mod','project':'.rwproject.json'}.get(kind)
                if suffix is None:raise ValueError('Unknown download type')
                file=app.store.root/'builds'/ident/(p['module_name']+suffix)
                return self.send(200,file.read_bytes(),'application/octet-stream',file.name)
            static={'/':'author.html','/legacy':'index.html','/app.js':'app.js','/style.css':'style.css','/spatial.js':'spatial.js','/presets.js':'presets.js','/design.js':'design.js','/catalog.js':'catalog.js','/editor.js':'editor.js','/provider-setup.js':'provider-setup.js','/safety.js':'safety.js','/editor.css':'editor.css','/player':'player.html','/player.js':'player.js','/startup':'startup.html','/startup.js':'startup.js','/startup.css':'startup.css','/branding/splash.png':'branding/splash.png'}
            if route not in static:return self.send(404,{'error':'Not found'})
            file=ROOT/'web'/static[route];mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            return self.send(200,file.read_bytes(),mime+('; charset=utf-8' if mime.startswith('text/') or mime=='application/javascript' else ''))
        except (ValueError,FileNotFoundError,KeyError):self.send(400,{'error':'Project or artifact not found'})
    def do_POST(self):
        if not self.trusted() or not secrets.compare_digest(self.headers.get('X-Studio-Token',''),self.server.app.token):return self.send(403,{'error':'Reload Studio to establish a local session'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=18_000_000:raise ValueError('Request is empty or too large')
            body=json.loads(self.rfile.read(length));result=self.server.app.post(urlsplit(self.path).path,body)
            self.send(200,result)
        except (ValueError,KeyError,TypeError) as exc:self.send(400,{'error':str(exc)[:6500]})
        except PermissionError:self.send(400,{'error':'Access to that location was denied. Check the configured folder permissions.'})
        except Exception:self.send(500,{'error':'The operation could not finish. Check the configured paths and retry.'})

def serve(data,port=8766,open_browser=False,player=False,adventure=None):
    from .service import adventure_document,install_adventure,startup_url
    app=Application(data)
    try:server=Server(('127.0.0.1',port),app)
    except Exception:
        app.bridge.stop.set()
        raise
    url=f'http://127.0.0.1:{server.server_port}'
    try:
        if adventure:
            document=adventure_document(adventure)
            app.store.register_player_build(document['build_id'],document['project'])
            install_adventure(adventure,app.config['user_dir'])
        app.bridge.enabled=True
        print('Role Weaver service '+VERSION+': '+url+'\nKeep this service window open while playing. Start NWN separately.',flush=True)
        if open_browser:webbrowser.open(startup_url(player,server.server_port))
        with service_lock(server.server_port):server.serve_forever()
    except KeyboardInterrupt:pass
    finally:app.bridge.stop.set();server.server_close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);parser.add_argument('--data',type=Path,default=default_data());parser.add_argument('--open',action='store_true');parser.add_argument('--player',action='store_true');args=parser.parse_args()
    serve(args.data,args.port,args.open,args.player)
