"""Compile an authored story/room/quest graph into a standalone NWN module."""
from collections import OrderedDict
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from .authoring import validate, review, CREATURES, DECOR, APPEARANCES, ITEM_BASES
from .content import canonical
from .layout import plan, native_tiles, center, exit_point
from .storage import write_json
from .nwn.gff import read,write,text
from .nwn.module_copy import resources
from .nwn.game_assets import GameAssets
from .nwn.area_tools import node,set_value as put,new_area,empty_objects,waypoint,comments_for,pack_module
from .builder import ROOT,TYPES,BUILD_LOCK,string,position,conversation,literal
from .story_actions import native as native_story
from .merchants import CATALOG as GOODS
from .runtime_ai import adapt as adapt_ai

def local(obj,values):
    table=obj[1].get('VarTable',(15,[]))[1]
    table=[v for v in table if v[1]['Name'][1].decode() not in values]
    for key,value in values.items():table.append(node(0,Name=(10,key.encode()),Type=(4,1 if isinstance(value,int) else 3),Value=(5,value) if isinstance(value,int) else (10,value.encode())))
    put(obj,'VarTable',table,15)

def json_function(name,values):
    def native(value):
        if isinstance(value,bool):return int(value)
        if isinstance(value,list):return [native(v) for v in value]
        if isinstance(value,dict):return {k:native(v) for k,v in value.items()}
        return value
    lines=['json '+name+'(){json a=JsonArray();']
    for value in values:lines.append('a=JsonArrayInsert(a,JsonParse('+literal(json.dumps(native(value),ensure_ascii=False,separators=(',',':')))+'));')
    return '\n'.join(lines+['return a;}'])

class Placement:
    def __init__(self,rooms):self.rooms=rooms;self.used={r:[] for r in rooms}
    def take(self,rid,side=None):
        r=self.rooms[rid][1];cx,cy=center(r);candidates=[]
        for y in range(r['y']*10+5,(r['y']+r['height'])*10-3,5):
            for x in range(r['x']*10+5,(r['x']+r['width'])*10-3,5):
                # Keep both central travel lanes clear, including start/arrival points.
                if abs(x-cx)<3 or abs(y-cy)<3:continue
                score=abs(x-cx)+abs(y-cy)
                if side in ('north','south','east','west'):
                    tx,ty=exit_point(r,side,5);score=abs(x-tx)+abs(y-ty)
                candidates.append((score,x,y))
        for _,x,y in sorted(candidates):
            if all((x-ox)**2+(y-oy)**2>=16 for ox,oy in self.used[rid]):self.used[rid].append((x,y));return x,y
        raise ValueError(r['name']+': too crowded for safe object placement; enlarge it or remove content')

def build(project,store,game_root,compiler):
    p=validate(project,complete=True);game_root=Path(game_root);compiler=Path(compiler)
    if not (game_root/'data').is_dir() or not compiler.is_file():raise ValueError('Set the installed NWN folder and NWScript compiler in Settings')
    with BUILD_LOCK:return _build(p,store,game_root,compiler)

