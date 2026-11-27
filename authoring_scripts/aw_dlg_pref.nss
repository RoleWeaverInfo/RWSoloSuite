// Player-local presentation preferences persist in the saved game.
// Unset integer locals also read as zero. Track explicit choices so Brief,
// Plain, Off and Only when needed remain selected after saving and loading.
int AWDGet(object pc,string field){int value=GetLocalInt(pc,"AWD_"+field);int maximum=field=="questions"?1:2;if(value<0 || value>maximum || (value==0 && !GetLocalInt(pc,"AWD_SET_"+field)))return 1;return value;}
void AWDSet(object pc,string field,int value){SetLocalInt(pc,"AWD_"+field,value);SetLocalInt(pc,"AWD_SET_"+field,TRUE);}
void AWDReset(object pc,string field){DeleteLocalInt(pc,"AWD_"+field);DeleteLocalInt(pc,"AWD_SET_"+field);}
json AWDSettings(object pc){json out=JsonObject();out=JsonObjectSet(out,"version",JsonInt(1));out=JsonObjectSet(out,"length",JsonInt(AWDGet(pc,"length")));out=JsonObjectSet(out,"voice",JsonInt(AWDGet(pc,"voice")));out=JsonObjectSet(out,"emotes",JsonInt(AWDGet(pc,"emotes")));return JsonObjectSet(out,"questions",JsonInt(AWDGet(pc,"questions")));}
string AWDLengthName(int value){if(value==1)return "Normal";if(value==2)return "Detailed";if(value==3)return "Use AI response settings";return "Brief";}
