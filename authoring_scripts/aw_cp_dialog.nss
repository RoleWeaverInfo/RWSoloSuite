// Observe native player orders, then chain the original creature conversation handler.
void main(){object owner=GetMaster();int depth=0;while(GetIsObjectValid(owner) && !GetIsPC(owner) && depth<8){owner=GetMaster(owner);depth++;}
 if(GetListenPatternNumber()!=-1 && (GetLastSpeaker()==owner || GetLastSpeaker()==GetMaster()))SetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH",GetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH")+1);
 string base=GetLocalString(OBJECT_SELF,"AWC_BASE_DIALOG");if(base!="" && base!="aw_cp_dialog")ExecuteScript(base,OBJECT_SELF);}
