#include "sp_inc"
string SPAddress(string name){if(name=="alia")return "alia";if(name=="arcanist")return "lysandra";if(name=="arcanist lysandra vale")return "lysandra";if(name=="bram")return "bram";if(name=="bram ironstock")return "bram";if(name=="captain")return "dain";if(name=="captain dain rusk")return "dain";if(name=="dain")return "dain";if(name=="elowen")return "elowen";if(name=="guard")return "nessa";if(name=="guard nessa pike")return "nessa";if(name=="hale")return "hale";if(name=="jory")return "jory";if(name=="lysandra")return "lysandra";if(name=="mara")return "mara";if(name=="mara reed")return "mara";if(name=="merrow")return "merrow";if(name=="nessa")return "nessa";if(name=="osric")return "osric";if(name=="osric moss")return "osric";if(name=="pella")return "pella";if(name=="pella rook")return "pella";if(name=="queen")return "elowen";if(name=="queen elowen vale")return "elowen";if(name=="rowan")return "rowan";if(name=="scout")return "rowan";if(name=="scout rowan fen")return "rowan";if(name=="sergeant")return "hale";if(name=="sergeant hale ward")return "hale";if(name=="sister")return "alia";if(name=="sister alia dawn")return "alia";if(name=="soldier")return "jory";if(name=="soldier jory fen")return "jory";if(name=="steward")return "merrow";if(name=="steward merrow voss")return "merrow";if(name=="tavin")return "tavin";if(name=="tavin quill")return "tavin";if(name=="tomas")return "tomas";if(name=="tomas reed")return "tomas";return "";}
object SPActorAddress(object pc,string name){string tag=SPAddress(name);object fixed=tag==""?OBJECT_INVALID:GetObjectByTag(tag);object owned=AWCFind(pc,name);if(GetLocalInt(pc,"AWC_AMBIGUOUS") || (GetIsObjectValid(fixed) && GetIsObjectValid(owned) && fixed!=owned))return OBJECT_INVALID;return GetIsObjectValid(fixed)?fixed:owned;}
void main(){object pc=GetPCChatSpeaker();string s=GetPCChatMessage();if(!GetIsPC(pc) || GetPCChatVolume()!=TALKVOLUME_TALK)return;
 string lower=GetStringLowerCase(s);
 if(lower=="!studio"){SetPCChatMessage("");SPServiceCheck(pc,TRUE);return;}
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
 int colon=FindSubString(s,":");int explicitAddress=colon>=0;if(colon<0)colon=FindSubString(s,",");if(colon<0)colon=FindSubString(s,".");if(colon>0 && colon<=80){object addressed=SPActorAddress(pc,GetStringLowerCase(GetStringLeft(s,colon)));if(!GetIsObjectValid(addressed) && explicitAddress){SPEnd(pc,FALSE);return;}if(GetIsObjectValid(addressed)){
  if(GetLocalObject(pc,"SP_FOCUS")!=addressed)SPEnd(pc,FALSE);
  SetLocalObject(pc,"SP_FOCUS",addressed);string addressedText=GetSubString(s,colon+1,1200);while(GetStringLeft(addressedText,1)==" ")addressedText=GetSubString(addressedText,1,1200);SPAsk(pc,"npc",addressedText);return;}}
 object focus=GetLocalObject(pc,"SP_FOCUS");if(!GetIsObjectValid(focus))return;
 if(GetLocalInt(pc,"AWC_CHAT_ARMED")){SPEnd(pc,FALSE);SetLocalObject(pc,"SP_FOCUS",focus);SetLocalInt(pc,"SP_FOCUS_AT",SPNow());}
 if(!SPNear(pc,focus) || SPNow()-GetLocalInt(pc,"SP_FOCUS_AT")>180){SPEnd(pc,FALSE);return;}
 SPAsk(pc,"npc",s);}

