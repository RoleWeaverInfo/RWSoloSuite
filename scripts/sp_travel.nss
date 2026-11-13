void main() {
    object pc=GetLastUsedBy();object mark=GetObjectByTag(GetLocalString(OBJECT_SELF,"SP_TARGET"));
    if(!GetIsObjectValid(mark) || !GetIsPC(pc)) return;
    object m=GetFirstFactionMember(pc,FALSE);
    while(GetIsObjectValid(m)) {if(GetArea(m)==GetArea(pc) && !GetIsDead(m)) AssignCommand(m,JumpToLocation(GetLocation(mark)));m=GetNextFactionMember(pc,FALSE);}
}
