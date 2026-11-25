"""Bound converted-runtime work by the actors in use, not the module's cast.

Only immutable configuration is cached. Ownership, stock, visibility, quest
state and companion preferences are still checked against the live game.
"""
import hashlib
import json
from collections import defaultdict

from .builder import literal


def native(value):
    if isinstance(value, bool):return int(value)
    if isinstance(value, dict):return {k:native(v) for k,v in value.items()}
    if isinstance(value, list):return [native(v) for v in value]
    return value


def json_expression(value):
    # Keep individual NCS string constants below their 16-bit byte limit,
    # including non-ASCII data and escaping. Parsing happens in the engine.
    raw=json.dumps(native(value),ensure_ascii=True,separators=(',',':'))
    return 'JsonParse('+ '+\n'.join(literal(raw[i:i+4000]) for i in range(0,len(raw),4000))+')'


def cached_json(name,value):
    key=literal('RWC_DATA_'+name)
    raw=json.dumps(native(value),ensure_ascii=True,separators=(',',':'))
    # Separate assignments avoid both the compiler's source-line limit and
    # constant folding a large table into an oversized NCS string operand.
    parts=[literal(raw[i:i+4000]) for i in range(0,len(raw),4000)]
    encoded='string encoded='+parts[0]+';\n'+''.join('encoded+='+part+';\n' for part in parts[1:])
    return ('json '+name+'(){object module=GetModule();string key='+key+';'
            'if(GetLocalString(module,key)==RWConfigVersion())return GetLocalJson(module,key);'
            '\n'+encoded+'json data=JsonParse(encoded);SetLocalJson(module,key,data);'
            'SetLocalString(module,key,RWConfigVersion());return data;}')


def record_tree(rows):
    """At most ceil(log2(n)) branches plus an exact identity check per miss."""
    if not rows:return 'return JsonNull();'
    if len(rows)==1:
        ident,record=rows[0]
        return 'if(id=='+literal(ident)+')return '+json_expression(record)+';return JsonNull();'
    middle=len(rows)//2
    pivot=int(rows[middle][0][4:])
    return ('if(index<'+str(pivot)+'){\n'+record_tree(rows[:middle])+
            '\n}else{\n'+record_tree(rows[middle:])+'\n}')


def configuration(p,arrays):
    identities={};names=defaultdict(set);aliases={}
    for n in p['npcs']:
        identities.setdefault(n['native_tag'],{})[n['native_resref']]=n['id']
        if n['ai_enabled']:
            aliases[n['alias']]=n['id']
            for name in (n['alias'],n['name'].lower(),n['name'].lower().split()[0]):names[name].add(n['id'])
    addresses={name:next(iter(ids)) for name,ids in names.items() if len(ids)==1}
    companions={n['id']:n for n in arrays['AWCompanionNPCs']}
    behaviors={n['id']:n for n in arrays['AWABehaviors']}
    shops={n['id']:n for n in arrays['AWShops']}
    records=sorted((n['id'],dict(companion=companions[n['id']],behavior=behaviors[n['id']],
                                merchant=shops.get(n['id']),ai_enabled=n['ai_enabled'])) for n in p['npcs'])
    version=hashlib.sha256(json.dumps([arrays,identities,addresses,aliases],sort_keys=True).encode()).hexdigest()[:20]
    return '\n'.join([
        'string RWConfigVersion(){return '+literal(version)+';}',
        *(cached_json(k,v) for k,v in arrays.items()),
        cached_json('RWIdentities',identities),cached_json('RWAddresses',addresses),cached_json('RWAliases',aliases),
        'string RWProfile(object body){if(!GetIsObjectValid(body) || GetObjectType(body)!=OBJECT_TYPE_CREATURE)return "";return JsonGetString(JsonObjectGet(JsonObjectGet(RWIdentities(),GetTag(body)),GetResRef(body)));}',
        'json RWReadRecord(string id){int index=StringToInt(GetSubString(id,4,4));'+record_tree(records)+'}',
        'json RWRecord(string id){if(GetStringLength(id)!=8 || GetStringLeft(id,4)!="cv_n")return JsonNull();object module=GetModule();string key="RWC_RECORD_"+id;'
        'if(GetLocalString(module,key)==RWConfigVersion())return GetLocalJson(module,key);json data=RWReadRecord(id);'
        'if(JsonGetType(data)!=JSON_TYPE_NULL){SetLocalJson(module,key,data);SetLocalString(module,key,RWConfigVersion());}return data;}',
        'json RWCompanion(object body){return JsonObjectGet(RWRecord(RWProfile(body)),"companion");}',
        'json RWBehavior(object body){return JsonObjectGet(RWRecord(RWProfile(body)),"behavior");}',
        'json RWShop(object body){return JsonObjectGet(RWRecord(RWProfile(body)),"merchant");}',
        'int RWIsNPC(string id){return JsonGetInt(JsonObjectGet(RWRecord(id),"ai_enabled"));}',
        'string RWAddress(string name){return JsonGetString(JsonObjectGet(RWAddresses(),name));}',
        'string RWAlias(string name){return JsonGetString(JsonObjectGet(RWAliases(),name));}',
    ])


