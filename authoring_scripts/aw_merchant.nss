// Native, finite-stock merchant. No NWNX or external payment commands.
#include "aw_quest"
#include "aw_ui"

json AWMShop(object actor){return AWFind(AWShops(),GetTag(actor));}
int AWMClock(){return GetLocalInt(GetModule(),"AWM_CLOCK");}
int AWMNear(object pc,object actor){return GetIsPC(pc) && GetIsObjectValid(actor) && !GetIsDead(pc) && !GetIsDead(actor) && !GetIsInCombat(pc) && !GetIsInCombat(actor) && !GetIsDMPossessed(actor) && GetArea(pc)==GetArea(actor) && GetDistanceBetween(pc,actor)<=6.0 && LineOfSightObject(pc,actor);}
object AWMItem(object actor,string tag){object item=GetFirstItemInInventory(actor);while(GetIsObjectValid(item)){if(GetTag(item)==tag && !GetLocalInt(item,"AWM_SOLD"))return item;item=GetNextItemInInventory(actor);}return OBJECT_INVALID;}
int AWMQuantity(object actor,string tag){int qty=0;object item=GetFirstItemInInventory(actor);while(GetIsObjectValid(item)){if(GetTag(item)==tag && !GetLocalInt(item,"AWM_SOLD"))qty+=GetItemStackSize(item);item=GetNextItemInInventory(actor);}return qty;}
int AWMDiscount(object pc,object actor){string id=GetTag(actor);if(GetLocalInt(pc,"AWM_EXP_"+id)<=AWMClock())return 0;return GetLocalInt(pc,"AWM_DISC_"+id);}
int AWMPrice(object pc,object actor,json sku){int price=AWInt(sku,"price")*(100-AWMDiscount(pc,actor))/100;if(price<1)price=1;return price;}
json AWMContext(object pc,object actor){json shop=AWMShop(actor);json out=JsonObject();if(AWText(shop,"id")=="")return out;
 out=JsonObjectSet(out,"npc",JsonString(GetTag(actor)));out=JsonObjectSet(out,"available",JsonInt(AWMNear(pc,actor)));json items=JsonArray();json stock=JsonObjectGet(shop,"stock");int i=0;
 while(i<JsonGetLength(stock)){json sku=JsonArrayGet(stock,i);json row=JsonObject();row=JsonObjectSet(row,"item",JsonString(AWText(sku,"item")));row=JsonObjectSet(row,"quantity",JsonInt(AWMQuantity(actor,AWText(sku,"tag"))));row=JsonObjectSet(row,"price",JsonInt(AWMPrice(pc,actor,sku)));items=JsonArrayInsert(items,row);i++;}
 out=JsonObjectSet(out,"items",items);out=JsonObjectSet(out,"haggle_available",JsonInt(AWInt(shop,"haggle_enabled")));return out;}
string AWMVersion(object pc,object actor){return JsonDump(AWMContext(pc,actor));}
void AWMClose(object pc){int token=GetLocalInt(pc,"AWM_TOKEN");DeleteLocalInt(pc,"AWM_TOKEN");DeleteLocalObject(pc,"AWM_ACTOR");if(token && GetLocalString(pc,"AWM_SESSION")==GetLocalString(GetModule(),"AWM_SESSION"))NuiDestroy(pc,token);}
void AWMHaggle(object pc,object actor,json shop){string id=GetTag(actor);if(!AWInt(shop,"haggle_enabled")){SendMessageToPC(pc,"This merchant does not haggle.");return;}
 if(GetLocalInt(pc,"AWM_EXP_"+id)>AWMClock()){SendMessageToPC(pc,"Your previous offer still applies. Discounts never stack.");return;}
 int roll=Random(100)+1;int discount=0;if(roll<=AWInt(shop,"haggle_chance"))discount=AWInt(shop,"discount_percent");
 SetLocalInt(pc,"AWM_EXP_"+id,AWMClock()+AWInt(shop,"offer_seconds"));SetLocalInt(pc,"AWM_DISC_"+id,discount);
 SendMessageToPC(pc,"Haggle roll "+IntToString(roll)+" / "+IntToString(AWInt(shop,"haggle_chance"))+": "+IntToString(discount)+"% discount. This result lasts "+IntToString(AWInt(shop,"offer_seconds"))+" active game seconds.");}
