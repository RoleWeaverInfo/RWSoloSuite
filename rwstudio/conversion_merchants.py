"""Link imported merchants to native shops without recreating stock or prices."""
import copy
import re
from .merchants import defaults


def trade_intent(message):
    """Only explicit requests may open a shop; questions stay in conversation."""
    s=message.lower().replace('\u2019', "'")
    if re.search(r"\b(don't|do not|not now|never mind|no thanks|wouldn't|if|hypothetically)\b",s):return ''
    if re.search(r'\b(story|background|childhood|history|your life|your past)\b',s):return ''
    if re.search(r'\b(tell me|what|why|how|who|where|when|do you|have you|is there|are there)\b',s) and not re.search(r'\b(show|showing|open|browse|see|look|let me|let us|let\'s)\b',s):
        return ''
    request=bool(re.search(r"\b(please|want|like|can i|can we|can you|could i|could we|could you|would you|may i|let me|let us|let's)\b",s) or re.match(r'\s*(show|shoe|open|browse|trade|barter|buy|purchase|sell|haggle|negotiate)\b',s))
    if not request:return ''
    if re.search(r'\b(haggle|negotiate)\b',s) or re.search(r'\b(discount|better price|lower.*price)\b',s):return 'haggle'
    if re.search(r'\b(trade|barter|buy|purchase|sell)\b',s):return 'browse'
    if re.search(r'\b(show|showing|shoe|open|browse|see|look at)\b',s) and re.search(r'\b(store|shop|wares|goods|inventory|stock|merchandise|equipment|selection|for sale)\b',s):return 'browse'
    return ''


def add_store_metadata(report, path):
    from .nwn.analysis_formats import Archive, gff
    report=copy.deepcopy(report);archive=Archive(path);stores=[];variables={};budget=0
    for (name,kind),entry in archive.index.items():
        if kind not in (2023,2027,2051):continue
        raw=archive.get(name,kind);budget+=len(raw)
        if budget>256_000_000:
            report.setdefault('warnings',[]).append('Merchant resource budget reached; some native store links are unresolved.');break
        try:d=gff(raw)
        except (ValueError,KeyError,OSError):continue # The main analyser reports malformed resources.
        rows=[(name+'.utc',d)] if kind==2027 else [(name+'.git/Creature List['+str(i)+']',c) for i,c in enumerate(d.get('Creature List',[]))]
        for source,c in rows:
            variables[source]=[{k:v.get(k) for k in ('Name','Type','Value')} for v in c.get('VarTable',[])
                               if v.get('Type')==3 and isinstance(v.get('Name'),str) and isinstance(v.get('Value'),str)]
        candidates=[d] if kind==2051 else d.get('StoreList',[]) if kind==2023 else []
        for s in candidates:
            if s.get('Tag'):stores.append(dict(tag=s['Tag'],resref=s.get('ResRef',name),area=name if kind==2023 else '',source=name+('.git' if kind==2023 else '.utm')))
    report['native_stores']=stores
    for c in report['characters']:c['native_store_variables']=variables.get(c['source'],[])
    report['merchant_metadata_version']=1
    return report


def binding(report,row):
    scripts={s['id']:s for s in report.get('scripts',[])};todo=list(row.get('script_refs',[]));seen=set();openers=[]
    while todo and len(seen)<2500:
        name=todo.pop()
        if name in seen:continue
        seen.add(name);s=scripts.get(name,{})
        if s.get('functions',{}).get('OpenStore'):openers.append(s)
        for c in s.get('calls',[]):
            args=c.get('arguments',[])
            if c.get('name') in ('ExecuteScript','ExecuteScriptEnhanced') and args and isinstance(args[0],str):todo.append(args[0].lower())
    stores={s['tag'] for s in report.get('native_stores',[]) if isinstance(s.get('tag'),str)}
    variables=set();tags=set()
    for s in openers:
        for c in s.get('calls',[]):
            args=c.get('arguments',[])
            if c.get('name')=='GetLocalString' and len(args)>1 and isinstance(args[1],str):variables.add(args[1])
        if any(s.get('functions',{}).get(fn) for fn in ('GetObjectByTag','GetNearestObjectByTag')):
            tags.update(v['value'] for v in s.get('literals',[]) if v.get('value') in stores)
    for v in row.get('native_store_variables',[]):
        if v['Name'] in variables and v['Value'] in stores:tags.add(v['Value'])
    return dict(detected=bool(openers),conversation=row.get('conversation',''),variables=sorted(variables)[:32],
                tags=sorted(tags)[:32],scripts=sorted(s['id'] for s in openers)[:64])


def refresh(p, report):
    rows=sorted(report['characters'],key=lambda c:c['kind']!='placed')
    for n in p['npcs']:
        row=next(c for c in rows if (c['tag'],c['resref'].lower())==(n['native_tag'],n['native_resref']))
        link=binding(report,row)
        if 'native_store' not in n:
            n['merchant']=dict(defaults(),enabled=link['detected'])
        n['native_store']=link
        if not link['detected']:n['merchant']['enabled']=False
    return p


