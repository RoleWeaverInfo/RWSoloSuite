"""Adventure authoring schema, independent of a running game or a fixed quest."""
import copy
import re
from .content import _obj, array, enum, S, I, B, schema_check
from .merchants import SCHEMA as MERCHANT_SCHEMA, defaults as merchant_defaults, validate as validate_merchant
from .companions import SCHEMA as COMPANION_SCHEMA, NPC_SCHEMA as NPC_COMPANION_SCHEMA, defaults as companion_defaults, npc_defaults as npc_companion_defaults, validate as validate_companions

from .ambient import SCHEMA as AMBIENT_SCHEMA,NPC_SCHEMA as BEHAVIOR_SCHEMA,defaults as ambient_defaults,npc_defaults as behavior_defaults,errors as behavior_errors

AREA_TYPES={'castle':'Castle interior','dungeon':'Stone dungeon','cave':'Cave / mine','forest':'Forest / wilderness'}
SIDES=('north','east','south','west')
CREATURES={'goblin':'nw_goblina','goblin_boss':'nw_goblinboss','rat':'nw_rat001','wolf':'nw_wolf','dire_wolf':'nw_direwolf','skeleton':'nw_skeleton','zombie':'nw_zombie01','orc':'nw_orca','orc_shaman':'nw_orcwiza','bandit':'nw_bandit001','spider':'nw_spidgiant','troll':'nw_troll','ogre':'nw_ogre01','kobold':'nw_kobold001','ghoul':'nw_ghoul','bear':'nw_bearbrwn'}
DECOR={'table':97,'chair':179,'barrel':49,'bookshelf':1,'crate':4,'chest':7,'sign':87,'candle':383,'bed':50}
APPEARANCES={'innkeeper':233,'woman':255,'man':267}
ITEM_BASES={'quest_token':'nw_it_msmlmisc05','healing_potion':'nw_it_mpotion001'}
ROOM_SCHEMA=_obj({'id':S,'name':S,'x':I,'y':I,'width':I,'height':I,'description':S,'purpose':S})
AREA_SCHEMA=_obj({'id':S,'name':S,'type':enum(*AREA_TYPES),'width':I,'height':I,'room_count':I,'description':S,'lighting':enum('warm','cold','dark','daylight'),'rooms':array(ROOM_SCHEMA)})
NPC_SCHEMA=_obj({**{k:S for k in ('id','name','alias','role','room','personality','knowledge','secret','reveal_after','motivation','game_notes','greeting')},'appearance':enum(*APPEARANCES),'ai_enabled':B,'dialogue':array(_obj({'topic':S,'text':S,'after_quest':S})),'merchant':MERCHANT_SCHEMA,'companion':NPC_COMPANION_SCHEMA,'behavior':BEHAVIOR_SCHEMA})
ENCOUNTER_SCHEMA=_obj({**{k:S for k in ('id','name','room','description','after_quest','prompt','success','failure')},'kind':enum('combat','ambush','puzzle','treasure','story'),'creature':enum(*CREATURES),'count':I,'maximum':I,'scale':B,'options':array(S),'answer':I,'gold':I,'xp':I})
STEP_SCHEMA=_obj({**{k:S for k in ('id','name','description','target','next')},'kind':enum('talk','visit','retrieve','defeat','interact','choice'),'consume':B,'choices':array(_obj({'label':S,'next':S,'text':S}))})
QUEST_SCHEMA=_obj({**{k:S for k in ('id','name','description','start_npc','completion')},'optional':B,'requires':array(S),'gold':I,'xp':I,'steps':array(STEP_SCHEMA)})
SCHEMA=_obj({'schema_version':I,**{k:S for k in ('id','module_name','title','summary','story','tone','opening','ending','start_room')},'level_min':I,'level_max':I,'party_size':I,'ai_conversations':B,'companions':COMPANION_SCHEMA,'ambient':AMBIENT_SCHEMA,
 'areas':array(AREA_SCHEMA),'connections':array(_obj({**{k:S for k in ('id','name','from_room','to_room','requires_quest')},'from_side':enum(*SIDES),'to_side':enum(*SIDES),'kind':enum('corridor','exit'),'two_way':B})),
 'npcs':array(NPC_SCHEMA),'encounters':array(ENCOUNTER_SCHEMA),
 'items':array(_obj({**{k:S for k in ('id','name','description','room','container')},'kind':enum(*ITEM_BASES),'quantity':I})),
 'furnishings':array(_obj({**{k:S for k in ('id','name','room','description')},'kind':enum(*DECOR),'placement':enum(*SIDES,'center')})),
 'quests':array(QUEST_SCHEMA)})

