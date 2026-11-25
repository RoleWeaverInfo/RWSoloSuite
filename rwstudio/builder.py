"""Export ordinary MOD/GFF/NWScript resources; no NWNX or hosted server."""
from collections import OrderedDict
from pathlib import Path
import copy
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import threading
import zipfile
from .content import validate_project, canonical, CREATURES, DECOR, APPEARANCES
from .module_names import module_tag
from .storage import write_json
from .nwn.gff import read, write, text
from .nwn.module_copy import resources
from .nwn.game_assets import GameAssets
from .nwn.area_tools import node, set_value as put, waypoint, comments_for, pack_module

ROOT=Path(__file__).resolve().parents[1]
TYPES={2014:'ifo',2012:'are',2023:'git',2046:'gic',2027:'utc',2025:'uti',2044:'utp',2029:'dlg',2056:'jrl',2038:'fac',2009:'nss',2010:'ncs'}
BUILD_LOCK=threading.Lock()

def string(obj,key,value,kind=None): put(obj,key,value.encode('utf-8'),kind)

def position(obj,x,y,facing=90,creature=False):
    for k,v in [('XPosition' if creature else 'X',x),('YPosition' if creature else 'Y',y),('ZPosition' if creature else 'Z',0.0)]: put(obj,k,float(v),8)
    if creature:
        put(obj,'XOrientation',math.cos(math.radians(facing)),8);put(obj,'YOrientation',math.sin(math.radians(facing)),8)
    else: put(obj,'Bearing',math.radians(facing),8)

def conversation(entries,replies,starts=None):
    def edge(i,j): return node(j,Index=(4,i),Active=(11,b''),IsChild=(0,0))
    def line(i,d,group):
        return node(i,Text=(12,text(d[0])),Speaker=(10,b''),Animation=(4,0),AnimLoop=(0,0),Delay=(4,0xffffffff),Comment=(10,b''),Script=(11,(d[2] if len(d)>2 else '').encode()),Sound=(11,b''),Quest=(10,b''),**{group:(15,[edge(n,j) for j,n in enumerate(d[1])])})
    starts=starts or [(0,'')]
    dlg=node(0xffffffff,DelayEntry=(4,0),DelayReply=(4,0),NumWords=(4,sum(len(d[0].split()) for d in entries+replies)),EndConversation=(11,b''),EndConverAbort=(11,b''),PreventZoomIn=(0,0),EntryList=(15,[line(i,d,'RepliesList') for i,d in enumerate(entries)]),ReplyList=(15,[line(i,d,'EntriesList') for i,d in enumerate(replies)]),StartingList=(15,[node(i,Index=(4,n),Active=(11,a.encode())) for i,(n,a) in enumerate(starts)]))
    owned={('EntryList',i) for i,_ in starts}
    def visit(group,index):
        other,links=('ReplyList','RepliesList') if group=='EntryList' else ('EntryList','EntriesList')
        for edge in dlg[1][group][1][index][1][links][1]:
            dest=edge[1]['Index'][1];linked=(other,dest) in owned;put(edge,'IsChild',int(linked),0)
            if linked: put(edge,'LinkComment',b'',10)
            else: owned.add((other,dest));visit(other,dest)
    for i,_ in starts:visit('EntryList',i)
    return dlg

def literal(s):
    # NWScript strings use a small C escape subset. JSON handles quotes/newlines.
    return json.dumps(s,ensure_ascii=False)

def config_script(p,build):
    es=[dict(id=e['id'],area=e['area'],resref=e['id'],count=e['count'],maximum=e['maximum'],scale=int(e['scale'])) for e in p['encounters'] if e['mode']=='director']
    lines=['// Generated allowlist. Edit the project and rebuild to update.',
        'string SPProject() { return '+literal(p['id'])+'; }',
        'string SPBuild() { return '+literal(build)+'; }',
        'json SPEncounters() { return JsonParse('+literal(json.dumps(es,separators=(',',':')))+'); }',
        'int SPIsNPC(string tag) { return '+' || '.join('tag=='+literal(n['tag']) for n in p['npcs'])+'; }',
        'string SPAlias(string alias) {']
    lines += ['if(alias=='+literal(n['alias'])+') return '+literal(n['tag'])+';' for n in p['npcs']]
    lines += ['return ""; }','string SPAliases() { return '+literal(', '.join(n['alias'] for n in p['npcs']))+'; }']
    return '\n'.join(lines)+'\n'

