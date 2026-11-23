"""Apply isolated, reviewed native mission call edits to a new module copy."""
import copy
import hashlib
import re
from .general_missions import ADAPTER, inspect, JOURNAL, PAYMENT
from .managed_missions import active_all
from .nwn.mission_bytecode import suppress
from .nwn.script_analysis import analyse
from .nwn.gff import read, write, text
from .nwn.area_tools import node
from .builder import ROOT, literal, conversation
from .adventure_builder import json_function
from .conversion_runtime import replace


def apply(entries, report, p, scripts, actions, path):
    missions=[m for m in active_all(p) if m['adapter']==ADAPTER]
    audit=dict(adapter=ADAPTER,missions=[],scripts=[],dialogues=[],journals=[],original_script_hashes={},removed_resources=[])
    if not missions:return audit
    tags={m['source_tag'] for m in missions}; selections={}
    for m in missions:
        meta=inspect(report,m['source_tag'],path)
        if meta['blockers']:raise ValueError(m['quest']['name']+': '+meta['blockers'][0])
        # Build only from server-derived call sites; profiles cannot inject offsets.
        for call in meta['journal_calls']+meta['reward_evidence']:
            name=call['script'];selections.setdefault(name,{})[call['offset']]=call['name']
        audit['missions'].append(dict(source_tag=m['source_tag'],name=m['quest']['name'],journal_calls=meta['journal_calls'],replaced_rewards=meta['reward_evidence'],warnings=meta['warnings']))
        audit['original_script_hashes'].update(meta['original_script_hashes'])
    for name, selected in selections.items():
        if name in scripts or name.startswith('rwg_'):raise ValueError('Native mission script collides with the Studio runtime: '+name)
        raw=entries[name,2010]
        if hashlib.sha256(raw).hexdigest()!=audit['original_script_hashes'].get(name):raise ValueError('Native script fingerprint changed: '+name)
        decoded=analyse(raw,actions)
        for c in decoded['calls']:
            if c['offset'] in selected and c['name'] in JOURNAL and (not c['arguments'] or c['arguments'][0] not in tags):raise ValueError('A native journal call belongs to another mission')
        entries[name,2010]=suppress(raw,actions,selected);audit['scripts'].append(name)
        # Retaining stale source/debug files would let Aurora silently undo the
        # conversion on recompilation. The originals are backed up in the export.
        for kind in (2009,2064):
            if (name,kind) in entries:
                del entries[name,kind];audit['removed_resources'].append([name,kind])
    for m in missions:
        original=next(q for q in report['quests'] if q['tag']==m['source_tag'])
        match=re.fullmatch(r'([a-z0-9_]{1,16})\.jrl/Categories\[([0-9]+)\]',original['source'],re.I)
        if not match or (match[1].lower(),2056) not in entries:raise ValueError('Mission journal is not editable inside this module')
        key=match[1].lower(),2056;kind,jrl=read(entries[key]);before=copy.deepcopy(jrl);q=m['quest'];category=jrl[1]['Categories'][1][int(match[2])]
        if category[1]['Tag'][1].decode('cp1252')!=m['source_tag']:raise ValueError('Journal binding changed')
        category[1]['Name']=(12,text(q['name']));category[1]['XP']=(8,0.0) # Explicit checked award; no native journal XP payout.
        category[1]['EntryList']=(15,[node(i,ID=(4,i+1),Text=(12,text(s['description'])),End=(0,0)) for i,s in enumerate(q['steps'])]+[node(999,ID=(4,999),Text=(12,text(q['completion'])),End=(0,1))])
        restored=copy.deepcopy(jrl);restored[1]['Categories'][1][int(match[2])]=before[1]['Categories'][1][int(match[2])]
        if restored!=before:raise ValueError('An unrelated journal category changed during mission conversion')
        entries[key]=write(kind,jrl);audit['journals'].append(key[0])
    for (name,kind),raw in list(entries.items()):
        if kind!=2029:continue
        magic,dlg=read(raw);before=copy.deepcopy(dlg);changed=False;edits=[]
        for collection in ('EntryList','ReplyList'):
            for line in dlg[1].get(collection,(15,[]))[1]:
                if line[1].get('Quest',(10,b''))[1].decode('cp1252') in tags:
                    edits.append((collection,dlg[1][collection][1].index(line),line[1].get('QuestEntry')))
                    line[1]['Quest']=(10,b'');line[1]['QuestEntry']=(4,0);changed=True
        if changed:
            restored=copy.deepcopy(dlg)
            for collection,index,old_entry in edits:
                fields=restored[1][collection][1][index][1];fields['Quest']=before[1][collection][1][index][1]['Quest']
                if old_entry is None:fields.pop('QuestEntry',None)
                else:fields['QuestEntry']=old_entry
            if restored!=before:raise ValueError('Unrelated native dialogue changed during mission conversion')
            entries[name,kind]=write(magic,dlg);audit['dialogues'].append(name)
    quests=[dict(m['quest'],source_tag=m['source_tag']) for m in missions]
    scripts['aw_config']+='\n'+json_function('RWGQuests',quests)
    scripts['rwg_mission']=(ROOT/'scripts/missions/rwg_mission.nss').read_text(encoding='utf-8')
    scripts['aw_story']='#include "rwg_mission"\n'+replace(scripts['aw_story'],'void AWAIAction(object pc,string tag,string verb){','void AWAIAction(object pc,string tag,string verb){RWGRequest(pc,RWFindActor(pc,tag),verb);')
    scripts['rwc_beat']=replace(scripts['rwc_beat'],'object pc=GetFirstPC();','RWGWatch();object pc=GetFirstPC();')
    scripts['rwc_beat']=replace(scripts['rwc_beat'],'AWXTick(pc);','RWGTick(pc);AWXTick(pc);')
    scripts['rwc_load']=replace(scripts['rwc_load'],'AWCInit();','RWGWatch();AWCInit();')
    scripts['rwc_enter']=replace(scripts['rwc_enter'],'SPReset(pc);','RWGWatch();SPReset(pc);')
    scripts['sp_inc']=replace(scripts['sp_inc'],'observed=JsonObjectSet(observed,"actor_name",','observed=JsonObjectSet(observed,"imported_missions",RWGContext(pc));observed=JsonObjectSet(observed,"actor_name",')
    scripts['rwg_death']='''void main(){SetLocalInt(GetModule(),"RWG_DEAD_"+GetTag(OBJECT_SELF),TRUE);string original=GetLocalString(OBJECT_SELF,"RWG_OLD_DEATH");if(original!="" && original!="rwg_death")ExecuteScript(original,OBJECT_SELF);}'''
    scripts['rwg_open']='''void main(){object pc=GetPCSpeaker();object actor=OBJECT_SELF;DelayCommand(0.3,AssignCommand(actor,ActionStartConversation(pc,"rwg_menu",TRUE,FALSE)));}'''
    command='''if(lower=="!missions" || GetStringLeft(lower,10)=="!missions "){
 SetPCChatMessage("");object actor=OBJECT_INVALID;
 if(lower!="!missions"){string who=GetSubString(lower,10,80);string alias=SPAlias(who);actor=alias!=""?RWFindActor(pc,alias):SPActorAddress(pc,who);}
 else {object candidate=GetFirstObjectInArea(GetArea(pc));int found=0;while(GetIsObjectValid(candidate)){if(RWGCanMenu(pc,candidate)){actor=candidate;found++;}candidate=GetNextObjectInArea(GetArea(pc));}if(found!=1)actor=OBJECT_INVALID;}
 if(!RWGCanMenu(pc,actor)){SendMessageToPC(pc,"Stand near the quest giver and use !missions <name or alias>.");return;}
 SPEnd(pc,FALSE);AssignCommand(actor,ActionStartConversation(pc,"rwg_menu",TRUE,FALSE));return;}
 '''
    scripts['sp_chat']=replace(scripts['sp_chat'],'if(s=="!companions"',command+'if(s=="!companions"')
    menu(entries,missions,scripts)
    audit['journals']=sorted(set(audit['journals']));audit['dialogues']=sorted(set(audit['dialogues']))
    audit['note']='Only listed journal/reward call sites are suppressed. Native conditions and other effects remain. Original source/debug files for patched bytecode are backed up, not shipped as misleading editable source. Static isolation does not prove quest compatibility; test the original story conditions and side quests in game.'
    return audit


