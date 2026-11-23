"""Opt-in mission copies: evidence-based imports plus dedicated native adapters."""
import copy
import re

SNOW_SHA = '3b0f6cbf7273a1ba00596fe61dbb812c458d317e14b7fa703d708544297c3d5e'
ADAPTER = 'snow_hunt_ogre_v1'
TAG = 'j_ogre'
SCRIPT_HASHES = {
    'sk_dthobzul001': '757aad7163449793a2af7d27986c9336d926824022a2bfe79f95fb6df42aa002',
    'sca_oberagh001': '7e63b2cb43e8987cbb83f49b2bdb8f5e150bba235373ed8b4daba2e9aa1e8645',
    'sca_oberagh002': '23e9afffb724478e009e57b4b0689c697d99c15f418d8e7dfc45f6d4c7a5b329',
}


def empty():
    return dict(version=1, missions=[])


def eligible(report, tag):
    return report['module']['sha256'] == SNOW_SHA and tag == TAG and any(q['tag'] == TAG for q in report['quests'])


def catalog(report, path):
    from .nwn.analysis_formats import Archive, gff
    # Bind only uniquely placed actors; template-only or repeated tags are ambiguous.
    placed = [c for c in report['characters'] if c['kind'] == 'placed' and c.get('tag')]
    actors = [dict(id=c['tag'], name=c['name']) for c in placed if sum(x['tag'] == c['tag'] for x in placed) == 1]
    areas = [dict(id=a['tag'], name=a['name']) for a in report['areas'] if a['tag'] and sum(x['tag']==a['tag'] for x in report['areas'])==1]
    archive = Archive(path); items = {}
    for name, kind in archive.index:
        if kind != 2025: continue
        obj = gff(archive.get(name, kind)); tag = obj.get('Tag', '')
        label=obj.get('LocalizedName', '')
        if isinstance(label,dict):label=label.get('text','')
        if tag: items[tag] = dict(id=tag, name=label or tag)
    from .general_missions import inspect
    missions=[];cache={}
    for q in report['quests']:
        if eligible(report,q['tag']): missions.append(dict(tag=q['tag'],supported=True,controllable=True,reason='Dedicated native adapter: maps and other quests retained.'))
        else:
            try: missions.append(inspect(report,q['tag'],archive,cache))
            except ValueError as exc: missions.append(dict(tag=q['tag'],supported=False,controllable=False,reason=str(exc)))
    return dict(missions=missions,
        targets=dict(talk=actors, visit=areas, retrieve=sorted(items.values(), key=lambda x: x['name']),
                     defeat=actors))


def draft(report, tag, path=None):
    if not eligible(report, tag):
        from .general_missions import draft as imported_draft
        return imported_draft(report,tag,catalog(report,path)['targets'] if path else None,path)
    def step(ident, name, kind, target, next_id='', consume=False):
        return dict(id=ident, name=name, description=name, kind=kind, target=target, next=next_id, consume=consume)
    return dict(adapter=ADAPTER, source_tag=TAG, mode='original', risk_acknowledged=False,
        quest=dict(id='rwm_ogre', name='Rival Ogre Mages',
            description="Oberagh seeks help against his rival Obzul in the western caves. Defeat Obzul, recover his head, and return it to Oberagh.",
            completion='You have completed your agreement with Oberagh.', gold=0, xp=500,
            steps=[step('defeat_obzul', 'Defeat Obzul', 'defeat', 'obzul001', 'recover_head'),
                   step('recover_head', "Recover Obzul's head", 'retrieve', 'ogrehead001', 'return_oberagh', True),
                   step('return_oberagh', 'Return to Oberagh to claim your reward', 'talk', 'oberagh001')]),
        rewards=dict(defeat_xp=125, treasure_chest=True, negotiation=True, bonus_gold=1000, bonus_xp=50))


def _text(v, limit, name, nonempty=False):
    if not isinstance(v, str) or len(v) > limit or '\0' in v or (nonempty and not v.strip()):
        raise ValueError('Invalid editable mission '+name)


def _int(v, name):
    if type(v) is not int or not 0 <= v <= 100000: raise ValueError(name+' must be a whole number from 0 to 100,000')


