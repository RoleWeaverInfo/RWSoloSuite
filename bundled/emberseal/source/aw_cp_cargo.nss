// A save-local escrow survives cancellation, death and associate disappearance.
// Never retry a delivery after any destination count change.
#include "aw_cp_ui"
void AWXFinish(object pc,string result,int success){object body=GetLocalObject(pc,"AWX_BODY");object src=GetLocalObject(pc,"AWX_SOURCE");object dest=GetLocalObject(pc,"AWX_DEST");
 if(GetObjectType(src)==OBJECT_TYPE_PLACEABLE)SetLocked(src,GetLocalInt(pc,"AWX_SRC_LOCK"));if(GetObjectType(dest)==OBJECT_TYPE_PLACEABLE)SetLocked(dest,GetLocalInt(pc,"AWX_DST_LOCK"));
 DeleteLocalInt(pc,"AWX_PHASE");DeleteLocalInt(pc,"AWT_TRANSFER_PENDING");AWCReceipt(pc,GetLocalString(pc,"AWX_ID"),result);
 if(GetIsObjectValid(body) && GetLocalInt(body,"AWT_ACTIVE") && GetLocalInt(body,"AWT_PHASE")==5){if(success){SetLocalString(body,"AWT_RESULT",result);SetLocalInt(body,"AWT_PHASE",4);}else AWTFinish(pc,body,result);}SendMessageToPC(pc,result);if(GetLocalString(pc,"AWC_VIEW")=="grid" && GetLocalInt(pc,"AWC_TOKEN"))AWCGridOpen(pc,GetLocalObject(pc,"AWC_STORAGE"));}
void AWXTick(object pc){int phase=GetLocalInt(pc,"AWX_PHASE");if(phase<=0)return;
 SetLocalInt(pc,"AWT_TRANSFER_PENDING",TRUE);SetLocalInt(pc,"AWT_TRANSFER_EXPIRES",AWMClock()+30);
 object original=GetLocalObject(pc,"AWX_ORIGINAL");object staged=GetLocalObject(pc,"AWX_STAGED");object escrow=GetLocalObject(pc,"AWX_ESCROW");object dest=GetLocalObject(pc,"AWX_DEST");
 string tag=GetLocalString(pc,"AWX_TAG");string res=GetLocalString(pc,"AWX_RES");int amount=GetLocalInt(pc,"AWX_AMOUNT");
 if(phase==1){int remaining=GetLocalInt(pc,"AWX_SOURCE_REMAINING");int sourceOK=remaining==0?!GetIsObjectValid(original):GetIsObjectValid(original) && GetItemPossessor(original,TRUE)==GetLocalObject(pc,"AWX_SOURCE") && GetItemStackSize(original)==remaining;if(!sourceOK){if(!GetIsObjectValid(original) || GetItemStackSize(original)!=GetLocalInt(pc,"AWX_SOURCE_ORIGINAL")){SetLocalInt(pc,"AWX_PHASE",-1);SendMessageToPC(pc,"The source items changed unexpectedly. The handoff is paused; no duplicate delivery will be attempted.");return;}DestroyObject(staged);DestroyObject(escrow);AWXFinish(pc,"I could not move the requested items. They remain with their original holder.",FALSE);return;}SetLocalInt(pc,"AWX_PHASE",2);phase=2;}
 if(phase==2){if(!GetIsObjectValid(dest) || !GetIsObjectValid(staged)){SetLocalInt(pc,"AWX_PHASE",-1);SendMessageToPC(pc,"The handoff needs recovery. I have not confirmed delivery; please retain this save.");return;}
 int before=AWCCount(dest,tag,res);object delivered=CopyItem(staged,dest,TRUE);int after=AWCCount(dest,tag,res);
 if(GetIsObjectValid(delivered) && GetItemPossessor(delivered,TRUE)==dest && after==before+amount){SetLocalInt(pc,"AWX_BEFORE",before);DestroyObject(staged);SetLocalInt(pc,"AWX_PHASE",3);return;}
 // Zero change can safely wait for capacity. Any partial/ambiguous change freezes recovery.
 if(after!=before || GetIsObjectValid(delivered)){SetLocalInt(pc,"AWX_PHASE",-1);SendMessageToPC(pc,"I could not verify the complete handoff. Please retain this save; no further copies will be made.");return;}
 if(!GetLocalInt(pc,"AWX_WARNED")){SetLocalInt(pc,"AWX_WARNED",TRUE);SendMessageToPC(pc,"The items are held safely while I wait for storage space.");}return;}
 if(phase==3){if(GetIsObjectValid(staged)){SetLocalInt(pc,"AWX_PHASE",-1);SendMessageToPC(pc,"The handoff could not be finalized. Please retain this save.");return;}
 // Delivery was verified in phase 2. The owner may already have used or equipped it.
 DestroyObject(escrow);AWXFinish(pc,GetLocalString(pc,"AWX_RESULT"),TRUE);}}