# Encode resource-name limits in Structured Outputs as well as local validation.
# Assign new field dictionaries: the primitive schema constants are shared.
SCHEMA=copy.deepcopy(SCHEMA)
def _constrain(schema,root=False):
    if schema.get('type')=='object':
        for key,spec in list(schema['properties'].items()):
            if key=='id':schema['properties'][key]=dict(spec,pattern='^[a-z][a-z0-9_]{0,'+('39' if root else '15')+'}$')
            elif key=='module_name':schema['properties'][key]=dict(spec,pattern='^[a-z][a-z0-9_]{0,15}$')
            elif key=='alias':schema['properties'][key]=dict(spec,pattern='^[a-z][a-z0-9_]{0,23}$')
            elif key in ('start_room','room','from_room','to_room','requires_quest','after_quest','reveal_after','start_npc','container','target','next'):
                schema['properties'][key]=dict(spec,pattern='^([a-z][a-z0-9_]{0,15})?$')
            _constrain(schema['properties'][key])
    elif schema.get('type')=='array':_constrain(schema['items'])
_constrain(SCHEMA,True)
SCHEMA['properties']['schema_version']={'type':'integer','enum':[2]}

def room(ident,name,x=2,y=2,width=3,height=3,description=''):
    return dict(id=ident,name=name,x=x,y=y,width=width,height=height,description=description,purpose='Exploration')

def npc(ident,name,room_id):
    return dict(id=ident,name=name,alias=ident,role='Supporting character',room=room_id,appearance='man',ai_enabled=True,
                personality='',knowledge='',secret='',reveal_after='',motivation='',game_notes='',greeting='Greetings, traveler.',dialogue=[],merchant=merchant_defaults(),companion=npc_companion_defaults(),behavior=behavior_defaults())

def encounter(ident,name,room_id,kind='combat'):
    return dict(id=ident,name=name,room=room_id,kind=kind,description='',creature='goblin',count=1,maximum=3,scale=False,after_quest='',prompt='',options=[],answer=0,success='',failure='',gold=0,xp=0)

def step(ident,name,kind,target,next_id='',description=''):
    return dict(id=ident,name=name,description=description or name,kind=kind,target=target,next=next_id,consume=False,choices=[])

def quest(ident,name,steps=None):
    return dict(id=ident,name=name,description='',start_npc='',completion='The task is complete.',optional=False,requires=[],gold=0,xp=100,steps=steps or [])

def blank(ident='my_adventure',title='My adventure'):
    return dict(schema_version=2,id=ident,module_name=ident[:16],title=title,summary='',story='',tone='Adventurous fantasy',opening='',ending='',start_room='arrival',level_min=1,level_max=3,party_size=1,ai_conversations=True,companions=companion_defaults(True),ambient=ambient_defaults(),
                areas=[dict(id='starting_area',name='Starting area',type='castle',width=12,height=12,room_count=1,description='',lighting='warm',rooms=[room('arrival','Arrival')])],connections=[],npcs=[],encounters=[],items=[],furnishings=[],quests=[])

