import json
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from unittest.mock import Mock
from rwstudio.bridge import Bridge,DDL

ROOT=Path(__file__).resolve().parents[1]
NATIVE_QUERY=re.search(r'SqlPrepareQueryCampaign\(SPDB,"(SELECT status FROM sp_service[^\"]*)"\)',(ROOT/'scripts/sp_inc.nss').read_text()).group(1)

@contextmanager
def connection(path):
    db=sqlite3.connect(path)
    try:
        with db:yield db
    finally:db.close()


class ServicePresenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'rwsp_bridge.sqlite3'
        self.provider=Mock();self.store=Mock();self.store.built_project.return_value={'id':'project'}
        self.bridge=Bridge(self.path,self.store,self.provider)
        with connection(self.path) as db:
            for statement in DDL:db.execute(statement)
            self.now=db.execute("SELECT CAST(strftime('%s','now') AS INTEGER)").fetchone()[0]
            db.execute('INSERT INTO sp_sessions VALUES(?,?,?,?,?)',('session','project','a'*20,'{}',self.now))
            db.execute('CREATE TABLE unrelated (value TEXT)');db.execute("INSERT INTO unrelated VALUES('leave untouched')")

    def tearDown(self):
        self.bridge.stop.set()
        for thread in (self.bridge.thread,self.bridge.presence_thread):
            if thread:thread.join(6)
        self.temp.cleanup()

    def native_status(self,session='session',build='a'*20,start=None):
        with connection(self.path) as db:
            return db.execute(NATIVE_QUERY,{'s':session,'b':build,'start':self.now if start is None else start}).fetchone()

    def test_old_database_migrates_and_reports_pause_without_calling_provider(self):
        self.bridge.publish_presence();self.assertEqual(self.native_status(),('paused',))
        self.bridge.enabled=True;self.bridge.publish_presence();self.assertEqual(self.native_status(),('connected',))
        self.assertEqual(self.provider.mock_calls,[])
        with connection(self.path) as db:self.assertEqual(db.execute('SELECT value FROM unrelated').fetchone()[0],'leave untouched')

    def test_native_probe_rejects_old_saved_session_wrong_build_future_and_stale_rows(self):
        self.bridge.enabled=True;self.bridge.publish_presence()
        # The writer can cross a wall-clock second after setUp. A new saved-game
        # session must reject the actual earlier acknowledgment, not a guessed time.
        with connection(self.path) as db:published=db.execute('SELECT updated FROM sp_service').fetchone()[0]
        self.assertIsNone(self.native_status(session='another-session'))
        self.assertIsNone(self.native_status(build='b'*20))
        self.assertIsNone(self.native_status(start=published+1))
        for stamp in (self.now-31,self.now+120):
            with connection(self.path) as db:db.execute('UPDATE sp_service SET updated=?',(stamp,))
            self.assertIsNone(self.native_status(start=0))

    def test_paused_game_keeps_presence_and_reloaded_sessions_remove_old_acknowledgments(self):
        with connection(self.path) as db:db.execute('UPDATE sp_sessions SET updated=?',(self.now-3600,))
        self.bridge.enabled=True;self.bridge.publish_presence();self.assertEqual(self.native_status(),('connected',))
        with connection(self.path) as db:
            db.execute('DELETE FROM sp_sessions');db.execute('INSERT INTO sp_sessions VALUES(?,?,?,?,?)',('new-session','project','b'*20,'{}',self.now))
        self.bridge.publish_presence();self.assertIsNone(self.native_status())
        self.assertEqual(self.native_status(session='new-session',build='b'*20),('connected',))
        with connection(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM sp_service').fetchone()[0],1)

    def test_long_ai_request_does_not_stop_presence(self):
        entered=threading.Event();release=threading.Event()
        def answer(*args):
            entered.set();release.wait(10);return {'reply':'Welcome.','action':'none'}
        self.provider.npc.side_effect=answer
        with connection(self.path) as db:
            db.execute('INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(?,?,?,?,?,?,?)',
                       ('request','session','npc','npc',json.dumps({'game':{},'message':'Hello'}),self.now,self.now))
        self.bridge.enabled=True;self.bridge.start()
        try:
            self.assertTrue(entered.wait(5),'AI worker did not start')
            with connection(self.path) as db:first=db.execute('SELECT updated FROM sp_service').fetchone()[0]
            deadline=time.monotonic()+5;last=first
            while time.monotonic()<deadline and last<=first:
                time.sleep(.1)
                with connection(self.path) as db:last=db.execute('SELECT updated FROM sp_service').fetchone()[0]
            self.assertGreater(last,first,'Presence stopped while waiting for a model')
            self.assertEqual(self.native_status(),('connected',));self.assertEqual(self.provider.npc.call_count,1)
        finally:release.set()

    def test_absent_game_database_is_not_created(self):
        missing=Path(self.temp.name)/'not-created.sqlite3';self.bridge.path=missing
        with self.assertRaises(FileNotFoundError):self.bridge.publish_presence()
        self.assertFalse(missing.exists())