def menu(entries,missions,scripts):
    if ('rwg_menu',2029) in entries:raise ValueError('Module already uses the Studio mission menu name')
    speeches=[];replies=[];starts=[];conditions=[]
    def condition(code):
        name='rwg_c'+str(len(conditions)).zfill(4);conditions.append(name)
        scripts[name]='#include "rwg_mission"\nint StartingConditional(){'+code+'}'
        return name
    def reply(label,verb='',ready=''):
        name=''
        if verb:
            name='rwg_a'+str(len(replies)).zfill(4)
            scripts[name]='#include "rwg_mission"\nvoid main(){RWGRequest(GetPCSpeaker(),OBJECT_SELF,'+literal(verb)+');}'
        replies.append((label,[],name));return len(replies)-1
    # One overview, with mission topics gated by giver/current talk target. Topics
    # lead to edited descriptions and checked native buttons, independent of AI.
    speeches.append(('Which task would you like to discuss?',[]));starts=[(0,'')]
    for i,m in enumerate(missions):
        q=m['quest'];access='json q=JsonArrayGet(RWGQuests(),'+str(i)+');'
        base=access+'return RWGNear(GetPCSpeaker(),OBJECT_SELF) && GetTag(OBJECT_SELF)==RWGT(q,"giver")'
        states=[(0,q['description']+f"\n\nReward: {q['gold']} gold and {q['xp']} XP.",[reply('I accept this task.',q['id']+':start'),reply('Not now.')])]
        for j,s in enumerate(q['steps']):
            choices=[reply('I have completed the task. May I claim my reward?',q['id']+':claim')] if not s['next'] else [reply('Let us discuss this task.',q['id']+':talk')]
            choices.append(reply('I will continue the task.'));states.append((j+1,s['description'],choices))
        states.append((-1,q['completion'],[reply('Thank you.')]))
        for state,message,choices in states:
            entry=len(speeches);speeches.append((message,choices))
            replies.append((q['name'],[entry]));ri=len(replies)-1;speeches[0][1].append(ri)
            c=condition(base+' && RWGState(q)=='+str(state)+';')
            # Attach after conversation() builds the graph below.
            starts.append((ri,c))
        for j,s in enumerate(q['steps'][:-1]):
            if s['kind']!='talk' or s['target']==q['giver']:continue
            entry=len(speeches);speeches.append((s['description'],[reply('Let us discuss this task.',q['id']+':talk'),reply('Another time.')]))
            replies.append((q['name'],[entry]));ri=len(replies)-1;speeches[0][1].append(ri)
            c=condition(access+'return RWGNear(GetPCSpeaker(),OBJECT_SELF) && GetTag(OBJECT_SELF)=='+literal(s['target'])+' && RWGState(q)=='+str(j+1)+';')
            starts.append((ri,c))
    speeches[0][1].append(reply('Farewell.'))
    dlg=conversation(speeches,replies)
    for ri,c in starts[1:]:
        edge=next(e for e in dlg[1]['EntryList'][1][0][1]['RepliesList'][1] if e[1]['Index'][1]==ri);edge[1]['Active']=(11,c.encode())
    entries['rwg_menu',2029]=write(b'DLG V3.2',dlg)
    scripts['rwg_can']='#include "rwg_mission"\nint StartingConditional(){return RWGCanMenu(GetPCSpeaker(),OBJECT_SELF);}'


