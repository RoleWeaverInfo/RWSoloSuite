void main() {
    object pc=GetPCSpeaker();SetLocalObject(pc,"SP_FOCUS",OBJECT_SELF);
    SetLocalObject(GetModule(),"SP_CONTROLLER",pc);
    SendMessageToPC(pc,"AI conversation: "+GetName(OBJECT_SELF)+". Type !ai followed by your message in the chat bar. Stay nearby while the reply arrives. Authored conversation choices remain available.");
}