def adapt(scripts,replace):
    """Apply after native identity/merchant adapters, before mission adapters."""
    for name in ('aw_companion','aw_cp_tasks','aw_ambient','aw_ct_poll','aw_merchant'):
        src=scripts[name]
        src=src.replace('AWFind(AWCompanionNPCs(),RWProfile(body))','RWCompanion(body)')
        src=src.replace('AWFind(AWABehaviors(),RWProfile(body))','RWBehavior(body)')
        src=src.replace('AWFind(AWABehaviors(),RWProfile(target))','RWBehavior(target)')
        src=src.replace('AWFind(AWShops(),RWProfile(actor))','RWShop(actor)')
        scripts[name]=src
    # Unowned NPCs cannot be recruited by this adapter. Familiar/summon policy
    # comes from the small template table, never the entire native NPC cast.
    src=scripts['aw_companion']
    src=replace(src,'json AWCPolicy(object body){json npc=RWCompanion(body);',
                'json AWCPolicy(object body){if(!GetIsObjectValid(body) || !GetIsPC(AWCOwner(body)))return JsonNull();json npc=JsonNull();if(GetAssociateType(body)==ASSOCIATE_TYPE_HENCHMAN)npc=RWCompanion(body);')
    src=replace(src,'if(name==full || name==first || name==slot || name==GetStringLowerCase(GetTag(body)))',
                'if(name==full || name==first || name==slot || name==GetStringLowerCase(GetTag(body)) || name==AWText(RWCompanion(body),"alias"))')
    scripts['aw_companion']=src
    src=scripts['aw_cp_ui'];start=src.index('object AWCByAlias(');end=src.index('\nint AWCChatControl(',start)
    scripts['aw_cp_ui']=src[:start]+'object AWCByAlias(object pc,string name){return AWCFind(pc,name);}\n'+src[end:]
    # Enumerate companions once per heartbeat. An active actor can be outside
    # the normal list (lost ownership/death); tick that actor once to cancel it.
    src=scripts['aw_cp_tasks']
    src=replace(src,'void AWTTick(object pc){','void RWTaskTick(object pc,json actors){object ticked=OBJECT_INVALID;')
    src=replace(src,'else {AWTBodyTick(pc,active);','else {ticked=active;AWTBodyTick(pc,active);')
    src=replace(src,'json actors=AWCActors(pc);int i=0;while(i<JsonGetLength(actors)){AWTBodyTick(pc,GetObjectByUUID(JsonGetString(JsonArrayGet(actors,i))));i++;}}',
                'int i=0;while(i<JsonGetLength(actors)){object body=GetObjectByUUID(JsonGetString(JsonArrayGet(actors,i)));if(body!=ticked)AWTBodyTick(pc,body);i++;}}\nvoid AWTTick(object pc){RWTaskTick(pc,AWCActors(pc));}')
    scripts['aw_cp_tasks']=src
    scripts['rwc_beat']=replace(scripts['rwc_beat'],'AWTTick(pc);json actors=AWCActors(pc);','json actors=AWCActors(pc);RWTaskTick(pc,actors);')
    # Heartbeats keep a fresh party/session snapshot. Expensive live stock,
    # container and companion context is collected only for an actual request.
    inc=scripts['sp_inc']
    inc=replace(inc,'json SPSnapshot(object pc)','json SPSnapshot(object pc,int detailed=TRUE)')
    inc=replace(inc,'j=JsonObjectSet(j,"merchant",AWMContext(pc,GetLocalObject(pc,"SP_FOCUS")));',
                'j=JsonObjectSet(j,"merchant",detailed?AWMContext(pc,GetLocalObject(pc,"SP_FOCUS")):JsonObject());')
    inc=replace(inc,'j=JsonObjectSet(j,"companion",AWCContext(pc,GetLocalObject(pc,"SP_FOCUS")));',
                'j=JsonObjectSet(j,"companion",detailed?AWCContext(pc,GetLocalObject(pc,"SP_FOCUS")):JsonObject());')
    inc=replace(inc,'JsonDump(SPSnapshot(pc))','JsonDump(SPSnapshot(pc,FALSE))')
    scripts['sp_inc']=inc
    src=scripts['sp_chat'];start=src.index('string SPAddress(');end=src.index('\nobject SPActorAddress(',start)
    scripts['sp_chat']=src[:start]+'string SPAddress(string name){return RWAddress(name);}'+src[end:]
