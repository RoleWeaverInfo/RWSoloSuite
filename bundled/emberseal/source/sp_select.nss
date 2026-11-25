#include "sp_inc"
void main(){object pc=GetPCSpeaker();SPEnd(pc,FALSE);SetLocalObject(pc,"SP_FOCUS",OBJECT_SELF);SetLocalInt(pc,"SP_FOCUS_AT",SPNow());
 SetLocalObject(GetModule(),"SP_CONTROLLER",pc);SendMessageToPC(pc,"AI conversation: "+GetName(OBJECT_SELF)+". Close the menu and speak normally in Talk, or type !ai <message>. Stay nearby. Use !aisettings for response preferences, or !end to finish. NPC menu choices share the same story progress.");}
