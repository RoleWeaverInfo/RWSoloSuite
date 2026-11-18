"""Persistent, content-free token accounting for gameplay and authoring."""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3
import threading
import time

PERIODS={'1h':3600,'24h':86400,'7d':604800,'30d':2592000,'90d':7776000}


def token_count(value):
    return value if type(value) is int and 0<=value<=1_000_000_000 else None


def counts(data,provider):
    data=data if isinstance(data,dict) else {}
    if provider=='gemini':
        u=data.get('usageMetadata',{});u=u if isinstance(u,dict) else {}
        incoming=token_count(u.get('promptTokenCount'));visible=token_count(u.get('candidatesTokenCount'))
        reasoning=token_count(u.get('thoughtsTokenCount'));cached=token_count(u.get('cachedContentTokenCount'))
        # Gemini reports thinking separately from candidate output tokens.
        outgoing=None if visible is None else visible+(reasoning or 0)
    else:
        u=data.get('usage',{});u=u if isinstance(u,dict) else {}
        incoming=token_count(u.get('input_tokens'));outgoing=token_count(u.get('output_tokens'))
        details=u.get('input_tokens_details');cached=token_count(details.get('cached_tokens')) if isinstance(details,dict) else None
        details=u.get('output_tokens_details');reasoning=token_count(details.get('reasoning_tokens')) if isinstance(details,dict) else None
    if cached is not None and (incoming is None or cached>incoming):cached=None
    if reasoning is not None and (outgoing is None or reasoning>outgoing):reasoning=None
    return dict(input_tokens=incoming,output_tokens=outgoing,cached_tokens=cached,reasoning_tokens=reasoning)


class UsageStore:
    def __init__(self,path,clock=time.time):
        self.path=path;self.clock=clock;self.lock=threading.RLock()
        with self.connect() as db,db:
            db.executescript('''CREATE TABLE IF NOT EXISTS ai_calls (
              id INTEGER PRIMARY KEY, created REAL NOT NULL, scope TEXT NOT NULL,
              provider TEXT NOT NULL, model TEXT NOT NULL, status TEXT NOT NULL,
              api_call INTEGER NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
              cached_tokens INTEGER, reasoning_tokens INTEGER, seconds REAL, category TEXT NOT NULL DEFAULT '');
              CREATE INDEX IF NOT EXISTS ai_calls_time ON ai_calls(created,scope);''')

    def connect(self):
        return closing(sqlite3.connect(self.path,timeout=10))

    def begin(self,scope,provider,model,limits=None,blocked=''):
        now=self.clock();reason=blocked
        with self.lock,self.connect() as db,db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM ai_calls WHERE created<?',(now-PERIODS['90d'],))
            self.expire_pending(db,now)
            if limits and not reason:
                for seconds,key in ((60,'requests_per_minute'),(3600,'requests_per_hour')):
                    used=db.execute('SELECT count(*) FROM ai_calls WHERE scope=? AND api_call=1 AND created>?',(scope,now-seconds)).fetchone()[0]
                    if used>=limits[key]:reason=key;break
                midnight=datetime.fromtimestamp(now,timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()
                if not reason and limits['daily_token_limit']:
                    used,unknown=db.execute('SELECT coalesce(sum(coalesce(input_tokens,0)+coalesce(output_tokens,0)),0), coalesce(sum(CASE WHEN status!=\'pending\' AND (input_tokens IS NULL OR output_tokens IS NULL) THEN 1 ELSE 0 END),0) FROM ai_calls WHERE scope=? AND api_call=1 AND created>=?',(scope,midnight)).fetchone()
                    if unknown:reason='unknown_usage_budget'
                    elif used>=limits['daily_token_limit']:reason='daily_token_limit'
            ident=db.execute('INSERT INTO ai_calls(created,scope,provider,model,status,api_call,category) VALUES(?,?,?,?,?,?,?)',
                (now,scope,provider,model,'blocked' if reason else 'pending',0 if reason else 1,reason)).lastrowid
        return ident,reason

    @staticmethod
    def expire_pending(db,now):
        # All provider timeouts are <= 5 minutes. Interrupted calls cannot be
        # assumed free, and must not bypass an enabled daily stop after restart.
        db.execute("UPDATE ai_calls SET status='failed',category='interrupted_request' WHERE status='pending' AND created<?",(now-900,))

    def finish(self,ident,status,usage=None,seconds=0,category=''):
        u=usage or {}
        with self.lock,self.connect() as db,db:
            db.execute('UPDATE ai_calls SET status=?,input_tokens=?,output_tokens=?,cached_tokens=?,reasoning_tokens=?,seconds=?,category=? WHERE id=?',
                (status,*(token_count(u.get(k)) for k in ('input_tokens','output_tokens','cached_tokens','reasoning_tokens')),round(seconds,3),category,ident))

    def report(self,period='24h'):
        if period not in PERIODS:raise ValueError('Choose a supported usage period')
        with self.lock,self.connect() as db,db:
            self.expire_pending(db,self.clock())
            db.execute('DELETE FROM ai_calls WHERE created<?',(self.clock()-PERIODS['90d'],))
            db.row_factory=sqlite3.Row
            rows=[dict(r) for r in db.execute('SELECT * FROM ai_calls WHERE created>=? ORDER BY id',(self.clock()-PERIODS[period],))]
        def total(items):
            return dict(requests=len(items),api_calls=sum(r['api_call'] for r in items),
                failed=sum(r['status']=='failed' for r in items),blocked=sum(r['status']=='blocked' for r in items),
                replaced=sum(r['status']=='replaced' for r in items),pending=sum(r['status']=='pending' for r in items),
                unknown_usage=sum(bool(r['api_call'] and (r['input_tokens'] is None or r['output_tokens'] is None)) for r in items),
                **{k:sum(r[k] or 0 for r in items) for k in ('input_tokens','output_tokens','cached_tokens','reasoning_tokens')})
        models=sorted({(r['scope'],r['provider'],r['model']) for r in rows})
        daily=sorted({datetime.fromtimestamp(r['created'],timezone.utc).strftime('%Y-%m-%d') for r in rows})
        return dict(period=period,retention_days=90,scopes={s:total([r for r in rows if r['scope']==s]) for s in ('gameplay','authoring')},
            models=[dict(scope=s,provider=p,model=m,**total([r for r in rows if (r['scope'],r['provider'],r['model'])==(s,p,m)])) for s,p,m in models],
            daily=[dict(day=d,**{s:sum((r['input_tokens'] or 0)+(r['output_tokens'] or 0) for r in rows if r['scope']==s and datetime.fromtimestamp(r['created'],timezone.utc).strftime('%Y-%m-%d')==d) for s in ('gameplay','authoring')}) for d in daily],
            events=[{k:r[k] for k in ('created','scope','provider','model','status','category')} for r in reversed(rows) if r['category']][:30])
