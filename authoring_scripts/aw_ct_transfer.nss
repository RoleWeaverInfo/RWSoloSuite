// A nearby owner receives/deposits the original item; no temporary summon cargo.
#include "aw_cp_ui"
int AWTItemMatches(object item,string query){string name=GetStringLowerCase(GetName(item));if(name==query || FindSubString(name,query)>=0)return TRUE;
 if(query=="healing potion" || query=="potion of healing"){json items=AWItems();int i=0;while(i<JsonGetLength(items)){json entry=JsonArrayGet(items,i);if(GetTag(item)==AWText(entry,"id") && AWText(entry,"kind")=="healing_potion")return TRUE;i++;}}return FALSE;}
void main(){object body=OBJECT_SELF;object pc=GetLocalObject(body,"AWT_OWNER");object chest=GetLocalObject(body,"AWT_TARGET");string kind=GetLocalString(body,"AWT_KIND");
 if(GetLocalInt(body,"AWT_PHASE")==5){
 object item=GetLocalObject(body,"AWT_ITEM");object dest=GetLocalObject(body,"AWT_ITEM_TO");object src=GetLocalObject(body,"AWT_ITEM_FROM");
 string tag=GetLocalString(body,"AWT_ITEM_TAG");string res=GetLocalString(body,"AWT_ITEM_RES");int amount=GetLocalInt(body,"AWT_ITEM_COUNT");
 int merged=!GetIsObjectValid(item) && AWCCount(dest,tag,res)>=GetLocalInt(body,"AWT_ITEM_BEFORE")+amount && AWCCount(src,tag,res)<=GetLocalInt(body,"AWT_ITEM_SOURCE")-amount;
 if((GetIsObjectValid(item) && GetItemPossessor(item,TRUE)==dest) || merged){DeleteLocalInt(pc,"AWT_TRANSFER_PENDING");SetLocalString(body,"AWT_RESULT",kind=="take"?"I handed you the requested item from the container.":"I put your requested item in the container.");SetLocalInt(body,"AWT_PHASE",4);return;}
 if(AWMClock()>=GetLocalInt(body,"AWT_ITEM_DEADLINE")){DeleteLocalInt(pc,"AWT_TRANSFER_PENDING");AWTFinish(pc,body,"I could not confirm the handoff. Please check your belongings and the container before asking again.");}return;}
 if(!AWTBase(pc,body) || !AWTPermitted(pc,body,kind) || !AWTChest(body,chest) || GetDistanceBetween(body,chest)>3.0)return;
 if(GetDistanceBetween(pc,chest)>3.0 || !LineOfSightObject(pc,chest)){AWTFinish(pc,body,"Come closer to the container so I can hand the items directly to you, or take them from you.");return;}
 if(GetLocalInt(pc,"AWC_TRANSFER_PENDING") || GetLocalInt(pc,"AWT_TRANSFER_PENDING")){AWTFinish(pc,body,"Please finish the other handoff first.");return;}
 object src=kind=="take"?chest:pc;object dest=kind=="take"?pc:chest;string query=GetStringLowerCase(GetLocalString(body,"AWT_ITEM_QUERY"));object item=GetFirstItemInInventory(src);object chosen=OBJECT_INVALID;int matches=0;int scan=0;
 while(GetIsObjectValid(item) && scan<2048){if(query!="" && GetIdentified(item) && GetItemPossessor(item,TRUE)==src && AWTItemMatches(item,query)){chosen=item;matches++;}item=GetNextItemInInventory(src);scan++;}
 if(matches!=1){AWTFinish(pc,body,matches>1?"More than one item matches. Tell me the exact name of the one you want.":"I could not find that item among the accessible belongings. Ask me to inspect the container for its item names.");return;}
 if(!AWCItemSafe(chosen,src)){AWTFinish(pc,body,"I cannot safely move that item. You may need to handle it yourself.");return;}
 if(GetLocalString(body,"AWT_QUANTITY")!="all" && GetItemStackSize(chosen)!=1){AWTFinish(pc,body,"Those items are bundled together. Ask for the whole stack, or separate one yourself.");return;}
 SetLocalObject(body,"AWT_ITEM",chosen);SetLocalObject(body,"AWT_ITEM_FROM",src);SetLocalObject(body,"AWT_ITEM_TO",dest);SetLocalString(body,"AWT_ITEM_TAG",GetTag(chosen));SetLocalString(body,"AWT_ITEM_RES",GetResRef(chosen));SetLocalInt(body,"AWT_ITEM_COUNT",GetItemStackSize(chosen));SetLocalInt(body,"AWT_ITEM_BEFORE",AWCCount(dest,GetTag(chosen),GetResRef(chosen)));SetLocalInt(body,"AWT_ITEM_SOURCE",AWCCount(src,GetTag(chosen),GetResRef(chosen)));SetLocalInt(body,"AWT_ITEM_DEADLINE",AWMClock()+18);SetLocalInt(body,"AWT_PHASE",5);SetLocalInt(pc,"AWT_TRANSFER_PENDING",TRUE);SetLocalInt(pc,"AWT_TRANSFER_EXPIRES",AWMClock()+18);
 AssignCommand(pc,ClearAllActions(TRUE));if(kind=="take")AssignCommand(pc,ActionTakeItem(chosen,chest));else AssignCommand(pc,ActionGiveItem(chosen,chest));}
