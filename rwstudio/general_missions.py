"""Evidence-based mission drafts for arbitrary imported NWN journals.

All drafts start inactive. Static evidence supplies candidates, not a walkthrough.
Only reviewed, bounded objectives and explicitly identified native calls become
executable. Difficult script relationships stay native with an actionable reason.
"""
import copy
import hashlib
import re
from .nwn.analysis_formats import Archive
from .nwn.script_analysis import analyse

ADAPTER = 'native_journal_v1'
JOURNAL = {'AddJournalQuestEntry', 'RemoveJournalQuestEntry'}
PAYMENT = {'GiveGoldToCreature', 'GiveXPToCreature'}
UNSUPPORTED = {'CreateItemOnObject', 'DestroyObject', 'ActionGiveItem', 'ActionTakeItem', 'TakeGoldFromCreature', 'CreateObject'}


def ident(tag):
    return 'rwg_' + hashlib.sha256(tag.encode('utf-8')).hexdigest()[:10]


def source(report, tag):
    found = [q for q in report.get('quests', []) if q['tag'] == tag]
    if len(found) != 1 or not tag: raise ValueError('Choose a uniquely tagged journal mission')
    return found[0]


def inspect(report, tag, path=None, cache=None):
    q = source(report, tag); scripts = {s['id']: s for s in report.get('scripts', [])}
    writers = {}; related = set(); blockers = []; warnings = []; rewards = []
    dialogue = []
    for s in scripts.values():
        for c in s.get('calls', []):
            args = c['arguments']
            if c['name']=='GetJournalQuestExperience' and args and args[0]==tag:related.add(s['id'])
            if c['name'] in JOURNAL:
                if not args or not isinstance(args[0], str):
                    blockers.append(s['id'] + ': dynamic journal tag cannot be isolated safely.')
                elif args[0] == tag:
                    writers.setdefault(s['id'], []).append(c); related.add(s['id'])
    for d in report.get('dialogues', []):
        for line in d['lines']:
            if line.get('quest') == tag:
                dialogue.append(dict(dialogue=d['id'], line=line['id'], entry=line.get('quest_entry')))
                if line.get('action'): related.add(line['action'].lower())
    # Follow literal helper calls in both directions; a helper shared with another
    # journal is never assigned wholesale to this quest.
    changed = True
    while changed:
        changed = False
        for name, s in scripts.items():
            callees = {c['arguments'][0].lower() for c in s.get('calls', []) if c['name'] in ('ExecuteScript','ExecuteScriptEnhanced') and c['arguments'] and isinstance(c['arguments'][0], str)}
            additions = (callees if name in related else set()) | ({name} if related & callees else set())
            if additions - related: related.update(additions); changed = True
    # String associations are useful to the human reviewer but do not authorize
    # edits to code. Include them as uncertainty, never as a patch allowlist.
    weak = [e['script'] for e in q.get('script_evidence', []) if e['script'] not in related]
    if weak: warnings.append('Additional string associations need inspection: ' + ', '.join(sorted(set(weak))) + '.')
    if any(c['name'] in PAYMENT|UNSUPPORTED for n in weak for c in scripts.get(n,{}).get('calls',[])):
        blockers.append('A weakly associated script contains possible rewards or item effects; their ownership needs a dedicated adapter.')
    if not writers and not dialogue: blockers.append('No direct native journal writer was recovered. Review this draft with original control.')
    archive = path if isinstance(path,Archive) else Archive(path) if path else None
    cache={} if cache is None else cache
    hashes = {}
    related_tags={c['arguments'][0] for n in related for c in scripts.get(n,{}).get('calls',[]) if c['name'] in JOURNAL and c['arguments'] and isinstance(c['arguments'][0],str)}
    related_tags.update(line.get('quest') for d in report.get('dialogues',[]) for line in d['lines'] if line.get('action') in related and line.get('quest'))
    if related_tags-{tag} and any(c['name'] in PAYMENT for n in related for c in scripts.get(n,{}).get('calls',[])):
        blockers.append('Connected reward helpers are shared with another mission; retain original control until the scripts are separated.')
    for name in sorted(related):
        s = scripts.get(name)
        if not s:
            blockers.append(name + ': referenced mission script was not recovered.'); continue
        if s.get('status') != 'decoded' or s.get('calls_total', len(s.get('calls', []))) > len(s.get('calls', [])):
            blockers.append(name + ': script evidence is incomplete; reanalyse or retain original control.')
        tags = {c['arguments'][0] for c in s.get('calls', []) if c['name'] in JOURNAL and c['arguments'] and isinstance(c['arguments'][0], str)}
        payments = [c for c in s.get('calls', []) if c['name'] in PAYMENT]
        if payments and tags - {tag}:
            blockers.append(name + ': rewards are shared with another quest; they cannot be assigned safely.')
        if any(c['name'] in UNSUPPORTED for c in s.get('calls', [])):
            blockers.append(name + ': item transfers, destruction or object creation require a dedicated adapter to preserve their side effects.')
        if any(c['name'] in ('ExecuteScript','ExecuteScriptEnhanced') and (not c['arguments'] or not isinstance(c['arguments'][0],str)) for c in s.get('calls', [])):
            blockers.append(name + ': dynamically selected helper scripts need manual analysis.')
        for c in payments:
            index = 1  # Both engine functions take recipient first, amount second.
            amount = c['arguments'][index] if len(c['arguments']) > index else None
            rewards.append(dict(script=name, offset=c['offset'], kind='gold' if c['name']=='GiveGoldToCreature' else 'xp', amount=amount if type(amount) is int else None,
                                source=name+'.ncs @ 0x'+format(c['offset'],'x'), name=c['name']))
        if name in writers or payments:
            if archive:
                if (name,2010) not in archive.index:
                    blockers.append(name + ': script belongs to a dependency pack; retain original control.'); continue
                if name not in cache:
                    raw=archive.get(name,2010);decoded=analyse(raw,include_instructions=True)
                    cache[name]=(hashlib.sha256(raw).hexdigest(),decoded['status'],any(r['op']=='STORESTATE' for r in decoded['bytecode']))
                digest,status,deferred=cache[name];hashes[name]=digest
                if status != 'decoded': blockers.append(name + ': bytecode could not be fully decoded.')
                if deferred: blockers.append(name + ': deferred actions require a dedicated adapter.')
    # Unknown engine IDs or truncated analysis can conceal a journal write. Fail
    # closed for execution, but never prevent importing/reviewing the draft.
    if any(any(n.startswith('ACTION_') for n in s.get('functions', {})) for s in scripts.values()):
        blockers.append('Engine function names are unavailable. Configure NWN and import the module again.')
    if any(s.get('status')!='decoded' for s in scripts.values()):
        blockers.append('An unreadable or partially decoded script could contain additional quest effects. Retain original control.')
    if report.get('missing_scripts'):
        blockers.append('Referenced scripts are missing. Resolve dependencies and reimport before transferring mission control.')
    if any('budget' in w.lower() or 'not inspected' in w.lower() for w in report.get('warnings', [])):
        blockers.append('The analysis reached a resource limit; native mission isolation is incomplete.')
    if len(q.get('entries', [])) > 19: warnings.append('Only the first 19 non-final entries are drafted. Review omitted stages before enabling control.')
    warnings += ['Journal entry order is a suggested editing order, not proven progression. Review branches and bind every objective.',
                 'Native conditions, local variables and unrelated side effects still run. Edited objectives can contradict original dialogue or script prerequisites.',
                 'Reward calls may be conditional, repeated or unreachable. Confirm the intended total; normal combat XP remains native.']
    return dict(tag=tag, supported=True, controllable=not blockers, reason='Import an editable draft; original control remains the default.',
                blockers=list(dict.fromkeys(blockers)), warnings=warnings, reward_evidence=rewards,
                journal_calls=[dict(script=n,offset=c['offset'],name=c['name'],entry=c['arguments'][1] if len(c['arguments'])>1 else None) for n,cs in writers.items() for c in cs],
                dialogue_writers=dialogue, related_scripts=sorted(related), original_script_hashes=hashes)


