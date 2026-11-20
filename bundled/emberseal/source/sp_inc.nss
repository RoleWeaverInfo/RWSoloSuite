// Role Weaver Solo: native save state + a bounded, local campaign mailbox.
#include "aw_story"
#include "sp_config"
string SPDB = "rwsp_bridge";
string SPSession() { return GetLocalString(GetModule(), "SP_SESSION"); }
string SPText(json j, string k) { return JsonGetString(JsonObjectGet(j,k)); }
int SPInt(json j, string k) { return JsonGetInt(JsonObjectGet(j,k)); }
int SPNow()
{
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"SELECT CAST(strftime('%s','now') AS INTEGER)");
    if (SqlStep(q)) return SqlGetInt(q,0);
    return 0;
}
void SPInit()
{
    sqlquery a=SqlPrepareQueryCampaign(SPDB,"CREATE TABLE IF NOT EXISTS sp_sessions (session_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, build_id TEXT NOT NULL, snapshot TEXT NOT NULL, updated INTEGER NOT NULL)"); SqlStep(a);
    sqlquery b=SqlPrepareQueryCampaign(SPDB,"CREATE TABLE IF NOT EXISTS sp_requests (request_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, kind TEXT NOT NULL, npc_tag TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', response TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL)"); SqlStep(b);
    sqlquery c=SqlPrepareQueryCampaign(SPDB,"CREATE TABLE IF NOT EXISTS sp_commands (command_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued', receipt TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, updated INTEGER NOT NULL)"); SqlStep(c);
    sqlquery presence=SqlPrepareQueryCampaign(SPDB,"CREATE TABLE IF NOT EXISTS sp_service (session_id TEXT PRIMARY KEY, build_id TEXT NOT NULL, status TEXT NOT NULL, updated INTEGER NOT NULL)");SqlStep(presence);
    SetLocalString(GetModule(),"SP_SESSION",GetRandomUUID());
    // All previous game instances are stale, even if a saved request was restored.
    sqlquery d=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_sessions SET updated=0"); SqlStep(d);
    sqlquery e=SqlPrepareQueryCampaign(SPDB,"DELETE FROM sp_requests WHERE created<CAST(strftime('%s','now') AS INTEGER)-86400"); SqlStep(e);
    sqlquery f=SqlPrepareQueryCampaign(SPDB,"DELETE FROM sp_commands WHERE created<CAST(strftime('%s','now') AS INTEGER)-86400"); SqlStep(f);
    sqlquery g=SqlPrepareQueryCampaign(SPDB,"DELETE FROM sp_sessions WHERE updated=0"); SqlStep(g);
    sqlquery stale=SqlPrepareQueryCampaign(SPDB,"DELETE FROM sp_service");SqlStep(stale);
}
json SPSnapshot(object pc)
{
    json j=JsonObject(); json party=JsonArray();
    j=JsonObjectSet(j,"player_uuid",JsonString(GetObjectUUID(pc)));
    j=JsonObjectSet(j,"player_name",JsonString(GetName(pc)));
    j=JsonObjectSet(j,"area",JsonString(GetTag(GetArea(pc))));
    j=JsonObjectSet(j,"quest_stage",JsonInt(AQProgress())); j=JsonObjectSet(j,"quests",AQStates());
    j=JsonObjectSet(j,"has_satchel",JsonBool(FALSE)); j=JsonObjectSet(j,"merchant",AWMContext(pc,GetLocalObject(pc,"SP_FOCUS"))); j=JsonObjectSet(j,"actor_uuid",JsonString(GetObjectUUID(GetLocalObject(pc,"SP_FOCUS"))));j=JsonObjectSet(j,"companion",AWCContext(pc,GetLocalObject(pc,"SP_FOCUS")));
    object m=GetFirstFactionMember(pc,FALSE); int count=0;
    while (GetIsObjectValid(m) && count<12)
    {
        json member=JsonObject(); json classes=JsonArray(); int k=1;
        member=JsonObjectSet(member,"name",JsonString(GetName(m)));
        member=JsonObjectSet(member,"level",JsonInt(GetHitDice(m)));
        member=JsonObjectSet(member,"hp",JsonInt(GetCurrentHitPoints(m)));
        member=JsonObjectSet(member,"max_hp",JsonInt(GetMaxHitPoints(m)));
        member=JsonObjectSet(member,"ac",JsonInt(GetAC(m)));
        member=JsonObjectSet(member,"in_combat",JsonBool(GetIsInCombat(m)));
        member=JsonObjectSet(member,"area",JsonString(GetTag(GetArea(m))));
        while(k<=3) { int cls=GetClassByPosition(k,m); json cl=JsonObject();
            cl=JsonObjectSet(cl,"class_id",JsonInt(cls)); cl=JsonObjectSet(cl,"levels",JsonInt(GetLevelByClass(cls,m)));
            classes=JsonArrayInsert(classes,cl); k++; }
        member=JsonObjectSet(member,"classes",classes); party=JsonArrayInsert(party,member);
        m=GetNextFactionMember(pc,FALSE); count++;
    }
    json used=JsonArray(); json es=SPEncounters(); int i=0;
    while(i<JsonGetLength(es)) { string id=SPText(JsonArrayGet(es,i),"id");
        if(GetLocalInt(GetModule(),"SP_USED_"+id)) used=JsonArrayInsert(used,JsonString(id)); i++; }
    j=JsonObjectSet(j,"party",party); j=JsonObjectSet(j,"used_encounters",used);
    return j;
}
void SPPublish(object pc)
{
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"INSERT OR REPLACE INTO sp_sessions(session_id,project_id,build_id,snapshot,updated) VALUES(@s,@p,@b,@j,CAST(strftime('%s','now') AS INTEGER))");
    SqlBindString(q,"@s",SPSession());SqlBindString(q,"@p",SPProject());SqlBindString(q,"@b",SPBuild());
    SqlBindString(q,"@j",JsonDump(SPSnapshot(pc)));SqlStep(q);
}
int SPNear(object pc,object npc)
{
    return GetIsObjectValid(npc) && !GetIsDead(pc) && !GetIsDead(npc) && GetArea(pc)==GetArea(npc) && GetDistanceBetween(pc,npc)<=12.0 && LineOfSightObject(pc,npc);
}
void SPReset(object pc)
{
    if(GetLocalString(pc,"SP_SESSION")!=SPSession()) {
        SetLocalString(pc,"SP_SESSION",SPSession()); DeleteLocalString(pc,"SP_PENDING"); }
}
// Presence uses SQLite wall time, not accelerated in-world time. Never gate
// native quests/inventory or API requests on this optional, versioned check.
void SPServiceBegin(object pc)
{
    SetLocalString(pc,"SP_SERVICE_SESSION",SPSession());
    SetLocalInt(pc,"SP_SERVICE_START",SPNow());
    SetLocalString(pc,"SP_SERVICE_STATE","checking");
    SendMessageToPC(pc,"Role Weaver: checking the connection to Module Studio. Keep the Role Weaver service running for live AI.");
}
string SPServiceState(object pc)
{
    int now=SPNow();if(now<=0)return "unavailable";
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"SELECT status FROM sp_service WHERE session_id=@s AND build_id=@b AND updated>=@start AND updated>=CAST(strftime('%s','now') AS INTEGER)-30 AND updated<=CAST(strftime('%s','now') AS INTEGER)");
    SqlBindString(q,"@s",SPSession());SqlBindString(q,"@b",SPBuild());SqlBindInt(q,"@start",GetLocalInt(pc,"SP_SERVICE_START"));
    if(SqlStep(q)){string status=SqlGetString(q,0);if(status=="connected" || status=="paused")return status;}
    if(now-GetLocalInt(pc,"SP_SERVICE_START")<12)return "checking";
    return "unavailable";
}
void SPServiceCheck(object pc,int force=FALSE)
{
    if(!GetIsPC(pc))return;
    if(GetLocalString(pc,"SP_SERVICE_SESSION")!=SPSession() || !GetLocalInt(pc,"SP_SERVICE_START"))SPServiceBegin(pc);
    string state=SPServiceState(pc);string previous=GetLocalString(pc,"SP_SERVICE_STATE");
    if(!force && state==previous)return;
    SetLocalString(pc,"SP_SERVICE_STATE",state);
    if(state=="checking"){if(force)SendMessageToPC(pc,"Role Weaver: checking Module Studio. Keep NWN unpaused and try !studio again in a few seconds.");return;}
    if(state=="connected"){
        SendMessageToPC(pc,previous=="unavailable" || previous=="paused"?"Role Weaver: the Module Studio connection is restored.":"Role Weaver: Module Studio is connected. Keep its service running; you may close the browser. AI still needs your configured key and this adventure's profile.");return;}
    if(state=="paused"){SendMessageToPC(pc,"Role Weaver: Module Studio is running, but the AI service is paused. Open its AI service page and choose Enable AI service.");return;}
    SendMessageToPC(pc,"ROLE WEAVER SERVICE NOT CONNECTED: Start Role Weaver Module Studio, enable its AI service, then return to NWN. If it is already running, check its version and NWN user folder. AI conversations and AI-directed companion actions need the service; normal menus, inventory and authored quests remain available. Type !studio to check again.");
}
void SPEnd(object pc,int notify=TRUE){
 string id=GetLocalString(pc,"SP_PENDING");if(id!=""){sqlquery cancel=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_requests SET state='expired' WHERE request_id=@i AND session_id=@s AND state IN ('queued','working')");SqlBindString(cancel,"@i",id);SqlBindString(cancel,"@s",SPSession());SqlStep(cancel);}
 DeleteLocalString(pc,"SP_PENDING");DeleteLocalObject(pc,"SP_PENDING_ACTOR");DeleteLocalObject(pc,"SP_FOCUS");DeleteLocalInt(pc,"SP_FOCUS_AT");DeleteLocalInt(pc,"AWC_CHAT_ARMED");DeleteLocalString(pc,"AWT_PENDING_OPTIONS");if(notify)SendMessageToPC(pc,"AI conversation ended. NPC menus remain available.");}
void SPAsk(object pc,string kind,string message)
{
    SPReset(pc);
    if(kind=="npc" && AWTParse(pc,GetLocalObject(pc,"SP_FOCUS"),message)){SPEnd(pc,FALSE);return;}
    SetLocalObject(GetModule(),"SP_CONTROLLER",pc);
    if(GetStringLength(message)<1) { SendMessageToPC(pc,"Type !ai <message>, !talk <alias> <message>, or !dm <request>."); return; }
    string pending=GetLocalString(pc,"SP_PENDING");
    if(pending!="" && SPNow()-GetLocalInt(pc,"SP_SENT")<100) { SendMessageToPC(pc,"An AI reply is still pending. You can keep playing."); return; }
    object npc=GetLocalObject(pc,"SP_FOCUS"); string tag="";
    if(kind=="npc") {
        tag=GetTag(npc);if(AWCOwner(npc)==pc && (AWCKind(npc)=="familiar" || AWCKind(npc)=="summon")){kind="companion";tag=AWText(AWCPolicy(npc),"id");}
        if((kind=="npc" && !SPIsNPC(tag)) || !SPNear(pc,npc) || !AWCAIReady(pc,npc) || (kind=="companion" && !AWCReady(pc,npc))) { SendMessageToPC(pc,"Stand near a key NPC and choose Talk freely with AI, or use !talk <alias> <message>."); return; }
    }
    if(kind=="npc" || kind=="companion"){AWATouch(npc);}if(kind=="npc" || kind=="companion")SetLocalInt(pc,"SP_FOCUS_AT",SPNow());
    SetLocalString(pc,"AWM_REQUEST",AWMVersion(pc,npc));SetLocalString(pc,"AWC_PENDING_VERSION",AWCEnabled() && AWText(AWCPolicy(npc),"id")!=""?AWCVersion(pc,npc):"");SetLocalObject(pc,"SP_PENDING_ACTOR",npc);
    json p=JsonObject(); p=JsonObjectSet(p,"message",JsonString(GetStringLeft(message,1200)));
    json taskOptions=AWTCandidates(pc,npc);SetLocalString(pc,"AWT_PENDING_OPTIONS",JsonDump(taskOptions));json observed=SPSnapshot(pc);observed=JsonObjectSet(observed,"task_targets",taskOptions);p=JsonObjectSet(p,"game",observed);
    p=JsonObjectSet(p,"history",JsonString(GetLocalString(pc,"AWC_PENDING_VERSION")!=""?AWText(AWCRecord(pc,AWCIdentity(pc,npc)),"history"):GetLocalString(pc,"SP_HIST_"+tag)));
    string id=GetRandomUUID(); SPPublish(pc);
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"INSERT INTO sp_requests(request_id,session_id,kind,npc_tag,payload,created,updated) VALUES(@i,@s,@k,@n,@p,CAST(strftime('%s','now') AS INTEGER),CAST(strftime('%s','now') AS INTEGER))");
    SqlBindString(q,"@i",id);SqlBindString(q,"@s",SPSession());SqlBindString(q,"@k",kind);SqlBindString(q,"@n",tag);SqlBindString(q,"@p",JsonDump(p));SqlStep(q);
    if(SqlGetError(q)!="") { SendMessageToPC(pc,"The local AI connection is unavailable. Authored conversations still work."); return; }
    SetLocalString(pc,"SP_PENDING",id);SetLocalInt(pc,"SP_SENT",SPNow());
    SetLocalString(pc,"SP_QUESTION",message);SetLocalString(pc,"SP_TAG",tag);
    // Also explain missing/paused service when the player first tries AI.
    if(SPServiceState(pc)!="connected")SPServiceCheck(pc,TRUE);
    SendMessageToPC(pc,"Role Weaver: request sent. Keep the module running while Studio replies.");
}
void SPPoll(object pc)
{
    SPReset(pc);string id=GetLocalString(pc,"SP_PENDING"); if(id=="") return;
    if(SPNow()-GetLocalInt(pc,"SP_SENT")>100) {
        DeleteLocalString(pc,"SP_PENDING"); SendMessageToPC(pc,"AI reply timed out. Type !studio to check the local service, or use the normal NPC menu. A connected service still needs a working API key and this adventure's matching profile."); return; }
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"SELECT state,response,kind,npc_tag FROM sp_requests WHERE request_id=@i AND session_id=@s");
    SqlBindString(q,"@i",id);SqlBindString(q,"@s",SPSession());
    if(!SqlStep(q)) return;
    string state=SqlGetString(q,0);
    if(state=="queued" || state=="working") return;
    DeleteLocalString(pc,"SP_PENDING");
    if(state!="ready" && state!="failed") return;
    json result=JsonParse(SqlGetString(q,1)); string kind=SqlGetString(q,2); string tag=SqlGetString(q,3);
    sqlquery ack=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_requests SET state='consumed' WHERE request_id=@i");SqlBindString(ack,"@i",id);SqlStep(ack);
    if(SqlGetError(ack)!="") return;
    string reply=GetStringLeft(SPText(result,"reply"),1200);
    if(kind=="npc" || kind=="companion") {
        object npc=GetLocalObject(pc,"SP_PENDING_ACTOR");
        if(!SPNear(pc,npc) || GetLocalObject(pc,"SP_FOCUS")!=npc) { SendMessageToPC(pc,"The conversation ended when you moved away. Speak to the NPC again to continue."); return; }
        if(AWText(AWMShop(npc),"id")!="" && GetLocalString(pc,"AWM_REQUEST")!=AWMVersion(pc,npc)){
 reply="My stock or prices changed while I was answering. Please reopen my goods panel for current information.";result=JsonObjectSet(result,"merchant_action",JsonString(""));}
        if(GetLocalString(pc,"AWC_PENDING_VERSION")!="" && (AWCVersion(pc,npc)!=GetLocalString(pc,"AWC_PENDING_VERSION") || !AWCAIReady(pc,npc) || IsInConversation(pc) || IsInConversation(npc))){SendMessageToPC(pc,"Companion control, ownership or preferences changed. The older AI reply was discarded.");return;}
        AWATouch(npc);if(state=="ready")AssignCommand(npc,SpeakString(AWCMode(npc)=="nonverbal"?"*"+reply+"*":reply,TALKVOLUME_TALK));else SendMessageToPC(pc,reply);
        if(state=="ready") {
            string history=(GetLocalString(pc,"AWC_PENDING_VERSION")!=""?AWText(AWCRecord(pc,AWCIdentity(pc,npc)),"history"):GetLocalString(pc,"SP_HIST_"+tag))+"\nPlayer: "+GetLocalString(pc,"SP_QUESTION")+"\nNPC: "+reply;
            if(GetLocalString(pc,"AWC_PENDING_VERSION")!="")AWCHistorySet(pc,npc,history);else SetLocalString(pc,"SP_HIST_"+tag,GetStringRight(history,6000));
            string verb=SPText(result,"action"); if(SPText(result,"task_target")!=""){AWTApplyAI(pc,npc,result);SPEnd(pc,FALSE);}else {if(kind=="npc")AWAIAction(pc,tag,SPText(result,"story_action")); string shopVerb=SPText(result,"merchant_action");if(kind=="npc" && (shopVerb=="browse" || shopVerb=="haggle"))AWMOpen(pc,npc,shopVerb=="haggle");string cpVerb=SPText(result,"companion_action");if(cpVerb!="")AWCApply(pc,npc,cpVerb);}
            // Quest decisions are made through native authored conversation choices.
            
        }
    } else SendMessageToPC(pc,"DM: "+reply);
}
string SPApply(object pc,json cmd)
{
    if(SPText(cmd,"player")!=GetObjectUUID(pc) || SPText(cmd,"area")!=GetTag(GetArea(pc)) || GetIsDead(pc)) return "Rejected: party or area changed.";
    string verb=SPText(cmd,"action");
    if(verb=="narrate") {SendMessageToPC(pc,"DM: "+GetStringLeft(SPText(cmd,"message"),1000)); return "Narration delivered.";}
    string id=SPText(cmd,"encounter_id"); json all=SPEncounters();json e=JsonNull();int i=0;
    while(i<JsonGetLength(all)) {json candidate=JsonArrayGet(all,i);if(SPText(candidate,"id")==id) e=candidate;i++;}
    if(SPText(e,"id")=="" || SPText(e,"area")!=GetTag(GetArea(pc))) return "Rejected: encounter is not allowed in this area.";
    if(verb=="cleanup") {
        int removed=0;object o=GetFirstObjectInArea(GetArea(pc));
        while(GetIsObjectValid(o)) {if(GetLocalString(o,"SP_OWNED")==id) {DestroyObject(o);removed++;} o=GetNextObjectInArea(GetArea(pc));}
        return "Removed "+IntToString(removed)+" Studio creatures. Encounter remains spent.";
    }
    if(verb!="spawn") return "Rejected: unsupported action.";
    if(GetLocalInt(GetModule(),"SP_USED_"+id)) return "Rejected: this encounter has already been deployed in this save.";
    object mark=GetObjectByTag(id);
    if(!GetIsObjectValid(mark) || GetArea(mark)!=GetArea(pc)) return "Rejected: encounter marker missing.";
    if(GetDistanceBetween(pc,mark)<6.0) return "Rejected: move at least six metres away from the encounter marker.";
    int live=0;int levels=0;int hp=0;int maxhp=0;int combat=FALSE;
    object m=GetFirstFactionMember(pc,FALSE);
    while(GetIsObjectValid(m)) {
        if(GetArea(m)==GetArea(pc) && !GetIsDead(m)) {live++; levels+=GetHitDice(m);hp+=GetCurrentHitPoints(m);maxhp+=GetMaxHitPoints(m);if(GetIsInCombat(m)) combat=TRUE;}
        m=GetNextFactionMember(pc,FALSE);
    }
    if(combat || live==0 || hp*2<maxhp) return "Rejected: finish combat and heal the party before adding enemies.";
    int count=SPInt(e,"count");
    if(SPInt(e,"scale")) { count+=(live-1)/2; if(levels/live>=4) count++; }
    if(count>SPInt(e,"maximum")) count=SPInt(e,"maximum");
    if(count<1 || count>6) return "Rejected: invalid encounter count.";
    SetLocalInt(GetModule(),"SP_USED_"+id,TRUE);int made=0;i=0;
    while(i<count) {
        object enemy=CreateObject(OBJECT_TYPE_CREATURE,SPText(e,"resref"),GetLocation(mark));
        if(GetIsObjectValid(enemy)) {SetLocalString(enemy,"SP_OWNED",id);made++;} i++;
    }
    if(made==0) {DeleteLocalInt(GetModule(),"SP_USED_"+id);return "Failed: no creature could be placed.";}
    return "Deployed "+IntToString(made)+" creatures. Party size "+IntToString(live)+"; total levels "+IntToString(levels)+".";
}
void SPCommands(object pc)
{
    sqlquery q=SqlPrepareQueryCampaign(SPDB,"SELECT command_id,payload FROM sp_commands WHERE session_id=@s AND state='queued' AND created>CAST(strftime('%s','now') AS INTEGER)-45 ORDER BY created LIMIT 1");
    SqlBindString(q,"@s",SPSession());if(!SqlStep(q)) return;
    string id=SqlGetString(q,0);json cmd=JsonParse(SqlGetString(q,1));
    sqlquery claim=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_commands SET state='processing' WHERE command_id=@i AND state='queued'");SqlBindString(claim,"@i",id);SqlStep(claim);
    if(SqlGetError(claim)!="") return;
    string receipt=SPApply(pc,cmd);
    sqlquery done=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_commands SET state='acknowledged',receipt=@r,updated=CAST(strftime('%s','now') AS INTEGER) WHERE command_id=@i");
    SqlBindString(done,"@i",id);SqlBindString(done,"@r",receipt);SqlStep(done);
    SendMessageToPC(pc,"Role Weaver: "+receipt);
}

