#include "aw_cp_cargo"
void main(){object pc=OBJECT_SELF;object storage=GetLocalObject(pc,"AWC_STORAGE");object item=GetLocalObject(pc,"AWG_REQUEST_ITEM");DeleteLocalObject(pc,"AWG_REQUEST_ITEM");if(!AWGReady(pc,storage) || !GetIsObjectValid(item))return;int side=GetLocalInt(pc,"AWG_REQUEST_SIDE");object src=GetItemPossessor(item,TRUE);object body=GetLocalObject(pc,"AWC_GRID_BODY");object dest=side?pc:storage;
 if((!side && src!=pc) || (side && src!=storage && (!GetIsObjectValid(body) || src!=body || AWCOwner(body)!=pc)))return;
 if(!AWCItemSafe(item,src)){NuiSetBind(pc,GetLocalInt(pc,"AWC_TOKEN"),"aw_grid_info",JsonString(GetName(item)+": "+AWCItemLock(item,src)));return;}
 int amount=GetLocalInt(pc,"AWG_REQUEST_ONE")?1:GetItemStackSize(item);string result="Transferred "+GetName(item)+" x"+IntToString(amount)+(side?" to your belongings.":" to companion storage.");
 if(AWXBegin(pc,OBJECT_INVALID,item,src,dest,result,amount)){SetLocalString(pc,"AWX_ID",GetLocalString(storage,"AWC_PACK_ID"));NuiSetBind(pc,GetLocalInt(pc,"AWC_TOKEN"),"aw_grid_info",JsonString("Transferring items. The panel will refresh after confirmation."));}}
