"""Generate an additive native runtime without taking over imported quest logic."""
import copy
import re
from .builder import ROOT,literal,conversation,string
from .conversion_performance import configuration,adapt as optimize_runtime
from .nwn.gff import read,write,text
from .nwn.area_tools import set_value as put

def replace(source,old,new,count=1):
    if source.count(old)!=count:raise ValueError('Conversion adapter needs review: '+old[:80])
    return source.replace(old,new)

def runtime(p,build,game,hooks):
    scripts={f.stem:f.read_text(encoding='utf-8') for f in (ROOT/'authoring_scripts').glob('*.nss')}
    # Include only the companion/bridge entry points, not authored quest hooks.
    entries={}
    escrow=read(game.get('nw_lostitems',2051))[1]
    for ident,label in [('aw_escrow','Temporary item transfer'),('aw_cp_storage','Companion inventory')]:
        obj=copy.deepcopy(escrow);string(obj,'ResRef',ident,11);string(obj,'Tag',ident);put(obj,'LocName',text(label))
        entries[ident,2051]=write(b'UTM V3.2',obj)
    entries['aw_grid_blank',3]=bytes([0,0,2,0,0,0,0,0,0,0,0,0,1,0,1,0,32,40,0,0,0,0])
    satchel=read(game.get('nw_it_contain001',2025))[1]
    string(satchel,'Tag','aw_satchel');string(satchel,'TemplateResRef','aw_satchel',11)
    for key,value in [('LocalizedName',text('Companion satchel')),('DescIdentified',text('Recoverable storage for your familiar or summon.')),('PropertiesList',[]),('Plot',1),('Identified',1),('Cost',0),('AddCost',0),('StackSize',1)]:put(satchel,key,value)
    entries['aw_satchel',2025]=write(b'UTI V3.2',satchel)
    replies=[('Talk freely with AI.',[],'aw_cp_talk'),('Companion controls.',[],'aw_cp_panel'),('Open companion inventory.',[],'aw_cp_visual'),('Normal companion dialogue.',[],'aw_cp_orig'),('Farewell.',[])]
    entries['aw_cp_native',2029]=write(b'DLG V3.2',conversation([('What would you like me to do?',list(range(len(replies))))],replies))
    scripts['aw_cp_panel']='#include "aw_cp_ui"\nvoid main(){AWCOpenControl(GetPCSpeaker(),OBJECT_SELF);}'
    scripts['aw_cp_visual']='#include "aw_cp_ui"\nvoid main(){AWCVisualInventory(GetPCSpeaker(),OBJECT_SELF);}'
    cfg={k:v for k,v in p['companions'].items() if k!='templates'};cfg['live_ai']=True
    arrays={'AWItems':[],'AWDoors':[],'AWAConfig':[dict(patrols=False,social=False)],'AWABehaviors':[dict(n['behavior'],id=n['id'],alias=n['alias'],ai_enabled=n['ai_enabled']) for n in p['npcs']],
            'AWQuests':[],'AWRooms':[],'AWEncounters':[],
            'AWShops':[dict(n['merchant'],id=n['id'],conversation=n.get('native_store',{}).get('conversation',''),store_variables=n.get('native_store',{}).get('variables',[]),store_tags=n.get('native_store',{}).get('tags',[])) for n in p['npcs'] if n['merchant']['enabled'] and n['ai_enabled']],
            'AWCompanionConfig':[cfg],'AWCompanionTemplates':p['companions']['templates'],
            'AWCompanionNPCs':[dict(n['companion'],id=n['id'],name=n['name'],alias=n['alias'],ai_enabled=n['ai_enabled']) for n in p['npcs']]}
    scripts['aw_config']='\n'.join([configuration(p,arrays),'string AWCWorld(){return '+literal(p['id'])+';}','string AWEnding(){return "";}','int AWLevelMax(){return 40;}',
        'object RWFindActor(object pc,string id){object match=OBJECT_INVALID;object body=GetFirstObjectInArea(GetArea(pc));int count=0;while(GetIsObjectValid(body)){if(GetObjectType(body)==OBJECT_TYPE_CREATURE && !GetIsPC(body) && !GetIsDead(body) && RWProfile(body)==id && GetDistanceBetween(pc,body)<=12.0 && GetObjectSeen(body,pc) && LineOfSightObject(pc,body)){match=body;count++;}body=GetNextObjectInArea(GetArea(pc));}if(count!=1)return OBJECT_INVALID;return match;}'])
    from .conversion_merchants import adapt_runtime
    adapt_runtime(scripts,p,literal,replace)
    from .inventory_icons import native_icons
    scripts['aw_g_icons']=native_icons(game,literal)
    scripts['nw_inc_nui']=game.get('nw_inc_nui',2009).decode('latin1')
    src=scripts['aw_companion']
    src=replace(src,'AWFind(AWCompanionNPCs(),GetTag(body))','AWFind(AWCompanionNPCs(),RWProfile(body))')
    src=replace(src,'GetResRef(body)==AWText(npc,"id") && (GetAssociateType(body)==ASSOCIATE_TYPE_NONE || GetAssociateType(body)==ASSOCIATE_TYPE_HENCHMAN)', 'GetAssociateType(body)==ASSOCIATE_TYPE_HENCHMAN && GetIsPC(AWCOwner(body))')
    src=replace(src,'int type=GetAssociateType(body);string kind="";', 'if(!GetIsPC(AWCOwner(body)))return JsonNull();int type=GetAssociateType(body);string kind="";')
    src=replace(src,'if(kind=="party")return id+GetTag(body);','if(kind=="party")return id+GetObjectUUID(body);')
    src=re.sub(r'int AWCCanRecruit\(object pc,object body\)\{.*?\n.*?\}', 'int AWCCanRecruit(object pc,object body){return FALSE;}',src,count=1)
    src=replace(src,'if(AWCKind(body)=="party")out=JsonArrayInsert(out,JsonString("dismiss"));','')
    src=replace(src,'void AWCOrder(object pc,object body,string command){','void AWCOrder(object pc,object body,string command){if(command=="recruit" || command=="dismiss"){SendMessageToPC(pc,"Use this character\'s original dialogue to recruit or dismiss them.");return;}')
    scripts['aw_companion']=src
    scripts['aw_cp_ui']=replace(scripts['aw_cp_ui'],'AWCButton(pc,"Leave my party","dismiss")','AWCLabel("Use original dialogue to recruit or dismiss this character.")')
    for name in ('aw_cp_tasks','aw_ct_request','aw_ct_poll','aw_ambient'):
        scripts[name]=scripts[name].replace('GetTag(target)','RWProfile(target)').replace('GetTag(body)','RWProfile(body)').replace('GetResRef(target)==AWText(p,"id")','RWProfile(target)==AWText(p,"id")').replace('GetResRef(body)==AWText(AWAPolicy(body),"id")','RWProfile(body)==AWText(AWAPolicy(body),"id")')
    scripts['aw_story']='#include "aw_ambient"\nvoid AWAIAction(object pc,string tag,string verb){}'
    inc=(ROOT/'scripts/sp_inc.nss').read_text(encoding='utf-8').replace('#include "mc_inc"','#include "aw_story"').replace('MCState()','AQProgress()').replace('GetIsObjectValid(MCSatchel(pc))','FALSE')
    inc=replace(inc,'string verb=SPText(result,"action");','string verb=SPText(result,"action"); AWAIAction(pc,tag,SPText(result,"story_action"));')
    inc=inc.replace('if(tag=="mc_edric" && verb=="accept_quest" && AQProgress()==0) MCAccept(pc);','').replace('if(tag=="mc_edric" && verb=="turn_in") MCReward(pc);','')
    from .runtime_ai import adapt
    inc,chat,select=adapt(inc,p['npcs'],literal)
    inc=replace(inc,'tag=GetTag(npc);','tag=RWProfile(npc);')
    inc=replace(inc,'return GetIsObjectValid(npc) && !GetIsDead(pc)', 'return GetIsObjectValid(npc) && GetObjectType(npc)==OBJECT_TYPE_CREATURE && !IsInConversation(pc) && !IsInConversation(npc) && !GetIsInCombat(pc) && !GetIsInCombat(npc) && GetObjectSeen(npc,pc) && !GetIsDead(pc)')
    inc=inc.replace('"SP_HIST_"+tag','"SP_HIST_"+GetObjectUUID(npc)')
    inc='#include "rwc_memory"\n'+inc
    scripts['rwc_memory']=(ROOT/'scripts/rwc_memory.nss').read_text(encoding='utf-8')
    scripts['aw_ct_request']=replace(scripts['aw_ct_request'],'json observed=JsonObject();','json observed=JsonObject();observed=JsonObjectSet(observed,"native_seen",RWSeen(pc,target));observed=JsonObjectSet(observed,"native_dialogue",JsonString(GetLocalString(pc,"RWC_HEARD_"+GetObjectUUID(target))));')
    inc=replace(inc,'json observed=SPSnapshot(pc);','json observed=SPSnapshot(pc);observed=JsonObjectSet(observed,"actor_name",JsonString(GetName(npc)));observed=JsonObjectSet(observed,"area",JsonString(GetName(GetArea(npc))));observed=JsonObjectSet(observed,"native_dialogue",JsonString(GetLocalString(pc,"RWC_HEARD_"+GetObjectUUID(npc))));observed=JsonObjectSet(observed,"native_seen",RWSeen(pc,npc));observed=JsonObjectSet(observed,"native_shared",JsonString(GetLocalString(pc,"RWC_SHARED")));')
    inc=replace(inc,'if(!SPNear(pc,npc) || GetLocalObject(pc,"SP_FOCUS")!=npc)', 'if(!SPNear(pc,npc) || (kind=="npc" && RWProfile(npc)!=tag) || GetLocalObject(pc,"SP_FOCUS")!=npc)')
    chat=chat.replace('GetObjectByTag(tag)','RWFindActor(pc,tag)')
    chat=replace(chat,'SPAsk(pc,"dm",GetSubString(s,4,1200));','SendMessageToPC(pc,"This adventure uses its original quest dialogue and journal. AI does not direct its quests.");')
    scripts.update(sp_inc=inc,sp_chat=chat,sp_select=select.replace('NPC menu choices share the same story progress.','Use original dialogue choices for quests, trading, recruitment and dismissal.'))
    scripts['sp_config']='\n'.join(['string SPProject(){return '+literal(p['id'])+';}','string SPBuild(){return '+literal(build)+';}','json SPEncounters(){return JsonArray();}',
        'int SPIsNPC(string tag){return RWIsNPC(tag);}',
        'string SPAlias(string alias){return RWAlias(alias);}',
        'string SPAliases(){return '+literal(', '.join(n['alias'] for n in p['npcs'] if n['ai_enabled']))+';}'])
    def native(event):return 'ExecuteScript('+literal(hooks[event])+',OBJECT_SELF);' if hooks.get(event) else ''
    scripts['rwc_load']='#include "sp_inc"\nvoid main(){'+native('Mod_OnModLoad')+'SetLocalString(GetModule(),"AWM_SESSION",GetRandomUUID());AWCInit();SPInit();}'
    scripts['rwc_enter']='#include "sp_inc"\nvoid main(){'+native('Mod_OnClientEntr')+'object pc=GetEnteringObject();if(!GetIsPC(pc))return;SPReset(pc);SPPublish(pc);SPServiceBegin(pc);DelayCommand(12.0,SPServiceCheck(pc));SendMessageToPC(pc,"Role Weaver AI edition: original quest menus remain available. Choose Talk freely with AI, or use !talk <alias> <message>. Use !companions for recruited allies, familiars and summons. Use !end to finish AI chat.");}'
    scripts['rwc_beat']='#include "sp_inc"\n#include "aw_cp_cargo"\nvoid main(){'+native('Mod_OnHeartbeat')+'SetLocalInt(GetModule(),"AWM_CLOCK",AWMClock()+6);object pc=GetFirstPC();while(GetIsObjectValid(pc)){AWXTick(pc);AWCTransferTick(pc);AWTTick(pc);json actors=AWCActors(pc);int i=0;while(i<JsonGetLength(actors)){object body=GetObjectByUUID(JsonGetString(JsonArrayGet(actors,i)));AWCObserve(pc,body);i++;}SPPublish(pc);SPServiceCheck(pc);SPPoll(pc);pc=GetNextPC();}}'
    # Deliver the unchanged event to the original handler exactly once, before
    # the optional chat layer. No mutation of native event hooks on creatures.
    scripts['rwc_chat']='#include "sp_inc"\nvoid main(){'+native('Mod_OnPlrChat')+'if(GetPCChatMessage()!="")ExecuteScript("sp_chat",OBJECT_SELF);}'
    scripts['rwc_can_chat']='#include "sp_inc"\nint StartingConditional(){return GetObjectType(OBJECT_SELF)==OBJECT_TYPE_CREATURE && SPIsNPC(RWProfile(OBJECT_SELF));}'
    optimize_runtime(scripts,replace)
    scripts['rwc_npcs']=(ROOT/'scripts/rwc_npcs.nss').read_text(encoding='utf-8')
    scripts['rwc_npc_evt']='#include "rwc_npcs"\nvoid main(){RWNPCEvent();}'
    scripts['sp_chat']=replace(scripts['sp_chat'],'#include "sp_inc"','#include "rwc_npcs"')
    scripts['sp_chat']=replace(scripts['sp_chat'],'string lower=GetStringLowerCase(s);','string lower=GetStringLowerCase(s);if(lower=="!npcs"){SetPCChatMessage("");SetLocalInt(pc,"RWNPC_PAGE",0);RWNPCOpen(pc);return;}')
    scripts['rwc_enter']=replace(scripts['rwc_enter'],'Use !companions for recruited allies, familiars and summons.','Use !npcs to select any available nearby AI character, and !companions for recruited allies, familiars and summons.')
    # Retain includes plus actual companion/merchant UI event handlers. Do not
    # ship the authoring builder\'s module/area/quest startup entry points.
    keep={'sp_inc','sp_chat','sp_select','sp_config','aw_story','aw_config','nw_inc_nui','aw_g_icons','rwc_load','rwc_enter','rwc_beat','rwc_chat','rwc_can_chat','rwc_memory','rwc_npcs','rwc_npc_evt'}
    keep.update(k for k in scripts if k.startswith(('aw_cp_','aw_ct_','aw_g_','aw_m_','aw_dlg_')))
    keep.update(('aw_companion','aw_merchant','aw_ambient','aw_quest','aw_encounter','aw_items','aw_ui','aw_shop_evt'))
    # Walk include dependencies rather than assuming a particular file layout.
    todo=list(keep)
    while todo:
        name=todo.pop()
        for include in re.findall(r'#include "([a-z0-9_]+)"',scripts.get(name,'')):
            if include in scripts and include not in keep:keep.add(include);todo.append(include)
    return {k:v for k,v in scripts.items() if k in keep},entries