int AWXBegin(object pc,object body,object item,object src,object dest,string result,int amount=0){if(GetLocalInt(pc,"AWX_PHASE") || !GetIsObjectValid(dest) || !AWCItemSafe(item,src))return FALSE;
 int originalCount=GetItemStackSize(item);if(amount==0)amount=originalCount;if(amount<1 || amount>originalCount)return FALSE;
 object escrow=CreateObject(OBJECT_TYPE_STORE,"aw_escrow",GetLocation(pc));if(!GetIsObjectValid(escrow))return FALSE;
 object staged=CopyItem(item,escrow,TRUE);if(!GetIsObjectValid(staged) || GetItemPossessor(staged,TRUE)!=escrow || GetItemStackSize(staged)!=GetItemStackSize(item)){if(GetIsObjectValid(staged))DestroyObject(staged);DestroyObject(escrow);return FALSE;}
 SetItemStackSize(staged,amount);if(GetItemStackSize(staged)!=amount){DestroyObject(staged);DestroyObject(escrow);return FALSE;}if(GetObjectType(src)!=OBJECT_TYPE_CREATURE)SetDroppableFlag(staged,TRUE);SetLocalInt(pc,"AWX_SOURCE_REMAINING",originalCount-amount);SetLocalInt(pc,"AWX_SOURCE_ORIGINAL",originalCount);
 SetLocalObject(pc,"AWX_ORIGINAL",item);SetLocalObject(pc,"AWX_STAGED",staged);SetLocalObject(pc,"AWX_ESCROW",escrow);SetLocalObject(pc,"AWX_SOURCE",src);SetLocalObject(pc,"AWX_DEST",dest);SetLocalObject(pc,"AWX_BODY",body);
 SetLocalString(pc,"AWX_TAG",GetTag(item));SetLocalString(pc,"AWX_RES",GetResRef(item));SetLocalInt(pc,"AWX_AMOUNT",amount);SetLocalString(pc,"AWX_ID",GetIsObjectValid(body)?AWCIdentity(pc,body):"");SetLocalString(pc,"AWX_RESULT",result);DeleteLocalInt(pc,"AWX_WARNED");
 SetLocalInt(pc,"AWX_SRC_LOCK",GetObjectType(src)==OBJECT_TYPE_PLACEABLE?GetLocked(src):FALSE);SetLocalInt(pc,"AWX_DST_LOCK",GetObjectType(dest)==OBJECT_TYPE_PLACEABLE?GetLocked(dest):FALSE);
 if(GetObjectType(src)==OBJECT_TYPE_PLACEABLE)SetLocked(src,TRUE);if(GetObjectType(dest)==OBJECT_TYPE_PLACEABLE)SetLocked(dest,TRUE);
 SetLocalInt(pc,"AWX_PHASE",1);SetLocalInt(pc,"AWT_TRANSFER_PENDING",TRUE);SetLocalInt(pc,"AWT_TRANSFER_EXPIRES",AWMClock()+30);if(GetIsObjectValid(body))SetLocalInt(body,"AWT_PHASE",5);if(amount==originalCount)DestroyObject(item);else SetItemStackSize(item,originalCount-amount);return TRUE;}

