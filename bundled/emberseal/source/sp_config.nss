string SPProject(){return "emberseal_demo";}
string SPBuild(){return "11b6a6549ebb36e7b5d1";}
json SPEncounters(){return JsonArray();}
int SPIsNPC(string tag){return tag=="elowen" || tag=="merrow" || tag=="lysandra" || tag=="hale" || tag=="nessa" || tag=="mara" || tag=="bram" || tag=="tavin" || tag=="alia" || tag=="pella" || tag=="osric" || tag=="dain" || tag=="jory" || tag=="tomas" || tag=="rowan";}
string SPAlias(string alias){if(alias=="elowen")return "elowen";if(alias=="merrow")return "merrow";if(alias=="lysandra")return "lysandra";if(alias=="hale")return "hale";if(alias=="nessa")return "nessa";if(alias=="mara")return "mara";if(alias=="bram")return "bram";if(alias=="tavin")return "tavin";if(alias=="alia")return "alia";if(alias=="pella")return "pella";if(alias=="osric")return "osric";if(alias=="dain")return "dain";if(alias=="jory")return "jory";if(alias=="tomas")return "tomas";if(alias=="rowan")return "rowan";return "";}
string SPAliases(){return "elowen, merrow, lysandra, hale, nessa, mara, bram, tavin, alia, pella, osric, dain, jory, tomas, rowan";}
