#include "aw_quest"
void main(){object pc=GetModuleItemAcquiredBy();if(GetObjectType(pc)!=OBJECT_TYPE_CREATURE)return;if(!GetIsPC(pc))pc=GetMaster(pc);if(GetIsPC(pc))AQTick(pc);}

