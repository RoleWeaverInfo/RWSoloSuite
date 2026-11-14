import copy
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import closing
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
from rwstudio.content import seed, validate_project, npc_context
from rwstudio.storage import Store, write_json
from rwstudio.bridge import Bridge, DDL
from rwstudio.provider import Provider, AIError
from rwstudio.server import Application, Server
from rwstudio.builder import build_project, ROOT
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read

class ContentTests(unittest.TestCase):
    def test_seed_and_role_validation(self):
        p=seed();self.assertEqual(validate_project(p),p)
        p['npcs'][0]['role']='support'
        with self.assertRaises(ValueError):validate_project(p)
    def test_invalid_placement_and_scaling(self):
        p=seed();p['encounters'][0]['x']=90
        with self.assertRaises(ValueError):validate_project(p)
        p=seed();p['encounters'][0]['scale']=True
        with self.assertRaises(ValueError):validate_project(p)
    def test_no_truthy_boolean_number_or_unknown_fields(self):
        for key,value in [('level_min',True),('extra','bad')]:
            p=seed();p[key]=value
            with self.assertRaises(ValueError):validate_project(p)
    def test_scope_and_reveal(self):
        p=seed();before=npc_context(p,'mc_edric',0);after=npc_context(p,'mc_edric',2)
        self.assertNotIn('secret',before['npc']);self.assertIn('secret',after['npc'])
        self.assertNotIn(p['npcs'][1]['secret'],json.dumps(after));self.assertNotIn('story',after)
    def test_reserved_object_tags_are_rejected(self):
        p=seed();p['encounters'][0]['id']='mc_satchel'
        with self.assertRaises(ValueError):validate_project(p)
        p=seed();p['furnishings']=[{'id':'spx_go_2','name':'Crate','area':'mc_hall','kind':'crate','x':20,'y':30,'facing':0}]
        with self.assertRaises(ValueError):validate_project(p)
    def test_npc_cannot_grant_quest_actions(self):
        provider=Provider('unused')
        with patch.object(provider,'request',return_value={'reply':'Hello','action':'turn_in'}):
            self.assertEqual(provider.npc(seed(),'mc_mara','hi',{'quest_stage':2,'has_satchel':True})['action'],'none')
            self.assertEqual(provider.npc(seed(),'mc_edric','hi',{'quest_stage':1,'has_satchel':False})['action'],'none')
    def test_dm_cannot_select_unbuilt_encounter(self):
        provider=Provider('unused')
        with patch.object(provider,'request',return_value={'reply':'Wait here','encounter_id':'invented_dragon','reason':'test'}):
            self.assertEqual(provider.dm(seed(),'more',{'area':'mc_cave'})['encounter_id'],'')

class FakeProvider:
    def __init__(self):self.calls=0;self.hook=None
    def npc(self,*args):
        self.calls+=1
        if self.hook:self.hook()
        return {'reply':'The cave lies east.','action':'none'}
    def visit(self,*args):
        self.calls+=1;return {'reply':'The road leads east.','action':'none'}
    def social(self,project,payload,can_continue):
        self.calls+=1;return {'line_a':'Hello','line_b':'Good day','action':'none'}
    def companion(self,*args):
        self.calls+=1;return {'reply':'Watches attentively.','action':'none','companion_action':''}
    def dm(self,*args):return {'reply':'Rest first.','encounter_id':'','reason':'Injured party'}