def seed():
    p=blank('silent_bell','The Silent Bell')
    p['companions']['enabled']=False
    p.update(module_name='rw_silent_bell',ai_conversations=False,summary='Recover the abbey bell’s stolen clapper, learn why it was silenced, and decide its fate.',
      story='The abbey bell once soothed restless dead. Its keeper secretly removed the clapper after hearing a voice demand a living sacrifice. A frightened scout saw the keeper hide it in the old vault. The player must clear the road, investigate the vault, solve its inscription, and choose to restore the bell or seal it away. Both choices conclude the story. The abbey keeper is remorseful, not a combat boss.',
      opening='At dusk, the abbey bell is silent. The road has become dangerous. Elder Ilyra waits in the guest hall, seeking someone willing to learn the truth.',
      ending='Your decision settles the fate of the Silent Bell. The abbey and its travelers can begin again. Your adventure is complete; you may keep exploring or save your game.',start_room='guest_hall')
    p['areas']=[
      dict(id='abbey',name='Emberwake Abbey',type='castle',width=14,height=10,room_count=2,description='A welcoming old abbey: worn stone, candlelit tables, supplies and a quiet bell sanctuary.',lighting='warm',rooms=[room('guest_hall','Guest hall',2,2,3,3,'Tables, beds and warm candles for travelers.'),room('sanctuary','Bell sanctuary',9,2,3,3,'A solemn chamber with a stand for the missing bell clapper.')]),
      dict(id='old_road',name='The Old Road',type='forest',width=14,height=10,room_count=2,description='Wooded clearings connected by a narrow trail. Wolves have driven travelers away.',lighting='daylight',rooms=[room('road_camp','Scout’s camp',2,2,3,3,'Supply crates beside a sheltered campsite.'),room('wolf_glade','Wolf glade',9,2,3,3,'A clearing littered with abandoned caravan supplies.')]),
      dict(id='bell_vault',name='The Forgotten Vault',type='dungeon',width=18,height=14,room_count=3,description='Three stone chambers: entrance, inscription room and sealed archive. Furnish with shelves, chests and candles.',lighting='cold',rooms=[room('vault_entry','Vault entrance',2,2,3,3),room('inscription','Inscription chamber',9,2,3,3),room('archive','Sealed archive',9,9,3,3)])]
    def connect(ident,a,b,kind='corridor',sa='east',sb='west'):
        return dict(id=ident,name='Passage',from_room=a,to_room=b,from_side=sa,to_side=sb,kind=kind,two_way=True,requires_quest='')
    p['connections']=[connect('hall_to_bell','guest_hall','sanctuary'),connect('abbey_road','guest_hall','road_camp','exit','south','west'),connect('road_trail','road_camp','wolf_glade'),connect('road_vault','wolf_glade','vault_entry','exit'),connect('vault_passage','vault_entry','inscription'),connect('archive_pass','inscription','archive','corridor','north','south')]
    ilyra=npc('ilyra','Elder Ilyra','guest_hall');ilyra.update(appearance='woman',role='Abbey elder and quest giver',personality='Patient, practical and kind.',knowledge='The bell is silent. Scout Rowan waits along the old road. Keeper Cael tends the sanctuary.',motivation='Protect travelers and learn why the bell stopped.',greeting='Our bell has fallen silent. Please speak with Rowan on the old road and make the route safe.',dialogue=[dict(topic='Why does the bell matter?',text='Its sound comforted the living and quieted the restless dead. I would rather lose the bell than a person.',after_quest='')])
    rowan=npc('rowan','Scout Rowan','road_camp');rowan.update(role='Witness and trail guide',personality='Alert, honest and a little ashamed of retreating.',knowledge='Wolves occupy the eastern clearing. The eastern exit beyond them leads to the vault. Cael carried a wrapped bronze object there.',motivation='Help the player safely reach the vault.',greeting='Keep your weapons ready. The wolves are in the eastern glade. I saw Cael take something into the vault beyond it.')
    cael=npc('cael','Keeper Cael','sanctuary');cael.update(role='Remorseful keeper',personality='Careful, fearful and deeply sincere.',knowledge='The clapper is in the archive chest in the vault. The inscription asks what can be given without being taken; the answer is trust.',secret='A voice in the bell demanded a sacrifice. Cael silenced it rather than risk a life.',reveal_after='road_safe',motivation='Let the player decide whether to restore or seal the bell.',greeting='I hid the clapper in the vault archive. The inscription’s answer is trust. Please learn the truth before judging me.')
    p['npcs']=[ilyra,rowan,cael]
    wolves=encounter('road_wolves','Wolves on the road','wolf_glade');wolves.update(creature='wolf',count=2,maximum=4,scale=True,description='A small wolf pack blocks the route to the vault.')
    puzzle=encounter('trust_stone','Inscribed stone','inscription','puzzle');puzzle.update(description='A stone asks a question before revealing its history.',prompt='What can be freely given, but never taken?',options=['Gold','Trust','A crown'],answer=1,success='The carving glows: the bell must never demand a life. Choose its fate with compassion.',failure='The letters darken. You may consider the question again.',xp=30)
    restore=encounter('bell_stand','Restore the bell','sanctuary','story');restore.update(prompt='You place the clapper in the bell. Its first quiet note carries no demand—only a promise.',success='The bell is restored.',description='The bell stand awaits the recovered clapper.')
    seal=encounter('seal_chest','Seal the clapper','archive','story');seal.update(prompt='You seal the clapper among the vault’s records. The abbey will find another way to protect the road.',success='The clapper is safely sealed.',description='A secure chest for a final decision.')
    p['encounters']=[wolves,puzzle,restore,seal]
    p['items']=[dict(id='bell_clapper',name='Bronze Bell Clapper',description='A worn bronze clapper, hidden to keep the abbey safe.',room='archive',container='',kind='quest_token',quantity=1),dict(id='road_potions',name='Healing supplies',description='Potions left for travelers.',room='guest_hall',container='',kind='healing_potion',quantity=3)]
    for rid,kinds in [('guest_hall',['table','chair','bed','candle','barrel']),('sanctuary',['candle','bookshelf']),('road_camp',['crate','barrel']),('wolf_glade',['crate']),('vault_entry',['barrel']),('inscription',['candle','bookshelf']),('archive',['bookshelf','chest','candle'])]:
        for i,kind in enumerate(kinds):p['furnishings'].append(dict(id=f'prop_{len(p["furnishings"])}',name=kind.title(),room=rid,kind=kind,placement=SIDES[i%4],description='Part of the room’s furnishings.'))
    q=quest('road_safe','A road through the silence',[step('meet_ilyra','Speak with Ilyra','talk','ilyra','find_rowan'),step('find_rowan','Find the scout','talk','rowan','clear_wolves'),step('clear_wolves','Clear the wolf glade','defeat','road_wolves','report_cael'),step('report_cael','Speak with the keeper','talk','cael')]);q.update(description='Learn what happened and make the road safe.',xp=100,gold=50,completion='The road is safe and the keeper has told you where to find the clapper.')
    q2=quest('bell_fate','The fate of the Silent Bell',[step('read_stone','Solve the vault inscription','interact','trust_stone','recover_bell'),step('recover_bell','Recover the bronze clapper','retrieve','bell_clapper','choose_fate'),step('choose_fate','Discuss the bell’s fate with Ilyra','choice','ilyra'),step('restore_bell','Restore the bell in the sanctuary','interact','bell_stand'),step('seal_bell','Seal the clapper in the archive','interact','seal_chest')]);q2.update(requires=['road_safe'],description='Recover the clapper and choose whether the bell should ring again.',completion='You have chosen the bell’s future and brought the adventure to its conclusion.',xp=200,gold=100)
    q2['steps'][2]['choices']=[dict(label='Restore the bell without sacrifice.',next='restore_bell',text='Then let its sound remind us to care for one another. Bring it to the sanctuary stand.'),dict(label='Keep the bell silent and seal the clapper.',next='seal_bell',text='Then we will keep the roads safe ourselves. Seal it in the archive chest.')]
    p['quests']=[q,q2]
    return p