def add_dialogue_links(entries,report,p,scripts,audit,changes):
    missions=[m for m in active_all(p) if m['adapter']==ADAPTER]
    if not missions:return
    tags={m['quest']['giver'] for m in missions}|{s['target'] for m in missions for s in m['quest']['steps'] if s['kind']=='talk'}
    names={c['conversation'] for c in report['characters'] if c['tag'] in tags and c.get('conversation')}
    for name in names:
        if (name,2029) not in entries:continue
        kind,dlg=read(entries[name,2029]);before=copy.deepcopy(dlg);replies=dlg[1].setdefault('ReplyList',(15,[]))[1];index=len(replies)
        new=conversation([('',[0])],[('Discuss our tasks.',[],'rwg_open')])[1]['ReplyList'][1][0]
        replies.append((index,new[1]))
        for i,line in enumerate(dlg[1].get('EntryList',(15,[]))[1]):
            links=line[1].setdefault('RepliesList',(15,[]))[1]
            links.append(node(len(links),Index=(4,index),Active=(11,b'rwg_can'),IsChild=(0,1 if i else 0)))
        restored=copy.deepcopy(dlg)
        if 'ReplyList' in before[1]:restored[1]['ReplyList'][1].pop()
        else:restored[1].pop('ReplyList')
        for i,line in enumerate(restored[1].get('EntryList',(15,[]))[1]):
            if 'RepliesList' in before[1]['EntryList'][1][i][1]:line[1]['RepliesList'][1].pop()
            else:line[1].pop('RepliesList')
        if restored!=before:raise ValueError('A task menu link changed existing native dialogue')
        entries[name,2029]=write(kind,dlg);audit['dialogues'].append(name)
    # Record actual conversations, but never let replaying a condition advance a task.
    for info in changes.values():
        for hook in info['action_wrappers']:
            if hook['collection']!='EntryList':continue
            name=hook['wrapper'];scripts[name]='#include "rwg_mission"\n'+scripts[name]
            scripts[name]=replace(scripts[name],'RWRemember(pc,actor,','RWGObserve(pc,actor);RWRemember(pc,actor,')
