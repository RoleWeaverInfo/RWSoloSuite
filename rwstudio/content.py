"""Bounded authoring data, shared by the editor, AI proposals and module export."""
import copy
import json
import math
import re
from .module_names import validate_module_name

CREATURES = {'goblin': 'nw_goblina', 'rat': 'nw_rat001'}
DECOR = {'table': 97, 'chair': 179, 'barrel': 49, 'bookshelf': 1,
         'crate': 4, 'chest': 7, 'sign': 87, 'candle': 383, 'bed': 50}
APPEARANCES = {'innkeeper': 233, 'woman': 255, 'man': 267}


def seed(project_id='missing_courier', title='The Missing Courier — AI Edition'):
    return {
        'schema_version': 1, 'id': project_id, 'module_name': 'mc_courier_ai',
        'title': title, 'summary': 'Recover a missing courier and his winter dispatches.',
        'story': 'Edric runs a caravan lodge. His courier Tavin is overdue. Scout Mara tracked him into Hollowstone Cave, where goblins stole his sealed dispatches. Find Tavin, recover the satchel, and return it to Edric. The adventure should feel warm, adventurous, and hopeful.',
        'tone': 'Grounded fantasy, warm characters, brief dialogue, light danger.',
        'level_min': 1, 'level_max': 3,
        'quest': {'title': 'The Missing Courier', 'item_name': "Tavin's Sealed Satchel",
                  'offer': 'Our courier vanished on the trail. Will you find him and bring back his sealed satchel?',
                  'accepted': 'Take these healing potions. Search the cave and return the sealed satchel to me.',
                  'found': 'You found the satchel! Please hand it over so the delivery can continue.',
                  'completed': 'The dispatches are safe. Thank you for helping our village.',
                  'gold': 150, 'xp': 300},
        'areas': [
            {'id': 'mc_hall', 'name': "Wayfarer's Hall", 'template': 'hall', 'description': 'A furnished caravan lodge and safe place to rest.'},
            {'id': 'mc_cave', 'name': 'Hollowstone Cave', 'template': 'cave', 'description': 'An old mine used by goblin scavengers.'}],
        'npcs': [
            {'tag': 'mc_edric', 'alias': 'edric', 'name': 'Edric', 'role': 'quest_giver', 'area': 'mc_hall', 'x': 24.0, 'y': 29.0, 'appearance': 'innkeeper',
             'personality': 'Kind, practical innkeeper. Worries about people before profit. Speaks plainly.',
             'knowledge': 'Tavin is overdue. Mara tracked him to the cave. The eastern doorway in the hall leads there. The sealed dispatches belong in the village. The promised reward is 150 gold and 300 XP. The hall is safe to rest in.',
             'secret': 'The dispatches contain winter supply agreements. No secret villain is involved.', 'reveal_stage': 2,
             'goal': 'Offer the retrieval quest and accept the recovered satchel. Do not require extra errands.',
             'boundaries': 'Do not invent new rewards, keys, locations, or quest requirements. Do not claim to have handed over items or paid a reward before the game confirms it.',
             'greeting': 'Welcome, traveler. Our courier is overdue, and I could use your help.'},
            {'tag': 'mc_mara', 'alias': 'mara', 'name': 'Mara', 'role': 'guide', 'area': 'mc_hall', 'x': 30.0, 'y': 27.0, 'appearance': 'woman',
             'personality': 'An observant trail scout with dry humor and a protective streak.',
             'knowledge': 'The cave entrance is the eastern doorway. A goblin lookout guards the first chamber. More stolen goods are at the far end. Equip weapons and armor; bring healing potions. Resting in the hall is safe.',
             'secret': 'Mara feels guilty for turning back when she saw the goblins.', 'reveal_stage': 1,
             'goal': 'Give useful directions and practical advice without solving the quest for the player.',
             'boundaries': 'Stay in the hall. Do not promise to join the party or invent an unbuilt route.',
             'greeting': 'You must be here about Tavin. I can show you where his tracks led.'},
            {'tag': 'mc_tavin', 'alias': 'tavin', 'name': 'Tavin', 'role': 'courier', 'area': 'mc_cave', 'x': 16.0, 'y': 55.0, 'appearance': 'man',
             'personality': 'Resourceful courier, embarrassed by a twisted ankle, grateful but proud.',
             'knowledge': 'Goblins stole the sealed satchel. It is in the chest across the back chamber. Edric needs it returned. Tavin can get home later; escorting him is not required.',
             'secret': 'He was reading a letter while walking and missed the goblin ambush.', 'reveal_stage': 2,
             'goal': 'Help the player locate the satchel and return it to Edric.',
             'boundaries': 'Do not fight, offer to travel with the player, or create an escort requirement.',
             'greeting': 'A friendly face! My ankle is twisted, but the dispatches need to get home.'}],
        'encounters': [
            {'id': 'sp_lookout', 'name': 'Goblin lookout', 'area': 'mc_cave', 'creature': 'goblin', 'count': 1, 'maximum': 1, 'x': 24.0, 'y': 32.0, 'mode': 'placed', 'scale': False, 'purpose': 'A small first combat.'},
            {'id': 'sp_scavenge', 'name': 'Goblin scavenger', 'area': 'mc_cave', 'creature': 'goblin', 'count': 1, 'maximum': 1, 'x': 31.0, 'y': 50.0, 'mode': 'placed', 'scale': False, 'purpose': 'Guard the stolen goods.'},
            {'id': 'sp_rat', 'name': 'Cave rat', 'area': 'mc_cave', 'creature': 'rat', 'count': 1, 'maximum': 1, 'x': 16.0, 'y': 41.0, 'mode': 'placed', 'scale': False, 'purpose': 'A brief interruption on the way north.'},
            {'id': 'sp_reserve', 'name': 'Returning scavengers', 'area': 'mc_cave', 'creature': 'goblin', 'count': 1, 'maximum': 3, 'x': 25.0, 'y': 44.0, 'mode': 'director', 'scale': True, 'purpose': 'An optional reinforcement scene, deployed only when the player chooses it in the dashboard.'}],
        'furnishings': [],
    }


