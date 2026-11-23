"""Audited takeover patching; every native difference has an explicit allowlist."""
import copy
import hashlib
from .builder import ROOT, literal, string
from .adventure_builder import json_function
from .nwn.gff import read, write, text
from .nwn.area_tools import node
from .conversion_runtime import replace
from .managed_missions import active, validate, SCRIPT_HASHES, dialogue_text, update_memory


def apply(entries, report, p, scripts):
    m=active(p)
    if not m:return dict(scripts=[],dialogues=[],journals=[],adapter='')
    validate(p['mission_control'],report)
    for name,digest in SCRIPT_HASHES.items():
        if hashlib.sha256(entries.get((name,2010),b'')).hexdigest()!=digest:
            raise ValueError('The audited native script changed: '+name)
    q=m['quest']; r=m['rewards'];update_memory(p)
    scripts['aw_config']+='\n'+json_function('RWMQuests',[q])+'\n'+json_function('RWMRewards',[r])
    scripts['rwm_quest']=(ROOT/'scripts/missions/rwm_quest.nss').read_text(encoding='utf-8')
    scripts['aw_story']='#include "aw_ambient"\n#include "rwm_quest"\nvoid AWAIAction(object pc,string tag,string verb){RWMRequest(pc,RWFindActor(pc,tag),verb);}'
    scripts['rwc_beat']=replace(scripts['rwc_beat'],'AWXTick(pc);','RWMTick(pc);AWXTick(pc);')
    scripts['sp_inc']=replace(scripts['sp_inc'],'observed=JsonObjectSet(observed,"actor_name",', 'observed=JsonObjectSet(observed,"managed_mission",RWMContext(pc));observed=JsonObjectSet(observed,"actor_name",')
    scripts['rwm_start']='#include "rwm_quest"\nvoid main(){RWMStart(GetPCSpeaker(),OBJECT_SELF);}'
    scripts['rwm_ready']='#include "rwm_quest"\nint StartingConditional(){return RWMReady(GetPCSpeaker());}'
    scripts['rwm_bonus']='#include "rwm_quest"\nint StartingConditional(){return RWMBonusReady();}'
    scripts['sca_oberagh001']='#include "rwm_quest"\nvoid main(){RWMClaim(GetPCSpeaker(),OBJECT_SELF);}'
    scripts['sca_oberagh002']='#include "rwm_quest"\nvoid main(){RWMBonus(GetPCSpeaker(),OBJECT_SELF);}'
    scripts['sk_dthobzul001']='''#include "x2_inc_compon"
#include "rwm_quest"
void main(){
 object killer=GetLastKiller();
 if(GetAssociateType(killer)!=ASSOCIATE_TYPE_NONE)killer=GetMaster(killer);
 if(GetObjectType(killer)==OBJECT_TYPE_TRIGGER && GetIsObjectValid(GetTrapCreator(killer)))killer=GetTrapCreator(killer);
 RWMDeath(killer);
 SpeakString("NW_I_AM_DEAD",TALKVOLUME_SILENT_TALK);
 SpeakString("NW_ATTACK_MY_TARGET",TALKVOLUME_SILENT_TALK);
 craft_drop_items(killer);
}'''
    # Native area placements, creature blueprints and their event assignments stay
    # identical. Only these audited script resources are replaced, not wrapped.
    kind,dlg=read(entries['cl_oberagh001',2029]);before=copy.deepcopy(dlg);edits=[]
    def change(collection,index,field,value):
        fields=dlg[1][collection][1][index][1];edits.append((collection,index,field,fields.get(field)))
        fields[field]=value
    for collection,index in [('EntryList',3),('ReplyList',15)]:
        fields=dlg[1][collection][1][index][1]
        if fields.get('Quest')!=(10,b'j_ogre'):raise ValueError('Original Ogre Mages dialogue binding changed')
        change(collection,index,'Quest',(10,b''));change(collection,index,'QuestEntry',(4,0))
    change('EntryList',3,'Script',(11,b'rwm_start'))
    for (collection,index),value in dialogue_text(m).items():change(collection,index,'Text',(12,text(value)))
    # Readiness replaces the native head-only condition; negotiation stays behind
    # its original Persuade roll, with a separate exactly-once eligibility check.
    links=dlg[1]['EntryList'][1][9][1]['RepliesList'][1]
    old_ready=copy.deepcopy(links)
    hit=[link for link in links if link[1]['Index'][1]==15]
    if len(hit)!=1 or hit[0][1]['Active']!=(11,b'scc_item001'):raise ValueError('Original hand-in condition changed')
    hit[0][1]['Active']=(11,b'rwm_ready')
    reward_links=dlg[1]['EntryList'][1][10][1]['RepliesList'][1];old_reward=copy.deepcopy(reward_links)
    bonus=[link for link in reward_links if link[1]['Index'][1]==21]
    if len(bonus)!=1 or bonus[0][1]['Active']!=(11,b''):raise ValueError('Original negotiation link changed')
    bonus[0][1]['Active']=(11,b'rwm_bonus')
    # AI hand-in does not traverse the native reward speech. Keep its Persuade
    # branch reachable on a later visit, using the same roll and payment guard.
    after_links=dlg[1]['EntryList'][1][16][1]['RepliesList'][1];old_after=copy.deepcopy(after_links)
    if after_links:raise ValueError('Original post-completion dialogue changed')
    after_links.append(copy.deepcopy(bonus[0]))
    restored=copy.deepcopy(dlg)
    for collection,index,field,old in edits:
        if old is None:restored[1][collection][1][index][1].pop(field,None)
        else:restored[1][collection][1][index][1][field]=old
    restored[1]['EntryList'][1][9][1]['RepliesList']=(15,old_ready)
    restored[1]['EntryList'][1][10][1]['RepliesList']=(15,old_reward)
    restored[1]['EntryList'][1][16][1]['RepliesList']=(15,old_after)
    if restored!=before:raise ValueError('Unrelated dialogue was changed during mission takeover')
    entries['cl_oberagh001',2029]=write(kind,dlg)
    # Replace this category alone. Native scripts no longer write its old states.
    kind,jrl=read(entries['module',2056]);before=copy.deepcopy(jrl)
    matches=[c for c in jrl[1]['Categories'][1] if c[1].get('Tag')==(10,b'j_ogre')]
    if len(matches)!=1:raise ValueError('Ambiguous native Ogre Mages journal')
    category=matches[0];original_category=copy.deepcopy(category)
    category[1]['Name']=(12,text(q['name']));category[1]['XP']=(8,float(q['xp']))
    category[1]['EntryList']=(15,[node(i,ID=(4,i+1),Text=(12,text(s['description'])),End=(0,0)) for i,s in enumerate(q['steps'])]+[node(999,ID=(4,999),Text=(12,text(q['completion'])),End=(0,1))])
    restored=copy.deepcopy(jrl);index=jrl[1]['Categories'][1].index(category);restored[1]['Categories'][1][index]=original_category
    if restored!=before:raise ValueError('An unrelated quest journal changed')
    entries['module',2056]=write(kind,jrl)
    return dict(adapter=m['adapter'],scripts=list(SCRIPT_HASHES),dialogues=['cl_oberagh001'],journals=['module'],
        source_tag=m['source_tag'],mode='studio',original_script_hashes=SCRIPT_HASHES,unmanaged_quests_unchanged=True,
        note='Replaced only audited quest actions. Maps/placements, original death loot handling, other quest categories and unrelated dialogue branches retained.')


def add_observers(scripts, changes):
    if 'rwm_quest' not in scripts:return
    for info in changes.values():
        for hook in info['action_wrappers']:
            if hook['collection']!='EntryList':continue
            name=hook['wrapper'];scripts[name]='#include "rwm_quest"\n'+scripts[name]
            scripts[name]=replace(scripts[name],'RWRemember(pc,actor,','RWMObserve(pc,actor);RWRemember(pc,actor,')
