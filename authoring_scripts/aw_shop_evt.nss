#include "aw_merchant"
void main(){object pc=NuiGetEventPlayer();int token=NuiGetEventWindow();if(!GetIsPC(pc) || token!=GetLocalInt(pc,"AWM_TOKEN") || GetLocalString(pc,"AWM_SESSION")!=GetLocalString(GetModule(),"AWM_SESSION"))return;
 string kind=NuiGetEventType();if(kind=="close"){DeleteLocalInt(pc,"AWM_TOKEN");DeleteLocalObject(pc,"AWM_ACTOR");return;}if(kind!="click")return;
 object actor=GetLocalObject(pc,"AWM_ACTOR");if(!AWMNear(pc,actor)){AWMClose(pc);return;}
 string element=NuiGetEventElement();string prefix=IntToString(GetLocalInt(pc,"AWM_GEN"))+"_";
 if(element=="close_"+prefix){AWMClose(pc);return;}
 if(element=="refresh_"+prefix){AWMOpen(pc,actor);return;}
 if(element=="haggle_"+prefix){AWMOpen(pc,actor,TRUE);return;}
 json stock=JsonObjectGet(AWMShop(actor),"stock");int i=0;while(i<JsonGetLength(stock)){if(element=="buy_"+prefix+IntToString(i)){AWMBuy(pc,actor,i);return;}i++;}}
