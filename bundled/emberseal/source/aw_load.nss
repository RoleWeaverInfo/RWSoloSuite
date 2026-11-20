#include "aw_social"
void main(){SetLocalString(GetModule(),"AWM_SESSION",GetRandomUUID());AWALoad();if(AWCEnabled()){AWCInit();SetMaxHenchmen(3);}SPInit();}
