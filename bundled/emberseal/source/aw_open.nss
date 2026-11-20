#include "aw_quest"
void main(){object pc=GetLastOpenedBy();if(GetIsPC(pc))AWResolve(pc,GetTag(OBJECT_SELF));}

