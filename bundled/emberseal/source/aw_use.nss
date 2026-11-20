#include "aw_quest"
void main(){object pc=GetLastUsedBy();if(!GetIsPC(pc))return;string id=GetTag(OBJECT_SELF);json e=AWFind(AWEncounters(),id);
 if(!AQDone(AWText(e,"after_quest"))){SendMessageToPC(pc,"There is more to learn before this can be used.");return;}
 if(AWText(e,"kind")=="story" && !AWStoryReady(id)){SendMessageToPC(pc,"This is not part of your current objective.");return;}
 if(AWText(e,"kind")=="puzzle"){BeginConversation(id,pc);return;}
 SendMessageToPC(pc,AWText(e,"prompt"));AWResolve(pc,id);}

