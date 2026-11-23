// Imported missions use observed engine state, never LLM assertions.
#include "aw_config"
string RWGT(json j,string k){return JsonGetString(JsonObjectGet(j,k));}
int RWGI(json j,string k){return JsonGetInt(JsonObjectGet(j,k));}
string RWGKey(json q){return "RWG_"+RWGT(q,"id");}
int RWGState(json q){return GetLocalInt(GetModule(),RWGKey(q));}
json RWGStep(json q){return JsonArrayGet(JsonObjectGet(q,"steps"),RWGState(q)-1);}
int RWGNear(object pc,object actor){return GetIsPC(pc) && GetIsObjectValid(actor) && GetObjectType(actor)==OBJECT_TYPE_CREATURE && !GetIsDead(pc) && !GetIsDead(actor) && GetArea(pc)==GetArea(actor) && GetDistanceBetween(pc,actor)<=12.0 && GetObjectSeen(actor,pc) && LineOfSightObject(pc,actor) && !GetIsInCombat(pc) && !GetIsInCombat(actor) && !GetIsEnemy(actor,pc) && GetObjectByTag(GetTag(actor))==actor && !GetIsObjectValid(GetObjectByTag(GetTag(actor),1));}
void RWGJournal(object pc,json q,int state){AddJournalQuestEntry(RWGT(q,"source_tag"),state==-1?999:state,pc,TRUE,FALSE,TRUE);}
void RWGStart(object pc,object actor,json q){
 if(!RWGNear(pc,actor) || GetTag(actor)!=RWGT(q,"giver") || RWGState(q)!=0)return;
 SetLocalInt(GetModule(),RWGKey(q),1);RWGJournal(pc,q,1);SendMessageToPC(pc,"QUEST: "+RWGT(q,"name"));
}
void RWGAdvance(object pc,json q){
 int state=RWGState(q);json s=RWGStep(q);if(state<=0 || RWGT(s,"next")=="")return;
 SetLocalInt(GetModule(),RWGKey(q)+"_"+RWGT(s,"id"),TRUE);SetLocalInt(GetModule(),RWGKey(q),state+1);RWGJournal(pc,q,state+1);
}
int RWGReady(object pc,json q){
 if(!GetIsPC(pc) || RWGState(q)<=0)return FALSE;
 json s=RWGStep(q);if(RWGT(s,"next")!="" || RWGT(s,"kind")!="talk" || RWGT(s,"target")!=RWGT(q,"giver"))return FALSE;
 json steps=JsonObjectGet(q,"steps");int i=0;
 while(i<JsonGetLength(steps)){json step=JsonArrayGet(steps,i);
  if(RWGT(step,"id")!=RWGT(s,"id") && !GetLocalInt(GetModule(),RWGKey(q)+"_"+RWGT(step,"id")))return FALSE;
  if(RWGI(step,"consume") && !GetIsObjectValid(GetItemPossessedBy(pc,RWGT(step,"target"))))return FALSE;i++;}
 return TRUE;
}
void RWGClaim(object pc,object actor,json q){
 if(!RWGNear(pc,actor) || GetTag(actor)!=RWGT(q,"giver") || !RWGReady(pc,q))return;
 // Commit before effects: repeated dialogue, AI retries and saved games cannot pay twice.
 SetLocalInt(GetModule(),RWGKey(q),-1);
 json steps=JsonObjectGet(q,"steps");int i=0;
 while(i<JsonGetLength(steps)){json s=JsonArrayGet(steps,i);if(RWGI(s,"consume"))DestroyObject(GetItemPossessedBy(pc,RWGT(s,"target")));i++;}
 RWGJournal(pc,q,-1);GiveGoldToCreature(pc,RWGI(q,"gold"));GiveXPToCreature(pc,RWGI(q,"xp"));SendMessageToPC(pc,RWGT(q,"completion"));
}
void RWGObserve(object pc,object actor){
 if(!RWGNear(pc,actor))return;json quests=RWGQuests();int i=0;
 while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);if(RWGState(q)>0){json s=RWGStep(q);if(RWGT(s,"kind")=="talk" && RWGT(s,"next")!="" && RWGT(s,"target")==GetTag(actor))RWGAdvance(pc,q);}i++;}
}
void RWGWatch(){
 json quests=RWGQuests();int i=0;
 while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);json steps=JsonObjectGet(q,"steps");int j=0;
  while(j<JsonGetLength(steps)){json s=JsonArrayGet(steps,j);if(RWGT(s,"kind")=="defeat"){
   object body=GetObjectByTag(RWGT(s,"target"));
   if(GetIsObjectValid(body) && GetObjectType(body)==OBJECT_TYPE_CREATURE && !GetIsPC(body) && !GetIsObjectValid(GetObjectByTag(RWGT(s,"target"),1))){
    if(GetIsDead(body))SetLocalInt(GetModule(),"RWG_DEAD_"+RWGT(s,"target"),TRUE);
    else if(!GetLocalInt(body,"RWG_HOOK")){SetLocalInt(body,"RWG_HOOK",TRUE);SetLocalString(body,"RWG_OLD_DEATH",GetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DEATH));SetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DEATH,"rwg_death");}
   }}j++;}i++;}
}
void RWGTick(object pc){
 if(!GetIsPC(pc) || GetIsDead(pc))return;json quests=RWGQuests();int i=0;
 while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);if(RWGState(q)>0){json s=RWGStep(q);string kind=RWGT(s,"kind");string target=RWGT(s,"target");int done=FALSE;
  if(kind=="defeat")done=GetLocalInt(GetModule(),"RWG_DEAD_"+target);
  if(kind=="retrieve")done=GetIsObjectValid(GetItemPossessedBy(pc,target));
  if(kind=="visit")done=GetTag(GetArea(pc))==target;
  if(done)RWGAdvance(pc,q);}i++;}
}
json RWGContext(object pc){
 json out=JsonObject();json quests=RWGQuests();int i=0;
 while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);json state=JsonObject();state=JsonObjectSet(state,"state",JsonInt(RWGState(q)));state=JsonObjectSet(state,"ready",JsonInt(RWGReady(pc,q)));out=JsonObjectSet(out,RWGT(q,"id"),state);i++;}return out;
}
void RWGRequest(object pc,object actor,string verb){
 json quests=RWGQuests();int i=0;while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);string id=RWGT(q,"id");
  if(verb==id+":start")RWGStart(pc,actor,q);
  if(verb==id+":claim")RWGClaim(pc,actor,q);
  if(verb==id+":talk" && RWGNear(pc,actor) && RWGState(q)>0){json s=RWGStep(q);if(RWGT(s,"kind")=="talk" && RWGT(s,"next")!="" && RWGT(s,"target")==GetTag(actor))RWGAdvance(pc,q);}i++;}
}
int RWGCanMenu(object pc,object actor){
 if(!RWGNear(pc,actor))return FALSE;json quests=RWGQuests();int i=0;
 while(i<JsonGetLength(quests)){json q=JsonArrayGet(quests,i);if(GetTag(actor)==RWGT(q,"giver"))return TRUE;
  if(RWGState(q)>0){json s=RWGStep(q);if(RWGT(s,"kind")=="talk" && GetTag(actor)==RWGT(s,"target"))return TRUE;}i++;}return FALSE;
}
