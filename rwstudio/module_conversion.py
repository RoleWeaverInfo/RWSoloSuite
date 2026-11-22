"""Copy-on-convert NWN modules. Original geometry and quest resources stay intact."""
from collections import OrderedDict
from pathlib import Path
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from .builder import ROOT,BUILD_LOCK,literal,conversation,string
from .content import canonical
from .storage import write_json
from .module_analysis import Resources,sha256
from .nwn.analysis_formats import Archive,gff
from .nwn.gff import read,write,text
from .nwn.area_tools import set_value as put,pack_module,node
from .imported_module import plan,validate
from .conversion_runtime import runtime

EVENTS={'Mod_OnModLoad':'rwc_load','Mod_OnClientEntr':'rwc_enter','Mod_OnHeartbeat':'rwc_beat','Mod_OnPlrChat':'rwc_chat'}

def patch_dialogues(entries,report,res,scripts):
    """Remember executed nodes; retain native actions and append safe AI exits."""
    changed={};counter=0;memory_count=0
    names={n['conversation'] for n in report['characters'] if n['conversation']}
    for name in sorted(names):
        key=name,2029
        if key not in entries:continue  # Never override an external HAK dialogue.
        raw=entries[key];plain=gff(raw);kind,dlg=read(raw)
        originals=copy.deepcopy(dlg);replies=dlg[1].get('ReplyList',(15,[]))[1]
        original_reply_count=len(replies);added=[];wrapped=[]
        for idx,entry in enumerate(dlg[1].get('EntryList',(15,[]))[1]):
            links=entry[1].get('RepliesList',(15,[]))[1];safe=False
            for link in links:
                ri=link[1].get('Index',(4,-1))[1]
                if not 0<=ri<original_reply_count or link[1].get('Active',(11,b''))[1]:continue
                reply=replies[ri][1]
                label=res.text(plain['ReplyList'][ri].get('Text',''))
                if (not reply.get('EntriesList',(15,[]))[1] and not reply.get('Script',(11,b''))[1]
                    and not reply.get('Quest',(10,b''))[1] and re.search(r'\b(farewell|goodbye|good bye|leave|bye|never mind|nothing else|see you later|perhaps later|right now|for now|on our way|thank(?:s| you) for your time)\b',label,re.I)):
                    safe=True;break
            # Ordinary one-line greetings previously closed without any AI option.
            terminal=not links and not any(entry[1].get(k,(11,b''))[1] for k in ('Script','Quest','Speaker'))
            if not safe and not terminal:continue
            script='rwc_s'+str(counter).zfill(5);counter+=1
            scripts[script]='#include "sp_inc"\nvoid main(){ExecuteScript("sp_select",OBJECT_SELF);}'
            reply=conversation([('',[0])],[('Talk freely with AI.',[],script)])[1]['ReplyList'][1][0]
            replies.append((len(replies),reply[1]))
            links.append(node(len(links),Index=(4,len(replies)-1),Active=(11,b'rwc_can_chat'),IsChild=(0,0)))
            if terminal:
                farewell=conversation([('',[0])],[('Farewell.',[])])[1]['ReplyList'][1][0]
                replies.append((len(replies),farewell[1]));links.append(node(len(links),Index=(4,len(replies)-1),Active=(11,b''),IsChild=(0,0)))
            put(entry,'RepliesList',links,15);added.append(dict(index=idx,links=2 if terminal else 1))
        # Actions execute only on the node actually reached. Do not wrap Active
        # conditions: the engine can probe conditions for unseen branches.
        for collection,short in [('EntryList','e'),('ReplyList','r')]:
            for idx,line in enumerate(dlg[1].get(collection,(15,[]))[1][:len(plain.get(collection,[]))]):
                original=plain[collection][idx];spoken=res.text(original.get('Text',''))[:6000]
                if not spoken:continue
                script='rwc_m'+str(memory_count).zfill(5);memory_count+=1
                old=original.get('Script','')
                speaker=original.get('Speaker','')
                label=literal('Player') if short=='r' else (literal(speaker) if speaker else 'GetName(actor)')
                action='ExecuteScript('+literal(old)+',OBJECT_SELF);' if old else ''
                scripts[script]='#include "rwc_memory"\nvoid main(){object pc=GetPCSpeaker();object actor=OBJECT_SELF;'+action+'RWRemember(pc,actor,'+literal(name+':'+short+':'+str(idx))+','+label+','+literal(spoken)+');}'
                string(line,'Script',script,11);wrapped.append(dict(collection=collection,index=idx,original_action=old,wrapper=script))
        if added or wrapped:
            if added:put(dlg,'ReplyList',replies,15)
            entries[key]=write(kind,dlg)
            changed[name]=dict(entries=[a['index'] for a in added],added_replies=len(replies)-original_reply_count,memory_nodes=len(wrapped),action_wrappers=wrapped)
            check=copy.deepcopy(dlg)
            # Reconstruct the original structure and demand exact equality.
            for item in wrapped:
                fields=check[1][item['collection']][1][item['index']][1]
                old=originals[1][item['collection']][1][item['index']][1]
                if 'Script' in old:fields['Script']=old['Script']
                else:fields.pop('Script',None)
            if 'ReplyList' in originals[1]:check[1]['ReplyList'][1][:]=check[1]['ReplyList'][1][:original_reply_count]
            else:check[1].pop('ReplyList',None)
            for item in added:
                idx=item['index'];fields=check[1]['EntryList'][1][idx][1]
                old=originals[1]['EntryList'][1][idx][1]
                if 'RepliesList' in old:del fields['RepliesList'][1][-item['links']:]
                else:fields.pop('RepliesList',None)
            if check!=originals:raise ValueError('Original dialogue changed unexpectedly: '+name)
    return changed