def adapt_runtime(scripts, p, literal, replace):
    """Read the real store; all trading continues through the authored dialogue."""
    src=scripts['aw_merchant']
    src=replace(src,'AWFind(AWShops(),GetTag(actor))','AWFind(AWShops(),RWProfile(actor))')
    start=src.index('object AWMStore(object actor)');end=src.index('\nobject AWMHolder',start)
    src=src[:start]+'''object AWMStore(object actor){
 json shop=AWMShop(actor);json vars=JsonObjectGet(shop,"store_variables");json tags=JsonArray();
 int i=0;while(i<JsonGetLength(vars)){string tag=GetLocalString(actor,JsonGetString(JsonArrayGet(vars,i)));if(tag!="")tags=JsonArrayInsert(tags,JsonString(tag));i++;}
 if(JsonGetLength(tags)==0)tags=JsonObjectGet(shop,"store_tags");
 object found=OBJECT_INVALID;int count=0;i=0;
 while(i<JsonGetLength(tags)){string tag=JsonGetString(JsonArrayGet(tags,i));int k=0;object candidate=GetObjectByTag(tag,k);
  while(GetIsObjectValid(candidate) && k<64){if(GetObjectType(candidate)==OBJECT_TYPE_STORE && candidate!=found){found=candidate;count++;}k++;candidate=GetObjectByTag(tag,k);}
  if(k==64 && GetIsObjectValid(candidate))return OBJECT_INVALID;i++;}
 if(count!=1)return OBJECT_INVALID;return found;
}'''+src[end:]
    src=src.replace('JsonString(GetTag(actor))','JsonString(RWProfile(actor))')
    # The original menu must grant access before stock is exposed. Only native
    # OpenStore updates GetLastOpenedBy; naming a shop is not an access grant.
    src=replace(src,'JsonInt(valid && AWMNear(pc,actor))','JsonInt(valid && GetLastOpenedBy(store)==pc && AWMNear(pc,actor))')
    src=replace(src,'JsonInt(!valid)','JsonInt(!valid || GetLastOpenedBy(store)!=pc)')
    src=replace(src,'object item=GetFirstItemInInventory(store);int count=0;', 'object item=OBJECT_INVALID;if(valid && GetLastOpenedBy(store)==pc)item=GetFirstItemInInventory(store);int count=0;')
    src=replace(src,'count<32','count<256')
    start=src.index('void AWMOpen(');end=src.index('\nvoid AWMBuy(',start)
    src=src[:start]+'''string RWMTradeDialogue(object actor){return "";}
void AWMOpen(object pc,object actor,int haggle=FALSE){
 json shop=AWMShop(actor);if(AWText(shop,"id")=="" || !AWMNear(pc,actor) || IsInConversation(pc) || IsInConversation(actor))return;
 // A separate trading dialogue retains native starting conditions and runs
 // the original store action in its required GetPCSpeaker context.
 string dlg=RWMTradeDialogue(actor);if(dlg=="")dlg=AWText(shop,"conversation");if(dlg==""){SendMessageToPC(pc,"Use this character's original trading interaction.");return;}
 AssignCommand(actor,ActionStartConversation(pc,dlg,TRUE,FALSE));
}'''+src[end:]
    # There is no custom transaction path for imported native stores.
    start=src.index('void AWMBuy(')
    src=src[:start]+'void AWMBuy(object pc,object actor,int index){}\n'
    scripts['aw_merchant']=src


def add_trade_dialogues(entries, extra, report, p, scripts, literal, replace):
    """Shortcut only script-free roots with one unconditional terminal shop choice.

    Clone the enhanced native dialogue, retaining start-condition order and all
    other paths. Native quest/action gates are never skipped. No NCS is changed.
    """
    from .nwn.gff import read,write,text
    from .nwn.area_tools import set_value
    records=[];dispatch=[];cache={}
    for n in p['npcs']:
        if not n['ai_enabled'] or not n['merchant']['enabled']:continue
        link=n.get('native_store',{});name=link.get('conversation','');key=(name,2029)
        if key not in entries:continue
        if name not in cache:
            original=next((d for d in report['dialogues'] if d['id']==name),None)
            if original is None:continue
            # Wrapped actions keep their original names in the report.
            actions={line['id']:line.get('action','') for line in original.get('lines',[])}
            kind,dlg=read(entries[key]);roots=dlg[1].get('StartingList',(15,[]))[1]
            changed=[]
            for idx in dict.fromkeys(r[1].get('Index',(4,-1))[1] for r in roots):
                nodes=dlg[1].get('EntryList',(15,[]))[1];replies=dlg[1].get('ReplyList',(15,[]))[1]
                if not 0<=idx<len(nodes):continue
                entry=nodes[idx];fields=entry[1]
                if 'EntryList:'+str(idx) not in actions or actions['EntryList:'+str(idx)] or any(fields.get(k,(10,b''))[1] for k in ('Quest','Speaker')):continue
                choices=[]
                for edge in fields.get('RepliesList',(15,[]))[1]:
                    ri=edge[1].get('Index',(4,-1))[1]
                    if not 0<=ri<len(replies):continue
                    action=actions.get('ReplyList:'+str(ri),'')
                    if action not in link.get('scripts',[]):continue
                    r=replies[ri][1]
                    if edge[1].get('Active',(11,b''))[1] or r.get('Quest',(10,b''))[1] or r.get('EntriesList',(15,[]))[1]:choices.append(None)
                    else:choices.append((ri,action))
                if len(choices)!=1 or choices[0] is None:continue
                ri,action=choices[0]
                set_value(entry,'Text',text(''),12);set_value(entry,'RepliesList',[],15)
                set_value(entry,'Script',action.encode('ascii'),11)
                changed.append(dict(entry=idx,reply=ri,action=action))
            if not changed:cache[name]='';continue
            target='rwc_t'+str(len(records)).zfill(5)
            extra[target,2029]=write(kind,dlg);cache[name]=target
            records.append(dict(dialogue=target,original=name,shortcuts=changed))
        if cache[name]:dispatch.append('if(RWProfile(actor)=='+literal(n['id'])+')return '+literal(cache[name])+';')
    if dispatch:
        scripts['aw_merchant']=replace(scripts['aw_merchant'],'string RWMTradeDialogue(object actor){return "";}',
            'string RWMTradeDialogue(object actor){'+''.join(dispatch)+'return "";}')
    return records
