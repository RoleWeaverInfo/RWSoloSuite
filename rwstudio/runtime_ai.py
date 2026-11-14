"""Format-2 native chat and merchant adapters; legacy courier scripts stay intact."""
from collections import defaultdict

def adapt(inc,npcs,literal):
    def replace(old,new):
        nonlocal inc
        if inc.count(old)!=1:raise ValueError('Native AI adapter source changed: '+old[:60])
        inc=inc.replace(old,new)
    replace('j=JsonObjectSet(j,"has_satchel",JsonBool(FALSE));',
            'j=JsonObjectSet(j,"has_satchel",JsonBool(FALSE)); j=JsonObjectSet(j,"merchant",AWMContext(pc,GetLocalObject(pc,"SP_FOCUS"))); j=JsonObjectSet(j,"actor_uuid",JsonString(GetObjectUUID(GetLocalObject(pc,"SP_FOCUS"))));j=JsonObjectSet(j,"companion",AWCContext(pc,GetLocalObject(pc,"SP_FOCUS")));')
    replace('void SPAsk(object pc,string kind,string message)',r'''void SPEnd(object pc,int notify=TRUE){
 string id=GetLocalString(pc,"SP_PENDING");if(id!=""){sqlquery cancel=SqlPrepareQueryCampaign(SPDB,"UPDATE sp_requests SET state='expired' WHERE request_id=@i AND session_id=@s AND state IN ('queued','working')");SqlBindString(cancel,"@i",id);SqlBindString(cancel,"@s",SPSession());SqlStep(cancel);}
 DeleteLocalString(pc,"SP_PENDING");DeleteLocalObject(pc,"SP_PENDING_ACTOR");DeleteLocalObject(pc,"SP_FOCUS");DeleteLocalInt(pc,"SP_FOCUS_AT");DeleteLocalInt(pc,"AWC_CHAT_ARMED");if(notify)SendMessageToPC(pc,"AI conversation ended. NPC menus remain available.");}
void SPAsk(object pc,string kind,string message)''')
    replace('    SPReset(pc);\n    SetLocalObject(GetModule(),"SP_CONTROLLER",pc);','    SPReset(pc);\n    if(kind=="npc" && AWTParse(pc,GetLocalObject(pc,"SP_FOCUS"),message)){SPEnd(pc,FALSE);return;}\n    SetLocalObject(GetModule(),"SP_CONTROLLER",pc);')
    replace('tag=GetTag(npc);','tag=GetTag(npc);if(AWCOwner(npc)==pc && (AWCKind(npc)=="familiar" || AWCKind(npc)=="summon")){kind="companion";tag=AWText(AWCPolicy(npc),"id");}')
    replace('if(!SPIsNPC(tag) || !SPNear(pc,npc))',
            'if((kind=="npc" && !SPIsNPC(tag)) || !SPNear(pc,npc) || !AWCAIReady(pc,npc) || (kind=="companion" && !AWCReady(pc,npc)))')
    replace('json p=JsonObject(); p=JsonObjectSet(p,"message",JsonString(GetStringLeft(message,1200)));',
            'if(kind=="npc" || kind=="companion"){AWATouch(npc);}if(kind=="npc" || kind=="companion")SetLocalInt(pc,"SP_FOCUS_AT",SPNow());\n    SetLocalString(pc,"AWM_REQUEST",AWMVersion(pc,npc));SetLocalString(pc,"AWC_PENDING_VERSION",AWCEnabled() && AWText(AWCPolicy(npc),"id")!=""?AWCVersion(pc,npc):"");SetLocalObject(pc,"SP_PENDING_ACTOR",npc);\n    json p=JsonObject(); p=JsonObjectSet(p,"message",JsonString(GetStringLeft(message,1200)));')
    replace('p=JsonObjectSet(p,"history",JsonString(GetLocalString(pc,"SP_HIST_"+tag)));',
            'p=JsonObjectSet(p,"history",JsonString(GetLocalString(pc,"AWC_PENDING_VERSION")!=""?AWText(AWCRecord(pc,AWCIdentity(pc,npc)),"history"):GetLocalString(pc,"SP_HIST_"+tag)));')
    replace('if(kind=="npc") {\n        object npc=GetObjectByTag(tag);','if(kind=="npc" || kind=="companion") {\n        object npc=GetLocalObject(pc,"SP_PENDING_ACTOR");')
    replace('SendMessageToPC(pc,GetName(npc)+": "+reply);',r'''if(AWText(AWMShop(npc),"id")!="" && GetLocalString(pc,"AWM_REQUEST")!=AWMVersion(pc,npc)){
 reply="My stock or prices changed while I was answering. Please reopen my goods panel for current information.";result=JsonObjectSet(result,"merchant_action",JsonString(""));}
        if(GetLocalString(pc,"AWC_PENDING_VERSION")!="" && (AWCVersion(pc,npc)!=GetLocalString(pc,"AWC_PENDING_VERSION") || !AWCAIReady(pc,npc) || IsInConversation(pc) || IsInConversation(npc))){SendMessageToPC(pc,"Companion control, ownership or preferences changed. The older AI reply was discarded.");return;}
        AWATouch(npc);if(state=="ready")AssignCommand(npc,SpeakString(AWCMode(npc)=="nonverbal"?"*"+reply+"*":reply,TALKVOLUME_TALK));else SendMessageToPC(pc,reply);''')
    replace('string history=GetLocalString(pc,"SP_HIST_"+tag)+"\\nPlayer: "+GetLocalString(pc,"SP_QUESTION")+"\\nNPC: "+reply;',
            'string history=(GetLocalString(pc,"AWC_PENDING_VERSION")!=""?AWText(AWCRecord(pc,AWCIdentity(pc,npc)),"history"):GetLocalString(pc,"SP_HIST_"+tag))+"\\nPlayer: "+GetLocalString(pc,"SP_QUESTION")+"\\nNPC: "+reply;')
    replace('SetLocalString(pc,"SP_HIST_"+tag,GetStringRight(history,6000));',
            'if(GetLocalString(pc,"AWC_PENDING_VERSION")!="")AWCHistorySet(pc,npc,history);else SetLocalString(pc,"SP_HIST_"+tag,GetStringRight(history,6000));')
    replace('AWAIAction(pc,tag,SPText(result,"story_action"));',
            'if(kind=="npc")AWAIAction(pc,tag,SPText(result,"story_action")); string shopVerb=SPText(result,"merchant_action");if(kind=="npc" && (shopVerb=="browse" || shopVerb=="haggle"))AWMOpen(pc,npc,shopVerb=="haggle");string cpVerb=SPText(result,"companion_action");if(cpVerb!="")AWCApply(pc,npc,cpVerb);')
    names=defaultdict(set)
    for n in npcs:
        if not n['ai_enabled']:continue
        for name in (n['alias'],n['name'].lower(),n['name'].lower().split()[0]):names[name].add(n['id'])
    resolver='string SPAddress(string name){'+''.join('if(name=='+literal(name)+')return '+literal(next(iter(ids)))+';' for name,ids in sorted(names.items()) if len(ids)==1)+'return "";}'
    chat='''#include "sp_inc"
'''+resolver+r'''
object SPActorAddress(object pc,string name){string tag=SPAddress(name);object fixed=tag==""?OBJECT_INVALID:GetObjectByTag(tag);object owned=AWCFind(pc,name);if(GetLocalInt(pc,"AWC_AMBIGUOUS") || (GetIsObjectValid(fixed) && GetIsObjectValid(owned) && fixed!=owned))return OBJECT_INVALID;return GetIsObjectValid(fixed)?fixed:owned;}
void main(){object pc=GetPCChatSpeaker();string s=GetPCChatMessage();if(!GetIsPC(pc) || GetPCChatVolume()!=TALKVOLUME_TALK)return;
 string lower=GetStringLowerCase(s);
 if(s=="!companions" || s=="!companion" || GetStringLeft(s,11)=="!companion "){SetPCChatMessage("");int handled=AWCChatControl(pc,s);object target=GetLocalObject(pc,"AWC_CHAT_TARGET");string message=GetLocalString(pc,"AWC_CHAT_TEXT");SPEnd(pc,FALSE);if(!handled && GetIsObjectValid(target)){SetLocalObject(pc,"SP_FOCUS",target);SPAsk(pc,"npc",message);}return;}
 if(lower=="!end" || lower=="bye" || lower=="goodbye" || lower=="farewell"){if(lower=="!end")SetPCChatMessage("");SPEnd(pc);return;}
 if(GetStringLeft(s,4)=="!ai "){SetPCChatMessage("");SPAsk(pc,"npc",GetSubString(s,4,1200));return;}
 if(GetStringLeft(s,4)=="!dm "){SetPCChatMessage("");SPAsk(pc,"dm",GetSubString(s,4,1200));return;}
 if(GetStringLeft(s,6)=="!talk "){SetPCChatMessage("");string rest=GetSubString(s,6,1300);int at=FindSubString(rest," ");
  if(at<1){SendMessageToPC(pc,"Use !talk <alias> <message>. Available aliases: "+SPAliases());return;}
  string tag=SPAlias(GetStringLowerCase(GetStringLeft(rest,at)));if(tag==""){SPEnd(pc,FALSE);SendMessageToPC(pc,"Unknown alias. Available aliases: "+SPAliases());return;}
  if(GetLocalObject(pc,"SP_FOCUS")!=GetObjectByTag(tag))SPEnd(pc,FALSE);
  SetLocalObject(pc,"SP_FOCUS",GetObjectByTag(tag));SPAsk(pc,"npc",GetSubString(rest,at+1,1200));return;}
 if(s=="!ai" || s=="!dm" || s=="!talk"){SetPCChatMessage("");SendMessageToPC(pc,"Use !talk <alias> <message>, !ai <message>, !dm <request>, or !end.");return;}
 if(GetStringLeft(s,1)=="!" || GetStringLeft(s,1)=="/" || GetStringLeft(s,2)=="((")return;
 int colon=FindSubString(s,":");if(colon>0 && colon<=80){object addressed=SPActorAddress(pc,GetStringLowerCase(GetStringLeft(s,colon)));if(!GetIsObjectValid(addressed)){SPEnd(pc,FALSE);return;}
  if(GetLocalObject(pc,"SP_FOCUS")!=addressed)SPEnd(pc,FALSE);
  SetLocalObject(pc,"SP_FOCUS",addressed);SPAsk(pc,"npc",GetSubString(s,colon+1,1200));return;}
 object focus=GetLocalObject(pc,"SP_FOCUS");if(!GetIsObjectValid(focus))return;
 if(GetLocalInt(pc,"AWC_CHAT_ARMED")){SPEnd(pc,FALSE);SetLocalObject(pc,"SP_FOCUS",focus);SetLocalInt(pc,"SP_FOCUS_AT",SPNow());}
 if(!SPNear(pc,focus) || SPNow()-GetLocalInt(pc,"SP_FOCUS_AT")>180){SPEnd(pc,FALSE);return;}
 SPAsk(pc,"npc",s);}
'''
    select=r'''#include "sp_inc"
void main(){object pc=GetPCSpeaker();SPEnd(pc,FALSE);SetLocalObject(pc,"SP_FOCUS",OBJECT_SELF);SetLocalInt(pc,"SP_FOCUS_AT",SPNow());
 SetLocalObject(GetModule(),"SP_CONTROLLER",pc);SendMessageToPC(pc,"AI conversation: "+GetName(OBJECT_SELF)+". Close the menu and speak normally in Talk, or type !ai <message>. Stay nearby. Use !end to finish. NPC menu choices share the same story progress.");}'''
    return inc,chat,select