def validate(value, report=None, targets=None):
    if not isinstance(value, dict) or set(value) != {'version', 'missions'} or type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Unsupported mission control settings')
    if not isinstance(value['missions'], list) or len(value['missions']) > 64: raise ValueError('Use at most 64 editable missions')
    seen=set()
    for m in value['missions']:
        if not isinstance(m,dict) or not isinstance(m.get('source_tag'),str) or m['source_tag'] in seen: raise ValueError('Use one editable copy per native mission')
        seen.add(m['source_tag'])
        from .general_missions import ADAPTER as GENERAL,validate as validate_general
        if m.get('adapter')==GENERAL:
            validate_general(m,report,targets);continue
        if not isinstance(m, dict) or set(m) != {'adapter', 'source_tag', 'mode', 'risk_acknowledged', 'quest', 'rewards'}:
            raise ValueError('Invalid mission control fields')
        if m['adapter'] != ADAPTER or m['source_tag'] != TAG: raise ValueError('Unknown mission control adapter')
        if m['mode'] not in ('original', 'studio') or type(m['risk_acknowledged']) is not bool: raise ValueError('Invalid mission control choice')
        if m['mode'] == 'studio' and not m['risk_acknowledged']: raise ValueError('Acknowledge experimental mission conversion before enabling Studio control')
        if report is not None and not eligible(report, m['source_tag']): raise ValueError('This mission adapter does not match the imported module')
        q = m['quest']; rewards = m['rewards']
        if not isinstance(q, dict) or set(q) != {'id', 'name', 'description', 'completion', 'gold', 'xp', 'steps'} or q['id'] != 'rwm_ogre': raise ValueError('Invalid editable quest fields')
        for k, limit in [('name', 160), ('description', 3000), ('completion', 1500)]: _text(q[k], limit, k, True)
        for k in ('gold', 'xp'): _int(q[k], k)
        if not isinstance(rewards, dict) or set(rewards) != {'defeat_xp', 'treasure_chest', 'negotiation', 'bonus_gold', 'bonus_xp'}: raise ValueError('Invalid editable rewards')
        for k in ('defeat_xp', 'bonus_gold', 'bonus_xp'): _int(rewards[k], k)
        for k in ('treasure_chest', 'negotiation'):
            if type(rewards[k]) is not bool: raise ValueError('Invalid reward switch')
        if not isinstance(q['steps'], list) or not 1 <= len(q['steps']) <= 20: raise ValueError('Use 1–20 objectives')
        ids = set()
        for s in q['steps']:
            if not isinstance(s, dict) or set(s) != {'id', 'name', 'description', 'kind', 'target', 'next', 'consume'}: raise ValueError('Invalid editable objective fields')
            _text(s['id'], 32, 'objective ID', True)
            if not re.fullmatch('[a-z][a-z0-9_]*', s['id']) or s['id'] in ids: raise ValueError('Use unique objective IDs')
            ids.add(s['id'])
            for k, limit in [('name', 160), ('description', 2000), ('target', 128), ('next', 32)]: _text(s[k], limit, k, k != 'next')
            if s['kind'] not in ('defeat', 'retrieve', 'visit', 'talk') or type(s['consume']) is not bool: raise ValueError('Unsupported objective type')
            if s['consume'] and s['kind'] != 'retrieve': raise ValueError('Only retrieval objectives can consume items')
            if s['kind'] == 'defeat' and s['target'] != 'obzul001': raise ValueError('Only Obzul has an audited death hook in this adapter')
            if targets is not None and s['target'] not in {t['id'] for t in targets[s['kind']]}: raise ValueError(s['name']+': choose an existing, unambiguous native target')
        if any(s['next']!=(q['steps'][i+1]['id'] if i+1<len(q['steps']) else '') for i,s in enumerate(q['steps'])):
            raise ValueError('This first adapter uses ordered objectives. Reorder them in the mission editor.')
        visited = set(); current = q['steps'][0]; by_id = {s['id']: s for s in q['steps']}
        while True:
            if current['id'] in visited: raise ValueError('Executable mission objectives cannot form a loop')
            visited.add(current['id'])
            if not current['next']: break
            if current['next'] not in by_id: raise ValueError('An objective points to a missing next objective')
            current = by_id[current['next']]
        if len(visited) != len(ids): raise ValueError('Every objective must be reachable from the first objective')
        if current['kind'] != 'talk' or current['target'] != 'oberagh001': raise ValueError('The final objective must return to Oberagh for the checked hand-in and reward')
        consumed = [s['target'] for s in q['steps'] if s['consume']]
        if len(consumed) != len(set(consumed)): raise ValueError('A consumed item can only be required once')
    return copy.deepcopy(value)


