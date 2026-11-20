#include "aw_ambient"
void AWAIAction(object pc,string npc,string verb){
if(verb=="")return;
if(GetIsDead(pc) || GetIsInCombat(pc))return;
object actor=GetObjectByTag(npc);if(!GetIsObjectValid(actor) || GetIsDead(actor) || GetIsInCombat(actor) || GetIsDMPossessed(actor))return;
if(GetArea(pc)!=GetArea(actor) || GetDistanceBetween(pc,actor)>12.0 || !LineOfSightObject(pc,actor))return;
if(verb=="start:pursuit" && npc=="elowen" && AQState("pursuit")==0 && AQReady(AWFind(AWQuests(),"pursuit"))){AQStart(pc,npc);return;}
if(verb=="talk:homecoming:2" && npc=="elowen" && AQState("homecoming")==2){AQAdvance(pc,"homecoming",2,"");return;}
SendMessageToPC(pc,"The story changed while this reply was pending. Continue the conversation to choose your next action.");}
