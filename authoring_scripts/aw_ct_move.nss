// Lease native associate modes for one explicit task. Never restore over a newer order.
#include "nw_i0_generic"
void main(){object pc=GetLocalObject(OBJECT_SELF,"AWT_OWNER");object master=GetMaster();int depth=0;while(GetIsObjectValid(master) && !GetIsPC(master) && depth<8){master=GetMaster(master);depth++;}
 if(pc!=master || !GetIsPC(pc) || GetIsPC(OBJECT_SELF) || GetIsDead(OBJECT_SELF) || GetIsPossessedFamiliar(OBJECT_SELF) || GetIsDMPossessed(OBJECT_SELF) || !GetCommandable() || (GetLocalInt(OBJECT_SELF,"AWT_EPOCH")!=GetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH") || GetLocalInt(OBJECT_SELF,"AWT_NATIVE")!=GetLastAssociateCommand()))return;
 string op=GetLocalString(OBJECT_SELF,"AWT_MOVE_OP");if(op=="restore"){if(!GetLocalInt(OBJECT_SELF,"AWT_LEASE"))return;SetAssociateState(NW_ASC_MODE_STAND_GROUND,GetLocalInt(OBJECT_SELF,"AWT_PRE_WAIT"));SetAssociateState(NW_ASC_MODE_DEFEND_MASTER,GetLocalInt(OBJECT_SELF,"AWT_PRE_GUARD"));
 if(!GetIsInCombat(OBJECT_SELF)){if(GetCurrentAction()==ACTION_MOVETOPOINT)ClearAllActions(TRUE);if(!GetLocalInt(OBJECT_SELF,"AWT_PRE_WAIT"))ActionForceFollowObject(GetMaster(),3.0);}DeleteLocalInt(OBJECT_SELF,"AWT_LEASE");return;}
 if(GetIsInCombat(OBJECT_SELF) || GetIsInCombat(pc) || IsInConversation(OBJECT_SELF))return;
 if(op=="start"){SetLocalInt(OBJECT_SELF,"AWT_PRE_WAIT",GetAssociateState(NW_ASC_MODE_STAND_GROUND));SetLocalInt(OBJECT_SELF,"AWT_PRE_GUARD",GetAssociateState(NW_ASC_MODE_DEFEND_MASTER));SetLocalInt(OBJECT_SELF,"AWT_LEASE",TRUE);ResetHenchmenState();SetAssociateState(NW_ASC_MODE_STAND_GROUND,TRUE);ClearAllActions(TRUE);SetLocalInt(OBJECT_SELF,"AWT_MOVE_OK",TRUE);return;}
 if(op=="pause"){if(GetCurrentAction()==ACTION_WAIT)ClearAllActions(TRUE);return;}object target=GetLocalObject(OBJECT_SELF,"AWT_DEST");if(!GetIsObjectValid(target) || GetArea(target)!=GetArea(OBJECT_SELF))return;
 if(op=="open"){if(GetCurrentAction()==ACTION_INVALID)ActionInteractObject(target);return;}
 if(GetCurrentAction()==ACTION_WAIT)ClearAllActions(TRUE);if(GetCurrentAction()==ACTION_INVALID)ActionMoveToObject(target,FALSE,1.5);}