void AWMOpen(object pc,object actor,int haggle=FALSE){json shop=AWMShop(actor);if(AWText(shop,"id")=="" || !AWMNear(pc,actor)){SendMessageToPC(pc,"Stand within six metres of the merchant, visible and out of combat.");return;}
 AWMClose(pc);if(haggle)AWMHaggle(pc,actor,shop);
 SetLocalString(pc,"AWM_SESSION",GetLocalString(GetModule(),"AWM_SESSION"));
 int gen=GetLocalInt(pc,"AWM_GEN")+1;SetLocalInt(pc,"AWM_GEN",gen);string prefix=IntToString(gen)+"_";
 SetLocalObject(pc,"AWM_ACTOR",actor);SetLocalInt(pc,"AWM_PANEL_EXP",AWMClock()+120);
 json rows=JsonArray();rows=JsonArrayInsert(rows,AWUIHeight(AWUILabel(JsonString(GetName(actor)+" | Your gold: "+IntToString(GetGold(pc))),JsonInt(1),JsonInt(0)),30.0));
 rows=JsonArrayInsert(rows,AWUIHeight(AWUILabel(JsonString("Buy one item per click. The displayed price is the exact cost."),JsonInt(1),JsonInt(0)),26.0));
 rows=JsonArrayInsert(rows,AWUIHeight(AWUILabel(JsonString("Current discount: "+IntToString(AWMDiscount(pc,actor))+"%. Stock is finite."),JsonInt(1),JsonInt(0)),26.0));
 json stock=JsonObjectGet(shop,"stock");int i=0;while(i<JsonGetLength(stock)){json sku=JsonArrayGet(stock,i);int qty=AWMQuantity(actor,AWText(sku,"tag"));int price=AWMPrice(pc,actor,sku);SetLocalInt(pc,"AWM_QUOTE_"+IntToString(i),price);
 string label="Buy "+AWText(sku,"name")+" | "+IntToString(price)+" gold | "+IntToString(qty)+" left";
 rows=JsonArrayInsert(rows,AWUIHeight(AWUIEnabled(AWUIId(AWUIButton(JsonString(label)),"buy_"+prefix+IntToString(i)),JsonBool(qty>0)),36.0));i++;}
 json buttons=JsonArray();buttons=JsonArrayInsert(buttons,AWUIId(AWUIButton(JsonString("Refresh")),"refresh_"+prefix));
 if(AWInt(shop,"haggle_enabled"))buttons=JsonArrayInsert(buttons,AWUIId(AWUIButton(JsonString("Negotiate price")),"haggle_"+prefix));
 buttons=JsonArrayInsert(buttons,AWUIId(AWUIButton(JsonString("Close")),"close_"+prefix));rows=JsonArrayInsert(rows,AWUIRow(buttons));
 json window=AWUIWindow(AWUIScroll(AWUIStack(rows,550.0)),JsonString("Merchant goods - scroll for all stock"),AWUIRect(-1.0,-1.0,620.0,520.0),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE),JsonBool(FALSE),JsonBool(TRUE));
 int token=NuiCreate(pc,window,"aw_shop_"+IntToString(gen),"aw_shop_evt");SetLocalInt(pc,"AWM_TOKEN",token);if(!token){DeleteLocalObject(pc,"AWM_ACTOR");SendMessageToPC(pc,"The goods panel could not open. Try again after closing another window.");}}
void AWMBuy(object pc,object actor,int index){if(!AWMNear(pc,actor) || GetLocalInt(pc,"AWM_PANEL_EXP")<=AWMClock()){AWMClose(pc);SendMessageToPC(pc,"This shop offer expired or you moved away. Reopen the goods panel.");return;}
 json stock=JsonObjectGet(AWMShop(actor),"stock");if(index<0 || index>=JsonGetLength(stock))return;json sku=JsonArrayGet(stock,index);int price=AWMPrice(pc,actor,sku);
 if(GetLocalInt(pc,"AWM_QUOTE_"+IntToString(index))!=price){SendMessageToPC(pc,"The price changed. Review the refreshed panel before buying.");AWMOpen(pc,actor);return;}
 object item=AWMItem(actor,AWText(sku,"tag"));if(!GetIsObjectValid(item)){SendMessageToPC(pc,"That item is sold out.");AWMOpen(pc,actor);return;}
 if(GetGold(pc)<price){SendMessageToPC(pc,"You do not have enough gold. Nothing was purchased.");return;}
 // Reserve the exact stock object before copying; queued duplicate clicks cannot sell it twice.
 SetLocalInt(item,"AWM_SOLD",TRUE);
 // CopyItem can return an existing merged stack. Split ONE unit in an empty
 // temporary store first; never resize the returned player-inventory object.
 object escrow=CreateObject(OBJECT_TYPE_STORE,"aw_escrow",GetLocation(actor));
 if(!GetIsObjectValid(escrow)){DeleteLocalInt(item,"AWM_SOLD");SendMessageToPC(pc,"Item transfer is unavailable. No gold was taken.");return;}
 object unit=CopyItem(item,escrow,FALSE);if(!GetIsObjectValid(unit)){DestroyObject(escrow);DeleteLocalInt(item,"AWM_SOLD");return;}
 SetItemStackSize(unit,1);object delivered=CopyItem(unit,pc,FALSE);DestroyObject(unit);DestroyObject(escrow);
 if(!GetIsObjectValid(delivered)){DeleteLocalInt(item,"AWM_SOLD");SendMessageToPC(pc,"The item could not be delivered. No gold was taken.");return;}
 int count=GetItemStackSize(item);TakeGoldFromCreature(price,pc,TRUE);GiveGoldToCreature(actor,price);
 if(count>1){SetItemStackSize(item,count-1);DeleteLocalInt(item,"AWM_SOLD");}else DestroyObject(item);
 SendMessageToPC(pc,"PURCHASE CONFIRMED: "+AWText(sku,"name")+" for "+IntToString(price)+" gold.");AWMOpen(pc,actor);}
