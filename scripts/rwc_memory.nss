// Save-local memory of dialogue nodes that actually executed. No conditions are
// evaluated a second time, and no unvisited dialogue branches are published.
string RWToken(string s,string token,string value){
 int at=FindSubString(s,token);int count=0;
 while(at>=0 && count<100){s=GetStringLeft(s,at)+value+GetSubString(s,at+GetStringLength(token),GetStringLength(s));at=FindSubString(s,token);count++;}
 return s;
}
string RWResolve(object pc,string s){
 s=RWToken(s,"<FullName>",GetName(pc));s=RWToken(s,"<FirstName>",GetName(pc));
 s=RWToken(s,"<quarterday>",GetTimeHour()<12?"morning":(GetTimeHour()<18?"afternoon":"evening"));
 // NWN has no getter for custom dialogue tokens. Omit unresolved markup;
 // never fabricate a substituted value or expose a token as world lore.
 int at=FindSubString(s,"<");int count=0;
 while(at>=0 && count<100){string tail=GetSubString(s,at,GetStringLength(s));int end=FindSubString(tail,">");if(end<0)break;
 s=RWToken(s,GetStringLeft(tail,end+1),"");at=FindSubString(s,"<");count++;}
 return s;
}
json RWSeen(object pc,object actor){
 string value=GetLocalString(pc,"RWC_SEEN_"+GetObjectUUID(actor));
 if(value=="")return JsonArray();return JsonParse(value);
}
void RWRemember(object pc,object actor,string id,string label,string text){
 if(!GetIsPC(pc) || !GetIsObjectValid(actor))return;
 text=RWResolve(pc,text);if(text=="")return;
 string key="RWC_HEARD_"+GetObjectUUID(actor);
 string line=label+": "+text;
 SetLocalString(pc,key,GetStringRight(GetLocalString(pc,key)+"\n"+line,12000));
 SetLocalString(pc,"RWC_SHARED",GetStringRight(GetLocalString(pc,"RWC_SHARED")+"\n[With "+GetName(actor)+"] "+line,12000));
 json seen=RWSeen(pc,actor);int i=0;
 while(i<JsonGetLength(seen)){if(JsonGetString(JsonArrayGet(seen,i))==id){seen=JsonArrayDel(seen,i);break;}i++;}
 seen=JsonArrayInsert(seen,JsonString(id));if(JsonGetLength(seen)>1024)seen=JsonArrayDel(seen,0);
 SetLocalString(pc,"RWC_SEEN_"+GetObjectUUID(actor),JsonDump(seen));
}