def validate(p,complete=False):
    p=copy.deepcopy(p)
    if isinstance(p,dict):p.setdefault('companions',companion_defaults());p.setdefault('ambient',ambient_defaults())
    # Upgrade format-2 projects made before merchant authoring was introduced.
    if isinstance(p,dict) and isinstance(p.get('npcs'),list):
        for n in p['npcs']:
            if isinstance(n,dict):n.setdefault('merchant',merchant_defaults());n.setdefault('companion',npc_companion_defaults());n.setdefault('behavior',behavior_defaults())
    if isinstance(p,dict):
        for n in (p.get('npcs',[]) if isinstance(p.get('npcs'),list) else []):
            if isinstance(n,dict):
                if isinstance(n.get('merchant'),dict):n['merchant'].setdefault('interface','list')
                if isinstance(n.get('companion'),dict):
                    n['companion'].setdefault('inspect_containers',False);n['companion'].setdefault('social_visits',False)
                if isinstance(n.get('behavior'),dict):n['behavior'].setdefault('accept_visits',False)
        for t in (p['companions'].get('templates',[]) if isinstance(p.get('companions'),dict) and isinstance(p['companions'].get('templates'),list) else []):
            if isinstance(t,dict):t.setdefault('inspect_containers',False);t.setdefault('social_visits',False)
    schema_check(p,SCHEMA)
    validate_companions(p)
    if not 60<=p['ambient']['social_interval']<=3600 or not 1<=p['ambient']['social_budget']<=12:raise ValueError('Ambient exchanges use 60–3600 seconds and 1–12 attempts per active hour.')
    for n in p['npcs']:
        b=n['behavior']
        if not 6<=b['wait_seconds']<=300 or not 60<=b['cooldown']<=3600 or len(b['route'])>16 or len(b['partners'])>16:raise ValueError('Use up to 16 patrol stops/partners, 6–300 second waits and 60–3600 second social cooldowns.')
    if p['schema_version']!=2:raise ValueError('Expected adventure project format 2')
    for k,limit in [('id',40),('module_name',16)]:
        if not re.fullmatch('[a-z][a-z0-9_]{0,'+str(limit-1)+'}',p[k]):raise ValueError('Invalid '+k)
    if not p['title'].strip() or len(p['title'])>100:raise ValueError('Give the adventure a title of 1–100 characters')
    if not 1<=p['level_min']<=p['level_max']<=40 or not 1<=p['party_size']<=8:raise ValueError('Use levels 1–40 and an intended party size of 1–8')
    for k,maximum in [('areas',16),('npcs',48),('encounters',64),('quests',16),('items',64),('furnishings',100),('connections',64)]:
        if len(p[k])>maximum:raise ValueError(f'Limit for {k}: {maximum}')
    ids=set()
    objects=[*p['areas'],*p['connections'],*p['npcs'],*p['encounters'],*p['items'],*p['furnishings'],*p['quests'],*[r for a in p['areas'] for r in a['rooms']]]
    for o in objects:
        ident=o['id']
        if not re.fullmatch('[a-z][a-z0-9_]{0,15}',ident) or ident.startswith(('aw_','aq_','spx_')) or ident in ids:raise ValueError('Use a unique ID of 1–16 lowercase letters/digits/underscores: '+ident)
        ids.add(ident)
        if not o['name'].strip() or len(o['name'])>100:raise ValueError('Object names must contain 1–100 characters')
    for a in p['areas']:
        if not 6<=a['width']<=32 or not 6<=a['height']<=32:raise ValueError(a['name']+': area dimensions must be 6–32 tiles')
        if not 1<=a['room_count']<=16 or len(a['rooms'])>16:raise ValueError(a['name']+': use 1–16 rooms')
        for r in a['rooms']:
            if not (2<=r['width']<=16 and 2<=r['height']<=16 and r['x']>=1 and r['y']>=1 and r['x']+r['width']<a['width'] and r['y']+r['height']<a['height']):raise ValueError(r['name']+': room must fit inside the area with a one-tile border')
    aliases=set()
    for n in p['npcs']:
        validate_merchant(n)
        if not re.fullmatch('[a-z][a-z0-9_]{0,23}',n['alias']) or n['alias'] in aliases:raise ValueError('Use a unique lowercase NPC chat alias')
        aliases.add(n['alias'])
        if len(n['dialogue'])>12:raise ValueError('Use at most 12 conversation topics per NPC')
    for e in p['encounters']:
        if not 1<=e['count']<=e['maximum']<=8:raise ValueError(e['name']+': counts must be 1–8, maximum at least base count')
        if not 0<=e['gold']<=10000 or not 0<=e['xp']<=10000:raise ValueError('Encounter rewards must be 0–10000')
    for item in p['items']:
        if not 1<=item['quantity']<=10:raise ValueError('Item quantity must be 1–10')
    for q in p['quests']:
        if len(q['steps'])>20 or not 0<=q['gold']<=10000 or not 0<=q['xp']<=10000:raise ValueError('Use at most 20 objectives per quest and rewards 0–10000')
        local=set()
        for s in q['steps']:
            if not re.fullmatch('[a-z][a-z0-9_]{0,15}',s['id']) or s['id'] in local:raise ValueError(q['name']+': objective ID must be unique, lowercase, and at most 16 characters: '+s['id'])
            local.add(s['id'])
    if complete:
        result=review(p)
        if result['errors']:raise ValueError('\n'.join(result['errors'][:16]))
    return p

