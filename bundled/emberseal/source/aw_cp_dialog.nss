// Add a real dialogue tree for owned familiars/summons; retain native speech orders.
#include "aw_companion"
void main(){object owner=GetMaster();int depth=0;while(GetIsObjectValid(owner) && !GetIsPC(owner) && depth<8){owner=GetMaster(owner);depth++;}
 if(GetListenPatternNumber()==-1 && GetLastSpeaker()==owner && GetIsPC(owner) && (AWCKind(OBJECT_SELF)=="familiar" || AWCKind(OBJECT_SELF)=="summon") && AWCReady(owner,OBJECT_SELF) && AWCObserve(owner,OBJECT_SELF)){BeginConversation("aw_cp_native",owner);return;}
 if(GetListenPatternNumber()!=-1 && (GetLastSpeaker()==owner || GetLastSpeaker()==GetMaster()))SetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH",GetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH")+1);
 string base=GetLocalString(OBJECT_SELF,"AWC_BASE_DIALOG");if(base!="" && base!="aw_cp_dialog")ExecuteScript(base,OBJECT_SELF);}

