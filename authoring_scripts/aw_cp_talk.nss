#include "aw_companion"
void main(){object pc=GetPCSpeaker();if(!AWCReady(pc,OBJECT_SELF) || !AWCObserve(pc,OBJECT_SELF) || !AWInt(AWCCfg(),"live_ai") || !AWCAIReady(pc,OBJECT_SELF))return;
 SetLocalObject(pc,"SP_FOCUS",OBJECT_SELF);SetLocalInt(pc,"AWC_CHAT_ARMED",TRUE);SendMessageToPC(pc,"Conversation ready. Speak normally in Talk after closing this dialogue; !end finishes it.");}