def draft(report, tag, targets=None, path=None):
    q = source(report,tag); meta = inspect(report,tag,path); targets = targets or {}
    conversations = {d['dialogue'] for d in meta['dialogue_writers']}
    conversations.update(d['id'] for d in report.get('dialogues', []) if any(l.get('action') in meta['related_scripts'] for l in d['lines']))
    candidates = {c['tag'] for c in report.get('characters', []) if c['kind']=='placed' and c.get('conversation') in conversations}
    allowed = {a['id'] for a in targets.get('talk', [])}
    candidates &= allowed; giver = next(iter(candidates)) if len(candidates)==1 else ''
    steps = []
    for entry in [e for e in q.get('entries', []) if not e['end']][:19]:
        description = entry['text'][:2000] or 'Review this journal objective.'
        # A name match is only a suggestion; the required review flag is false.
        matches = []
        for kind, words in [('retrieve',r'find|recover|collect|bring|retrieve'),('defeat',r'kill|defeat|slay'),('visit',r'visit|reach|travel|enter'),('talk',r'talk|speak|ask|meet')]:
            if not re.search(r'\b('+words+r')\b', description, re.I): continue
            for target in targets.get(kind, []):
                name=target['name'].strip()
                if len(name)>2 and re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',description,re.I): matches.append((kind,target['id']))
        stage_scripts={e['script'] for e in q.get('script_evidence',[]) if e.get('journal_entry')==entry['id']}
        item_ids={t['id'] for t in targets.get('retrieve',[])}
        for s in report.get('scripts',[]):
            if s['id'] in stage_scripts:
                matches.extend(('retrieve',c['arguments'][1]) for c in s.get('calls',[]) if c['name']=='GetItemPossessedBy' and len(c['arguments'])>1 and c['arguments'][1] in item_ids)
        for c in report.get('characters',[]):
            if c['kind']=='placed' and c['tag'] in {t['id'] for t in targets.get('defeat',[])} and any(h['script'] in stage_scripts and h['source']==c['source']+'/ScriptDeath' for h in report.get('hooks',[])):
                matches.append(('defeat',c['tag']))
        matches=list(dict.fromkeys(matches));kind, target = matches[0] if len(matches)==1 else ('review','')
        steps.append(dict(id='objective_'+str(len(steps)+1), name=re.sub(r'\s+',' ',description)[:120], description=description, kind=kind, target=target, next='', consume=False))
    steps.append(dict(id='hand_in',name='Return for the reward',description='Return to the quest giver to complete the mission.',kind='talk',target=giver,next='',consume=False))
    for a,b in zip(steps,steps[1:]): a['next']=b['id']
    finals=[e for e in q.get('entries',[]) if e['end']]
    def amount(kind):
        values=[e['amount'] for e in meta['reward_evidence'] if e['kind']==kind]
        return values[0] if len(values)==1 and type(values[0]) is int and 0<=values[0]<=100000 else 0
    return dict(adapter=ADAPTER,source_tag=tag,source_sha256=report['module']['sha256'],mode='original',risk_acknowledged=False,
                objectives_reviewed=False,rewards_reviewed=False,
                quest=dict(id=ident(tag),name=q['name'][:160] or tag,description=(q.get('entries') or [dict(text='Review the agreement for this mission.')])[0]['text'][:3000] or 'Review the agreement for this mission.',
                           completion=finals[0]['text'][:1500] if finals and finals[0]['text'] else 'The mission is complete.',giver=giver,gold=amount('gold'),xp=amount('xp'),steps=steps),rewards={})


