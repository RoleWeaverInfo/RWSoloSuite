"""Evidence-led module inventory. Source modules, maps and scripts are read only."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import re
import struct
from .nwn.analysis_formats import Archive,TalkTable,TYPES,gff,decode
from .nwn.script_analysis import analyse as script_analysis,prototypes
from .nwn.game_assets import GameAssets

def sha256(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def safe_name(value):
    return isinstance(value,str) and value not in ('.','..') and bool(re.fullmatch(r'[^/\\:\x00-\x1f?*"<>|]{1,64}',value))

class Resources:
    def __init__(self,path,config):
        self.module=Archive(path);self.config=config;self.packs=[];self.dependencies=[];self.issues=[];self.unresolved=set();self.tables={};self.bundle={}
        self.game=None
        try:self.game=GameAssets(config['game_root']) if config.get('game_root') else None
        except (ValueError,OSError,AssertionError,IndexError,struct.error) as exc:self.issues.append('Installed game resources could not be indexed: '+str(exc))
        self.ifo=gff(self.module.get('module',2014))
        user=Path(config.get('user_dir') or '.');content=Path(config.get('content_root') or user/'hak');game=Path(config.get('game_root') or '.')
        if config.get('analysis_bundle_root'):
            base=Path(config['analysis_bundle_root']).resolve();seen=0
            for folder,dirs,files in os.walk(base,followlinks=False):
                dirs[:]=sorted(d for d in dirs if not (Path(folder)/d).is_symlink() and not getattr(Path(folder)/d,'is_junction',lambda:False)())
                if len(Path(folder).relative_to(base).parts)>=8:
                    if dirs:self.issues.append('Dependency folder search stopped at eight levels; deeper packs were not inspected.')
                    dirs[:]=[]
                seen+=1+len(files)
                if seen>50000:self.issues.append('Dependency folder search budget reached; some packs may be reported missing.');break
                for file in sorted(files):
                    p=Path(folder)/file
                    if p.suffix.lower() in ('.hak','.tlk') and not p.is_symlink():
                        if file.lower() in self.bundle:self.issues.append('Multiple copies of dependency '+file+' found; the first folder match was used.')
                        else:self.bundle[file.lower()]=p
        roots=[content,user/'hak',game/'hak']
        for item in self.ifo.get('Mod_HakList',[]):
            name=item.get('Mod_Hak','');file=self.find(name,'.hak',roots)
            dep={'name':name,'kind':'HAK','found':False}
            if file:
                try:
                    pack=Archive(file,allow_duplicates=True);self.packs.append((file.name,pack));dep.update(found=True,resources=len(pack.index))
                    if pack.duplicates:
                        dep['duplicate_entries']=len(pack.duplicates);self.issues.append(file.name+': '+str(len(pack.duplicates))+' duplicate resource entries; first definitions used for inspection. Runtime selection may differ.')
                except (ValueError,OSError) as exc:dep['error']=str(exc)
            self.dependencies.append(dep)
        custom=self.ifo.get('Mod_CustomTlk','')
        if custom:
            file=self.find(custom,'.tlk',[user/'tlk',content,content.parent/'tlk',game/'tlk'])
            dep={'name':custom,'kind':'TLK','found':False}
            if file:
                try:self.tables['custom']=TalkTable(file);dep['found']=True
                except (ValueError,OSError) as exc:dep['error']=str(exc)
            self.dependencies.append(dep)
        for file in (game/'lang/en/data/dialog.tlk',game/'data/dialog.tlk',game/'dialog.tlk'):
            if file.is_file():
                try:self.tables['base']=TalkTable(file)
                except (ValueError,OSError) as exc:self.issues.append('Base talk table: '+str(exc))
                break
        self.collisions=sum(key in self.module.index for _,pack in self.packs for key in pack.index)
    def find(self,name,suffix,roots):
        if not safe_name(name):return None
        wanted=name.lower()+suffix
        if wanted in self.bundle:return self.bundle[wanted]
        for root in roots:
            if not root.is_dir():continue
            for p in root.iterdir():
                if p.name.lower()==wanted and p.is_file():return p
        return None
    def get(self,name,kind):
        key=(str(name).lower(),kind)
        if key in self.module.index:return self.module.get(*key),key[0]+'.'+TYPES.get(kind,str(kind))
        for label,pack in self.packs:
            if key in pack.index:return pack.get(*key),label+':'+key[0]+'.'+TYPES.get(kind,str(kind))
        if self.game and key in self.game.index:
            path,index=self.game.index[key]
            with path.open('rb') as f:
                f.seek(16);table=struct.unpack('<I',f.read(4))[0];f.seek(table+index*16)
                _,off,size,actual=struct.unpack('<4I',f.read(16))
                if size>32_000_000 or actual!=kind:raise ValueError('Invalid or oversized game resource.')
                f.seek(off);raw=f.read(size)
                if len(raw)!=size:raise ValueError('Truncated game resource.')
                return raw,'game:'+key[0]+'.'+TYPES.get(kind,str(kind))
        raise KeyError(name)
    def text(self,value):
        if isinstance(value,str):return value
        if not isinstance(value,dict):return ''
        if value.get('text'):return value['text']
        ref=value.get('strref',0xffffffff)
        if ref==0xffffffff:return ''
        table='custom' if ref&0x01000000 else 'base';index=ref&0x00ffffff
        try:return self.tables[table].get(index)
        except (KeyError,ValueError,OSError):
            self.unresolved.add(ref);return '[unresolved text '+str(ref)+']'

def build_report(path,config,progress=lambda s:None,actions=None):
    res=Resources(path,config);ifo=res.ifo
    report={'format_version':1,'module':{'name':res.text(ifo.get('Mod_Name')) or Path(path).stem,'description':res.text(ifo.get('Mod_Description')),'tag':ifo.get('Mod_Tag',''),'sha256':sha256(path),'bytes':Path(path).stat().st_size,'resource_count':len(res.module.index)},
        'areas':[],'characters':[],'encounters':[],'quests':[],'dialogues':[],'scripts':[],'hooks':[],'lore':[],'dependencies':res.dependencies,'warnings':res.issues,'story':{},'ai_explanation':None}
    warnings=report['warnings'];hooks=report['hooks'];todo_dialogues=set();todo_scripts=set();parsed={};budget=0
    def document(name,kind):
        nonlocal budget
        key=name,kind
        if key in parsed:return parsed[key]
        raw,source=res.get(name,kind);budget+=len(raw)
        if budget>256_000_000:raise ValueError('Analysis text budget reached; remaining resources were not inspected.')
        node=gff(raw);parsed[key]=(node,source);return node,source
    def scan_hooks(node,owner,source):
        for field,val in node.items():
            if isinstance(val,str) and val and (field.startswith(('Mod_On','Script')) or field.startswith('On')):
                name=val.lower();hooks.append({'owner':owner,'event':field,'script':name,'source':source+'/'+field});todo_scripts.add(name)
    def text_field(node,*names):return next((res.text(node[n]) for n in names if n in node and res.text(node[n])), '')
    def character(node,source,area='',kind='blueprint',ref=''):
        name=(text_field(node,'FirstName')+' '+text_field(node,'LastName')).strip() or text_field(node,'LocName','LocalizedName') or node.get('Tag') or ref
        dialogue=node.get('Conversation','').lower()
        if dialogue:todo_dialogues.add(dialogue)
        row={'name':name,'tag':node.get('Tag',''),'resref':ref or node.get('TemplateResRef',''),'kind':kind,'area':area,'description':text_field(node,'Description'),'conversation':dialogue,'faction_id':node.get('FactionID'),'race':node.get('Race'),'appearance':node.get('Appearance_Type'),'classes':node.get('ClassList',[]),'source':source,
             'position':{k:node[k] for k in ('XPosition','YPosition','ZPosition') if k in node},
             'inventory':[i.get('InventoryRes',i.get('TemplateResRef','')) for i in node.get('ItemList',[])],
             'inferred_role':[]}
        scan_hooks(node,name,source);report['characters'].append(row)
    def encounter(node,source,area='',kind='blueprint',ref=''):
        name=text_field(node,'LocalizedName','LocName') or node.get('Tag') or ref
        row={'name':name,'tag':node.get('Tag',''),'resref':ref or node.get('TemplateResRef',''),'area':area,'kind':kind,'active':node.get('Active'),'difficulty':node.get('Difficulty'),'minimum':node.get('RecCreatures'),'maximum':node.get('MaxCreatures'),'respawns':node.get('Respawns'),'creatures':node.get('CreatureList',[]),'source':source}
        report['encounters'].append(row);scan_hooks(node,name,source)
    scan_hooks(ifo,'Module', 'module.ifo')
    keys=list(res.module.index)
    if len(keys)>15000:warnings.append('Only the first 15,000 resources are inventoried in this pass.');keys=keys[:15000]
    for idx,(name,kind) in enumerate(keys):
        if idx%30==0:progress('Reading resources '+str(idx+1)+' / '+str(len(keys)))
        try:
            if kind in (2012,2023,2027,2040,2056,2029,2025,2044,2032,2051,2042):node,source=document(name,kind)
            else:
                if kind==2010:todo_scripts.add(name)
                continue
            if kind==2012:
                report['areas'].append({'id':name,'name':text_field(node,'Name') or name,'tag':node.get('Tag',''),'tileset':node.get('Tileset',''),'width':node.get('Width'),'height':node.get('Height'),'source':source});scan_hooks(node,name,source)
            elif kind==2023:
                for i,obj in enumerate(node.get('Creature List',[])):character(obj,source+'/Creature List['+str(i)+']',name,'placed')
                for i,obj in enumerate(node.get('Encounter List',[])):encounter(obj,source+'/Encounter List['+str(i)+']',name,'placed')
                for collection in ('Placeable List','Door List','TriggerList','StoreList','WaypointList'):
                    for i,obj in enumerate(node.get(collection,[])):
                        location=source+'/'+collection+'['+str(i)+']';scan_hooks(obj,name,location)
                        if obj.get('Conversation'):todo_dialogues.add(obj['Conversation'].lower())
                        text=text_field(obj,'Description','DescIdentified')
                        if text:report['lore'].append({'name':text_field(obj,'LocName','LocalizedName') or obj.get('Tag',''),'text':text,'source':location})
            elif kind==2027:character(node,source,ref=name)
            elif kind==2040:encounter(node,source,ref=name)
            elif kind==2056:
                for i,q in enumerate(node.get('Categories',[])):
                    report['quests'].append({'name':text_field(q,'Name') or q.get('Tag',''),'tag':q.get('Tag',''),'xp':q.get('XP'),'source':source+'/Categories['+str(i)+']',
                        'entries':[{'id':e.get('ID'),'text':res.text(e.get('Text')),'end':bool(e.get('End')),'source':source+'/Categories['+str(i)+']/EntryList['+str(j)+']'} for j,e in enumerate(q.get('EntryList',[]))]})
            elif kind==2029:todo_dialogues.add(name)
            else:
                scan_hooks(node,name,source)
                if node.get('Conversation'):todo_dialogues.add(node['Conversation'].lower())
                text=text_field(node,'Description','DescIdentified')
                if text:report['lore'].append({'name':text_field(node,'LocName','LocalizedName') or name,'text':text,'source':source})
        except (ValueError,KeyError,OSError,struct.error,RecursionError) as exc:warnings.append(name+'.'+TYPES.get(kind,str(kind))+': '+str(exc))
    for name in sorted(todo_dialogues)[:2000]:
        try:
            node,source=document(name,2029);lines=[]
            for collection,role in (('EntryList','NPC'),('ReplyList','Player')):
                for i,line in enumerate(node.get(collection,[])):
                    at=source+'/'+collection+'['+str(i)+']';scan_hooks(line,name,at)
                    links=[]
                    for link in line.get('RepliesList' if role=='NPC' else 'EntriesList',[]):
                        target=link.get('Index');condition=link.get('Active','')
                        if condition:todo_scripts.add(condition.lower());hooks.append({'owner':name,'event':'Dialogue condition','script':condition.lower(),'source':at+'/link['+str(target)+']'})
                        links.append({'index':target,'condition':condition,'is_link':bool(link.get('IsChild'))})
                    lines.append({'id':collection+':'+str(i),'role':role,'text':res.text(line.get('Text')),'speaker':line.get('Speaker',''),'action':line.get('Script',''),'links':links,'source':at,'quest':line.get('Quest',''),'quest_entry':line.get('QuestEntry')})
            starts=[]
            for link in node.get('StartingList',[]):
                condition=link.get('Active','');starts.append({'index':link.get('Index'),'condition':condition})
                if condition:todo_scripts.add(condition.lower());hooks.append({'owner':name,'event':'Dialogue start condition','script':condition.lower(),'source':source+'/StartingList'})
            report['dialogues'].append({'id':name,'source':source,'starts':starts,'lines':lines})
        except (ValueError,KeyError,OSError,struct.error,RecursionError) as exc:warnings.append('Dialogue '+name+': '+str(exc))
    if len(todo_dialogues)>2000:warnings.append('Dialogue budget reached: only 2,000 conversations inspected.')
    if actions is None:
        try:
            # Read the installed engine header, not a module-supplied replacement.
            if not res.game or ('nwscript',2009) not in res.game.index:raise ValueError('NWN installation not configured')
            module_header=res.module.index.pop(('nwscript',2009),None);packs=res.packs;res.packs=[]
            try:raw,source=res.get('nwscript',2009);actions=prototypes(raw);report['engine_definitions']=source
            finally:
                res.packs=packs
                if module_header:res.module.index['nwscript',2009]=module_header
        except (ValueError,OSError,KeyError):actions={};warnings.append('Engine action names unavailable. Set the NWN installation in Local settings; script calls are shown by numeric ID.')
    details={};processed=set();missing=[];script_bytes=0
    while todo_scripts and len(processed)<2500:
        name=min(todo_scripts);todo_scripts.remove(name)
        if name in processed:continue
        processed.add(name);progress('Analysing compiled script '+str(len(processed))+': '+name)
        try:
            raw,source=res.get(name,2010)
            if len(raw)>8_000_000:raise ValueError('Compiled script exceeds the 8 MB decoding budget.')
            script_bytes+=len(raw)
            if script_bytes>64_000_000:
                warnings.append('Compiled script data budget reached (64 MB); remaining scripts were not inspected.');break
            result=script_analysis(raw,actions);details[name]=result
            calls=[c for c in result['calls'] if c['categories']]
            for call in calls:
                if call['name'] in ('ExecuteScript','ExecuteScriptEnhanced') and call['arguments'] and isinstance(call['arguments'][0],str):todo_scripts.add(call['arguments'][0].lower())
            summary={k:result[k] for k in ('status','bytes','instructions','warnings','functions','categories','interpretation')}
            summary.update(id=name,source=source,source_available=(name,2009) in res.module.index,debug_available=(name,2064) in res.module.index,
                calls=calls[:120],calls_total=len(calls),literals=[{'offset':s['offset'],'value':s['value'][:1000]} for s in result['strings'][:80]],literals_total=len(result['strings']))
            report['scripts'].append(summary)
        except KeyError:missing.append(name)
        except (ValueError,OSError,struct.error) as exc:report['scripts'].append({'id':name,'source':name+'.ncs','status':'unreadable','warnings':[str(exc)],'functions':{},'categories':{},'calls':[],'literals':[]})
    if todo_scripts:warnings.append('Script budget reached: only 2,500 scripts inspected.')
    if missing:warnings.append('Referenced compiled scripts not found: '+', '.join(missing[:60])+(' …' if len(missing)>60 else ''))
    script_by={s['id']:s for s in report['scripts']}
    for q in report['quests']:
        q['script_evidence']=[]
        for name,result in details.items():
            for c in result['calls']:
                if c['name']=='AddJournalQuestEntry' and c['arguments'] and c['arguments'][0]==q['tag']:
                    q['script_evidence'].append({'script':name,'offset':c['offset'],'journal_entry':c['arguments'][1] if len(c['arguments'])>1 else None,'finding':'Direct journal-call argument; prerequisites and reachability are not established.'})
            if not any(e['script']==name for e in q['script_evidence']) and q['tag'] and any(s['value']==q['tag'] for s in result['strings']):
                q['script_evidence'].append({'script':name,'finding':'Matching string literal only; a quest relationship is inferred, not verified.'})
    for char in report['characters']:
        relevant={h['script'] for h in hooks if h['source'].startswith(char['source']+'/') or (char['conversation'] and h['source'].startswith(char['conversation']+'.dlg/'))}
        char['script_refs']=sorted(relevant)
        if any('companions' in script_by.get(s,{}).get('categories',{}) for s in relevant):char['inferred_role'].append('Possible companion-related dialogue/script; recruitment not proven')
        if any('OpenStore' in script_by.get(s,{}).get('functions',{}) for s in relevant):char['inferred_role'].append('Possible merchant; linked script contains OpenStore')
    report['unresolved_texts']=sorted(res.unresolved)
    if res.unresolved:warnings.append(str(len(res.unresolved))+' talk-table references could not be resolved. Text is incomplete.')
    if res.collisions:warnings.append(str(res.collisions)+' dependency resources overlap module resources. This report inventories module definitions first; runtime override precedence is not simulated.')
    if any(not d['found'] for d in res.dependencies):warnings.append('Required dependencies are missing. Referenced text, creatures or scripts may be incomplete.')
    report['counts']={'areas':len(report['areas']),'placed_characters':sum(c['kind']=='placed' for c in report['characters']),'character_blueprints':sum(c['kind']=='blueprint' for c in report['characters']),'encounters':len(report['encounters']),'journal_quests':len(report['quests']),'dialogues':len(report['dialogues']),'compiled_scripts':len(report['scripts'])}
    evidence=[]
    if report['module']['description']:evidence.append({'text':report['module']['description'],'source':'module.ifo/Mod_Description','kind':'Module description'})
    for q in report['quests']:
        for e in q['entries'][:3]:
            if e['text']:evidence.append({'text':e['text'],'source':e['source'],'kind':'Journal: '+q['name']})
    for dlg in report['dialogues']:
        for line in dlg['lines']:
            if line['role']=='NPC' and len(line['text'])>50:evidence.append({'text':line['text'],'source':line['source'],'kind':'Dialogue: '+dlg['id']});break
    report['story']={'overview':report['module']['description'] or 'No authored module description. Review the journal and dialogue evidence below, or request an AI explanation.',
        'evidence':evidence[:120],'evidence_total':len(evidence),'note':'Recovered author text. Journal entry numbers do not establish a quest order. Personality, motives and chronology require interpretation.'}
    report['limitations']=['Read-only analysis; no conversion, registration, installation or gameplay execution.',
        'Static script calls do not prove that an action executes, or establish its prerequisites. Dynamic values and inter-script state may be unresolved.',
        'Module resources are inventoried first; missing references are searched in declared HAKs and installed game data. Overrides, NWSync and external campaign databases are not simulated.',
        'Authored journal entries and conversations may describe mutually exclusive branches or spoilers. Inferred roles and AI explanations require review.',
        'Budgets: 15,000 module resources, 2,000 dialogues, 2,500 scripts, 256 MB parsed resource data, 64 MB compiled script data, 250,000 instructions per script. Any incomplete inspection is reported.']
    report['resource_types']=dict(Counter(TYPES.get(k,str(k)) for _,k in res.module.index))
    report['missing_scripts']=missing
    report['warnings']=list(dict.fromkeys(warnings))
    from .conversion_merchants import add_store_metadata
    return add_store_metadata(report,path),details
