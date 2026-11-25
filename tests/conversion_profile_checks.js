const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={window:{},console};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('web/conversion.js','utf8'),ctx);
function host(){
  const els={};
  const element=()=>({innerHTML:'',textContent:'',disabled:false,classList:{toggle(){}},querySelectorAll(selector){
    if(selector!=='[data-merchant-field]')return [];
    return this.merchantFields??=Array.from(this.innerHTML.matchAll(/<input[^>]*data-merchant-field="([^"]+)"[^>]*>/g),m=>({dataset:{merchantField:m[1]},checked:m[0].includes('checked'),disabled:false}));
  }});
  let html='';
  return {els,isConnected:true,get innerHTML(){return html;},set innerHTML(value){html=value;for(const match of value.matchAll(/class="([^"]+)"/g))for(const name of match[1].split(' '))els['.'+name]??=element();},querySelector(s){return els[s]??=element();},querySelectorAll(){return Object.values(els);}};
}
const npc={name:'Keeper',alias:'keeper',native_tag:'keeper',native_resref:'keeper',ai_enabled:true,
  role:'Keeper',personality:'Calm',background:'Before generation',motivation:'Help',knowledge:'Public',
  behavior:{communication:'speech'},companion:{},profile_origin:'Authored',profile_sources:['<unsafe>'],native_lines:[],
  merchant:{enabled:true,haggle_enabled:true},native_store:{detected:true,tags:['<store>'],scripts:['trade']}};
const project={title:'Copy',module_name:'copy',summary:'The setting',companions:{enabled:true},npcs:[npc]};
let saved={project:structuredClone(project),dependency_folder:'',build:null},requests=[],finish=0;
async function api(path,body){
  requests.push([path,structuredClone(body)]);
  if(path.endsWith('/conversion-plan'))return structuredClone(saved);
  if(path.endsWith('/profiles')){saved=structuredClone(saved);saved.project.npcs[0].background='Generated background';return {status:'profiling',message:'Generating'};}
  return {saved:true};
}
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const h=host();ctx.window.ModuleConversion.mount(h,api,'analysis',false,async()=>{finish++;});await tick();
  assert(h.innerHTML.includes('Generate detailed AI profiles'));
  assert(h.els['.conversion-npc'].innerHTML.includes('Personal background'));
  assert(h.els['.conversion-npc'].innerHTML.includes('&lt;unsafe&gt;'));
  assert(h.innerHTML.includes('1 merchant profiles detected'));
  assert(h.els['.conversion-npc'].innerHTML.includes('&lt;store&gt;'));
  const merchantFields=h.els['.conversion-npc'].querySelectorAll('[data-merchant-field]');
  assert.equal(merchantFields.length,2);assert(merchantFields.every(el=>el.checked));
  merchantFields[0].checked=false;merchantFields[0].onchange();
  h.els['.conversion-summary'].oninput({target:{value:'Edited setting'}});
  await h.els['.conversion-save'].onclick();
  assert.equal(requests.find(([url])=>url.endsWith('/conversion-save'))[1].project.summary,'Edited setting');
  assert.equal(requests.find(([url])=>url.endsWith('/conversion-save'))[1].project.npcs[0].merchant.enabled,false);
  await h.els['.conversion-profiles'].onclick();assert.equal(finish,1);
  const refreshed=host();ctx.window.ModuleConversion.mount(refreshed,api,'analysis',false,async()=>{});await tick();
  assert(refreshed.els['.conversion-npc'].innerHTML.includes('Generated background')); // Old draft must not mask result.
  const busy=host();ctx.window.ModuleConversion.mount(busy,api,'analysis',true,async()=>{});await tick();
  assert(busy.els['.conversion-profiles'].disabled);
  assert(busy.els['.conversion-npc'].querySelectorAll('[data-merchant-field]').every(el=>el.disabled));
  let mounted=[],destroyed=0;
  ctx.window.MissionEditor={mount(host,options){mounted.push(options.getProject().summary);return {destroy(){destroyed++;},setDisabled(){}};}};
  saved.project.mission_editor={version:1,storyline:'',quests:[],links:[]};
  const shared=host();const controller=ctx.window.ModuleConversion.mount(shared,api,'mission-analysis',false,async()=>{});await tick();
  assert.equal(mounted.length,1);
  shared.els['.conversion-show-profiles'].onclick();assert.equal(destroyed,1);
  shared.els['.conversion-summary'].oninput({target:{value:'Changed in profiles'}});
  shared.els['.conversion-show-missions'].onclick();assert.equal(mounted.at(-1),'Changed in profiles');
  await shared.els['.conversion-save'].onclick();
  assert(requests.at(-1)[1].project.mission_editor);
  controller.destroy();assert.equal(destroyed,2);
  saved.profile_generation={completed:6,total:13,remaining_requests:2,resumable:true};
  const partial=host();const partialController=ctx.window.ModuleConversion.mount(partial,api,'partial',false,async()=>{});await tick();
  assert(partial.innerHTML.includes('Resume detailed AI profiles'));assert(partial.innerHTML.includes('2 AI requests remaining'));
  partialController.setBusy(true);assert(partial.els['.conversion-profiles'].disabled);
  partialController.setBusy(false);assert(!partial.els['.conversion-profiles'].disabled);
  saved.profile_generation={completed:13,total:13,remaining_requests:0};await partialController.refresh();
  assert(partial.innerHTML.includes('All detailed profiles saved'));assert(partial.els['.conversion-profiles'].disabled);
  partialController.setBusy(false);assert(partial.els['.conversion-profiles'].disabled);
  ctx.confirm=()=>false;const count=requests.length;await partial.els['.conversion-profiles-restart'].onclick();assert.equal(requests.length,count);
  ctx.confirm=()=>true;await partial.els['.conversion-profiles-restart'].onclick();assert.equal(requests.at(-1)[1].restart,true);
  partialController.destroy();
  console.log('Conversion profiles: edited setting, escaped evidence, merchant opt-out, generation dispatch, result refresh and busy controls passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
