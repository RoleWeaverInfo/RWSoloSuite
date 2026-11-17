#include "aw_config"
string AWText(json j,string key) {return JsonGetString(JsonObjectGet(j,key));}
int AWInt(json j,string key) {return JsonGetInt(JsonObjectGet(j,key));}
int AQState(string id) {return GetLocalInt(GetModule(),"AQ_"+id);}
int AQDone(string id) {return id=="" || AQState(id)==-1;}
json AWFind(json list,string id) {int i=0;while(i<JsonGetLength(list)){json j=JsonArrayGet(list,i);if(AWText(j,"id")==id)return j;i++;}return JsonNull();}
json AQStates() {json j=JsonObject();json qs=AWQuests();int i=0;while(i<JsonGetLength(qs)){string id=AWText(JsonArrayGet(qs,i),"id");j=JsonObjectSet(j,id,JsonInt(AQState(id)));i++;}return j;}
int AQProgress(){json qs=AWQuests();int i=0;int n=0;while(i<JsonGetLength(qs)){if(AQState(AWText(JsonArrayGet(qs,i),"id"))==-1)n++;i++;}return n;}
int AQReady(json q){json deps=JsonObjectGet(q,"requires");int i=0;while(i<JsonGetLength(deps)){if(!AQDone(JsonGetString(JsonArrayGet(deps,i))))return FALSE;i++;}return TRUE;}
object AWItem(object pc,string tag) {
    object item=GetItemPossessedBy(pc,tag);if(GetIsObjectValid(item))return item;
    object m=GetFirstFactionMember(pc,FALSE);while(GetIsObjectValid(m)){item=GetItemPossessedBy(m,tag);if(GetIsObjectValid(item))return item;m=GetNextFactionMember(pc,FALSE);}return OBJECT_INVALID;
}
int AWInRoom(object pc,string id) {
    json r=AWFind(AWRooms(),id);if(AWText(r,"area")!=GetTag(GetArea(pc)))return FALSE;
    vector v=GetPosition(pc);return v.x>=IntToFloat(AWInt(r,"x")*10) && v.x<=(IntToFloat(AWInt(r,"x")*10)+JsonGetFloat(JsonObjectGet(r,"width_m"))) && v.y>=IntToFloat(AWInt(r,"y")*10) && v.y<=(IntToFloat(AWInt(r,"y")*10)+JsonGetFloat(JsonObjectGet(r,"depth_m")));
}
void AQJournal(object pc,json q,int state){AddJournalQuestEntry(AWText(q,"id"),state==-1?999:state,pc,TRUE,FALSE,TRUE);}
void AQStart(object pc,string speaker="") {
    json qs=AWQuests();int i=0;
    while(i<JsonGetLength(qs)){json q=JsonArrayGet(qs,i);string id=AWText(q,"id");string starter=AWText(q,"start_npc");
        if(AQState(id)==0 && AQReady(q) && (starter=="" || starter==speaker)) {SetLocalInt(GetModule(),"AQ_"+id,1);AQJournal(pc,q,1);SendMessageToPC(pc,"QUEST: "+AWText(q,"name"));}
        i++;}
}
void AQEndCheck(object pc) {
    if(GetLocalInt(GetModule(),"AW_FINISHED"))return;
    json qs=AWQuests();int i=0;while(i<JsonGetLength(qs)){json q=JsonArrayGet(qs,i);if(!AWInt(q,"optional") && AQState(AWText(q,"id"))!=-1)return;i++;}
    SetLocalInt(GetModule(),"AW_FINISHED",TRUE);SendMessageToPC(pc,"ADVENTURE COMPLETE: "+AWEnding());
}
void AQAdvance(object pc,string questID,int expected,string nextID) {
    if(AQState(questID)!=expected)return;
    json q=AWFind(AWQuests(),questID);json steps=JsonObjectGet(q,"steps");int nextState=-1;int i=0;
    if(nextID!=""){while(i<JsonGetLength(steps)){if(AWText(JsonArrayGet(steps,i),"id")==nextID)nextState=i+1;i++;}if(nextState==-1)return;}
    // Commit save-local progress before rewards so repeated calls cannot pay twice.
    SetLocalInt(GetModule(),"AQ_"+questID,nextState);AQJournal(pc,q,nextState);
    if(nextState==-1){GiveGoldToCreature(pc,AWInt(q,"gold"));GiveXPToCreature(pc,AWInt(q,"xp"));SendMessageToPC(pc,AWText(q,"completion")+" Reward: "+IntToString(AWInt(q,"gold"))+" gold, "+IntToString(AWInt(q,"xp"))+" XP.");}
    else SendMessageToPC(pc,"OBJECTIVE: "+AWText(JsonArrayGet(steps,nextState-1),"description"));
    AQStart(pc);AQEndCheck(pc);
}
void AQTalk(object pc,string npc) {
    AQStart(pc,npc);json qs=AWQuests();int i=0;
    while(i<JsonGetLength(qs)){json q=JsonArrayGet(qs,i);string id=AWText(q,"id");int state=AQState(id);
        if(state>0){json s=JsonArrayGet(JsonObjectGet(q,"steps"),state-1);if(AWText(s,"kind")=="talk" && AWText(s,"target")==npc)AQAdvance(pc,id,state,AWText(s,"next"));}i++;}
}
void AQTick(object pc) {
    json gates=AWEncounters();int gi=0;
    while(gi<JsonGetLength(gates)){json gate=JsonArrayGet(gates,gi);if(AWText(gate,"kind")=="treasure" && AWText(gate,"after_quest")!=""){object chest=GetObjectByTag(AWText(gate,"id"));if(GetIsObjectValid(chest))SetLocked(chest,!AQDone(AWText(gate,"after_quest")));}gi++;}
    AQStart(pc);json qs=AWQuests();int i=0;
    while(i<JsonGetLength(qs)){json q=JsonArrayGet(qs,i);string id=AWText(q,"id");int state=AQState(id);
        if(state>0){json s=JsonArrayGet(JsonObjectGet(q,"steps"),state-1);string kind=AWText(s,"kind");string target=AWText(s,"target");int done=FALSE;
            if(kind=="visit")done=AWInRoom(pc,target);
            if(kind=="retrieve") {object item=AWItem(pc,target);done=GetIsObjectValid(item);if(done && AWInt(s,"consume"))DestroyObject(item);}
            if(kind=="defeat") {int expected=GetLocalInt(GetModule(),"AW_EXPECT_"+target);done=expected>0 && GetLocalInt(GetModule(),"AW_KILL_"+target)>=expected;}
            if(kind=="interact")done=GetLocalInt(GetModule(),"AW_USED_"+target);
            if(done)AQAdvance(pc,id,state,AWText(s,"next"));}
        i++;}
}
int AWCount(object pc,json e) {
    int n=AWInt(e,"count");if(!AWInt(e,"scale"))return n;
    int members=0;int levels=0;object m=GetFirstFactionMember(pc,FALSE);
    while(GetIsObjectValid(m)){if(GetArea(m)==GetArea(pc) && !GetIsDead(m)){members++;levels+=GetHitDice(m);}m=GetNextFactionMember(pc,FALSE);}
    if(members>0){n+=(members-1)/2;int avg=levels/members;if(avg>AWLevelMax())n++;}
    if(n>AWInt(e,"maximum"))n=AWInt(e,"maximum");return n;
}
void AWSpawn(object pc,json e,int extraOnly=FALSE) {
    string id=AWText(e,"id");if(GetLocalInt(GetModule(),"AW_SPAWN_"+id))return;
    object marker=GetObjectByTag("aw_m_"+IntToString(AWInt(e,"index")));if(!GetIsObjectValid(marker))return;
    int desired=AWCount(pc,e);int count=desired;int made=0;if(extraOnly){count-=AWInt(e,"count");made=AWInt(e,"count");}
    SetLocalInt(GetModule(),"AW_SPAWN_"+id,TRUE);int i=0;
    while(i<count){object enemy=CreateObject(OBJECT_TYPE_CREATURE,id,GetLocation(marker));if(GetIsObjectValid(enemy)){SetLocalString(enemy,"AW_ENC",id);made++;}i++;}
    SetLocalInt(GetModule(),"AW_EXPECT_"+id,made);
}
void AWArea(object pc) {
    json es=AWEncounters();int i=0;
    while(i<JsonGetLength(es)){json e=JsonArrayGet(es,i);if(AWText(e,"area")==GetTag(GetArea(pc)) && AWText(e,"kind")=="combat")AWSpawn(pc,e,TRUE);i++;}
}
void AWAmbushes(object pc) {
    json es=AWEncounters();int i=0;while(i<JsonGetLength(es)){json e=JsonArrayGet(es,i);if(AWText(e,"kind")=="ambush" && AQDone(AWText(e,"after_quest")) && AWInRoom(pc,AWText(e,"room")))AWSpawn(pc,e);i++;}
}
int AWStoryReady(string id) {
    // Quest outcome objects are usable only on the currently selected path.
    int bound=FALSE;json qs=AWQuests();int i=0;
    while(i<JsonGetLength(qs)){json q=JsonArrayGet(qs,i);json steps=JsonObjectGet(q,"steps");int j=0;
        while(j<JsonGetLength(steps)){json s=JsonArrayGet(steps,j);if(AWText(s,"kind")=="interact" && AWText(s,"target")==id){bound=TRUE;if(AQState(AWText(q,"id"))==j+1)return TRUE;}j++;}i++;}
    return !bound;
}
void AWResolve(object pc,string id) {
    json e=AWFind(AWEncounters(),id);if(AWText(e,"id")=="" || !AQDone(AWText(e,"after_quest")))return;
    if(AWText(e,"kind")=="story" && !AWStoryReady(id))return;
    if(GetLocalInt(GetModule(),"AW_USED_"+id))return;
    SetLocalInt(GetModule(),"AW_USED_"+id,TRUE);GiveGoldToCreature(pc,AWInt(e,"gold"));GiveXPToCreature(pc,AWInt(e,"xp"));
    SendMessageToPC(pc,AWText(e,"success"));AQTick(pc);
}
