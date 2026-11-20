// Standard native associate modes; original heartbeat and combat scripts stay installed.
#include "nw_i0_generic"
void main(){object owner=GetLocalObject(OBJECT_SELF,"AWC_ORDER_OWNER");object master=GetMaster();int depth=0;while(GetIsObjectValid(master) && !GetIsPC(master) && depth<8){master=GetMaster(master);depth++;}
 if(!GetIsPC(owner) || owner!=master || GetIsPC(OBJECT_SELF) || GetIsDead(OBJECT_SELF) || GetIsDMPossessed(OBJECT_SELF) || GetIsPossessedFamiliar(OBJECT_SELF) || GetIsInCombat(OBJECT_SELF) || GetIsInCombat(owner) || !GetCommandable())return;
 string command=GetLocalString(OBJECT_SELF,"AWC_ORDER");if(command!="follow" && command!="stay" && command!="guard")return;
 ClearAllActions(TRUE);ResetHenchmenState();SetAssociateState(NW_ASC_MODE_STAND_GROUND,command=="stay");SetAssociateState(NW_ASC_MODE_DEFEND_MASTER,command=="guard");if(command!="stay")ActionForceFollowObject(GetMaster(),3.0);SetLocalInt(OBJECT_SELF,"AWC_ORDER_OK",TRUE);}

