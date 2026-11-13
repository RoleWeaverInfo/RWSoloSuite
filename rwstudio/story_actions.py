"""Exact authored story actions shared by the model and native exporter."""

def actions(project, npc, states):
    available=[]
    for q in project['quests']:
        state=states.get(q['id'],0)
        if type(state) is not int:continue
        if state==0:
            if q['start_npc']==npc and all(states.get(dep)==-1 for dep in q['requires']):
                available.append(dict(id='start:'+q['id'],description='Offer and start '+q['name']))
            continue
        if not 0<state<=len(q['steps']):continue
        step=q['steps'][state-1]
        if step['target']!=npc:continue
        if step['kind']=='talk':
            available.append(dict(id=f'talk:{q["id"]}:{state}',description=step['description']))
        elif step['kind']=='choice':
            for i,c in enumerate(step['choices']):
                available.append(dict(id=f'choice:{q["id"]}:{state}:{i}',description=c['label']))
    return available

def native(project, literal):
    lines=['#include "aw_quest"','void AWAIAction(object pc,string npc,string verb){',
           'if(verb=="")return;',
           'if(GetIsDead(pc) || GetIsInCombat(pc))return;',
           'object actor=GetObjectByTag(npc);if(!GetIsObjectValid(actor) || GetIsDead(actor) || GetIsInCombat(actor) || GetIsDMPossessed(actor))return;',
           'if(GetArea(pc)!=GetArea(actor) || GetDistanceBetween(pc,actor)>12.0 || !LineOfSightObject(pc,actor))return;']
    for q in project['quests']:
        qid=literal(q['id'])
        if q['start_npc']:
            lines.append('if(verb=='+literal('start:'+q['id'])+' && npc=='+literal(q['start_npc'])+' && AQState('+qid+')==0 && AQReady(AWFind(AWQuests(),'+qid+'))){AQStart(pc,npc);return;}')
        for i,s in enumerate(q['steps']):
            if s['kind'] not in ('talk','choice'):continue
            choices=s['choices'] if s['kind']=='choice' else [dict(next=s['next'],text='')]
            for ci,c in enumerate(choices):
                ident=f'choice:{q["id"]}:{i+1}:{ci}' if s['kind']=='choice' else f'talk:{q["id"]}:{i+1}'
                lines.append('if(verb=='+literal(ident)+' && npc=='+literal(s['target'])+' && AQState('+qid+')=='+str(i+1)+'){'+
                             ('SendMessageToPC(pc,'+literal(c['text'])+');' if c['text'] else '')+
                             'AQAdvance(pc,'+qid+','+str(i+1)+','+literal(c['next'])+');return;}')
    lines.append('SendMessageToPC(pc,"The story changed while this reply was pending. Continue the conversation to choose your next action.");}')
    return '\n'.join(lines)
