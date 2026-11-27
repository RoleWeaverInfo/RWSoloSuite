// Execute the actual, small NWScript handler with mocked engine events. Only
// declarations are translated; the production branches and calls run unchanged.
// Native compiler integration tests separately check NWScript compatibility.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
function translate(source){
  return source.replace(/^#include.*$/gm,'').replace(/\/\/[^\n]*/g,'')
    .replace(/\b(?:void|string) (main|AWCVersion)\(([^)]*)\)/g,(_,name,args)=>
      'function '+name+'('+args.replace(/\bobject /g,'')+')')
    .replace(/\b(?:object|int|string|json) ([a-zA-Z_]\w*)/g,'let $1');
}
const handler=translate(fs.readFileSync(path.join(root,'authoring_scripts/aw_cp_dialog.nss'),'utf8'));
const core=fs.readFileSync(path.join(root,'authoring_scripts/aw_companion.nss'),'utf8');
const version=translate(core.match(/^string AWCVersion\([^\n]+/m)[0]);

function scene(options={}){
  const s={pattern:20600,speaker:'player',master:'player',kind:'familiar',ready:true,
    command:-5,commandable:1,modes:256,epoch:7,preferences:3,instance:'body',
    base:'original_dialogue',calls:[],menus:[],...options};
  function getMaster(body='body'){return body==='body'?s.master:body==='henchman'?'player':null;}
  const api={OBJECT_SELF:'body',FALSE:0,TRUE:1,
    GetMaster:getMaster,GetIsObjectValid:o=>o!==null&&o!==undefined,
    GetIsPC:o=>o==='player'||o==='stranger',GetLastSpeaker:()=>s.speaker,
    GetListenPatternNumber:()=>s.pattern,GetLastAssociateCommand:()=>s.command,
    GetCommandable:()=>s.commandable,
    GetLocalInt:(body,key)=>key==='AWC_CONTROL_EPOCH'?s.epoch:key==='NW_ASSOCIATE_MASTER'?s.modes:0,
    SetLocalInt:(body,key,value)=>{assert.equal(body,'body');assert.equal(key,'AWC_CONTROL_EPOCH');s.epoch=value;},
    GetLocalString:(body,key)=>{assert.equal(key,'AWC_BASE_DIALOG');return s.base;},
    AWCKind:()=>s.kind,AWCReady:()=>s.ready,AWCObserve:()=>true,
    AWCRecord:()=>({epoch:s.preferences}),AWCIdentity:()=>s.instance,
    AWCOwner:()=>s.master==='henchman'?'player':s.master,
    AWInt:(record,key)=>record[key],IntToString:String,
    GetObjectUUID:o=>o==='body'?s.instance:o,
    BeginConversation:(dialogue,owner)=>s.menus.push([dialogue,owner]),
    ExecuteScript:(script,body)=>{
      assert.equal(script,'original_dialogue');assert.equal(body,'body');
      s.calls.push({pattern:s.pattern,speaker:s.speaker});
      if(s.native)s.native(s);
    }};
  vm.createContext(api);vm.runInContext(handler+'\n'+version,api);
  return {s,run:()=>api.main(),stamp:()=>api.AWCVersion('player','body')};
}

// Catch-all/custom positive IDs must not reject the very line being answered.
// No DMFI-specific exemption: any module may choose any nonnegative ID.
for(const pattern of [0,101,777,20600,31000]){
  const x=scene({pattern});const pending=x.stamp();x.run();
  assert.equal(x.stamp(),pending,'ordinary speech must retain its pending reply');
  assert.deepEqual(x.s.calls,[{pattern,speaker:'player'}]);
  assert.equal(x.s.menus.length,0);
}

// Every native associate command, including an unchanged repeated order,
// still supersedes pending dialogue/tasks. They are not swallowed by Studio.
for(let pattern=-2;pattern>=-23;pattern--){
  const x=scene({pattern,command:pattern});const pending=x.stamp();x.run();
  assert.notEqual(x.stamp(),pending,'native orders must invalidate pending replies');
  assert.equal(x.s.epoch,8);assert.equal(x.s.calls.length,1);
}

// Custom textual orders remain supported by the module's original handler.
for(const change of [s=>s.modes=512,s=>s.command=-2,s=>s.commandable=0,s=>s.master='stranger']){
  const x=scene({pattern:400,native:change});const pending=x.stamp();x.run();
  assert.notEqual(x.stamp(),pending);assert.equal(x.s.epoch,8);assert.equal(x.s.calls.length,1);
}

// Follow chains of masters for summons owned by recruited party members.
for(const speaker of ['player','henchman']){
  const speech=scene({master:'henchman',speaker});const pending=speech.stamp();speech.run();
  assert.equal(speech.stamp(),pending);assert.equal(speech.s.calls.length,1);
  const order=scene({master:'henchman',speaker,pattern:-2});order.run();assert.equal(order.s.epoch,8);
}
for(const speaker of ['stranger',null]){
  const x=scene({speaker,pattern:-2});x.run();assert.equal(x.s.epoch,7);assert.equal(x.s.calls.length,1);
}
const unowned=scene({speaker:null,master:null,pattern:-2});unowned.run();assert.equal(unowned.s.epoch,7);

// Click-to-talk still opens Studio's familiar/summon menu; recruited party
// dialogue still reaches the original recruitment/quest handler exactly once.
for(const kind of ['familiar','summon']){
  const x=scene({pattern:-1,kind});x.run();
  assert.deepEqual(x.s.menus,[['aw_cp_native','player']]);assert.equal(x.s.calls.length,0);
}
const party=scene({pattern:-1,kind:'party'});party.run();assert.equal(party.s.calls.length,1);assert.equal(party.s.menus.length,0);
for(const base of ['','aw_cp_dialog']){
  const x=scene({base});x.run();assert.equal(x.s.calls.length,0);assert.equal(x.s.epoch,7);
}

// Ownership, preferences, body replacement, possession/unavailability and
// actual native command changes still fail the existing reply-version guard.
for(const change of [s=>s.master='stranger',s=>s.preferences++,s=>s.instance='new-body',s=>s.ready=false,s=>s.command=-7]){
  const x=scene();const pending=x.stamp();change(x.s);assert.notEqual(x.stamp(),pending);
}
console.log('Companion speech, native/custom orders, ownership and dialogue routing checks passed.');
