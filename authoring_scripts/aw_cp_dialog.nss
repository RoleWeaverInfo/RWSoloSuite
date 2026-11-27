// Add a real dialogue tree for owned familiars/summons; retain native speech orders.
#include "aw_companion"
void main(){object master=GetMaster();object owner=master;int depth=0;while(GetIsObjectValid(owner) && !GetIsPC(owner) && depth<8){owner=GetMaster(owner);depth++;}
 int pattern=GetListenPatternNumber();object speaker=GetLastSpeaker();
 if(pattern==-1 && speaker==owner && GetIsPC(owner) && (AWCKind(OBJECT_SELF)=="familiar" || AWCKind(OBJECT_SELF)=="summon") && AWCReady(owner,OBJECT_SELF) && AWCObserve(owner,OBJECT_SELF)){BeginConversation("aw_cp_native",owner);return;}
 int ownerSpeech=GetIsObjectValid(speaker) && (speaker==owner || speaker==master);
 // Native ASSOCIATE_COMMAND_* events use IDs below -1. Positive listen IDs
 // belong to module scripts and may match ALL speech (DMFI, custom emotes,
 // etc.). Hearing a line is not, by itself, a change of companion control.
 // Count even repeated native orders so they still supersede pending AI.
 if(ownerSpeech && pattern < -1)SetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH",GetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH")+1);
 int command=GetLastAssociateCommand();int modes=GetLocalInt(OBJECT_SELF,"NW_ASSOCIATE_MASTER");int commandable=GetCommandable();
 string base=GetLocalString(OBJECT_SELF,"AWC_BASE_DIALOG");if(base!="" && base!="aw_cp_dialog")ExecuteScript(base,OBJECT_SELF);
 // Preserve custom text commands too: delegate once, then invalidate only
 // when their handler actually changes an order, mode, master or control.
 if(ownerSpeech && pattern>=0 && (GetLastAssociateCommand()!=command || GetLocalInt(OBJECT_SELF,"NW_ASSOCIATE_MASTER")!=modes || GetMaster()!=master || GetCommandable()!=commandable))SetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH",GetLocalInt(OBJECT_SELF,"AWC_CONTROL_EPOCH")+1);
}