def review(p):
    errors=[];warnings=[]
    rooms={r['id']:(a,r) for a in p['areas'] for r in a['rooms']};npcs={n['id']:n for n in p['npcs']};quests={q['id']:q for q in p['quests']};items={i['id']:i for i in p['items']};encs={e['id']:e for e in p['encounters']}
    if not p['areas']:errors.append('Add at least one area.')
    if not p['quests'] or not any(not q['optional'] for q in p['quests']):errors.append('Add at least one main quest with a complete path to an ending.')
    if p['start_room'] not in rooms:errors.append('Choose an existing starting room.')
    if not p['opening'].strip() or not p['ending'].strip():errors.append('Write the opening and ending narration.')
    for a in p['areas']:
        if len(a['rooms'])!=a['room_count']:errors.append(f"{a['name']}: requested {a['room_count']} rooms, but {len(a['rooms'])} are defined. Generate or edit the layout.")
    graph={r:[] for r in rooms};ports=set()
    for c in p['connections']:
        if c['from_room'] not in rooms or c['to_room'] not in rooms or c['from_room']==c['to_room']:errors.append(c['name']+': select two different existing rooms.');continue
        if c['kind']=='corridor' and rooms[c['from_room']][0]['id']!=rooms[c['to_room']][0]['id']:errors.append(c['name']+': different areas require an exit connection.')
        if c['kind']=='corridor' and (c['requires_quest'] or not c['two_way']):errors.append(c['name']+': physical corridors must be two-way and ungated; use an exit for a gate or one-way passage.')
        if c['requires_quest'] and c['requires_quest'] not in quests:errors.append(c['name']+': gate references an unknown quest.')
        graph[c['from_room']].append(c['to_room'])
        if c['two_way']:graph[c['to_room']].append(c['from_room'])
        for rid,side in [(c['from_room'],c['from_side']),(c['to_room'],c['to_side'])]:
            if (rid,side) in ports:errors.append(f'{rid}: {side} exit is used more than once.')
            ports.add((rid,side))
    reached=set();todo=[p['start_room']]
    while todo:
        r=todo.pop()
        if r in reached:continue
        reached.add(r);todo.extend(graph.get(r,[]))
    for rid in rooms:
        if rid not in reached:errors.append('Room is unreachable from the start: '+rooms[rid][1]['name'])
    for collection in ('npcs','encounters','items','furnishings'):
        for o in p[collection]:
            if o['room'] not in rooms:errors.append(o['name']+': choose an existing room.')
    errors.extend(behavior_errors(p))
    if p['ambient']['social'] and not p['ai_conversations']:warnings.append('NPC social conversations require live AI enabled at export; native patrols still work offline.')
    for n in p['npcs']:
        if n['behavior']['social_enabled'] and not n['ai_enabled']:warnings.append(n['name']+': enable character AI to allow social conversations.')
        if n['companion']['requires_quest'] and n['companion']['requires_quest'] not in quests:errors.append(n['name']+': recruitment requires an unknown quest.')
        if n['companion']['recruitable'] and not p['companions']['enabled']:errors.append(n['name']+': enable companions before recruiting this NPC.')
        if n['companion']['recruitable'] and not n['companion']['essential'] and any(not q['optional'] and any(s['target']==n['id'] for s in q['steps']) for q in p['quests']):warnings.append(n['name']+' is a mortal recruitable main-quest character; death can block the story.')
        if n['merchant']['enabled'] and not n['merchant']['stock']:warnings.append(n['name']+' is a merchant with no initial stock.')
        for qid in [n['reveal_after'],*[d['after_quest'] for d in n['dialogue']]]:
            if qid and qid not in quests:errors.append(n['name']+': unknown knowledge-unlock quest '+qid)
        if not n['knowledge'].strip():warnings.append(n['name']+' has no authored knowledge yet.')
    for e in p['encounters']:
        if e['after_quest'] and e['after_quest'] not in quests:errors.append(e['name']+': unknown prerequisite quest.')
        if e['kind']=='combat' and e['after_quest']:errors.append(e['name']+': use ambush for enemies that appear after a quest.')
        if e['kind']=='puzzle' and (not 2<=len(e['options'])<=6 or not 0<=e['answer']<len(e['options'])):errors.append(e['name']+': give the puzzle 2–6 options and a valid correct answer.')
    for i in p['items']:
        if i['container'] and (i['container'] not in encs or encs[i['container']]['kind']!='treasure' or encs[i['container']]['room']!=i['room']):errors.append(i['name']+': container must be a treasure encounter in the same room.')
    def cycle(graph):
        active=set();done=set()
        def walk(n):
            if n in active:return True
            if n in done:return False
            active.add(n)
            if any(walk(x) for x in graph.get(n,[]) if x in graph):return True
            active.remove(n);done.add(n);return False
        return any(walk(n) for n in graph)
    if cycle({q['id']:q['requires'] for q in p['quests']}):errors.append('Quest prerequisites contain a cycle.')
    for q in p['quests']:
        if q['start_npc'] and q['start_npc'] not in npcs:errors.append(q['name']+': unknown starting NPC.')
        for dep in q['requires']:
            if dep not in quests:errors.append(q['name']+': unknown prerequisite '+dep)
        if not q['steps']:errors.append(q['name']+': add at least one objective.');continue
        steps={s['id']:s for s in q['steps']};edges={}
        for s in q['steps']:
            targets={'talk':npcs,'choice':npcs,'visit':rooms,'retrieve':items,'defeat':encs,'interact':encs}[s['kind']]
            if s['target'] not in targets:errors.append(q['name']+' / '+s['name']+': target does not exist or has the wrong type.')
            if s['kind']=='defeat' and s['target'] in encs and encs[s['target']]['kind'] not in ('combat','ambush'):errors.append(s['name']+': defeat requires a combat or ambush encounter.')
            if s['kind']=='interact' and s['target'] in encs and encs[s['target']]['kind'] in ('combat','ambush'):errors.append(s['name']+': interact requires puzzle, treasure or story encounter.')
            if s['kind']=='choice' and not 2<=len(s['choices'])<=6:errors.append(s['name']+': provide 2–6 choices.')
            if s['kind']!='choice' and s['choices']:errors.append(s['name']+': only choice objectives can have branches.')
            edges[s['id']]=[c['next'] for c in s['choices']] if s['kind']=='choice' else [s['next']]
            for dest in edges[s['id']]:
                if dest and dest not in steps:errors.append(s['name']+': unknown next objective '+dest)
        if cycle(edges):errors.append(q['name']+': objective paths must end, not loop.')
        seen=set();todo=[q['steps'][0]['id']]
        while todo:
            cur=todo.pop()
            if not cur or cur in seen:continue
            seen.add(cur);todo.extend(edges.get(cur,[]))
        for sid in steps:
            if sid not in seen:errors.append(q['name']+': unreachable objective '+sid)
        # A one-way passage must not strand a later objective in the same path.
        def target_room(s):
            target=s['target'];kind=s['kind']
            if kind=='visit':return target
            table=npcs if kind in ('talk','choice') else items if kind=='retrieve' else encs
            return table.get(target,{}).get('room','')
        for sid,destinations in edges.items():
            start=target_room(steps[sid]);reachable=set();todo=[start]
            while todo:
                rid=todo.pop()
                if rid in reachable:continue
                reachable.add(rid);todo.extend(graph.get(rid,[]))
            for dest in destinations:
                if dest in steps and target_room(steps[dest]) not in reachable:errors.append(q['name']+': a one-way exit prevents travel from '+steps[sid]['name']+' to '+steps[dest]['name'])
    # Prove that quest gates cannot strand required objectives behind themselves.
    if not errors:
        completed=set();remaining=list(p['quests'])
        while remaining:
            progress=False
            for q in list(remaining):
                if not set(q['requires'])<=completed:continue
                accessible={p['start_room']};changed=True
                while changed:
                    changed=False
                    for c in p['connections']:
                        if c['requires_quest'] and c['requires_quest'] not in completed:continue
                        for a,b in [(c['from_room'],c['to_room'])]+([(c['to_room'],c['from_room'])] if c['two_way'] else []):
                            if a in accessible and b not in accessible:accessible.add(b);changed=True
                needed=[];encounter_gates=[]
                if q['start_npc']:needed.append(npcs[q['start_npc']]['room'])
                for s in q['steps']:
                    target=s['target'];kind=s['kind']
                    if kind in ('talk','choice'):needed.append(npcs[target]['room'])
                    elif kind=='visit':needed.append(target)
                    elif kind=='retrieve':
                        needed.append(items[target]['room']);container=items[target]['container']
                        if container:encounter_gates.append(encs[container]['after_quest'])
                    else:needed.append(encs[target]['room']);encounter_gates.append(encs[target]['after_quest'])
                if all(r in accessible for r in needed) and all(not gate or gate in completed for gate in encounter_gates):completed.add(q['id']);remaining.remove(q);progress=True
            if not progress:break
        for q in remaining:errors.append(q['name']+': objectives are blocked by quest gates/prerequisites; check for a circular dependency.')
        consumed={s['target'] for q in p['quests'] for s in q['steps'] if s['kind']=='retrieve' and s['consume']}
        for ident in consumed:
            if sum(s['kind']=='retrieve' and s['target']==ident for q in p['quests'] for s in q['steps'])>1:errors.append('An item consumed by one objective is also required elsewhere: '+ident)
    if not errors:
        try:
            from .layout import plan
            layouts=plan(p)
        except ValueError as exc:errors.append(str(exc));layouts={}
    else:layouts={}
    for rid in rooms:
        if not any(o['room']==rid for o in p['furnishings']+p['encounters']+p['npcs']+p['items']):warnings.append(rooms[rid][1]['name']+' is empty; add content or ask AI to populate it.')
    from .furnishing import warnings as furnishing_warnings
    warnings.extend(furnishing_warnings(p))
    return {'errors':errors,'warnings':warnings,'ready':not errors,'layouts':layouts,'summary':{'areas':len(p['areas']),'rooms':len(rooms),'connections':len(p['connections']),'npcs':len(p['npcs']),'encounters':len(p['encounters']),'quests':len(p['quests']),'objectives':sum(len(q['steps']) for q in p['quests'])}}