def validate_plan_for_report(p,report):
    p=validate(p);base=plan(report)
    if p['source_sha256']!=report['module']['sha256'] or p['id']!=base['id']:raise ValueError('The conversion plan belongs to a different imported module')
    identity=lambda rows:{n['id']:(n['native_tag'],n['native_resref']) for n in rows}
    if identity(p['npcs'])!=identity(base['npcs']):raise ValueError('Native character identities cannot be changed during conversion')
    from .conversion_profiles import refresh
    p=validate(refresh(p,report))
    source_stem=Path(report['module']['filename']).stem
    if p['module_name'].casefold()==source_stem.casefold():raise ValueError('Choose a different filename for the AI copy')
    return p

def build(path,report,profile,store,config,progress=lambda s:None):
    with BUILD_LOCK:return _build(Path(path),report,profile,store,config,progress)

def _build(path,report,profile,store,config,progress):
    p=validate_plan_for_report(profile,report)
    if sha256(path)!=p['source_sha256']:raise ValueError('The analysed snapshot changed. Import it again.')
    if path.stat().st_size>512_000_000:raise ValueError('This conversion pass supports module archives up to 512 MB. External HAKs are streamed without this limit.')
    compiler=Path(config.get('compiler',''));game_root=Path(config.get('game_root',''))
    if not compiler.is_file() or not (game_root/'data').is_dir():raise ValueError('Set the installed NWN folder and NWScript compiler in Local settings')
    progress('Resolving original module dependencies')
    res=Resources(path,config)
    missing=[d['name'] for d in res.dependencies if not d['found']]
    if missing:raise ValueError('Missing dependencies: '+', '.join(missing)+'. Set the dependency folder before converting.')
    if not res.game:raise ValueError('Installed NWN resources are required for conversion')
    # Stream BIF reads instead of loading large game archives into memory.
    class Game:
        index=res.game.index
        def get(self,name,kind):
            path,index=self.index[name.lower(),kind]
            import struct
            with path.open('rb') as f:
                f.seek(16);table=struct.unpack('<I',f.read(4))[0];f.seek(table+index*16)
                _,offset,size,actual=struct.unpack('<4I',f.read(16))
                if actual!=kind or size>32_000_000:raise ValueError('Invalid game resource')
                f.seek(offset);return f.read(size)
    raw=path.read_bytes();entries=OrderedDict((key,res.module.get(*key)) for key in res.module.index)
    original=dict(entries);ifo_kind,module=read(entries['module',2014])
    hooks={k:res.ifo.get(k,'') for k in EVENTS}
    scripts,extra=runtime(p,'0'*20,Game(),hooks)
    changes=patch_dialogues(entries,report,res,scripts)
    dependencies=[]
    for filename,archive in res.packs:dependencies.append((archive.path,dict(file=filename,kind='hak',sha256=sha256(archive.path))))
    if 'custom' in res.tables:
        file=res.tables['custom'].path;dependencies.append((file,dict(file=file.name,kind='tlk',sha256=sha256(file))))
    instructions=play_instructions(p,report,changes)
    digest=hashlib.sha256(canonical(dict(profile=p,scripts=scripts,extra={n+'.'+str(k):hashlib.sha256(v).hexdigest() for (n,k),v in extra.items()},dependencies=[d for _,d in dependencies],instructions=instructions,format=1)).encode()).hexdigest()[:20]
    scripts['sp_config']=scripts['sp_config'].replace('"'+'0'*20+'"','"'+digest+'"')
    destination=store.root/'builds'/digest
    if (destination/'manifest.json').is_file():
        manifest=json.loads((destination/'manifest.json').read_text(encoding='utf-8'))
        if sha256(destination/manifest['module'])!=manifest['sha256']:raise ValueError('Existing converted build checksum mismatch')
        if not all((destination/name).is_file() for name in ('project.json','preservation.json',p['module_name']+'.rwproject.json',p['module_name']+'-aurora.zip')):raise ValueError('Existing converted build is incomplete')
        return manifest
    # Never replace a resource from the module or its required HAKs. Includes
    # from the installed engine are compile-only and not injected into a module.
    candidates=set(extra)|{(k,t) for k in scripts if k!='nw_inc_nui' for t in (2009,2010)}
    collisions=candidates.intersection(original)
    for _,pack in res.packs:collisions.update(candidates.intersection(pack.index))
    if collisions:raise ValueError('Module already uses Role Weaver runtime names: '+', '.join(n for n,k in sorted(collisions)[:12])+'. Start from an unconverted original.')
    entries.update(extra)
    for field,script in EVENTS.items():string(module,field,script,11)
    put(module,'Mod_Name',text(p['title']),12);put(module,'Mod_ID',hashlib.sha256(digest.encode()).digest()[:16],13)
    entries['module',2014]=write(ifo_kind,module)
    with tempfile.TemporaryDirectory(prefix='conversion-',dir=store.root) as temp:
        out=Path(temp);source=out/'source';source.mkdir();compiled=out/'compiled';compiled.mkdir()
        for name,body in scripts.items():(source/(name+'.nss')).write_text(body+'\n',encoding='utf-8')
        progress('Compiling the additional AI and companion scripts')
        result=subprocess.run([str(compiler.resolve()),'-n',str(game_root.resolve()),'-i',str(source.resolve()),'-b',str(compiled.resolve()),*[f.name for f in sorted(source.glob('*.nss'))]],cwd=source,capture_output=True,text=True,timeout=240,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode:raise ValueError('Conversion script compilation failed: '+(result.stdout+result.stderr)[-6000:])
        (out/'compile.log').write_text(result.stdout+result.stderr,encoding='utf-8')
        for name,body in scripts.items():
            if name=='nw_inc_nui':continue
            entries[name,2009]=(source/(name+'.nss')).read_bytes();ncs=compiled/(name+'.ncs')
            if ('void main(' in body or 'StartingConditional(' in body) and not ncs.is_file():raise ValueError('Missing compiled script: '+name)
            if ncs.is_file():entries[name,2010]=ncs.read_bytes()
        progress('Verifying original maps, quests, creatures and compiled scripts')
        allowed={('module',2014)}|{(name,2029) for name in changes}
        unexpected=[k for k,v in original.items() if entries.get(k)!=v and k not in allowed]
        if unexpected:raise ValueError('Preservation check failed: '+str(unexpected[:10]))
        old_ifo=read(original['module',2014])[1][1];new_ifo=module[1]
        if {k:v for k,v in old_ifo.items() if k not in set(EVENTS)|{'Mod_Name','Mod_ID'}}!={k:v for k,v in new_ifo.items() if k not in set(EVENTS)|{'Mod_Name','Mod_ID'}}:raise ValueError('Original module settings changed unexpectedly')
        mod=out/(p['module_name']+'.mod');mod.write_bytes(pack_module(raw,entries));packed=Archive(mod)
        if set(packed.index)!=set(entries) or any(packed.get(*key)!=value for key,value in entries.items()):raise ValueError('Exported module failed resource verification')
        preservation=dict(source_sha256=p['source_sha256'],source_filename=report['module']['filename'],original_resources=len(original),unchanged_resources=len(original)-len(allowed),
            maps_byte_identical=True,original_scripts_byte_identical=True,creatures_byte_identical=True,quests_byte_identical=True,
            wrapped_events=hooks,dialogue_additions=changes,gameplay_tested=False,
            note='Static preservation checks passed. Native callbacks still require in-game regression testing.',
            resources=[dict(name=n,type=k,sha256=hashlib.sha256(v).hexdigest(),unchanged=entries[n,k]==v) for (n,k),v in original.items()])
        manifest=dict(build_id=digest,project_id=p['id'],title=p['title'],module=mod.name,sha256=sha256(mod),resources=len(entries),areas=len(report['areas']),rooms=0,quests=len(report['quests']),compiled_scripts=sum(k==2010 for n,k in entries),standalone=True,optional_live_ai=True,gameplay_tested=False,converted=True,path=str(destination/mod.name))
        write_json(out/'project.json',p);write_json(out/(p['module_name']+'.rwproject.json'),dict(build_id=digest,project=p));write_json(out/'manifest.json',manifest);write_json(out/'preservation.json',preservation)
        write_json(out/'dependencies.json',[d for _,d in dependencies])
        for file,dep in dependencies:
            target=out/dep['kind']/dep['file'];target.parent.mkdir(exist_ok=True);shutil.copy2(file,target)
            if sha256(target)!=dep['sha256']:raise ValueError('Dependency changed during conversion: '+dep['file'])
        (out/'PLAY.txt').write_text(instructions,encoding='utf-8')
        shutil.copy2(ROOT/'ROLE-WEAVER-LICENSE.txt',out/'ROLE-WEAVER-LICENSE.txt')
        # A converted community adventure is not a Studio authoring project.
        # Package only this copy and explicit dependencies, never local settings.
        from .player_package import export_keys,write_checked
        keys=export_keys()
        with zipfile.ZipFile(out/(p['module_name']+'-aurora.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for file in [mod,out/(p['module_name']+'.rwproject.json'),out/'manifest.json',out/'preservation.json',out/'dependencies.json',out/'PLAY.txt',out/'ROLE-WEAVER-LICENSE.txt',*source.glob('*.nss'),*(out/'hak').glob('*.hak'),*(out/'tlk').glob('*.tlk')]:write_checked(z,file,file.relative_to(out).as_posix(),keys)
        if sha256(path)!=p['source_sha256']:raise ValueError('Original snapshot changed during conversion')
        if destination.exists():
            # A previously registered runtime context is not an output to overwrite.
            raise ValueError('Build destination already exists without a complete export. Delete the incomplete build folder after backing it up.')
        root=store.root.resolve()
        if not out.resolve().is_relative_to(root) or destination.resolve().parent!=root/'builds':raise ValueError('Invalid conversion output path')
        os.replace(out,destination)
    return manifest

def play_instructions(p,report,changes):
    return f'''{p['title']}
AI-enabled copy of {report['module']['filename']}

Requires NWN: Enhanced Edition and a Role Weaver Module Studio build with module conversion support. Original module/HAK authors retain their rights. This local conversion grants no redistribution permission. Obtain permission before sharing somebody else's adventure or content packs.

1. Keep the .mod and matching .rwproject.json together. Start the updated Role Weaver service, import the sidecar on AI service status, and configure your own OpenAI or Gemini key.
2. With NWN closed, install the module using Module Conversion > AI conversion > Install copy. For a downloaded copy, copy the .mod to Neverwinter Nights/modules, hak files to hak, and tlk files to tlk; preserve their original names. Do not overwrite different existing packs.
3. Start NWN separately and choose a NEW GAME with {p['module_name']}. Existing saves of the original module do not contain these additions. Keep Role Weaver running.
4. Original NPC menus handle quest acceptance, journal progress, rewards, stores, recruitment and dismissal. AI roleplay does not control those choices. Original maps, creature blueprints, encounters, journal and all original compiled scripts were retained byte-for-byte.
5. At safe farewell choices and ordinary one-line greetings, eligible conversations include Talk freely with AI ({len(changes)} dialogue files enhanced). Close the menu and speak in Talk. Else use !talk <alias> <message> nearby, or address a unique nearby NPC by name followed by a colon. Use !end to finish. Duplicate nearby creatures must be selected individually through dialogue; aliases never guess between them.
6. Recruit allies through the module's original dialogue. Type !companions for AI chat, follow/stay/guard, inventory and errands with recruited allies, familiars or summons. Native recruitment, party limits, XP rules and dismissal remain unchanged. Locked/trapped containers, protected items, possession and combat restrictions still apply. Animals use nonverbal responses.
7. Companion errands are optional and may interact with module-specific item scripts; test ordinary quest pickup and reward paths. AI profiles include public descriptions, setting and optional generated characterization. Original NPC lines and player replies are remembered as they occur and persist in saves. Unvisited branches are withheld from AI prompts. Companions can discuss recent conversations shared by their owner. Creator-edited knowledge is public. Native quest state is not inferred from static scripts; use original menus for progression and rewards.
8. Detected native merchants have AI merchant abilities enabled by default unless the creator disables them. Open their original shop once before asking AI about current stock. Requests to browse, buy or negotiate return to the original trading conversation; choose its shop option to trade. Native access conditions, prices, Appraise rules, discounts and item transfers stay in control. AI cannot grant an extra discount or complete a sale outside that interface.

Open the AI copy in Aurora to edit it. Keep edits in another file: converting again always starts from the original snapshot. The preservation.json file records resource hashes and dialogue additions. Static checks do not prove a full playthrough; test quest completion, transitions, rest/death, recruitment/dismissal, save/load, summoned companion conversation and inventory.

NPC aliases:
'''+ '\n'.join(n['alias']+' — '+n['name'] for n in p['npcs'] if n['ai_enabled'])+'\n'