class BridgeTests(unittest.TestCase):
    def test_bridge_normalizes_display_punctuation_without_changing_actions(self):
        self.request()
        with patch.object(self.provider,'npc',return_value=dict(reply='I can\u2019t\u2014ask \u201cBram\u201d\u2026',action='none',story_action='keep_id')):
            self.bridge.process_one()
        with self.bridge.connect() as db:result=json.loads(db.execute('SELECT response FROM sp_requests').fetchone()[0])
        self.assertEqual(result,dict(reply='I can\'t - ask "Bram"...',action='none',story_action='keep_id'))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=Store(self.root/'data');self.provider=FakeProvider()
        self.path=self.root/'rwsp_bridge.sqlite3';self.bridge=Bridge(self.path,self.store,self.provider);self.bridge.enabled=True
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                for ddl in DDL:db.execute(ddl)
        write_json(self.store.root/'builds'/('a'*20)/'project.json',seed())
        self.snapshot={'area':'mc_cave','player_uuid':'hero','quest_stage':1,'has_satchel':False,'party':[]}
        self.now=int(time.time())
        with self.bridge.connect() as db:db.execute('INSERT INTO sp_sessions VALUES(?,?,?,?,?)',('session','missing_courier','a'*20,json.dumps(self.snapshot),self.now))
    def tearDown(self):self.temp.cleanup()
    def request(self,created=None):
        with self.bridge.connect() as db:db.execute('INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(?,?,?,?,?,?,?)',('request','session','npc','mc_edric',json.dumps({'game':self.snapshot,'message':'Where?'}),created or self.now,self.now))
    def state(self):
        with self.bridge.connect() as db:return db.execute('SELECT state FROM sp_requests').fetchone()[0]
    def test_single_claim_and_reply(self):
        self.request();self.bridge.process_one();self.bridge.process_one()
        self.assertEqual(self.provider.calls,1);self.assertEqual(self.state(),'ready')
    def test_companion_requests_use_separate_dispatch(self):
        from rwstudio.companions import example
        write_json(self.store.root/'builds'/('a'*20)/'project.json',example())
        self.request()
        with self.bridge.connect() as db:
            db.execute("UPDATE sp_sessions SET project_id='companion_trial'")
            db.execute("UPDATE sp_requests SET kind='companion',npc_tag='fam_cat'")
        self.bridge.process_one();self.assertEqual(self.state(),'ready');self.assertEqual(self.provider.calls,1)
        with self.bridge.connect() as db:response=json.loads(db.execute('SELECT response FROM sp_requests').fetchone()[0])
        self.assertEqual(response['reply'],'Watches attentively.')
    def test_player_requests_take_priority_over_older_social_work(self):
        self.request()
        with self.bridge.connect() as db:
            db.execute("INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(?,?,?,?,?,?,?)",('social','session','social','',json.dumps({'game':{},'source':'mira','target':'tomas'}),self.now-10,self.now))
        self.bridge.process_one()
        with self.bridge.connect() as db:
            states=dict(db.execute('SELECT request_id,state FROM sp_requests').fetchall())
        self.assertEqual(states,dict(request='ready',social='queued'))
    def test_visit_uses_separate_recipient_dispatch(self):
        self.request()
        with self.bridge.connect() as db:db.execute("UPDATE sp_requests SET kind='visit'")
        self.bridge.process_one();self.assertEqual(self.state(),'ready')
        with self.bridge.connect() as db:response=json.loads(db.execute('SELECT response FROM sp_requests').fetchone()[0])
        self.assertEqual(response['reply'],'The road leads east.')
    def test_social_dispatch_and_continuation_checks(self):
        self.request()
        with self.bridge.connect() as db:db.execute("UPDATE sp_requests SET kind='social'")
        self.bridge.process_one();self.assertEqual(self.state(),'ready')
        with self.bridge.connect() as db:db.execute("UPDATE sp_requests SET state='working'")
        self.assertTrue(self.bridge.social_current('request','session'))
        with self.bridge.connect() as db:db.execute("INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(?,?,?,?,?,?,?)",('player','session','npc','mc_edric','{}',self.now,self.now))
        self.assertFalse(self.bridge.social_current('request','session'))
    def test_reload_during_model_request_discards_reply(self):
        self.request()
        def reload():
            with self.bridge.connect() as db:db.execute('DELETE FROM sp_sessions')
        self.provider.hook=reload;self.bridge.process_one();self.assertEqual(self.state(),'expired')
    def test_pause_during_model_request_discards_reply(self):
        self.request();self.provider.hook=lambda:setattr(self.bridge,'enabled',False)
        self.bridge.process_one();self.assertEqual(self.state(),'expired')
    def test_expired_request_never_uses_api(self):
        self.request(self.now-121);self.bridge.process_one();self.assertEqual(self.state(),'expired');self.assertEqual(self.provider.calls,0)
    def test_commands_restricted_to_live_area_and_allowlist(self):
        for action,enc in [('execute_script',''),('spawn','unknown'),('spawn','sp_lookout')]:
            with self.assertRaises(ValueError):self.bridge.command('session',action,enc)
        result=self.bridge.command('session','spawn','sp_reserve');self.assertEqual(result['state'],'queued')
        with self.bridge.connect() as db:payload=json.loads(db.execute('SELECT payload FROM sp_commands').fetchone()[0])
        self.assertEqual(payload['player'],'hero');self.assertEqual(payload['area'],'mc_cave')
    def test_closed_transactions_leave_no_lock(self):
        for _ in range(20):self.bridge.sessions()
        with closing(sqlite3.connect(self.path,timeout=.1)) as db:db.execute('BEGIN EXCLUSIVE');db.rollback()
    def test_missing_build_is_a_safe_failed_reply(self):
        self.request()
        with self.bridge.connect() as db:db.execute('UPDATE sp_sessions SET build_id=?',('b'*20,))
        self.bridge.process_one();self.assertEqual(self.state(),'failed');self.assertEqual(self.provider.calls,0)
    def test_expired_commands_have_a_receipt(self):
        self.bridge.command('session','spawn','sp_reserve')
        with self.bridge.connect() as db:db.execute('UPDATE sp_commands SET created=?',(self.now-46,))
        self.bridge.process_one();self.assertEqual(self.bridge.receipts()[0]['state'],'expired')

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=Application(Path(self.temp.name));self.server=Server(('127.0.0.1',0),self.app)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.app.bridge.stop.set();self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def request(self,path,body=None,headers=None):
        h={'Content-Type':'application/json','X-Studio-Token':self.app.token};h.update(headers or {})
        request=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
        with urllib.request.urlopen(request) as r:return r.status,r.read()
    def test_state_is_secret_free(self):
        with patch.dict('os.environ',{'OPENAI_API_KEY':'SENTINEL_MUST_NOT_LEAK'}):
            status,raw=self.request('/api/state');self.assertEqual(status,200);self.assertNotIn(b'SENTINEL_MUST_NOT_LEAK',raw);self.assertTrue(json.loads(raw)['key_available'])
    def test_host_origin_and_csrf_rejected(self):
        for headers in [{'Host':'attacker.example'},{'Origin':'https://attacker.example'},{'X-Studio-Token':'bad'}]:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/bridge',{'enabled':True},headers)
            self.assertEqual(error.exception.code,403)
    def test_traversal_and_invalid_payload_do_not_mutate(self):
        before=len(self.app.store.list())
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/project?id=..%2Fsettings')
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/project/save',{'project':{'id':'bad'}})
        self.assertEqual(len(self.app.store.list()),before)
    def test_authoring_roundtrip_and_import_build(self):
        p=seed('another','Another adventure');p['module_name']='another'
        self.request('/api/project/save',{'project':p});_,raw=self.request('/api/project?id=another');self.assertEqual(json.loads(raw)['project'],p)
        self.request('/api/project/import',{'document':{'build_id':'c'*20,'project':p}})
        self.assertEqual(self.app.store.built_project('c'*20),p)
    def test_player_build_registration_preserves_authoring_project(self):
        from rwstudio.authoring import seed as authored_seed
        built=authored_seed();draft=copy.deepcopy(built);draft['story']='Authoring draft must survive'
        self.request('/api/project/save',{'project':draft});status,raw=self.request('/api/player/register',{'build_id':'d'*20,'project':built})
        self.assertEqual(status,200);self.assertTrue(json.loads(raw)['registered']);self.assertEqual(self.app.store.get(built['id'])['story'],draft['story'])
    def test_static_dashboard_assets(self):
        for url in ['/','/app.js','/style.css']:
            status,raw=self.request(url);self.assertEqual(status,200);self.assertGreater(len(raw),100)

