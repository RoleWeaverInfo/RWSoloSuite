// Persistent storage belongs to the owner, never to an expiring associate body.
int AWCPersistentOwned(object pc,object pack){return GetIsObjectValid(pack) && GetObjectType(pack)==OBJECT_TYPE_STORE && GetResRef(pack)=="aw_cp_storage" && GetLocalObject(pack,"AWP_OWNER")==pc;}
object AWCPersistentPack(object pc,string identity,string label,int create=FALSE){
 int count=GetLocalInt(pc,"AWP_COUNT");int i=0;while(i<count){if(GetLocalString(pc,"AWP_ID_"+IntToString(i))==identity){object pack=GetLocalObject(pc,"AWP_OBJ_"+IntToString(i));if(AWCPersistentOwned(pc,pack))return pack;return OBJECT_INVALID;}i++;}
 if(!create || count>=64)return OBJECT_INVALID;
 object pack=CreateObject(OBJECT_TYPE_STORE,"aw_cp_storage",GetLocation(pc));if(!GetIsObjectValid(pack) || !GetHasInventory(pack))return OBJECT_INVALID;
 SetName(pack,label+"'s pack");SetLocalObject(pack,"AWP_OWNER",pc);SetLocalString(pack,"AWC_PACK_ID",identity);
 SetLocalString(pc,"AWP_ID_"+IntToString(count),identity);SetLocalObject(pc,"AWP_OBJ_"+IntToString(count),pack);SetLocalInt(pc,"AWP_COUNT",count+1);return pack;}

