// An on-demand, instance-specific chat selector. Never runs on the heartbeat
// and never replaces a creature's native dialogue, quest or combat scripts.
#include "sp_inc"
#include "aw_dlg_ui"

int RWNPCReady(object pc,object body){
 if(!GetIsPC(pc) || GetIsDM(pc) || !GetCommandable(pc) || GetCutsceneMode(pc))return FALSE;
 return SPNear(pc,body) && !GetIsPC(body) && !GetIsDM(body) && !GetIsDMPossessed(body) && !GetIsPossessedFamiliar(body) && GetCommandable(body) && !GetCutsceneMode(body) && SPIsNPC(RWProfile(body)) && AWCAIReady(pc,body);
}
void RWNPCClose(object pc){
 int token=GetLocalInt(pc,"RWNPC_TOKEN");DeleteLocalInt(pc,"RWNPC_TOKEN");
 if(token && GetLocalString(pc,"RWNPC_SESSION")==GetLocalString(GetModule(),"AWM_SESSION"))NuiDestroy(pc,token);
}
json RWNPCButton(object pc,string text,string id,int enabled=TRUE){
 return AWUIHeight(AWUIEnabled(AWUIId(AWUIButton(JsonString(text)),id+"_"+IntToString(GetLocalInt(pc,"RWNPC_GEN"))),JsonBool(enabled)),34.0);
}
void RWNPCOpen(object pc){
 if(!GetIsPC(pc) || GetIsDead(pc) || GetIsInCombat(pc) || IsInConversation(pc) || GetCutsceneMode(pc) || !GetCommandable(pc)){
  SendMessageToPC(pc,"Finish your current dialogue or combat before choosing someone for AI chat.");return;
 }
 RWNPCClose(pc);SetLocalInt(pc,"RWNPC_GEN",GetLocalInt(pc,"RWNPC_GEN")+1);
 SetLocalString(pc,"RWNPC_SESSION",GetLocalString(GetModule(),"AWM_SESSION"));
 json actors=JsonArray();int n=1;object body=GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR,PLAYER_CHAR_NOT_PC,pc,n);
 while(GetIsObjectValid(body) && n<=128 && JsonGetLength(actors)<64){
  if(GetDistanceBetween(pc,body)>12.0)break;
  if(RWNPCReady(pc,body))actors=JsonArrayInsert(actors,JsonString(GetObjectUUID(body)));
  n++;body=GetNearestCreature(CREATURE_TYPE_PLAYER_CHAR,PLAYER_CHAR_NOT_PC,pc,n);
 }
 int page=GetLocalInt(pc,"RWNPC_PAGE");if(page<0 || page*8>=JsonGetLength(actors))page=0;SetLocalInt(pc,"RWNPC_PAGE",page);
 json rows=JsonArray();rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("Talk freely with AI: select a nearby character. Original dialogue remains available by talking to them normally."),56.0));
 int i=page*8;int shown=0;
 while(i<JsonGetLength(actors) && shown<8){
  string uuid=JsonGetString(JsonArrayGet(actors,i));body=GetObjectByUUID(uuid);
  SetLocalString(pc,"RWNPC_ROW_"+IntToString(shown),uuid);SetLocalString(pc,"RWNPC_ID_"+IntToString(shown),RWProfile(body));
  string label=GetName(body)+" | "+IntToString(FloatToInt(GetDistanceBetween(pc,body)))+"m | #"+IntToString(i+1);
  rows=JsonArrayInsert(rows,RWNPCButton(pc,label,"actor"+IntToString(shown)));shown++;i++;
 }
 SetLocalInt(pc,"RWNPC_ROWS",shown);
 if(!shown)rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("No available AI characters in sight within 12m. Move closer; use !companions for familiars and summons."),56.0));
 if(n>128 || JsonGetLength(actors)>=64)rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("Showing the nearest available characters. Move closer and refresh for others."),44.0));
 json nav=JsonArray();nav=JsonArrayInsert(nav,RWNPCButton(pc,"Previous","previous",page>0));nav=JsonArrayInsert(nav,RWNPCButton(pc,"Next","next",i<JsonGetLength(actors)));nav=JsonArrayInsert(nav,RWNPCButton(pc,"Refresh","refresh"));
 rows=JsonArrayInsert(rows,AWUIRow(nav));rows=JsonArrayInsert(rows,RWNPCButton(pc,"AI response settings","settings"));rows=JsonArrayInsert(rows,RWNPCButton(pc,"Close","close"));
 json window=AWUIWindow(AWUIScroll(AWUIStack(rows,520.0)),JsonString("Nearby NPCs - Talk freely with AI"),AWUIRect(-1.0,-1.0,590.0,540.0),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE));
 int token=NuiCreate(pc,window,"rwc_npcs_"+IntToString(GetLocalInt(pc,"RWNPC_GEN")),"rwc_npc_evt");SetLocalInt(pc,"RWNPC_TOKEN",token);
 if(!token)SendMessageToPC(pc,"The NPC selector could not open. You can still use an NPC's AI dialogue option or !talk <alias> <message>.");
}
void RWNPCEvent(){
 object pc=NuiGetEventPlayer();int token=GetLocalInt(pc,"RWNPC_TOKEN");
 if(!GetIsPC(pc) || !token || NuiGetEventWindow()!=token || GetLocalString(pc,"RWNPC_SESSION")!=GetLocalString(GetModule(),"AWM_SESSION"))return;
 if(NuiGetEventType()=="close"){DeleteLocalInt(pc,"RWNPC_TOKEN");return;}if(NuiGetEventType()!="click")return;
 string id=NuiGetEventElement();string suffix="_"+IntToString(GetLocalInt(pc,"RWNPC_GEN"));
 if(id=="close"+suffix){RWNPCClose(pc);return;}
 if(id=="settings"+suffix){RWNPCClose(pc);AWDOpen(pc);return;}
 if(id=="refresh"+suffix || id=="next"+suffix || id=="previous"+suffix){
  if(id!="refresh"+suffix)SetLocalInt(pc,"RWNPC_PAGE",GetLocalInt(pc,"RWNPC_PAGE")+(id=="next"+suffix?1:-1));RWNPCOpen(pc);return;
 }
 int i=0;while(i<GetLocalInt(pc,"RWNPC_ROWS")){
  if(id=="actor"+IntToString(i)+suffix){
   object body=GetObjectByUUID(GetLocalString(pc,"RWNPC_ROW_"+IntToString(i)));
   if(RWProfile(body)!=GetLocalString(pc,"RWNPC_ID_"+IntToString(i)) || !RWNPCReady(pc,body)){
    SendMessageToPC(pc,"That character is no longer available for AI chat. Refresh or move closer.");return;
   }
   RWNPCClose(pc);SPEnd(pc,FALSE);SetLocalObject(pc,"SP_FOCUS",body);SetLocalInt(pc,"SP_FOCUS_AT",SPNow());SetLocalObject(GetModule(),"SP_CONTROLLER",pc);
   SendMessageToPC(pc,"AI conversation: "+GetName(body)+". Speak normally in Talk with the game unpaused. Use !end to finish.");return;
  }i++;
 }
}
