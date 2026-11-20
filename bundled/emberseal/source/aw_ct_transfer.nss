// Arrival is checked on the companion; cargo survives an expiring associate.
#include "aw_cp_cargo"
int AWTItemMatches(object item,string query){string name=GetStringLowerCase(GetName(item));if(name==query || FindSubString(name,query)>=0)return TRUE;
 if(query=="healing potion" || query=="potion of healing"){json items=AWItems();int i=0;while(i<JsonGetLength(items)){json entry=JsonArrayGet(items,i);if(GetTag(item)==AWText(entry,"id") && AWText(entry,"kind")=="healing_potion")return TRUE;i++;}}return FALSE;}
void main(){object body=OBJECT_SELF;object pc=GetLocalObject(body,"AWT_OWNER");object chest=GetLocalObject(body,"AWT_TARGET");string kind=GetLocalString(body,"AWT_KIND");
 if(GetLocalInt(body,"AWT_PHASE")==5)return;
 if(!AWTBase(pc,body) || !AWTPermitted(pc,body,kind) || !AWTChest(body,chest) || GetDistanceBetween(body,chest)>3.0)return;
 if(GetLocalInt(pc,"AWC_TRANSFER_PENDING") || GetLocalInt(pc,"AWT_TRANSFER_PENDING") || GetLocalInt(pc,"AWX_PHASE")){AWTFinish(pc,body,"Please finish the other handoff first.");return;}
 object src=kind=="take"?chest:pc;object dest=kind=="take"?AWCPersistentPack(pc,AWCIdentity(pc,body),GetName(body),TRUE):chest;string query=GetStringLowerCase(GetLocalString(body,"AWT_ITEM_QUERY"));object item=GetFirstItemInInventory(src);object chosen=OBJECT_INVALID;int matches=0;int scan=0;
 while(GetIsObjectValid(item) && scan<2048){if(query!="" && GetIdentified(item) && GetItemPossessor(item,TRUE)==src && AWTItemMatches(item,query)){chosen=item;matches++;}item=GetNextItemInInventory(src);scan++;}
 if(matches!=1){AWTFinish(pc,body,matches>1?"More than one item matches. Tell me the exact name of the one you want.":"I could not find that item among the accessible belongings. Ask me to inspect the container for its item names.");return;}
 if(!AWCItemSafe(chosen,src)){AWTFinish(pc,body,"I cannot move "+GetName(chosen)+": "+AWCItemLock(chosen,src)+".");return;}
 int amount=GetLocalString(body,"AWT_QUANTITY")=="all"?GetItemStackSize(chosen):1;
 string result=kind=="take"?"I collected "+GetName(chosen)+" x"+IntToString(amount)+" in my pack.":"I placed "+GetName(chosen)+" x"+IntToString(amount)+" in "+GetName(chest)+".";
 if(!AWXBegin(pc,body,chosen,src,dest,result,amount)){AWTFinish(pc,body,"I could not arrange safe storage. The requested items have not been moved.");SendMessageToPC(pc,"The companion could not arrange safe storage; no items were moved.");}}

