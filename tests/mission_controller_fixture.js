// Run by test_mission_editor.py with its authoring fixture on stdin.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
// Minimal event surface, like the existing dashboard tests. Graph geometry is
// checked separately; these tests exercise real field/action handlers and history.
class Element {
  constructor(attrs={}){this.attrs=attrs;this.dataset={};this.options=[];this.isConnected=true;this.value=attrs.value||'';this.type=attrs.type||'';this.tagName=(attrs.tag||'div').toUpperCase();this.children=[];
    for(const [key,value] of Object.entries(attrs))if(key.startsWith('data-'))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=value;
  }
  set innerHTML(value){this.html=value;this.children=[];for(const tag of value.matchAll(/<([a-z]+)\b([^>]*)>/g)){
    const attrs={tag:tag[1]};for(const match of tag[2].matchAll(/([\w-]+)="([^"]*)"/g))attrs[match[1]]=match[2];this.children.push(new Element(attrs));
  }}
  get innerHTML(){return this.html||'';}
  querySelectorAll(selector){if(selector.startsWith('.'))return this.children.filter(el=>(el.attrs.class||'').split(' ').includes(selector.slice(1)));
    const match=selector.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);return this.children.filter(el=>match&&Object.hasOwn(el.attrs,match[1])&&(match[2]===undefined||el.attrs[match[1]]===match[2]));
  }
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
let current=JSON.parse(fs.readFileSync(0,'utf8')),changes=0,confirmations=0,approve=false,notices=[],graphOptions;
const window={confirm:()=>{confirmations++;return approve;},MissionGraph:{mount:(host,options)=>{graphOptions=options;return {setGraph(){},focus(){},fit(){},zoom(){},destroy(){}};}}};
const ctx={window};vm.createContext(ctx);
for(const name of ['mission-model','mission-editor'])vm.runInContext(fs.readFileSync('web/'+name+'.js','utf8'),ctx);
let host=new Element();
const mount=()=>window.MissionEditor.mount(host,{getProject:()=>current,onChange:()=>changes++,onNotice:t=>notices.push(t),onCheck:async()=>({errors:[],warnings:[]}),onGenerate:()=>{}});
let controller=mount();
const action=async name=>{const b=host.querySelector(`[data-mission-action="${name}"]`);assert(b,`Missing button ${name}`);await b.onclick();};
const edit=(field,value)=>{const c=host.querySelector(`[data-mission-field="${field}"]`);assert(c,`Missing field ${field}`);c.value=value;c.oninput();c.onblur();};
(async()=>{
  edit('quest.name','Edited mission');assert.equal(current.quests[0].name,'Edited mission');
  const old=current;current=JSON.parse(JSON.stringify(current)); // Server normalization replaces the project on save.
  edit('quest.gold','175');assert.equal(current.quests[0].gold,175);assert.notEqual(old.quests[0].gold,175);
  await action('undo');assert.equal(current.quests[0].gold,old.quests[0].gold);assert.equal(current.quests[0].name,'Edited mission');
  await action('redo');assert.equal(current.quests[0].gold,175);
  await action('removeQuest');assert.equal(confirmations,0);assert(notices.some(n=>n.includes('references first')));
  await action('addQuest');const newId=current.quests.at(-1).id;
  await action('addDecision');assert.equal(current.quests.at(-1).steps[0].kind,'choice');
  await action('removeStep');assert.equal(confirmations,1);assert.equal(current.quests.at(-1).steps.length,1,'Cancel must preserve objectives');
  approve=true;await action('removeStep');assert.equal(current.quests.at(-1).steps.length,0);
  await action('undo');assert.equal(current.quests.at(-1).steps.length,1);
  // Return to mission settings after undo; delete and restore the whole mission.
  await action('overview');await action('removeQuest');assert(!current.quests.some(q=>q.id===newId));
  await action('undo');assert(current.quests.some(q=>q.id===newId));
  const before=JSON.stringify(current),count=changes;
  await action('fit');await action('focus');await action('zoomIn');assert.equal(JSON.stringify(current),before);assert.equal(changes,count);
  controller.destroy();host=new Element();controller=mount();
  assert(!host.querySelector('[data-mission-action="undo"]').disabled,'Navigation should retain history');
  controller.destroy();current.quests[0].name='Applied external AI proposal';host=new Element();controller=mount();
  assert(host.querySelector('[data-mission-action="undo"]').disabled,'New proposals must not inherit stale mission undo history');
  controller.destroy();process.stdout.write('Mission controller events passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
