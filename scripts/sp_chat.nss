#include "sp_inc"
void main() {
    object pc=GetPCChatSpeaker();string s=GetPCChatMessage();if(!GetIsPC(pc)) return;
    if(GetStringLeft(s,4)=="!ai ") {SetPCChatMessage("");SPAsk(pc,"npc",GetSubString(s,4,1200));}
    else if(GetStringLeft(s,4)=="!dm ") {SetPCChatMessage("");SPAsk(pc,"dm",GetSubString(s,4,1200));}
    else if(GetStringLeft(s,6)=="!talk ") {
        SetPCChatMessage("");string rest=GetSubString(s,6,1300);int at=FindSubString(rest," ");
        if(at<1) {SendMessageToPC(pc,"Use !talk <alias> <message>. Available aliases: "+SPAliases());return;}
        string tag=SPAlias(GetStringLowerCase(GetStringLeft(rest,at)));
        if(tag=="") {SendMessageToPC(pc,"Available aliases: "+SPAliases());return;}
        SetLocalObject(pc,"SP_FOCUS",GetObjectByTag(tag));SPAsk(pc,"npc",GetSubString(rest,at+1,1200));
    }
    else if(s=="!ai" || s=="!dm" || s=="!talk") {SetPCChatMessage("");SendMessageToPC(pc,"Type !ai <message>, !talk <alias> <message>, or !dm <request>.");}
}