def validate(m, report=None, targets=None):
    from .managed_missions import _text, _int
    if set(m) != {'adapter','source_tag','source_sha256','mode','risk_acknowledged','objectives_reviewed','rewards_reviewed','quest','rewards'}: raise ValueError('Invalid imported mission fields')
    _text(m['source_tag'],128,'source tag',True)
    if not isinstance(m['source_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',m['source_sha256']): raise ValueError('Invalid mission source fingerprint')
    if m['mode'] not in ('original','studio') or any(type(m[k]) is not bool for k in ('risk_acknowledged','objectives_reviewed','rewards_reviewed')): raise ValueError('Invalid mission control choice')
    if m['rewards'] != {}: raise ValueError('Unsupported imported reward settings')
    q=m['quest']
    if not isinstance(q,dict) or set(q)!={'id','name','description','completion','giver','gold','xp','steps'} or q['id']!=ident(m['source_tag']): raise ValueError('Invalid imported quest fields')
    for key,limit in [('name',160),('description',3000),('completion',1500),('giver',128)]: _text(q[key],limit,key,key!='giver')
    for key in ('gold','xp'): _int(q[key],key)
    if not isinstance(q['steps'],list) or not 1<=len(q['steps'])<=20: raise ValueError('Use 1–20 objectives')
    ids=set(); consumed=set()
    for i,s in enumerate(q['steps']):
        if not isinstance(s,dict) or set(s)!={'id','name','description','kind','target','next','consume'}: raise ValueError('Invalid imported objective fields')
        _text(s['id'],32,'objective ID',True)
        if not re.fullmatch('[a-z][a-z0-9_]*',s['id']) or s['id'] in ids: raise ValueError('Use unique objective IDs')
        ids.add(s['id'])
        for key,limit in [('name',160),('description',2000),('target',128),('next',32)]: _text(s[key],limit,key,key in ('name','description'))
        if s['kind'] not in ('review','defeat','retrieve','visit','talk') or type(s['consume']) is not bool: raise ValueError('Unsupported objective type')
        if s['consume']:
            if s['kind']!='retrieve' or s['target'] in consumed: raise ValueError('Consume each required item only once')
            consumed.add(s['target'])
    if any(s['next']!=(q['steps'][i+1]['id'] if i+1<len(q['steps']) else '') for i,s in enumerate(q['steps'])):raise ValueError('Reorder objectives in the editor to change their sequence')
    if q['steps'][-1]['kind']!='talk' or q['steps'][-1]['target']!=q['giver']: raise ValueError('Final hand-in must return to the chosen quest giver')
    if report is not None:
        source(report,m['source_tag'])
        if m['source_sha256']!=report['module']['sha256']: raise ValueError('Mission belongs to a different imported module')
    if m['mode']=='studio':
        if not m['risk_acknowledged']: raise ValueError('Acknowledge experimental mission conversion before enabling Studio control')
        if not m['objectives_reviewed'] or not m['rewards_reviewed']: raise ValueError(q['name']+': review the objective order, bindings and reward evidence first')
        if not q['giver']: raise ValueError(q['name']+': choose a quest giver')
        for s in q['steps']:
            if s['kind']=='review' or not s['target']: raise ValueError(s['name']+': choose an objective type and native target')
            if targets is not None and s['target'] not in {t['id'] for t in targets.get(s['kind'],[])}: raise ValueError(s['name']+': choose an existing, unambiguous native target')
        if report is not None:
            problems=inspect(report,m['source_tag'])['blockers']
            if problems: raise ValueError(q['name']+': '+problems[0])
    return copy.deepcopy(m)


def ai_context(p,npc,snapshot):
    raw=snapshot.get('imported_missions'); contexts=[];actions=[]
    if not isinstance(raw,dict): return None,[]
    for m in p.get('mission_control',{}).get('missions',[]):
        if m['adapter']!=ADAPTER or m['mode']!='studio': continue
        q=m['quest']; value=raw.get(q['id'],{})
        if not isinstance(value,dict): continue
        state=value.get('state'); owner=npc['native_tag']==q['giver']
        if type(state) is not int or state not in [-1,*range(len(q['steps'])+1)] or (state==0 and not owner): continue
        out=dict(id=q['id'],name=q['name'],state='completed' if state==-1 else 'offered' if state==0 else 'active')
        if owner: out.update(agreement=q['description'],rewards=f"{q['gold']} gold and {q['xp']} XP on completion.")
        if state==0 and owner: actions.append(q['id']+':start')
        elif state>0:
            s=q['steps'][state-1];out['current_objective']=s['description']
            if owner and value.get('ready')==1: actions.append(q['id']+':claim')
            elif s['kind']=='talk' and s['next'] and s['target']==npc['native_tag']: actions.append(q['id']+':talk')
        contexts.append(out)
    return contexts or None,actions
