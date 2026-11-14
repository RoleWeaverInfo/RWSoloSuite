// Bounded authored movement; no creature heartbeat or combat script replacement.
#include "aw_cp_ui"
json AWACfg(){return JsonArrayGet(AWAConfig(),0);}
json AWAPolicy(object body){return AWFind(AWABehaviors(),GetTag(body));}
int AWAActor(object body){return GetIsObjectValid(body) && GetObjectType(body)==OBJECT_TYPE_CREATURE && !GetIsPC(body) && !GetIsDM(body) && !GetIsDMPossessed(body) && !GetIsPossessedFamiliar(body) && !GetIsDead(body) && !GetIsObjectValid(GetMaster(body)) && GetResRef(body)==AWText(AWAPolicy(body),"id");}
int AWASafe(object body){if(GetLocalString(body,"AWA_VISIT_LOCK")!="" || !AWAActor(body) || !GetCommandable(body) || GetIsInCombat(body) || IsInConversation(body) || AWMClock()<GetLocalInt(body,"AWA_HOLD"))return FALSE;
 object pc=GetFirstPC();while(GetIsObjectValid(pc)){if(IsInConversation(pc) && GetArea(pc)==GetArea(body) && GetDistanceBetween(pc,body)<12.0)return FALSE;if(GetLocalInt(pc,"AWM_TOKEN") && GetLocalObject(pc,"AWM_ACTOR")==body)return FALSE;pc=GetNextPC();}return TRUE;}
void AWAStop(object body){if(GetLocalInt(body,"AWA_MOVING") && AWAActor(body) && GetCommandable(body) && !GetIsInCombat(body) && !IsInConversation(body) && GetCurrentAction(body)==ACTION_MOVETOPOINT)AssignCommand(body,ClearAllActions(TRUE));DeleteLocalInt(body,"AWA_MOVING");}
void AWATouch(object body){if(!GetIsObjectValid(body))return;SetLocalInt(body,"AWA_EPOCH",GetLocalInt(body,"AWA_EPOCH")+1);SetLocalInt(body,"AWA_HOLD",AWMClock()+30);AWAStop(body);}
int AWANearPlayer(object body){object pc=GetFirstPC();while(GetIsObjectValid(pc)){if(!GetIsDead(pc) && GetArea(pc)==GetArea(body) && GetDistanceBetween(pc,body)<=45.0)return TRUE;pc=GetNextPC();}return FALSE;}
void AWALoad(){DeleteLocalString(GetModule(),"AWS_PENDING");DeleteLocalInt(GetModule(),"AWS_STAGE");json all=AWABehaviors();int i=0;while(i<JsonGetLength(all)){json b=JsonArrayGet(all,i);object body=GetObjectByTag(AWText(b,"id"));DeleteLocalInt(body,"AWA_SOCIAL_LOCK");
 if(AWAActor(body) && ((AWInt(AWACfg(),"patrols") && AWInt(b,"patrol_enabled")) || (AWInt(AWACfg(),"social") && AWInt(b,"social_enabled")) || AWInt(b,"accept_visits"))){
 string base=GetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DIALOGUE);if(base!="aw_am_dialog" && base!="aw_cp_dialog"){SetLocalString(body,"AWA_BASE_DIALOG",base);SetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DIALOGUE,"aw_am_dialog");}
 base=GetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DEATH);if(base!="aw_am_dead" && base!="aw_cp_dead"){SetLocalString(body,"AWA_BASE_DEATH",base);SetEventScript(body,EVENT_SCRIPT_CREATURE_ON_DEATH,"aw_am_dead");}}
 i++;}}
void AWAPatrol(object body){json p=AWAPolicy(body);if(!AWInt(AWACfg(),"patrols") || !AWInt(p,"patrol_enabled"))return;
 if(!AWAActor(body)){DeleteLocalInt(body,"AWA_MOVING");return;}if(!AWASafe(body)){AWAStop(body);return;}
 if(!AWANearPlayer(body) || GetLocalInt(body,"AWA_SOCIAL_LOCK"))return;
 json route=JsonObjectGet(p,"route");int count=JsonGetLength(route);if(count<2)return;int index=GetLocalInt(body,"AWA_STOP");if(index<0 || index>=count)index=0;
 string room=JsonGetString(JsonArrayGet(route,index));json r=AWFind(AWRooms(),room);if(AWText(r,"area")!=GetTag(GetArea(body)))return;
 vector pos=Vector(IntToFloat(AWInt(r,"x")*10+AWInt(r,"width")*5),IntToFloat(AWInt(r,"y")*10+AWInt(r,"height")*5),0.0);location destination=Location(GetArea(body),pos,0.0);
 if(GetDistanceBetweenLocations(GetLocation(body),destination)<=2.5){AWAStop(body);int direction=GetLocalInt(body,"AWA_DIRECTION");if(direction==0)direction=1;
 if(AWText(p,"mode")=="pingpong"){if(index==count-1)direction=-1;else if(index==0)direction=1;index+=direction;}else index=(index+1)%count;
 SetLocalInt(body,"AWA_DIRECTION",direction);SetLocalInt(body,"AWA_STOP",index);SetLocalInt(body,"AWA_WAIT",AWMClock()+AWInt(p,"wait_seconds"));SetLocalString(body,"AWA_STATUS","Arrived at "+room);return;}
 if(GetLocalInt(body,"AWA_MOVING")){if(AWMClock()-GetLocalInt(body,"AWA_STARTED")>=120 || (GetCurrentAction(body)==ACTION_INVALID && AWMClock()-GetLocalInt(body,"AWA_STARTED")>=6)){AWAStop(body);SetLocalInt(body,"AWA_WAIT",AWMClock()+60);SetLocalString(body,"AWA_STATUS","Route blocked or timed out; waiting before retry.");}return;}
 if(AWMClock()<GetLocalInt(body,"AWA_WAIT") || GetCurrentAction(body)!=ACTION_INVALID)return;
 SetLocalInt(body,"AWA_MOVING",TRUE);SetLocalInt(body,"AWA_STARTED",AWMClock());SetLocalString(body,"AWA_STATUS","Walking to "+room);AssignCommand(body,ActionMoveToLocation(destination,AWInt(p,"run")));}
void AWATick(){json all=AWABehaviors();int i=0;while(i<JsonGetLength(all)){AWAPatrol(GetObjectByTag(AWText(JsonArrayGet(all,i),"id")));i++;}}
