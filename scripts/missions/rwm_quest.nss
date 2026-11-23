// Conversion-only mission template. State is save-local; the service cannot assert success.
#include "aw_config"
int RWMState(){return GetLocalInt(GetModule(),"RWM_STATE");}
json RWMQ(){return JsonArrayGet(RWMQuests(),0);}
json RWMStep(){return JsonArrayGet(JsonObjectGet(RWMQ(),"steps"),RWMState()-1);}
string RWMT(json j,string k){return JsonGetString(JsonObjectGet(j,k));}
int RWMI(json j,string k){return JsonGetInt(JsonObjectGet(j,k));}
int RWMNear(object pc,object actor){return GetIsPC(pc) && GetIsObjectValid(actor) && GetObjectType(actor)==OBJECT_TYPE_CREATURE && !GetIsDead(pc) && !GetIsDead(actor) && GetArea(pc)==GetArea(actor) && GetDistanceBetween(pc,actor)<=12.0 && GetObjectSeen(actor,pc) && !GetIsInCombat(pc) && !GetIsInCombat(actor) && !GetIsEnemy(actor,pc);}
void RWMJournal(object pc,int state){AddJournalQuestEntry("j_ogre",state==-1?999:state,pc,TRUE,FALSE,TRUE);}
void RWMStart(object pc,object actor){
 if(!RWMNear(pc,actor) || GetTag(actor)!="oberagh001" || RWMState()!=0)return;
 SetLocalInt(GetModule(),"RWM_STATE",1);SetLocalInt(actor,"PCTALK",1);RWMJournal(pc,1);
 SendMessageToPC(pc,"QUEST: "+RWMT(RWMQ(),"name"));
}
void RWMAdvance(object pc){
 if(RWMState()<=0)return;json s=RWMStep();string next=RWMT(s,"next");if(next=="")return;
 json steps=JsonObjectGet(RWMQ(),"steps");int i=0;
 while(i<JsonGetLength(steps)){if(RWMT(JsonArrayGet(steps,i),"id")==next){SetLocalInt(GetModule(),"RWM_DONE_"+RWMT(s,"id"),TRUE);SetLocalInt(GetModule(),"RWM_STATE",i+1);RWMJournal(pc,i+1);return;}i++;}
}
void RWMTick(object pc){
 if(!GetIsPC(pc) || GetIsDead(pc) || RWMState()<=0)return;
 json s=RWMStep();string kind=RWMT(s,"kind");string target=RWMT(s,"target");int done=FALSE;
 if(kind=="defeat")done=GetLocalInt(GetModule(),"RWM_DEAD_"+target);
 if(kind=="retrieve")done=GetIsObjectValid(GetItemPossessedBy(pc,target));
 if(kind=="visit")done=GetTag(GetArea(pc))==target;
 if(done)RWMAdvance(pc);
}
void RWMObserve(object pc,object actor){
 if(RWMState()<=0 || !RWMNear(pc,actor))return;
 json s=RWMStep();if(RWMT(s,"kind")=="talk" && RWMT(s,"next")!="" && RWMT(s,"target")==GetTag(actor))RWMAdvance(pc);
}
int RWMReady(object pc){
 if(!GetIsPC(pc) || RWMState()<=0)return FALSE;
 json s=RWMStep();if(RWMT(s,"next")!="" || RWMT(s,"kind")!="talk" || RWMT(s,"target")!="oberagh001")return FALSE;
 json steps=JsonObjectGet(RWMQ(),"steps");int i=0;
 while(i<JsonGetLength(steps)){json step=JsonArrayGet(steps,i);
  if(RWMT(step,"id")!=RWMT(s,"id") && !GetLocalInt(GetModule(),"RWM_DONE_"+RWMT(step,"id")))return FALSE;
  if(RWMI(step,"consume") && !GetIsObjectValid(GetItemPossessedBy(pc,RWMT(step,"target"))))return FALSE;i++;}
 return TRUE;
}
void RWMClaim(object pc,object actor){
 if(!RWMNear(pc,actor) || GetTag(actor)!="oberagh001" || !RWMReady(pc) || GetLocalInt(GetModule(),"RWM_PAID"))return;
 json q=RWMQ();json r=JsonArrayGet(RWMRewards(),0);object marker=GetObjectByTag("wp_rwrdchest001");
 if(RWMI(r,"treasure_chest") && !GetIsObjectValid(marker)){SendMessageToPC(pc,"The promised chest cannot be delivered here yet.");return;}
 int previous=RWMState();SetLocalInt(GetModule(),"RWM_STATE",-1);SetLocalInt(GetModule(),"RWM_PAID",TRUE);
 if(RWMI(r,"treasure_chest")){object chest=CreateObject(OBJECT_TYPE_PLACEABLE,"rwrdchest001",GetLocation(marker));
  if(!GetIsObjectValid(chest)){SetLocalInt(GetModule(),"RWM_STATE",previous);DeleteLocalInt(GetModule(),"RWM_PAID");SendMessageToPC(pc,"I could not conjure your reward chest. Please speak with me again.");return;}
  ApplyEffectAtLocation(DURATION_TYPE_INSTANT,EffectVisualEffect(VFX_FNF_SUMMON_MONSTER_1),GetLocation(marker));}
 json steps=JsonObjectGet(q,"steps");int i=0;while(i<JsonGetLength(steps)){json s=JsonArrayGet(steps,i);if(RWMI(s,"consume"))DestroyObject(GetItemPossessedBy(pc,RWMT(s,"target")));i++;}
 SetLocalInt(actor,"PCTALK",2);RWMJournal(pc,-1);
 GiveGoldToCreature(pc,RWMI(q,"gold"));GiveXPToCreature(pc,RWMI(q,"xp"));SendMessageToPC(pc,RWMT(q,"completion"));
}
int RWMBonusReady(){return RWMState()==-1 && RWMI(JsonArrayGet(RWMRewards(),0),"negotiation") && !GetLocalInt(GetModule(),"RWM_BONUS");}
void RWMBonus(object pc,object actor){
 if(!RWMNear(pc,actor) || GetTag(actor)!="oberagh001" || !RWMBonusReady())return;
 SetLocalInt(GetModule(),"RWM_BONUS",TRUE);json r=JsonArrayGet(RWMRewards(),0);GiveGoldToCreature(pc,RWMI(r,"bonus_gold"));GiveXPToCreature(pc,RWMI(r,"bonus_xp"));
}
void RWMDeath(object killer){
 if(GetLocalInt(GetModule(),"RWM_DEAD_obzul001"))return;
 SetLocalInt(GetModule(),"RWM_DEAD_obzul001",TRUE);
 if(GetIsPC(killer)){GiveXPToCreature(killer,RWMI(JsonArrayGet(RWMRewards(),0),"defeat_xp"));RWMTick(killer);}
}
json RWMContext(object pc){json j=JsonObject();j=JsonObjectSet(j,"state",JsonInt(RWMState()));return JsonObjectSet(j,"ready",JsonInt(RWMReady(pc)));}
void RWMRequest(object pc,object actor,string verb){
 if(verb=="rwm_start")RWMStart(pc,actor);
 if(verb=="rwm_talk")RWMObserve(pc,actor);
 if(verb=="rwm_claim")RWMClaim(pc,actor);
}