class ExportTests(unittest.TestCase):
    def test_three_area_native_export(self):
        game=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights');compiler=ROOT/'vendor/nwnsc/nwnsc.exe'
        if not game.is_dir() or not compiler.is_file():self.skipTest('Installed NWN/compiler required')
        with tempfile.TemporaryDirectory() as temp:
            store=Store(Path(temp));p=seed();p['areas'].append({'id':'side_cave','name':'Side cave','template':'cave','description':'Optional chamber.'})
            p['quest']['gold']=77;p['quest']['xp']=222
            p['encounters'].append(dict(p['encounters'][0],id='side_goblin',area='side_cave'))
            m=build_project(p,store,game,compiler)
            entries={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
            self.assertEqual(m['areas'],3);self.assertEqual(m['compiled_scripts'],18)
            for script in ['sp_load','sp_enter','sp_chat','sp_beat','sp_select','sp_travel','mc_reward']:self.assertIn((script,2010),entries)
            self.assertIn(b'GiveGoldToCreature(pc, 77)',entries['mc_inc',2009]);self.assertIn(b'GiveXPToCreature(pc, 222)',entries['mc_inc',2009])
            tags=[];links=[]
            for area in ('mc_hall','mc_cave','side_cave'):
                git=read(entries[area,2023])[1]
                for group in ('Placeable List','WaypointList','Door List','Creature List'):
                    for obj in git[1][group][1]:
                        tags.append(obj[1]['Tag'][1])
                        for v in obj[1].get('VarTable',(15,[]))[1]:
                            if v[1]['Name'][1]==b'SP_TARGET':links.append(v[1]['Value'][1])
            self.assertTrue(links);self.assertTrue(all(link in tags for link in links));self.assertEqual(tags.count(b'mc_cache'),1)
            self.assertEqual(len(tags),len(set(tags)))
            for tag in ('mc_edric','mc_mara','mc_tavin'):
                dlg=read(entries[tag,2029])[1];replies=dlg[1]['ReplyList'][1]
                self.assertTrue(any(r[1]['Script'][1]==b'sp_select' for r in replies))
            self.assertFalse(any(b'NWNX' in data for (name,kind),data in entries.items() if kind==2010))
            self.assertFalse(m['gameplay_tested'])

if __name__=='__main__':unittest.main()
