#include "aw_ambient"
void main(){if(GetIsPC(GetLastSpeaker()))AWATouch(OBJECT_SELF);string base=GetLocalString(OBJECT_SELF,"AWA_BASE_DIALOG");if(base!="" && base!="aw_am_dialog")ExecuteScript(base,OBJECT_SELF);}

