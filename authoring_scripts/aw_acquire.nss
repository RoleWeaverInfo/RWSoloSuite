#include "aw_quest"
void main(){object pc=GetModuleItemAcquiredBy();if(!GetIsPC(pc))pc=GetMaster(pc);if(GetIsPC(pc))AQTick(pc);}
