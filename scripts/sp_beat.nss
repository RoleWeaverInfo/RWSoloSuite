#include "sp_inc"
void main() {
    if(SPSession()=="") SPInit();object pc=GetLocalObject(GetModule(),"SP_CONTROLLER");
    if(!GetIsObjectValid(pc)) pc=GetFirstPC();
    if(!GetIsObjectValid(pc)) return;
    SPPublish(pc);SPCommands(pc);
    object member=GetFirstPC();
    while(GetIsObjectValid(member)) {SPServiceCheck(member);SPPoll(member);member=GetNextPC();}
}
