#include "aw_cp_ui"
void main(){object pc=NuiGetEventPlayer();if(!GetIsPC(pc) || NuiGetEventWindow()!=GetLocalInt(pc,"AWC_TOKEN") || GetLocalString(pc,"AWC_UI_SESSION")!=GetLocalString(GetModule(),"AWM_SESSION"))return;
 if(NuiGetEventType()=="close"){DeleteLocalInt(pc,"AWC_TOKEN");return;}if(NuiGetEventType()!="click")return;
 string suffix="_"+IntToString(GetLocalInt(pc,"AWC_UI_GEN"));string id=NuiGetEventElement();string view=GetLocalString(pc,"AWC_VIEW");object body=GetLocalObject(pc,"AWC_UI_ACTOR");
 if(id=="close"+suffix){AWCUIClose(pc);return;}if(id=="back"+suffix){AWCOpenList(pc);return;}if(id=="recover"+suffix){AWCOpenRecover(pc);return;}
 if(view=="list"){if(id=="previous"+suffix){SetLocalInt(pc,"AWC_LIST_PAGE",GetLocalInt(pc,"AWC_LIST_PAGE")-1);AWCOpenList(pc);return;}if(id=="next"+suffix){SetLocalInt(pc,"AWC_LIST_PAGE",GetLocalInt(pc,"AWC_LIST_PAGE")+1);AWCOpenList(pc);return;}
 int i=0;while(i<GetLocalInt(pc,"AWC_ROWS")){if(id=="actor"+IntToString(i)+suffix){AWCOpenControl(pc,GetLocalObject(pc,"AWC_ROW_"+IntToString(i)));return;}i++;}return;}
 if(view=="recover"){int i=0;while(i<GetLocalInt(pc,"AWC_PACK_ROWS")){if(id=="bag"+IntToString(i)+suffix){SetLocalInt(pc,"AWC_PACK_PAGE",0);SetLocalInt(pc,"AWC_GIVING",FALSE);AWCOpenPack(pc,GetLocalObject(pc,"AWC_PACK_ROW_"+IntToString(i)));return;}i++;}return;}
 if(view=="pack"){object storage=GetLocalObject(pc,"AWC_STORAGE");if(!AWCPackReady(pc,storage)){AWCUIClose(pc);return;}
 if(id=="discard_empty"+suffix){if(AWCPackOwned(pc,storage) && !GetIsObjectValid(GetFirstItemInInventory(storage)) && !GetLocalInt(pc,"AWC_TRANSFER_PENDING")){DestroyObject(storage);AWCOpenRecover(pc);}return;}
 if(id=="pack_previous"+suffix)SetLocalInt(pc,"AWC_PACK_PAGE",GetLocalInt(pc,"AWC_PACK_PAGE")-1);
 else if(id=="pack_next"+suffix)SetLocalInt(pc,"AWC_PACK_PAGE",GetLocalInt(pc,"AWC_PACK_PAGE")+1);
 else if(id=="pack_side"+suffix){SetLocalInt(pc,"AWC_GIVING",!GetLocalInt(pc,"AWC_GIVING"));SetLocalInt(pc,"AWC_PACK_PAGE",0);}
 else if(id!="pack_refresh"+suffix){int i=0;while(i<GetLocalInt(pc,"AWC_ITEMS")){if(id=="item"+IntToString(i)+suffix){AWCTransfer(pc,storage,GetLocalObject(pc,"AWC_ITEM_"+IntToString(i)));return;}i++;}return;}
 AWCOpenPack(pc,storage);return;}
 if(view!="control" || !AWCReady(pc,body,FALSE) || !AWCObserve(pc,body)){AWCUIClose(pc);return;}string identity=AWCIdentity(pc,body);json record=AWCRecord(pc,identity);
 if(id=="chat"+suffix){if(!AWInt(AWCCfg(),"live_ai") || !AWCAIReady(pc,body))return;SetLocalObject(pc,"SP_FOCUS",body);SetLocalInt(pc,"AWC_CHAT_ARMED",TRUE);AWCUIClose(pc);SendMessageToPC(pc,"Speak normally in Talk. Use !end to finish this companion conversation.");return;}
 if(id=="toggle_ai"+suffix)AWCSet(pc,identity,"ai",!AWInt(record,"ai"));
 else if(id=="toggle_move"+suffix)AWCSet(pc,identity,"movement",!AWInt(record,"movement"));
 else if(id=="toggle_pack"+suffix)AWCSet(pc,identity,"inventory",!AWInt(record,"inventory"));
 else if(id=="reply"+suffix)AWCSet(pc,identity,"reply",(AWInt(record,"reply")+1)%3);
 else if(id=="tone"+suffix)AWCSet(pc,identity,"tone",(AWInt(record,"tone")+1)%5);
 else if(id=="inventory"+suffix){AWCInventory(pc,body);return;}
 else if(id=="recruit"+suffix)AWCOrder(pc,body,"recruit");
 else if(id=="dismiss"+suffix){AWCOrder(pc,body,"dismiss");AWCOpenList(pc);return;}
 else if(id=="follow"+suffix)AWCOrder(pc,body,"follow");
 else if(id=="stay"+suffix)AWCOrder(pc,body,"stay");
 else if(id=="guard"+suffix)AWCOrder(pc,body,"guard");
 AWCOpenControl(pc,body);}
