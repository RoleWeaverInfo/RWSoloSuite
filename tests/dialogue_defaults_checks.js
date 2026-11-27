// Exercise the real preference helpers and UI event handler with save-local
// engine mocks. NWScript compilation is covered by the native companion tests.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
function translate(source){
  return source.replace(/^#include.*$/gm,'').replace(/\/\/[^\n]*/g,'')
    .replace(/\b(?:int|void|string|json) (\w+)\(([^)]*)\)/g,(_,name,args)=>
      'function '+name+'('+args.replace(/\b(?:object|string|int) /g,'')+')')
    .replace(/\b(?:object|int|string|json) ([a-zA-Z_]\w*)/g,'let $1');
}
const prefs=fs.readFileSync(path.join(root,'authoring_scripts/aw_dlg_pref.nss'),'utf8');
const ui=fs.readFileSync(path.join(root,'authoring_scripts/aw_dlg_ui.nss'),'utf8');
const code=translate(prefs+'\n'+ui.slice(ui.indexOf('void AWDEvent()')));
function game(saved={}){
  const locals={AWD_TOKEN:10,AWD_GEN:1,AWD_SESSION:'session',...saved};
  const event={type:'click',window:10,id:''};
  const api={TRUE:1,FALSE:0,
    GetLocalInt:(pc,key)=>locals[key]||0,GetLocalString:(pc,key)=>pc==='module'?'session':locals[key]||'',
    SetLocalInt:(pc,key,value)=>{locals[key]=value;},DeleteLocalInt:(pc,key)=>{delete locals[key];},
    GetModule:()=>'module',GetIsPC:pc=>pc==='player',IntToString:String,
    JsonObject:()=>({}),JsonInt:value=>value,JsonObjectSet:(obj,key,value)=>({...obj,[key]:value}),
    NuiGetEventPlayer:()=>'player',NuiGetEventWindow:()=>event.window,
    NuiGetEventType:()=>event.type,NuiGetEventElement:()=>event.id,
    AWDOpen:()=>{locals.AWD_GEN++;},AWDClose:()=>{delete locals.AWD_TOKEN;}};
  vm.createContext(api);vm.runInContext(code,api);
  return {locals,event,api,settings:()=>JSON.parse(JSON.stringify(api.AWDSettings('player'))),
    click:field=>{event.id=field+'_'+locals.AWD_GEN;api.AWDEvent();}};
}
const defaults={version:1,length:1,voice:1,emotes:1,questions:1};
const fresh=game();assert.deepEqual(fresh.settings(),defaults);
assert.equal(fresh.api.AWDLengthName(1),'Normal');

// Cycling to each zero-valued choice must survive a save/reload and must not
// be confused with an unset local (which also reads as zero in NWScript).
for(const field of ['length','voice','emotes','questions']){
  const x=game();x.click(field);
  if(field!=='questions')x.click(field);
  assert.equal(x.settings()[field],0);assert.equal(x.locals['AWD_SET_'+field],1);
  const loaded=game(JSON.parse(JSON.stringify(x.locals)));
  assert.equal(loaded.settings()[field],0);loaded.click(field);assert.equal(loaded.settings()[field],1);
}
const customized=game();
for(const field of ['length','voice','emotes','questions'])customized.api.AWDSet('player',field,0);
customized.click('reset');assert.deepEqual(customized.settings(),defaults);
assert.deepEqual(game(customized.locals).settings(),defaults);
// Retain valid nonzero preferences from older scripts; invalid values fall back.
assert.equal(game({AWD_length:2,AWD_voice:2}).settings().length,2);
assert.equal(game({AWD_length:-1,AWD_voice:99,AWD_questions:2}).settings().voice,1);
const stale=game();stale.event.id='length_0';stale.api.AWDEvent();assert.deepEqual(stale.settings(),defaults);
stale.event.window=999;stale.click('length');assert.deepEqual(stale.settings(),defaults);
console.log('AI defaults, reset, explicit zero choices, save/load and stale UI checks passed.');