def build_project(project,store,game_root,compiler):
    if project.get('schema_version')==2:
        from .adventure_builder import build
        return build(project,store,game_root,compiler)
    p=validate_project(project);game_root=Path(game_root);compiler=Path(compiler)
    if not (game_root/'data').is_dir(): raise ValueError('Choose the Neverwinter Nights installation folder in Settings')
    if not compiler.is_file(): raise ValueError('NWScript compiler not found; choose the bundled nwnsc compiler in Settings')
    with BUILD_LOCK:
        return _build(p,store,game_root,compiler)

def _build(p,store,game_root,compiler):
    base=(ROOT/'assets/authoring-template.erf').read_bytes()
    # Schema-1 exports use only their sp_* runtime. Conversion helpers depend
    # on authoring includes and must not be compiled into legacy projects.
    runtime_files=sorted((ROOT/'scripts').glob('sp_*.nss'))
    runtime=b''.join(f.read_bytes() for f in runtime_files)+Path(__file__).read_bytes()+base
    ident=hashlib.sha256(canonical(p).encode()+runtime).hexdigest()[:20]
    destination=store.root/'builds'/ident
    if (destination/'manifest.json').is_file(): return json.loads((destination/'manifest.json').read_text(encoding='utf-8'))
    entries=OrderedDict(((n,k),b) for n,k,b in resources(base));game=GameAssets(game_root)
    module=read(entries['module',2014])[1]
    put(module,'Mod_Name',text(p['title']));put(module,'Mod_Description',text(p['summary']+' Local adventure with optional Role Weaver Solo AI.'))
    string(module,'Mod_Tag',module_tag(p['module_name']));put(module,'Mod_ID',hashlib.sha256(ident.encode()).digest()[:16],13)
    put(module,'Mod_Area_list',[node(6,Area_Name=(11,a['id'].encode())) for a in p['areas']],15)
    for field,script in [('Mod_OnModLoad','sp_load'),('Mod_OnClientEntr','sp_enter'),('Mod_OnHeartbeat','sp_beat'),('Mod_OnPlrChat','sp_chat')]:string(module,field,script,11)
    entries['module',2014]=write(b'IFO V3.2',module)
    areas={};gits={};reserved=set()
    for area_index,a in enumerate(p['areas']):
        source='mc_hall' if a['template']=='hall' else 'mc_cave'
        ar=read(entries[source,2012])[1];git=read(entries[source,2023])[1]
        string(ar,'Tag',a['id']);string(ar,'ResRef',a['id']);put(ar,'Name',text(a['name']));string(ar,'Comments',a['description'])
        put(git,'Creature List',[],15)
        if a['id'] not in ('mc_hall','mc_cave'):
            put(git,'Door List',[],15);put(git,'WaypointList',[],15)
            # Keep template furniture, excluding the unique quest cache and notice.
            props=[]
            for i,obj in enumerate(git[1]['Placeable List'][1]):
                if obj[1]['Tag'][1] in (b'mc_cache',b'mc_board'):continue
                string(obj,'Tag',f'spx_{area_index}_{i}');string(obj,'TemplateResRef',f'spx_{area_index}_{i}')
                props.append(obj)
            put(git,'Placeable List',props,15)
        areas[a['id']]=ar;gits[a['id']]=git
        for group in ('Door List','WaypointList','Placeable List'):
            reserved.update(o[1]['Tag'][1].decode() for o in git[1][group][1])
    for group,field in [('npcs','tag'),('encounters','id'),('furnishings','id')]:
        if any(o[field] in reserved or o[field].startswith('spx_') for o in p[group]):raise ValueError('Content ID conflicts with a template object; use a different ID')
    # Remove old unused enemy blueprints; their replacements are editable exports.
    for key in [('mc_goblin_a',2027),('mc_goblin_b',2027),('mc_rat',2027)]:entries.pop(key,None)
    def creature(tag,name,base,area,x,y,npc=None):
        c=read(game.get(base,2027))[1];string(c,'Tag',tag);string(c,'TemplateResRef',tag,11);put(c,'FirstName',text(name));put(c,'LastName',text(''))
        string(c,'Conversation',tag if npc else '',11)
        if npc:
            put(c,'Appearance_Type',APPEARANCES[npc['appearance']]);put(c,'Gender',int(npc['appearance']=='woman'))
            put(c,'FactionID',2);put(c,'Plot',1);put(c,'IsImmortal',1,0);put(c,'Equip_ItemList',[],15);string(c,'ScriptHeartbeat','',11)
        entries[tag,2027]=write(b'UTC V3.2',c)
        if area:
            inst=copy.deepcopy(c);position(inst,x,y,270,True);gits[area][1]['Creature List'][1].append((4,inst[1]))
        return c
    q=p['quest']
    for n in p['npcs']:
        creature(n['tag'],n['name'],'nw_guard',n['area'],n['x'],n['y'],n)
        if n['role']=='quest_giver':
            dlg=conversation([(q['completed'],[0,4]),(q['found'],[1,0,4]),(q['accepted'],[0,4]),(n['greeting']+' '+q['offer']+f" Reward: {q['gold']} gold and {q['xp']} XP.",[2,0,4]),(q['accepted'],[0,4]),(q['completed'],[0,4])],
                [('Farewell.',[]),('Here is the recovered item.',[5],'mc_reward'),('I will help.',[4],'mc_accept'),('Goodbye.',[]),('Talk freely with AI.',[],'sp_select')],[(0,'mc_done'),(1,'mc_has'),(2,'mc_active'),(3,'')])
        else:
            dlg=conversation([(n['greeting'],[0,1,2]),(n['knowledge'],[1,2])],[('What can you tell me?',[1]),('Talk freely with AI.',[],'sp_select'),('Farewell.',[])])
        entries[n['tag'],2029]=write(b'DLG V3.2',dlg)
    for e in p['encounters']:
        c=creature(e['id'],e['name'],CREATURES[e['creature']],None,0,0)
        if e['mode']=='placed':
            for i in range(e['count']):
                inst=copy.deepcopy(c);position(inst,e['x']+(i%2)*0.7,e['y']+(i//2)*0.7,270,True)
                gits[e['area']][1]['Creature List'][1].append((4,inst[1]))
        else:gits[e['area']][1]['WaypointList'][1].append(waypoint(e['id'],e['name']+' (optional encounter)',e['x'],e['y'],map_note=True))
    pbase=read(entries['mc_crate1',2044])[1]
    def place(tag,name,appearance,area,x,y,facing=0,target=''):
        obj=copy.deepcopy(pbase);string(obj,'Tag',tag);string(obj,'TemplateResRef',tag);put(obj,'LocName',text(name));put(obj,'Appearance',appearance)
        put(obj,'Static',int(not target));put(obj,'Useable',int(bool(target)))
        if target:
            string(obj,'OnUsed','sp_travel',11)
            put(obj,'VarTable',[node(0,Name=(10,b'SP_TARGET'),Type=(4,3),Value=(10,target.encode()))],15)
        entries[tag,2044]=write(b'UTP V3.2',obj)
        position(obj,x,y,facing);gits[area][1]['Placeable List'][1].append((9,obj[1]))
    for f in p['furnishings']:place(f['id'],f['name'],DECOR[f['kind']],f['area'],f['x'],f['y'],f['facing'])
    # Usable signposts make new template areas reachable with native party travel.
    for i,a in enumerate(p['areas']):
        if a['id'] in ('mc_hall','mc_cave'):continue
        arrival=f'spx_arr_{i}';back=f'spx_back_{i}'
        gits[a['id']][1]['WaypointList'][1].append(waypoint(arrival,a['name'],25,26,map_note=True))
        gits['mc_hall'][1]['WaypointList'][1].append(waypoint(back,'Return to the hall',25,23))
        place(f'spx_go_{i}','Travel to '+a['name'],87,'mc_hall',31+(i%2)*3,46+(i//2)*3,target=arrival)
        place(f'spx_out_{i}','Return to '+next(a['name'] for a in p['areas'] if a['id']=='mc_hall'),87,a['id'],26,27,target=back)
    # Update quest item, cache instance, journal, and ordinary script text/rewards.
    item=read(entries['mc_satchel',2025])[1];put(item,'LocalizedName',text(q['item_name']));put(item,'DescIdentified',text('Return this quest item to '+next(n['name'] for n in p['npcs'] if n['tag']=='mc_edric')+'.'))
    entries['mc_satchel',2025]=write(b'UTI V3.2',item)
    j=read(entries['module',2056])[1];cat=j[1]['Categories'][1][0];put(cat,'Name',text(q['title']));put(cat,'XP',q['xp'])
    for ent,line in zip(cat[1]['EntryList'][1],[q['offer'],q['found'],q['completed']+f" Reward: {q['gold']} gold, {q['xp']} XP."]):put(ent,'Text',text(line))
    entries['module',2056]=write(b'JRL V3.2',j)
    names={a['id']:a['name'] for a in p['areas']}
    giver=next(n['name'] for n in p['npcs'] if n['tag']=='mc_edric')
    for area_id,git in gits.items():
        for obj in git[1]['Door List'][1]:
            target='mc_cave' if obj[1]['Tag'][1]==b'mc_to_cave' else 'mc_hall'
            put(obj,'LocName',text(names[target]));put(obj,'Description',text(names[target]))
        for obj in git[1]['Placeable List'][1]:
            tag=obj[1]['Tag'][1]
            if tag in (b'mc_cache',b'mc_board'):
                label=q['item_name']+' cache' if tag==b'mc_cache' else q['title']+' notice'
                description='Quest supplies and the missing item.' if tag==b'mc_cache' else q['offer']+' Speak to '+giver+'.'
                put(obj,'LocName',text(label));put(obj,'Description',text(description))
                blueprint=read(entries[tag.decode(),2044])[1];put(blueprint,'LocName',text(label));put(blueprint,'Description',text(description));entries[tag.decode(),2044]=write(b'UTP V3.2',blueprint)
        for mark in git[1]['WaypointList'][1]:
            tag=mark[1]['Tag'][1]
            label={b'mc_start':names['mc_hall'],b'mc_arr_hall':'Return from '+names['mc_cave'],b'mc_arr_cave':'Return to '+names['mc_hall'],b'mc_edric_mark':giver+' - Quest giver',b'mc_cache_mark':q['item_name']}.get(tag)
            if label:
                for field in ('LocalizedName','Description','MapNote'):put(mark,field,text(label))
    for ident_area in areas:
        entries[ident_area,2012]=write(b'ARE V3.2',areas[ident_area]);entries[ident_area,2023]=write(b'GIT V3.2',gits[ident_area]);entries[ident_area,2046]=write(b'GIC V3.2',comments_for(gits[ident_area]))
    with tempfile.TemporaryDirectory(prefix='build-',dir=store.root) as temp:
        out=Path(temp);source=out/'source';source.mkdir();compiled=out/'compiled';compiled.mkdir()
        for (name,kind),data in list(entries.items()):
            if kind==2009:(source/(name+'.nss')).write_bytes(data)
            if kind==2010:entries.pop((name,kind))
        for f in runtime_files:shutil.copy2(f,source/f.name)
        (source/'sp_config.nss').write_text(config_script(p,ident),encoding='utf-8')
        inc=(source/'mc_inc.nss').read_text(encoding='utf-8')
        inc=inc.replace('GiveGoldToCreature(pc, 150);',f"GiveGoldToCreature(pc, {q['gold']});").replace('GiveXPToCreature(pc, 300);',f"GiveXPToCreature(pc, {q['xp']});")
        inc=inc.replace('"QUEST COMPLETE: The Missing Courier. Reward: 150 gold and 300 XP."',literal('QUEST COMPLETE: '+q['title']+f". Reward: {q['gold']} gold and {q['xp']} XP."))
        giver=next(n['name'] for n in p['npcs'] if n['tag']=='mc_edric')
        inc=inc.replace('"Edric gives you three potions of Cure Light Wounds."',literal(giver+' gives you three potions of Cure Light Wounds.'))
        inc=inc.replace('reward=150 xp=300',f"reward={q['gold']} xp={q['xp']}")
        (source/'mc_inc.nss').write_text(inc,encoding='utf-8')
        (source/'mc_enter.nss').write_text('#include "mc_inc"\nvoid main(){object pc=GetEnteringObject();if(!GetIsPC(pc))return; if(MCState()==1)MCJournal(pc,10);if(MCState()==2)MCJournal(pc,20);if(MCState()>=3)MCJournal(pc,30);}\n',encoding='utf-8')
        (source/'mc_note.nss').write_text('void main(){SendMessageToPC(GetLastUsedBy(),'+literal(q['offer']+' Speak to '+giver+'.')+');}\n',encoding='utf-8')
        (source/'mc_cache.nss').write_text('void main(){object pc=GetLastOpenedBy();if(GetIsPC(pc)&&!GetLocalInt(OBJECT_SELF,"MC_SEEN")){SetLocalInt(OBJECT_SELF,"MC_SEEN",TRUE);SendMessageToPC(pc,'+literal('You find '+q['item_name']+' among the stored goods.')+');}}\n',encoding='utf-8')
        (source/'mc_death.nss').write_text('void main(){object pc=GetLastPlayerDied();DelayCommand(1.0,PopUpDeathGUIPanel(pc,TRUE,TRUE,0,'+literal('Return to '+names['mc_hall']+', or reload a saved game.')+'));}\n',encoding='utf-8')
        scripts=sorted(source.glob('*.nss'))
        result=subprocess.run([str(compiler.resolve()),'-n',str(game_root.resolve()),'-i',str(source.resolve()),'-b',str(compiled.resolve()),*[p.name for p in scripts]],cwd=source,capture_output=True,text=True,timeout=150,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (out/'compile.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode: raise ValueError('NWScript compile failed: '+(result.stdout+result.stderr)[-6000:])
        for script in scripts:
            entries[script.stem,2009]=script.read_bytes();ncs=compiled/(script.stem+'.ncs')
            if 'void main(' in script.read_text(encoding='utf-8') or 'void main()' in script.read_text(encoding='utf-8'):
                if not ncs.is_file():raise ValueError('Compiler did not produce '+ncs.name)
            if ncs.is_file():entries[script.stem,2010]=ncs.read_bytes()
        mod=out/(p['module_name']+'.mod');mod.write_bytes(pack_module(base,entries))
        packed=OrderedDict(((n,k),b) for n,k,b in resources(mod.read_bytes()))
        if packed!=entries:raise ValueError('Module resource round-trip failed')
        for (name,kind),data in entries.items():
            if kind not in (2009,2010) and write(*read(data))!=data:raise ValueError('GFF round-trip failed: '+name)
            (source/(name+'.'+TYPES[kind])).write_bytes(data)
        manifest={'build_id':ident,'project_id':p['id'],'title':p['title'],'module':mod.name,'sha256':hashlib.sha256(mod.read_bytes()).hexdigest(),'resources':len(entries),'areas':len(areas),'compiled_scripts':sum(k==2010 for _,k in entries),'gameplay_tested':False,'path':str(destination/mod.name)}
        write_json(out/'manifest.json',manifest);write_json(out/'project.json',p)
        write_json(out/(p['module_name']+'.rwproject.json'),{'build_id':ident,'project':p})
        with zipfile.ZipFile(out/(p['module_name']+'-aurora.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for f in [mod,out/'manifest.json',out/(p['module_name']+'.rwproject.json'),*source.iterdir()]:z.write(f,f.relative_to(out))
        if destination.exists():
            # An imported sidecar may already occupy this build directory.
            existing=destination/'project.json'
            if existing.is_file() and canonical(json.loads(existing.read_text(encoding='utf-8')))!=canonical(p):raise ValueError('Build ID collision')
        shutil.copytree(out,destination,dirs_exist_ok=True)
    return manifest

def install_build(store,ident,user_dir):
    from .launcher import game_running
    if game_running():raise ValueError('Save and exit NWN before installing a module or its dependencies')
    project=store.built_project(ident);folder=store.root/'builds'/ident
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    source=folder/manifest['module'];target=Path(user_dir)/'modules'/source.name
    if target.name=='mc_courier.mod':raise ValueError('Choose a new module name; keep the original adventure intact')
    if not Path(user_dir).is_dir():raise ValueError('NWN user folder does not exist')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('Build checksum mismatch')
    target.parent.mkdir(parents=True,exist_ok=True)
    backup=None
    if target.exists() and target.read_bytes()!=source.read_bytes():
        digest=hashlib.sha256(target.read_bytes()).hexdigest()[:12]
        backup=target.parent/'RoleWeaverBackups'/(target.stem+'-'+digest+'.mod')
        backup.parent.mkdir(exist_ok=True);shutil.copy2(target,backup)
    from .custom_assets import install_dependencies
    install_dependencies(folder,user_dir)
    shutil.copy2(source,target)
    return {'installed':str(target),'backup':str(backup) if backup else None,'sha256':manifest['sha256']}
