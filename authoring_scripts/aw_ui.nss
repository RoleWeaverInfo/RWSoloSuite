// Small native NUI JSON constructors. Only the engine's nwscript header is required.
json AWUIElement(string kind){json out=JsonObject();out=JsonObjectSet(out,"type",JsonString(kind));out=JsonObjectSet(out,"label",JsonNull());return JsonObjectSet(out,"value",JsonNull());}
json AWUILabel(json value,json horizontal,json vertical){json out=AWUIElement("label");out=JsonObjectSet(out,"value",value);out=JsonObjectSet(out,"text_halign",horizontal);return JsonObjectSet(out,"text_valign",vertical);}
json AWUIButton(json label){return JsonObjectSet(AWUIElement("button"),"label",label);}
json AWUICol(json children){return JsonObjectSet(AWUIElement("col"),"children",children);}
json AWUIRow(json children){return JsonObjectSet(AWUIElement("row"),"children",children);}
json AWUIHeight(json element,float height){return JsonObjectSet(element,"height",JsonFloat(height));}
json AWUIEnabled(json element,json enabled){return JsonObjectSet(element,"enabled",enabled);}
json AWUIId(json element,string id){return JsonObjectSet(element,"id",JsonString(id));}
json AWUIRect(float x,float y,float width,float height){json out=JsonObject();out=JsonObjectSet(out,"x",JsonFloat(x));out=JsonObjectSet(out,"y",JsonFloat(y));out=JsonObjectSet(out,"w",JsonFloat(width));return JsonObjectSet(out,"h",JsonFloat(height));}
json AWUIWindow(json root,json title,json geometry,json resizable,json collapsed,json closable,json transparent,json border){json out=JsonObject();out=JsonObjectSet(out,"version",JsonInt(1));out=JsonObjectSet(out,"root",root);out=JsonObjectSet(out,"title",title);out=JsonObjectSet(out,"geometry",geometry);out=JsonObjectSet(out,"resizable",resizable);out=JsonObjectSet(out,"collapsed",collapsed);out=JsonObjectSet(out,"closable",closable);out=JsonObjectSet(out,"transparent",transparent);out=JsonObjectSet(out,"border",border);return JsonObjectSet(out,"accepts_input",JsonBool(TRUE));}

// Match the installed nw_inc_nui constructors; scrolling contains oversized content.
json AWUIWidth(json element,float width){return JsonObjectSet(element,"width",JsonFloat(width));}
json AWUIText(string text){json out=AWUIElement("text");out=JsonObjectSet(out,"value",JsonString(text));out=JsonObjectSet(out,"border",JsonBool(FALSE));return JsonObjectSet(out,"scrollbars",JsonInt(0));}
json AWUIScroll(json child){json out=AWUIElement("group");out=JsonObjectSet(out,"children",JsonArrayInsert(JsonArray(),child));out=JsonObjectSet(out,"border",JsonBool(FALSE));return JsonObjectSet(out,"scrollbars",JsonInt(4));}
json AWUIStack(json children,float width){json rows=JsonArray();int i=0;while(i<JsonGetLength(children)){json child=JsonArrayGet(children,i);float height=JsonGetFloat(JsonObjectGet(child,"height"));if(height<1.0)height=36.0;
 if(JsonGetString(JsonObjectGet(child,"type"))!="row"){child=AWUIWidth(child,width);child=AWUIRow(JsonArrayInsert(JsonArray(),child));}
 rows=JsonArrayInsert(rows,AWUIWidth(AWUIHeight(child,height),width));i++;}return AWUICol(rows);}
