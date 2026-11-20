#include "aw_companion"
void main(){object pc=GetEnteringObject();if(!GetIsPC(pc))pc=GetLastUsedBy();if(!GetIsPC(pc))return;
 string need=GetLocalString(OBJECT_SELF,"AW_GATE");if(!AQDone(need)){SendMessageToPC(pc,"This passage opens after the quest: "+need);return;}
 object marker=GetObjectByTag(GetLocalString(OBJECT_SELF,"AW_TARGET"));if(!GetIsObjectValid(marker))return;
 object area=GetArea(pc);AssignCommand(pc,JumpToLocation(GetLocation(marker)));object m=GetFirstFactionMember(pc,FALSE);
 while(GetIsObjectValid(m)){if(m!=pc && GetArea(m)==area && !GetIsDead(m) && AWCTravel(pc,m))AssignCommand(m,JumpToLocation(GetLocation(marker)));m=GetNextFactionMember(pc,FALSE);}}

