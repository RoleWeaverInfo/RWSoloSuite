"""Shared SQLite mailbox, never edits NWN's built-in campaign tables."""
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from .provider import AIError

DDL = [
    'CREATE TABLE IF NOT EXISTS sp_sessions (session_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, build_id TEXT NOT NULL, snapshot TEXT NOT NULL, updated INTEGER NOT NULL)',
    "CREATE TABLE IF NOT EXISTS sp_requests (request_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, kind TEXT NOT NULL, npc_tag TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', response TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS sp_commands (command_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', receipt TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL)",
]


class Bridge:
    def __init__(self,path,store,provider):
        self.path=path;self.store=store;self.provider=provider
        self.enabled=False;self.error='';self.stop=threading.Event();self.thread=None
        self.proposals={};self.lock=threading.Lock()

    @contextmanager
    def connect(self):
        # Do not create a campaign database before the game establishes its own file.
        if not self.path.is_file(): raise FileNotFoundError('Start the AI module once to create its local connection.')
        db=sqlite3.connect(str(self.path),timeout=0.4)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def sessions(self):
        try:
            with self.connect() as db:
                rows=db.execute('SELECT * FROM sp_sessions WHERE updated>? ORDER BY updated DESC LIMIT 8',(int(time.time())-45,)).fetchall()
                return [dict(r)|{'snapshot':json.loads(r['snapshot'])} for r in rows]
        except (FileNotFoundError,sqlite3.Error,json.JSONDecodeError): return []

    def status(self):
        return {'enabled':self.enabled,'database_found':self.path.is_file(),'error':self.error,'sessions':self.sessions()}

    def start(self):
        if self.thread is None:
            self.thread=threading.Thread(target=self.loop,daemon=True,name='roleweaver-game-bridge');self.thread.start()

    def loop(self):
        while not self.stop.wait(1):
            if not self.enabled: continue
            try:
                self.process_one();self.error=''
            except FileNotFoundError: self.error='Waiting for the AI module to start.'
            except sqlite3.OperationalError: self.error='Waiting for the game database; close other game instances if this persists.'
            except Exception: self.error='The bridge could not process a request. Check the project/build and retry.'

    def process_one(self):
        now=int(time.time())
        with self.connect() as db:
            db.execute("UPDATE sp_commands SET state='expired',receipt='Game did not acknowledge within 45 seconds',updated=? WHERE state='queued' AND created<?",(now,now-45))
            db.execute("UPDATE sp_requests SET state='expired',updated=? WHERE state IN ('queued','working') AND created<?",(now,now-120))
            row=db.execute("SELECT r.*,s.project_id,s.build_id,s.snapshot FROM sp_requests r JOIN sp_sessions s USING(session_id) WHERE r.state='queued' AND s.updated>? AND r.created>? ORDER BY CASE WHEN r.kind='social' THEN 2 WHEN r.kind='visit' THEN 1 ELSE 0 END,r.created LIMIT 1",(now-45,now-90)).fetchone()
            if row is None: return
            # Atomic claim; more than one Studio worker cannot process the same turn.
            if db.execute("UPDATE sp_requests SET state='working',updated=? WHERE request_id=? AND state='queued'",(now,row['request_id'])).rowcount!=1: return
        response={'reply':'The connection is unavailable. You can continue using the authored conversation.','action':'none'}
        state='ready'
        try:
            project=self.store.built_project(row['build_id'])
            if project['id']!=row['project_id']: raise ValueError('Build/project mismatch')
            payload=json.loads(row['payload'])
            snapshot=payload['game']
            if row['kind']=='npc': response=self.provider.npc(project,row['npc_tag'],payload['message'],snapshot,payload.get('history',''))
            elif row['kind']=='companion':response=self.provider.companion(project,payload['message'],snapshot,payload.get('history',''))
            elif row['kind']=='visit':response=self.provider.visit(project,payload)
            elif row['kind']=='social':response=self.provider.social(project,payload,lambda:self.social_current(row['request_id'],row['session_id']))
            elif row['kind']=='dm':
                proposal=self.provider.dm(project,payload['message'],snapshot)
                response={'reply':proposal['reply'],'action':'none'}
                if proposal['encounter_id']:
                    response['reply']+=' [An optional encounter is ready to review in Solo Studio.]'
                with self.lock: self.proposals[row['session_id']]=proposal
            else: raise ValueError('Unsupported request kind')
        except AIError as exc:
            response={'reply':str(exc),'action':'none'};state='failed'
        except (ValueError,KeyError,FileNotFoundError):
            response={'reply':'Studio cannot find the matching adventure build. Import its .rwproject.json companion file, then retry.','action':'none'};state='failed'
        # Stop/reload/timeout must not deliver a stale completion or change the quest.
        with self.connect() as db:
            fresh=db.execute('SELECT updated FROM sp_sessions WHERE session_id=?',(row['session_id'],)).fetchone()
            if not self.enabled or not fresh or fresh['updated']<int(time.time())-45: state='expired'
            db.execute("UPDATE sp_requests SET state=?,response=?,updated=? WHERE request_id=? AND state='working'",(state,json.dumps(response),int(time.time()),row['request_id']))

    def social_current(self,request_id,session_id):
        if not self.enabled:return False
        with self.connect() as db:
            now=int(time.time())
            row=db.execute("SELECT 1 FROM sp_requests r JOIN sp_sessions s USING(session_id) WHERE r.request_id=? AND r.session_id=? AND r.state='working' AND r.created>? AND s.updated>?",(request_id,session_id,now-90,now-45)).fetchone()
            player=db.execute("SELECT 1 FROM sp_requests r JOIN sp_sessions s USING(session_id) WHERE r.kind!='social' AND r.state='queued' AND r.created>? AND s.updated>? LIMIT 1",(now-90,now-45)).fetchone()
            return bool(row) and player is None

    def command(self,session_id,action,encounter_id='',message=''):
        if not self.enabled: raise ValueError('Start the local companion before sending a game action')
        session=next((s for s in self.sessions() if s['session_id']==session_id),None)
        if session is None: raise ValueError('No current game connection; resume the module and retry')
        project=self.store.built_project(session['build_id'])
        if action not in ('narrate','spawn','cleanup'): raise ValueError('Unsupported game action')
        if action!='narrate':
            e=next((e for e in project['encounters'] if e['id']==encounter_id and e.get('mode')=='director'),None)
            if e is None or e['area']!=session['snapshot'].get('area'): raise ValueError('Choose a director encounter in the current area')
        payload={'action':action,'encounter_id':encounter_id,'message':message[:1000],
                 'area':session['snapshot'].get('area',''),'player':session['snapshot'].get('player_uuid','')}
        ident=uuid.uuid4().hex;now=int(time.time())
        with self.connect() as db:
            count=db.execute("SELECT count(*) FROM sp_commands WHERE session_id=? AND state='queued' AND created>?",(session_id,now-45)).fetchone()[0]
            if count>=4: raise ValueError('Wait for the game to acknowledge pending actions')
            db.execute('INSERT INTO sp_commands(command_id,session_id,payload,created,updated) VALUES(?,?,?,?,?)',(ident,session_id,json.dumps(payload),now,now))
        return {'command_id':ident,'state':'queued'}

    def receipts(self):
        try:
            with self.connect() as db:
                rows=db.execute('SELECT command_id,session_id,state,receipt,created FROM sp_commands ORDER BY created DESC LIMIT 15').fetchall()
                return [dict(r) for r in rows]
        except (FileNotFoundError,sqlite3.Error): return []
