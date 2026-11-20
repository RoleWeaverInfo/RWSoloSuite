#include "sp_inc"
void main() {
    ExecuteScript("mc_enter",GetModule());object pc=GetEnteringObject();if(!GetIsPC(pc)) return;
    SPReset(pc);SPPublish(pc);SPServiceBegin(pc);DelayCommand(12.0,SPServiceCheck(pc));
    SendMessageToPC(pc,"ROLE WEAVER SOLO | Talk to an NPC and choose Talk freely with AI; then type !ai <message>. Or !talk edric <message>. Use !dm <request> for the DM Assistant. Keep Solo Studio's companion running. The authored quest works without AI.");
}
