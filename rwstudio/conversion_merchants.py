"""Link imported merchants to native shops without recreating stock or prices."""
import copy
from .merchants import defaults


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
    start=src.index('void AWMOpen(');end=src.index('\nvoid AWMBuy(',start)
    src=src[:start]+'''void AWMOpen(object pc,object actor,int haggle=FALSE){
 json shop=AWMShop(actor);if(AWText(shop,"id")=="" || !AWMNear(pc,actor) || IsInConversation(pc) || IsInConversation(actor))return;
 // Re-enter the original dialogue. Its conditions, trade scripts, Appraise
 // rules, discounts and purchase/sale events remain authoritative.
 string dlg=AWText(shop,"conversation");if(dlg==""){SendMessageToPC(pc,"Use this character's original trading interaction.");return;}
 AssignCommand(actor,ActionStartConversation(pc,dlg,TRUE,FALSE));
}'''+src[end:]
    # There is no custom transaction path for imported native stores.
    start=src.index('void AWMBuy(')
    src=src[:start]+'void AWMBuy(object pc,object actor,int index){}\n'
    scripts['aw_merchant']=src
