// Player-local presentation preferences persist in the saved game.
int AWDGet(object pc,string field){int value=GetLocalInt(pc,"AWD_"+field);int maximum=field=="questions"?1:2;if(value<0 || value>maximum)return 0;return value;}
json AWDSettings(object pc){json out=JsonObject();out=JsonObjectSet(out,"version",JsonInt(1));out=JsonObjectSet(out,"length",JsonInt(AWDGet(pc,"length")));out=JsonObjectSet(out,"voice",JsonInt(AWDGet(pc,"voice")));out=JsonObjectSet(out,"emotes",JsonInt(AWDGet(pc,"emotes")));return JsonObjectSet(out,"questions",JsonInt(AWDGet(pc,"questions")));}
string AWDLengthName(int value){if(value==1)return "Natural";if(value==2)return "Detailed";if(value==3)return "Use AI response settings";return "Brief";}
