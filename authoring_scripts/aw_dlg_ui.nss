#include "aw_companion"
#include "aw_dlg_pref"
void AWDClose(object pc){int token=GetLocalInt(pc,"AWD_TOKEN");DeleteLocalInt(pc,"AWD_TOKEN");if(token && GetLocalString(pc,"AWD_SESSION")==GetLocalString(GetModule(),"AWM_SESSION"))NuiDestroy(pc,token);}
json AWDButton(object pc,string label,string id){return AWUIHeight(AWUIId(AWUIButton(JsonString(label)),id+"_"+IntToString(GetLocalInt(pc,"AWD_GEN"))),36.0);}
void AWDOpen(object pc){
 if(!GetIsPC(pc))return;AWDClose(pc);SetLocalInt(pc,"AWD_GEN",GetLocalInt(pc,"AWD_GEN")+1);SetLocalString(pc,"AWD_SESSION",GetLocalString(GetModule(),"AWM_SESSION"));
 json rows=JsonArray();rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("Click a setting to cycle its choices. Changes apply to new replies and are saved with your game."),52.0));
 rows=JsonArrayInsert(rows,AWDButton(pc,"Reply length: "+AWDLengthName(AWDGet(pc,"length")),"length"));
 rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("Brief: 1-2 short sentences. Natural: 2-4. Detailed: up to 6."),38.0));
 int voice=AWDGet(pc,"voice");rows=JsonArrayInsert(rows,AWDButton(pc,"Speaking style: "+(voice==0?"Plain":voice==1?"Characterful":"Dramatic"),"voice"));
 int emotes=AWDGet(pc,"emotes");rows=JsonArrayInsert(rows,AWDButton(pc,"Action descriptions: "+(emotes==0?"Off":emotes==1?"Occasional":"Expressive"),"emotes"));
 rows=JsonArrayInsert(rows,AWDButton(pc,"Follow-up questions: "+(AWDGet(pc,"questions")==0?"Only when needed":"Conversational"),"questions"));
 rows=JsonArrayInsert(rows,AWUIHeight(AWUIText("All NPCs, merchants and companions keep their personalities. Nonverbal creatures still use gestures. A companion's own reply-length choice overrides this default."),68.0));
 rows=JsonArrayInsert(rows,AWDButton(pc,"Restore short, plain defaults","reset"));rows=JsonArrayInsert(rows,AWDButton(pc,"Close","close"));
 json window=AWUIWindow(AWUIScroll(AWUIStack(rows,510.0)),JsonString("AI response settings"),AWUIRect(-1.0,-1.0,580.0,510.0),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE));
 int token=NuiCreate(pc,window,"aw_dialogue_"+IntToString(GetLocalInt(pc,"AWD_GEN")),"aw_dlg_evt");SetLocalInt(pc,"AWD_TOKEN",token);if(!token)SendMessageToPC(pc,"The AI response settings window could not open. Try !aisettings again.");
}
void AWDEvent(){
 object pc=NuiGetEventPlayer();int token=GetLocalInt(pc,"AWD_TOKEN");if(!GetIsPC(pc) || !token || NuiGetEventWindow()!=token || GetLocalString(pc,"AWD_SESSION")!=GetLocalString(GetModule(),"AWM_SESSION"))return;
 if(NuiGetEventType()=="close"){DeleteLocalInt(pc,"AWD_TOKEN");return;}if(NuiGetEventType()!="click")return;
 string id=NuiGetEventElement();string suffix="_"+IntToString(GetLocalInt(pc,"AWD_GEN"));
 if(id=="close"+suffix){AWDClose(pc);return;}
 if(id=="reset"+suffix){DeleteLocalInt(pc,"AWD_length");DeleteLocalInt(pc,"AWD_voice");DeleteLocalInt(pc,"AWD_emotes");DeleteLocalInt(pc,"AWD_questions");AWDOpen(pc);return;}
 string field="";if(id=="length"+suffix)field="length";else if(id=="voice"+suffix)field="voice";else if(id=="emotes"+suffix)field="emotes";else if(id=="questions"+suffix)field="questions";
 if(field=="")return;SetLocalInt(pc,"AWD_"+field,(AWDGet(pc,field)+1)%(field=="questions"?2:3));AWDOpen(pc);
}