def _obj(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


S = {'type': 'string'}
I = {'type': 'integer'}
N = {'type': 'number'}
B = {'type': 'boolean'}
def enum(*values): return {'type': 'string', 'enum': list(values)}
def array(spec): return {'type': 'array', 'items': spec}

PROJECT_SCHEMA = _obj({
    'schema_version': I, 'id': S, 'module_name': S, 'title': S, 'summary': S, 'story': S, 'tone': S,
    'level_min': I, 'level_max': I,
    'quest': _obj({**{k:S for k in ('title','item_name','offer','accepted','found','completed')}, 'gold':I,'xp':I}),
    'areas': array(_obj({'id':S,'name':S,'template':enum('hall','cave'),'description':S})),
    'npcs': array(_obj({**{k:S for k in ('tag','alias','name','area','personality','knowledge','secret','goal','boundaries','greeting')},
                        'role':enum('quest_giver','guide','courier','support'), 'x':N,'y':N,
                        'appearance':enum(*APPEARANCES),'reveal_stage':I})),
    'encounters': array(_obj({**{k:S for k in ('id','name','area','purpose')}, 'creature':enum(*CREATURES),
                             'count':I,'maximum':I,'x':N,'y':N,'mode':enum('placed','director'),'scale':B})),
    'furnishings': array(_obj({'id':S,'name':S,'area':S,'kind':enum(*DECOR),'x':N,'y':N,'facing':N})),
})


def schema_check(value, spec, path='project'):
    kind = spec['type']
    if kind == 'object':
        if not isinstance(value, dict) or set(value) != set(spec['properties']):
            raise ValueError(f'{path}: fields do not match the supported format')
        for k,s in spec['properties'].items(): schema_check(value[k],s,f'{path}.{k}')
    elif kind == 'array':
        if not isinstance(value,list) or len(value)>100: raise ValueError(f'{path}: invalid list')
        for i,v in enumerate(value): schema_check(v,spec['items'],f'{path}[{i}]')
    elif kind == 'string':
        if not isinstance(value,str) or len(value)>spec.get('maxLength',12000) or '\x00' in value: raise ValueError(f'{path}: invalid text')
        if 'enum' in spec and value not in spec['enum']: raise ValueError(f'{path}: unsupported choice')
        if 'pattern' in spec and not re.fullmatch(spec['pattern'],value):raise ValueError(f'{path}: invalid identifier {value!r}; follow the lowercase resource-name limit')
    elif kind == 'boolean':
        if type(value) is not bool: raise ValueError(f'{path}: expected yes/no')
    elif kind in ('number','integer'):
        if type(value) not in ((int,) if kind=='integer' else (int,float)) or not math.isfinite(value):
            raise ValueError(f'{path}: invalid number')


def validate_project(value):
    if isinstance(value,dict) and value.get('schema_version')==3:
        from .imported_module import validate
        return validate(value)
    if isinstance(value,dict) and value.get('schema_version')==2:
        from .authoring import validate
        return validate(value)
    schema_check(value, PROJECT_SCHEMA)
    p=copy.deepcopy(value)
    if p['schema_version']!=1: raise ValueError('Unsupported project version')
    validate_module_name(p['module_name'])
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',p['id']): raise ValueError('Invalid id')
    if not 1<=p['level_min']<=p['level_max']<=20: raise ValueError('Levels must be between 1 and 20')
    if not 2<=len(p['areas'])<=8 or not 3<=len(p['npcs'])<=24 or len(p['encounters'])>24 or len(p['furnishings'])>64:
        raise ValueError('Use 2–8 areas, 3–24 NPCs, at most 24 encounters and 64 extra furnishings')
    seen=set()
    for collection,field in [('areas','id'),('npcs','tag'),('encounters','id'),('furnishings','id')]:
        for v in p[collection]:
            ident=v[field]
            if not re.fullmatch(r'[a-z][a-z0-9_]{0,15}',ident) or ident in seen: raise ValueError('Resource IDs must be unique, lowercase, and at most 16 characters: '+ident)
            if ident.startswith('spx_') or (ident.startswith('mc_') and ident not in ('mc_hall','mc_cave','mc_edric','mc_mara','mc_tavin')):
                raise ValueError('That ID is reserved for template objects: '+ident)
            seen.add(ident)
            if not v['name'].strip() or len(v['name'])>100: raise ValueError('Names must contain 1–100 characters')
    areas={a['id']:a for a in p['areas']}
    if areas.get('mc_hall',{}).get('template')!='hall' or areas.get('mc_cave',{}).get('template')!='cave':
        raise ValueError('This recovery template requires mc_hall (hall) and mc_cave (cave)')
    aliases=set()
    for n in p['npcs']:
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,23}',n['alias']) or n['alias'] in aliases: raise ValueError('NPC aliases must be unique lowercase words')
        aliases.add(n['alias'])
        if not 0<=n['reveal_stage']<=3: raise ValueError('Secret reveal stage must be 0–3')
    npcs={n['tag']:n for n in p['npcs']}
    for tag,role in [('mc_edric','quest_giver'),('mc_mara','guide'),('mc_tavin','courier')]:
        if npcs.get(tag,{}).get('role')!=role: raise ValueError('Keep the three template quest roles; names and personalities may change')
    if sum(n['role']=='quest_giver' for n in p['npcs'])!=1: raise ValueError('Use one quest giver')
    for collection in ('npcs','encounters','furnishings'):
        for v in p[collection]:
            if v['area'] not in areas: raise ValueError('Unknown area: '+v['area'])
            bounds=(15,35,18,55) if areas[v['area']]['template']=='hall' else (13,37,25,57)
            if not (bounds[0]<=v['x']<=bounds[1] and bounds[2]<=v['y']<=bounds[3]): raise ValueError(v['name']+': position is outside the template placement region')
    for e in p['encounters']:
        if not 1<=e['count']<=e['maximum']<=6: raise ValueError('Encounter count must be 1–6 and at most its maximum')
        if e['mode']=='placed' and e['scale']: raise ValueError('Party scaling is available for director encounters at deployment')
    if not 0<=p['quest']['gold']<=10000 or not 0<=p['quest']['xp']<=10000: raise ValueError('Rewards must be 0–10000')
    if not p['title'].strip() or len(p['title'])>100: raise ValueError('Give the adventure a title of at most 100 characters')
    return p


def canonical(p): return json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def npc_context(project,tag,stage):
    npc=next((copy.deepcopy(n) for n in project['npcs'] if n['tag']==tag),None)
    if npc is None: raise ValueError('Unknown NPC')
    if stage<npc['reveal_stage']: npc.pop('secret')
    # Other NPCs' secrets and the author's unrestricted story are intentionally absent.
    return {'npc':npc,'tone':project['tone'],'public_summary':project['summary'],
            'quest_stage':stage,'quest_title':project['quest']['title'],
            'reward':{'gold':project['quest']['gold'],'xp':project['quest']['xp']},
            'areas':[{'id':a['id'],'name':a['name']} for a in project['areas']]}
