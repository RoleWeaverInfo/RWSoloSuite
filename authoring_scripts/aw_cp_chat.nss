// Native companion commands remain available in builds without live AI.
#include "aw_cp_ui"
void main(){object pc=GetPCChatSpeaker();string text=GetPCChatMessage();if(!GetIsPC(pc) || GetPCChatVolume()!=TALKVOLUME_TALK)return;
 if(text=="!companions" || text=="!companion" || GetStringLeft(text,11)=="!companion "){SetPCChatMessage("");if(!AWCChatControl(pc,text))SendMessageToPC(pc,"This build has native companion controls only. Use !companions for orders and inventory.");}}