def active(p):
    return next((m for m in active_all(p) if m['adapter']==ADAPTER), None)


def active_all(p):
    return [m for m in p.get('mission_control', {}).get('missions', []) if m['mode']=='studio']


def reward_text(m):
    q=m['quest']; r=m['rewards']; parts=[f"{q['xp']} XP and {q['gold']} gold on completion"]
    if r['treasure_chest']: parts.append('one magical item of your choice from the conjured chest')
    if r['defeat_xp']: parts.append(f"{r['defeat_xp']} additional XP for defeating Obzul")
    if r['negotiation']: parts.append(f"a successful persuasion check can add {r['bonus_gold']} gold and {r['bonus_xp']} XP")
    return '; '.join(parts)+'.'


def dialogue_text(m):
    q=m['quest']; r=m['rewards']
    return {('EntryList',3):q['description']+'\n\nAgreed rewards: '+reward_text(m),
        ('EntryList',9):'How is your task progressing? We can review your progress when you are ready.',
        ('EntryList',10):q['completion']+'\n\n'+('Choose one item from the conjured chest. It vanishes after you take an item. ' if r['treasure_chest'] else '')+f"The agreed payment is {q['gold']} gold and {q['xp']} XP.",
        ('EntryList',15):f"Your argument is persuasive. Here is an additional {r['bonus_gold']} gold and {r['bonus_xp']} XP.",
        ('ReplyList',3):'I will consider the task.',('ReplyList',4):'I will undertake the task.',
        ('ReplyList',6):'I understand the agreement.',('ReplyList',7):'I will undertake the task.',
        ('ReplyList',9):'I will see this task through.',('ReplyList',14):'I am still working on the task.',
        ('ReplyList',15):'I have completed the objectives. Let us settle the agreement.',
        ('ReplyList',16):'Thank you for the agreed reward.',
        ('ReplyList',21):'<StartCheck>[Persuade]</Start> Considering my efforts, could you offer an additional reward?'}


def update_memory(p):
    """The retained dialogue IDs must recall the text actually exported."""
    m=active(p)
    if not m:return
    replacements=dialogue_text(m)
    for npc in p['npcs']:
        if npc['native_tag']!='oberagh001':continue
        for line in npc.get('native_lines',[]):
            parts=line['id'].split(':')
            if len(parts)==3 and parts[0]=='cl_oberagh001':
                key=('EntryList' if parts[1]=='e' else 'ReplyList',int(parts[2]))
                if key in replacements:line['text']=replacements[key][:3000]


def ai_context(p, npc, snapshot):
    from .general_missions import ai_context as general_context
    imported, imported_actions=general_context(p,npc,snapshot)
    m=active(p)
    raw=snapshot.get('managed_mission')
    if not m or not isinstance(raw,dict):return imported,imported_actions
    state=raw.get('state'); q=m['quest']; owner=npc['native_tag']=='oberagh001'
    if type(state) is not int or state not in [-1,*range(len(q['steps'])+1)]:return imported,imported_actions
    if state==0 and not owner:return imported,imported_actions
    out=dict(name=q['name'],state='completed' if state==-1 else 'offered' if state==0 else 'active')
    if owner:out.update(agreement=q['description'],rewards=reward_text(m))
    actions=[]
    if state==0 and owner:actions=['rwm_start']
    elif state>0:
        s=q['steps'][state-1];out['current_objective']=s['description']
        if owner and raw.get('ready')==1:actions=['rwm_claim']
        elif s['kind']=='talk' and s['next'] and s['target']==npc['native_tag']:actions=['rwm_talk']
    return ([out,*imported] if imported else out),actions+imported_actions