def _build(p,store,game_root,compiler):
    source_files=[Path(__file__),Path(__file__).with_name('layout.py'),Path(__file__).with_name('authoring.py'),Path(__file__).with_name('story_actions.py'),Path(__file__).with_name('merchants.py'),Path(__file__).with_name('companions.py'),Path(__file__).with_name('ambient.py'),Path(__file__).with_name('runtime_ai.py'),*sorted((ROOT/'authoring_scripts').glob('*.nss')),*sorted((ROOT/'scripts').glob('*.nss'))]
    base=(ROOT/'assets/base.mod').read_bytes();digest=hashlib.sha256(canonical(p).encode()+base+b''.join(f.read_bytes() for f in source_files)).hexdigest()[:20]
    destination=store.root/'builds'/digest
    if (destination/'manifest.json').exists():
        result=json.loads((destination/'manifest.json').read_text(encoding='utf-8'));result['path']=str(destination/result['module']);return result
    original={(n,k):b for n,k,b in resources(base)};entries=OrderedDict();entries['repute',2038]=original['repute',2038]
    game=GameAssets(game_root);layouts=plan(p);rooms={r['id']:(a,r) for a in p['areas'] for r in a['rooms']};placement=Placement(rooms)
    escrow=read(game.get('nw_lostitems',2051))[1];string(escrow,'ResRef','aw_escrow',11);string(escrow,'Tag','aw_escrow');put(escrow,'LocName',text('Temporary item transfer'))
    entries['aw_escrow',2051]=write(b'UTM V3.2',escrow)
    satchel=read(game.get('nw_it_contain001',2025))[1];string(satchel,'Tag','aw_satchel');string(satchel,'TemplateResRef','aw_satchel',11);put(satchel,'LocalizedName',text('Companion satchel'));put(satchel,'PropertiesList',[],15);put(satchel,'Plot',1);put(satchel,'Identified',1);put(satchel,'Cost',0);put(satchel,'AddCost',0);put(satchel,'StackSize',1)
    put(satchel,'DescIdentified',text('A recoverable companion satchel kept in its owner’s inventory. Its contents remain when a familiar or summon disappears.'));entries['aw_satchel',2025]=write(b'UTI V3.2',satchel)
    areas={};gits={};room_index={r:i for i,r in enumerate(rooms)};enc_index={e['id']:i for i,e in enumerate(p['encounters'])};npcs={n['id']:n for n in p['npcs']};quest_index={q['id']:i for i,q in enumerate(p['quests'])}
    area_template=read(original['mc_hall',2012])[1];git_template=read(original['mc_hall',2023])[1];tile_template=area_template[1]['Tile_List'][1][0]
    for a in p['areas']:
        ar=new_area(area_template,a['id'],a['name'],layouts[a['id']]['tileset'],a['width'],a['height'],native_tiles(tile_template,a,layouts[a['id']]),a['type']=='forest')
        string(ar,'Comments',a['description']);string(ar,'OnEnter','aw_area',11);put(ar,'NoRest',0,0)
        ambient={'warm':0x8297B5,'cold':0xB0A080,'dark':0x505050,'daylight':0xC0D0D0}[a['lighting']]
        for key in ('SunAmbientColor','MoonAmbientColor'):put(ar,key,ambient)
        areas[a['id']]=ar;gits[a['id']]=empty_objects(git_template,a['type']=='forest')
        for r in a['rooms']:
            x,y=center(r);gits[a['id']][1]['WaypointList'][1].append(waypoint('aw_r_'+str(room_index[r['id']]),r['name'],x,y,map_note=True))
    start_area,start_room=rooms[p['start_room']];sx,sy=center(start_room)
    gits[start_area['id']][1]['WaypointList'][1].append(waypoint('aw_start','Adventure start',sx,sy))
    module=read(original['module',2014])[1]
    for key in list(module[1]):
        if key.startswith('Mod_On'):put(module,key,b'')
    for key,value in [('Mod_Name',text(p['title'])),('Mod_Description',text(p['summary']+f" A standalone single-player adventure for levels {p['level_min']}-{p['level_max']}.")),('Mod_Tag',p['module_name'].encode()),('Mod_Entry_Area',start_area['id'].encode())]:put(module,key,value)
    put(module,'Mod_ID',hashlib.sha256(digest.encode()).digest()[:16],13);put(module,'Mod_HakList',[],15);put(module,'Mod_Area_list',[node(6,Area_Name=(11,a['id'].encode())) for a in p['areas']],15)
    for k,v in [('Mod_Entry_X',sx),('Mod_Entry_Y',sy),('Mod_Entry_Z',0.),('Mod_Entry_Dir_X',0.),('Mod_Entry_Dir_Y',1.)]:put(module,k,float(v),8)
    for k,s in [('Mod_OnModLoad','aw_load'),('Mod_OnClientEntr','aw_enter'),('Mod_OnHeartbeat','aw_beat'),('Mod_OnAcquirItem','aw_acquire'),('Mod_OnPlrDeath','aw_death'),('Mod_OnSpawnBtnDn','aw_respawn')]:string(module,k,s,11)
    if p['ai_conversations']:string(module,'Mod_OnPlrChat','sp_chat',11)
    elif p['companions']['enabled']:string(module,'Mod_OnPlrChat','aw_cp_chat',11)
    entries['module',2014]=write(b'IFO V3.2',module)
    scripts={f.stem:f.read_text(encoding='utf-8') for f in (ROOT/'authoring_scripts').glob('*.nss')}
    def script(name,body):scripts[name]=body+'\n';return name
    def conditional(name,expression,header='aw_quest'):return script(name,'#include "'+header+'"\nint StartingConditional(){return '+expression+';}')
    shops=[];merchant_inventory={}
    item_table=game.get('baseitems',2017).decode('latin1').splitlines()
    item_header=next(line.split() for line in item_table if 'InvSlotWidth' in line and 'InvSlotHeight' in line)
    item_sizes={}
    for line in item_table:
        parts=line.split()
        if parts and parts[0].isdigit():
            values=dict(zip(item_header,parts[1:]))
            if values.get('InvSlotWidth','').isdigit() and values.get('InvSlotHeight','').isdigit():item_sizes[int(parts[0])]=(int(values['InvSlotWidth']),int(values['InvSlotHeight']))
    for ni,n in enumerate(p['npcs']):
        if not n['merchant']['enabled']:continue
        shop=dict(n['merchant'],id=n['id']);stock=[];inventory=[];occupied=set()
        for si,s in enumerate(shop['stock']):
            good=GOODS[s['item']];ref=f'aw_s_{ni}_{si}'
            obj=read(game.get(good['resref'],2025))[1];string(obj,'Tag',ref);string(obj,'TemplateResRef',ref,11)
            put(obj,'LocalizedName',text(good['name']));put(obj,'StackSize',1);put(obj,'Plot',0);put(obj,'Identified',1)
            entries[ref,2025]=write(b'UTI V3.2',obj)
            stock.append(dict(s,name=good['name'],tag=ref,resref=ref))
            width,height=item_sizes[obj[1]['BaseItem'][1]]
            for _ in range(s['quantity']):
                position_found=None
                for y in range(512):
                    for x in range(9-width):
                        cells={(x+dx,y+dy) for dx in range(width) for dy in range(height)}
                        if not cells&occupied:position_found=(x,y,cells);break
                    if position_found:break
                if position_found is None:raise ValueError(n['name']+': stock cannot fit in the merchant inventory')
                x,y,cells=position_found;occupied.update(cells)
                inventory.append(node(len(inventory),InventoryRes=(11,ref.encode()),Repos_PosX=(2,x),Repos_Posy=(2,y)))
        shop['stock']=stock;shops.append(shop);merchant_inventory[n['id']]=inventory
    def creature(ident,name,base_name,rid=None,appearance=None,enemy=False,enc=None):
        obj=read(game.get(base_name,2027))[1];string(obj,'Tag',ident);string(obj,'TemplateResRef',ident,11);put(obj,'FirstName',text(name));put(obj,'LastName',text(''))
        recruitable=not enemy and npcs[ident]['companion']['recruitable']
        protected=not enemy and (not recruitable or npcs[ident]['companion']['essential'])
        string(obj,'Conversation','' if enemy else ident,11);put(obj,'FactionID',1 if enemy else 2);put(obj,'Plot',int(protected));put(obj,'IsImmortal',int(protected),0)
        if appearance is not None:put(obj,'Appearance_Type',appearance);put(obj,'Gender',int(appearance==255))
        if enemy:
            local(obj,{'AW_ENC':ident,'AW_BASE_DEATH':obj[1].get('ScriptDeath',(11,b''))[1].decode()});string(obj,'ScriptDeath','aw_dead',11)
        else:
            if not recruitable:put(obj,'Equip_ItemList',[],15);string(obj,'ScriptHeartbeat','',11)
            if ident in merchant_inventory:
                put(obj,'ItemList',merchant_inventory[ident],15);string(obj,'ScriptSpawn','',11)
        entries[ident,2027]=write(b'UTC V3.2',obj)
        if rid:
            count=enc['count'] if enc else 1
            for i in range(count):
                x,y=placement.take(rid);inst=copy.deepcopy(obj);position(inst,x,y,270,True);gits[rooms[rid][0]['id']][1]['Creature List'][1].append((4,inst[1]))
        return obj
    pbase=read(original['mc_crate1',2044])[1]
    def place(ident,name,rid,appearance,usable=False,inventory=None,onused='',onopen='',description='',side=None,gate='',variables=None):
        obj=copy.deepcopy(pbase)
        for key in list(obj[1]):
            if key.startswith('On'):put(obj,key,b'')
        string(obj,'Tag',ident);string(obj,'TemplateResRef',ident,11);put(obj,'LocName',text(name));put(obj,'Description',text(description));put(obj,'Appearance',appearance)
        put(obj,'Static',int(not usable));put(obj,'Useable',int(usable));put(obj,'HasInventory',int(inventory is not None));put(obj,'Plot',1)
        put(obj,'Locked',int(bool(gate)));put(obj,'Lockable',int(bool(gate)));put(obj,'KeyRequired',int(bool(gate)),0);put(obj,'OpenLockDC',255 if gate else 0,0)
        if inventory is not None:put(obj,'ItemList',[node(i,InventoryRes=(11,item.encode()),Repos_PosX=(2,i),Repos_PosY=(2,0)) for i,item in enumerate(inventory)],15)
        if onused:string(obj,'OnUsed',onused,11)
        if onopen:string(obj,'OnOpen',onopen,11)
        if variables:local(obj,variables)
        entries[ident,2044]=write(b'UTP V3.2',obj)
        x,y=placement.take(rid,side);position(obj,x,y);gits[rooms[rid][0]['id']][1]['Placeable List'][1].append((9,obj[1]));return x,y
    for ni,n in enumerate(p['npcs']):
        creature(n['id'],n['name'],'nw_guard',n['room'],APPEARANCES[n['appearance']])
        lines=[];replies=[];starts=[];choice_entries=[]
        # Active choice objectives take precedence over ordinary conversation topics.
        for qi,q in enumerate(p['quests']):
            for si,s in enumerate(q['steps']):
                if s['kind']!='choice' or s['target']!=n['id']:continue
                options=[]
                for ci,choice in enumerate(s['choices']):
                    act=script(f'aqa_{qi}_{si}_{ci}','#include "aw_quest"\nvoid main(){SendMessageToPC(GetPCSpeaker(),'+literal(choice['text'])+');AQAdvance(GetPCSpeaker(),'+literal(q['id'])+','+str(si+1)+','+literal(choice['next'])+');}')
                    options.append(len(replies));replies.append((choice['label'],[],act))
                cond=conditional(f'aqc_{qi}_{si}','AQState('+literal(q['id'])+')=='+str(si+1))
                choice_entries.append(len(lines));starts.append((len(lines),cond));lines.append((s['description'],options))
        farewell=len(replies);replies.append(('Farewell.',[]));topics=[farewell]
        if p['ai_conversations'] and n['ai_enabled']:topics.insert(0,len(replies));replies.append(('Talk freely with AI.',[],'sp_select'))
        if n['merchant']['enabled']:
            for verb,label,flag in [('browse','Show me your goods.',False),('haggle','Can you offer a better price?',True)]:
                if flag and not n['merchant']['haggle_enabled']:continue
                act=script(f'aw_shop_{ni}_{int(flag)}','#include "aw_merchant"\nvoid main(){AWMOpen(GetPCSpeaker(),OBJECT_SELF,'+('TRUE' if flag else 'FALSE')+');}')
                topics.insert(0,len(replies));replies.append((label,[],act))
        if n['companion']['recruitable'] and p['companions']['enabled']:
            act=script(f'aw_cp_menu_{ni}','#include "aw_cp_ui"\nvoid main(){AWCOpenControl(GetPCSpeaker(),OBJECT_SELF);}')
            topics.insert(0,len(replies));replies.append(('Companion controls.',[],act))
            act=script(f'aw_cp_join_{ni}','#include "aw_companion"\nvoid main(){AWCOrder(GetPCSpeaker(),OBJECT_SELF,"recruit");}')
            topics.insert(0,len(replies));replies.append(('Join my party.',[],act))
        greeting=len(lines);lines.append((n['greeting'],topics,'aw_talk'));starts.append((greeting,''))
        for di,d in enumerate([dict(topic='What can you tell me?',text=n['knowledge'],after_quest='')]+n['dialogue']):
            if not d['text'].strip():continue
            line_index=len(lines);lines.append((d['text'],[farewell]));reply_index=len(replies);replies.append((d['topic'],[line_index]));topics.insert(len(topics)-1,reply_index)
        for entry in choice_entries:lines[entry][1].extend(topics)
        dlg=conversation(lines,replies,starts)
        if n['companion']['recruitable'] and p['companions']['enabled']:
            cond=conditional(f'aw_cp_can_{ni}','AWCCanRecruit(GetPCSpeaker(),OBJECT_SELF)','aw_companion')
            ri=next(i for i,r in enumerate(replies) if r[0]=='Join my party.')
            for entry in dlg[1]['EntryList'][1]:
                for edge in entry[1]['RepliesList'][1]:
                    if edge[1]['Index'][1]==ri:string(edge,'Active',cond,11)
        # Conditional topics are native Aurora dialogue edges, not LLM-only rules.
        ds=[d for d in [dict(topic='What can you tell me?',text=n['knowledge'],after_quest='')]+n['dialogue'] if d['text'].strip()]
        for di,d in enumerate(ds):
            if d['after_quest']:
                cond=conditional(f'awd_{ni}_{di}','AQDone('+literal(d['after_quest'])+')')
                ri=next(i for i,r in enumerate(replies) if r[0]==d['topic'])
                for entry in dlg[1]['EntryList'][1]:
                    for edge in entry[1]['RepliesList'][1]:
                        if edge[1]['Index'][1]==ri:string(edge,'Active',cond,11)
        entries[n['id'],2029]=write(b'DLG V3.2',dlg)
    for i,item in enumerate(p['items']):
        obj=read(game.get(ITEM_BASES[item['kind']],2025))[1];string(obj,'Tag',item['id']);string(obj,'TemplateResRef',item['id'],11)
        put(obj,'LocalizedName',text(item['name']));put(obj,'DescIdentified',text(item['description']));put(obj,'Description',text(item['description']));put(obj,'Identified',1);put(obj,'Plot',int(item['kind']=='quest_token'));put(obj,'StackSize',item['quantity'])
        entries[item['id'],2025]=write(b'UTI V3.2',obj)
        if not item['container']:place('aw_item_'+str(i),item['name']+' cache',item['room'],7,True,[item['id']],description=item['description'])
    native_enc=[]
    for ei,e in enumerate(p['encounters']):
        rid=e['room'];ar=rooms[rid][0]['id'];cx,cy=center(rooms[rid][1]);gits[ar][1]['WaypointList'][1].append(waypoint('aw_m_'+str(ei),e['name'],cx,cy,map_note=True))
        native_enc.append(dict(e,index=ei,area=ar))
        if e['kind'] in ('combat','ambush'):
            creature(e['id'],e['name'],CREATURES[e['creature']],rid if e['kind']=='combat' else None,enemy=True,enc=e)
        elif e['kind']=='treasure':
            inventory=[i['id'] for i in p['items'] if i['container']==e['id']];place(e['id'],e['name'],rid,7,True,inventory,onopen='aw_open',description=e['description'],gate=e['after_quest'])
        else:
            place(e['id'],e['name'],rid,87,True,onused='aw_use',description=e['description'])
            if e['kind']=='puzzle':
                replies=[]
                for oi,option in enumerate(e['options']):
                    body='AWResolve(GetPCSpeaker(),'+literal(e['id'])+');' if oi==e['answer'] else 'SendMessageToPC(GetPCSpeaker(),'+literal(e['failure'])+');'
                    act=script(f'awp_{ei}_{oi}','#include "aw_quest"\nvoid main(){'+body+'}')
                    replies.append((option,[],act))
                replies.append(('Leave it for now.',[]));entries[e['id'],2029]=write(b'DLG V3.2',conversation([(e['prompt'],list(range(len(replies))))],replies))
    for f in p['furnishings']:place(f['id'],f['name'],f['room'],DECOR[f['kind']],description=f['description'],side=f['placement'])
    for ci,c in enumerate(p['connections']):
        if c['kind']!='exit':continue
        legs=[(c['from_room'],c['from_side'],c['to_room'],c['to_side'])]
        if c['two_way']:legs.append((c['to_room'],c['to_side'],c['from_room'],c['from_side']))
        for li,(a,side,b,bside) in enumerate(legs):
            dest='aw_dest_'+str(ci)+'_'+str(li);dr=rooms[b][1];dx,dy=exit_point(dr,bside,8)
            gits[rooms[b][0]['id']][1]['WaypointList'][1].append(waypoint(dest,'Arrival from '+rooms[a][1]['name'],dx,dy))
            tag='aw_exit_'+str(ci)+'_'+str(li);tr=read(game.get('newgeneric',2032))[1];string(tr,'Tag',tag);string(tr,'TemplateResRef',tag,11);put(tr,'LocalizedName',text('To '+dr['name']));string(tr,'ScriptOnEnter','aw_exit',11)
            local(tr,{'AW_TARGET':dest,'AW_GATE':c['requires_quest']});entries[tag,2032]=write(b'UTT V3.2',tr)
            x,y=exit_point(rooms[a][1],side,2);put(tr,'XPosition',float(x),8);put(tr,'YPosition',float(y),8);put(tr,'ZPosition',0.,8)
            for key in ('XOrientation','YOrientation','ZOrientation'):put(tr,key,0.,8)
            hw,hh=(3.,1.) if side in ('north','south') else (1.,3.)
            put(tr,'Geometry',[node(3,PointX=(8,px),PointY=(8,py),PointZ=(8,0.)) for px,py in [(-hw,-hh),(hw,-hh),(hw,hh),(-hw,hh)]],15)
            gits[rooms[a][0]['id']][1]['TriggerList'][1].append((1,tr[1]));gits[rooms[a][0]['id']][1]['WaypointList'][1].append(waypoint('aw_sign_'+str(ci)+'_'+str(li),'Exit: '+dr['name'],x,y,map_note=True))
            place('aw_port_'+str(ci)+'_'+str(li),'Passage to '+dr['name'],a,87,True,onused='aw_exit',description='Use this passage marker, or walk through the marked exit.',side=side,variables={'AW_TARGET':dest,'AW_GATE':c['requires_quest']})
    categories=[]
    for qi,q in enumerate(p['quests']):
        journals=[node(si,ID=(4,si+1),End=(2,0),Text=(12,text(s['description']))) for si,s in enumerate(q['steps'])]
        journals.append(node(len(journals),ID=(4,999),End=(2,1),Text=(12,text(q['completion']))))
        categories.append(node(qi,Name=(12,text(q['name'])),Tag=(10,q['id'].encode()),XP=(4,q['xp']),Priority=(4,0 if q['optional'] else 1),Picture=(2,65535),Comment=(10,q['description'].encode()),EntryList=(15,journals)))
    entries['module',2056]=write(b'JRL V3.2',node(0xffffffff,Categories=(15,categories)))
    for a in p['areas']:
        ident=a['id'];entries[ident,2012]=write(b'ARE V3.2',areas[ident]);entries[ident,2023]=write(b'GIT V3.2',gits[ident]);entries[ident,2046]=write(b'GIC V3.2',comments_for(gits[ident]))
    native_rooms=[dict(r,area=a['id']) for a in p['areas'] for r in a['rooms']]
    companion_cfg={k:v for k,v in p['companions'].items() if k!='templates'};companion_cfg['live_ai']=p['ai_conversations']
    companion_npcs=[dict(n['companion'],id=n['id'],name=n['name'],alias=n['alias'],ai_enabled=n['ai_enabled']) for n in p['npcs'] if n['companion']['recruitable']]
    behaviors=[dict(n['behavior'],id=n['id'],ai_enabled=n['ai_enabled']) for n in p['npcs']]
    scripts['aw_config']='\n'.join([json_function('AWAConfig',[p['ambient']]),json_function('AWABehaviors',behaviors),json_function('AWQuests',p['quests']),json_function('AWRooms',native_rooms),json_function('AWEncounters',native_enc),json_function('AWShops',shops),json_function('AWCompanionConfig',[companion_cfg]),json_function('AWCompanionTemplates',p['companions']['templates']),json_function('AWCompanionNPCs',companion_npcs),'string AWCWorld(){return '+literal(p['id'])+';}','string AWEnding(){return '+literal(p['ending'])+';}','int AWLevelMax(){return '+str(p['level_max'])+';}'])
    ai=p['ai_conversations'];include='#include "aw_social"' if ai else '#include "aw_ambient"'
    scripts['aw_load']=include+'\nvoid main(){SetLocalString(GetModule(),"AWM_SESSION",GetRandomUUID());AWALoad();if(AWCEnabled()){AWCInit();SetMaxHenchmen('+str(p['companions']['party_limit'])+');}'+('SPInit();' if ai else '')+'}'
    scripts['aw_enter']=include+'\nvoid main(){object pc=GetEnteringObject();if(!GetIsPC(pc))return;if(!GetLocalInt(pc,"AW_WELCOME")){SetLocalInt(pc,"AW_WELCOME",TRUE);SendMessageToPC(pc,'+literal(p['opening'])+');}AQStart(pc);AWArea(pc);'+('SPReset(pc);SPPublish(pc);SendMessageToPC(pc,"AI: choose Talk freely with AI and then speak normally, or type !talk <alias> <message>. Use !end to finish.");' if ai else '')+'}'
    scripts['aw_beat']=include+'\nvoid main(){SetLocalInt(GetModule(),"AWM_CLOCK",AWMClock()+6);object pc=GetFirstPC();while(GetIsObjectValid(pc)){if(GetLocalInt(pc,"AWM_TOKEN") && !AWMNear(pc,GetLocalObject(pc,"AWM_ACTOR")))AWMClose(pc);AWCTransferTick(pc);AWArea(pc);AWAmbushes(pc);AQTick(pc);'+('SPPublish(pc);SPPoll(pc);' if ai else '')+'pc=GetNextPC();}AWATick();'+('AWSTick(GetFirstPC());' if ai else '')+'}'
    if not ai:scripts.pop('aw_social',None)
    if ai:
        for name in ('sp_inc','sp_chat','sp_select'):scripts[name]=(ROOT/'scripts'/(name+'.nss')).read_text(encoding='utf-8')
        scripts['aw_story']=native_story(p,literal)
        scripts['aw_story']=scripts['aw_story'].replace('#include "aw_quest"','#include "aw_ambient"')
        inc=scripts['sp_inc'].replace('#include "mc_inc"','#include "aw_story"').replace('MCState()','AQProgress()').replace('GetIsObjectValid(MCSatchel(pc))','FALSE')
        inc=inc.replace('string verb=SPText(result,"action");','string verb=SPText(result,"action"); AWAIAction(pc,tag,SPText(result,"story_action"));')
        inc=inc.replace('j=JsonObjectSet(j,"quest_stage",JsonInt(AQProgress()));','j=JsonObjectSet(j,"quest_stage",JsonInt(AQProgress())); j=JsonObjectSet(j,"quests",AQStates());')
        inc=inc.replace('if(tag=="mc_edric" && verb=="accept_quest" && AQProgress()==0) MCAccept(pc);','// Quest decisions are made through native authored conversation choices.')
        inc=inc.replace('if(tag=="mc_edric" && verb=="turn_in") MCReward(pc);','')
        scripts['sp_inc'],scripts['sp_chat'],scripts['sp_select']=adapt_ai(inc,p['npcs'],literal)
        scripts['sp_config']='\n'.join(['string SPProject(){return '+literal(p['id'])+';}','string SPBuild(){return '+literal(digest)+';}','json SPEncounters(){return JsonArray();}',
          'int SPIsNPC(string tag){return '+(' || '.join('tag=='+literal(n['id']) for n in p['npcs'] if n['ai_enabled']) or 'FALSE')+';}',
          'string SPAlias(string alias){'+''.join('if(alias=='+literal(n['alias'])+')return '+literal(n['id'])+';' for n in p['npcs'] if n['ai_enabled'])+'return "";}',
          'string SPAliases(){return '+literal(', '.join(n['alias'] for n in p['npcs'] if n['ai_enabled']))+';}'])
    with tempfile.TemporaryDirectory(prefix='adventure-',dir=store.root) as temp:
        out=Path(temp);source=out/'source';source.mkdir();compiled=out/'compiled';compiled.mkdir()
        for name,body in scripts.items():(source/(name+'.nss')).write_text(body+'\n',encoding='utf-8')
        result=subprocess.run([str(compiler),'-n',str(game_root),'-i',str(source),'-b',str(compiled),*map(str,sorted(source.glob('*.nss')))],capture_output=True,text=True,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode:raise ValueError('NWScript compilation failed: '+(result.stdout+result.stderr)[-6500:])
        (out/'compile.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        for name,body in scripts.items():
            entries[name,2009]=(source/(name+'.nss')).read_bytes();ncs=compiled/(name+'.ncs')
            if ('void main(' in body or 'StartingConditional(' in body) and not ncs.exists():raise ValueError('Missing compiled script: '+name)
            if ncs.exists():entries[name,2010]=ncs.read_bytes()
        types=TYPES|{2032:'utt',2051:'utm'}
        for (name,kind),raw in entries.items():
            if kind not in (2009,2010) and write(*read(raw))!=raw:raise ValueError('Native resource round-trip failed: '+name)
            (source/(name+'.'+types[kind])).write_bytes(raw)
        mod=out/(p['module_name']+'.mod');mod.write_bytes(pack_module(base,entries))
        if {(n,k):b for n,k,b in resources(mod.read_bytes())}!=entries:raise ValueError('Module resource index verification failed')
        report=review(p);report.pop('layouts',None)
        manifest=dict(build_id=digest,project_id=p['id'],title=p['title'],module=mod.name,sha256=hashlib.sha256(mod.read_bytes()).hexdigest(),resources=len(entries),areas=len(p['areas']),rooms=len(rooms),quests=len(p['quests']),compiled_scripts=sum(k==2010 for _,k in entries),standalone=True,optional_live_ai=ai,gameplay_tested=False,path=str(destination/mod.name))
        write_json(out/'project.json',p);write_json(out/'manifest.json',manifest);write_json(out/'validation.json',report);write_json(out/'layout.json',layouts)
        write_json(out/(p['module_name']+'.rwproject.json'),dict(build_id=digest,project=p))
        instructions='Install '+mod.name+' in your Neverwinter Nights/modules folder. Start a NEW single-player game. The complete adventure, authored conversations, quest journal, encounter scaling and ending run without Studio or an API key.\n\nOpen the .mod in Aurora to edit native resources. Keep a separate copy: rebuilding uses the authoring project, not Aurora edits.\n'
        if ai:instructions+='\nOptional freeform NPC chat: run Role Weaver Module Studio’s AI Player companion, import the .rwproject.json file, and use your own OPENAI_API_KEY. Stay near an AI NPC and type !talk <alias> <message>. The ordinary quest does not depend on this service.\n'
        if p['companions']['enabled']:instructions+='\nCompanions: use !companions, approach an authored recruit and choose Join my party. Summon familiars and creatures normally with your own class abilities. Their profiles attach to those actual native creatures. Use Talk freely with AI, then close the controls and speak in Talk; !companion familiar <message> also works. Follow/stay/guard and inventory do not require an API. Familiar/summon satchels remain in the owner inventory after expiry. Native menus still handle their dismissal.\n'
        if p['ambient']['patrols'] or p['ambient']['social']:instructions+='\nAmbient NPCs: patrols walk the authored same-area room stops without AI. Social chat requires both NPCs to opt in, plus live AI Player. It has no quest/reward actions, uses public profile knowledge and pauses for players/combat/recruitment. Creator switches are in Behaviors.\n'
        (out/'PLAY.txt').write_text(instructions,encoding='utf-8')
        shutil.copy2(ROOT/'ROLE-WEAVER-LICENSE.txt',out/'ROLE-WEAVER-LICENSE.txt')
        with zipfile.ZipFile(out/(p['module_name']+'-aurora.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for f in [mod,out/'PLAY.txt',out/'ROLE-WEAVER-LICENSE.txt',out/'manifest.json',out/'validation.json',out/'layout.json',out/(p['module_name']+'.rwproject.json'),*source.iterdir()]:z.write(f,f.relative_to(out))
        shutil.copytree(out,destination,dirs_exist_ok=True)
    return manifest
