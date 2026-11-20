// The creature's original Conversation resource has not been changed.
void OpenOriginal(object pc){if(GetIsObjectValid(pc) && GetArea(pc)==GetArea(OBJECT_SELF))BeginConversation("",pc);}
void main(){DelayCommand(0.3,OpenOriginal(GetPCSpeaker()));}

